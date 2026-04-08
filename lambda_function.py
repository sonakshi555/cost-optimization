import boto3
import os

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    sns = boto3.client('sns')

    deleted_snapshots = []  
    skipped_snapshots = []

    # Get all EBS snapshots
    response = ec2.describe_snapshots(OwnerIds=['self'])

    # Get all active EC2 instance IDs
    instances_response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    active_instance_ids = set()

    for reservation in instances_response['Reservations']:
        for instance in reservation['Instances']:
            active_instance_ids.add(instance['InstanceId'])

    for snapshot in response['Snapshots']:
        snapshot_id = snapshot['SnapshotId']
        volume_id = snapshot.get('VolumeId')

        # Tag checking for "retain=true" to skip deletion
        tags = {t['Key']: t['Value'] for t in snapshot.get('Tags', [])}
        if tags.get('retain', '').lower() == 'true':
            print(f"Skipping snapshot {snapshot_id} — marked as retain=true")
            skipped_snapshots.append(snapshot_id) 
            continue
        # if no volume ID is associated with the snapshot, it can be safely deleted
        if not volume_id:
            ec2.delete_snapshot(SnapshotId=snapshot_id)
            deleted_snapshots.append(snapshot_id) 
            print(f"Deleted EBS snapshot {snapshot_id} as it was not attached to any volume.")
        else:
            try:
                # Check if the associated volume is attached to any active instance
                volume_response = ec2.describe_volumes(VolumeIds=[volume_id])
                if not volume_response['Volumes'][0]['Attachments']:
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                    deleted_snapshots.append(snapshot_id)  
                    print(f"Deleted EBS snapshot {snapshot_id} as it was taken from a volume not attached to any running instance.")
            except ec2.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidVolume.NotFound':
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                    deleted_snapshots.append(snapshot_id) 
                    print(f"Deleted EBS snapshot {snapshot_id} as its associated volume was not found.")

    # Sending SNS summary email, after all snapshots deleted or skipped (when the tag "retain" is present)
    if deleted_snapshots or skipped_snapshots:
        message = f"""
AWS Snapshot Cleanup Report
============================
 Deleted Snapshots ({len(deleted_snapshots)}):
{chr(10).join(deleted_snapshots) if deleted_snapshots else 'None'}

 Skipped Snapshots - retain=true ({len(skipped_snapshots)}):
{chr(10).join(skipped_snapshots) if skipped_snapshots else 'None'}

Total Snapshots Deleted: {len(deleted_snapshots)}
Total Snapshots Skipped: {len(skipped_snapshots)}
        """

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='AWS Snapshot Cleanup Report',
            Message=message
        )
        print("SNS alert sent successfully")