# 🧹 AWS EBS Snapshot Cleanup — Cost Optimization

An automated AWS Lambda function that identifies and deletes orphaned EBS snapshots to reduce unnecessary AWS storage costs.

---

## 📌 Problem Statement

When an EC2 instance is terminated, its associated EBS snapshots are **not automatically deleted**. These orphaned snapshots accumulate silently over time and result in unnecessary AWS billing.

This project automates the cleanup process using a serverless Lambda function triggered by CloudWatch Events.

---

## 🏗️ Architecture

```
CloudWatch Events (Scheduled Trigger)
            ↓
      Lambda Function
            ↓
  Describe all EBS Snapshots
            ↓
  Check retain=true tag → Skip if protected
            ↓
  Check if Volume exists (DescribeVolumes)
            ↓
  Check if Volume attached to Instance (DescribeInstances)
            ↓
  Delete Orphaned Snapshot (DeleteSnapshot)
            ↓
  SNS Email Notification (Cleanup Report)
```

![alt text](<Screenshot 2026-04-08 110437.png>)

---
![alt text](<Screenshot 2026-04-08 110451-1.png>)
## ✅ Features

- 🗑️ **Auto-deletes** orphaned EBS snapshots not linked to any active EC2 instance or volume
- 🏷️ **Tag-based exclusion** — snapshots tagged `retain=true` are skipped and protected
- 📅 **Scheduled trigger** via CloudWatch Events (runs every 7 days)
- 📧 **SNS email alert** — sends a cleanup summary report after every run
- 🔐 **IAM Least Privilege** — only 5 permissions granted to the Lambda role

---

## 🔐 IAM Permissions (Least Privilege)

The Lambda execution role is scoped to only the required permissions:

```json
{
  "Effect": "Allow",
  "Action": [
    "ec2:DescribeSnapshots",
    "ec2:DeleteSnapshot",
    "ec2:DescribeInstances",
    "ec2:DescribeVolumes",
    "sns:Publish"
  ],
  "Resource": "*"
}
```
![alt text](<Screenshot 2026-04-08 110538.png>)
---

## ⚙️ Environment Variables

| Key | Description |
|---|---|
| `SNS_TOPIC_ARN` | ARN of the SNS topic for email alerts |

---

## 📅 CloudWatch Trigger

- **Type:** EventBridge (CloudWatch Events) Scheduled Rule
- **Schedule:** `rate(7 days)` — runs every 7 days automatically

---

## 📧 SNS Email Report Sample

![alt text](<Screenshot 2026-04-08 111030.png>)
```
AWS EBS Snapshot Cleanup Report
————————————————————
Date   : 2024-01-15 06:00:00 UTC
Region : us-east-1

Deleted : 3 snapshot(s)
Skipped : 1 snapshot(s)

For logs: CloudWatch → /aws/lambda/snapshot-cleanup
————————————————————
System-generated notification. Do not reply.
```
![alt text](<images/Screenshot 2026-04-08-110556.png>)

---

## 🏷️ How to Protect a Snapshot

To prevent a specific snapshot from being deleted, add this tag in the AWS Console:

```
Key:   retain
Value: true
```

---

## 🛠️ Services Used

| Service | Purpose |
|---|---|
| AWS Lambda | Serverless function execution |
| Amazon EC2 | Snapshot and volume management |
| Amazon SNS | Email notification |
| Amazon CloudWatch | Scheduled trigger and logging |
| AWS IAM | Least privilege access control |

---
![alt text](<Screenshot 2026-04-08 110828.png>)

## 💰 Cost Impact

This automation helps reduce AWS costs by:
- Eliminating storage charges for orphaned EBS snapshots
- Running serverlessly — no EC2 instance required
- Scheduled weekly — minimal Lambda invocation cost

---
