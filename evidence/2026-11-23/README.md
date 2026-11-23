# SES evidence for Cybersecurity, 2026-11-23

Screenshots of the AWS console, taken by John Tyndall while signed in as `AdministratorAccess/jh.jbt8@arl.psu.edu` in the `arl-its` account (890884507059). SES and CloudTrail pages are in region US-Gov-West (`us-gov-west-1`). The Organizations pages are global.

Capture times come from the Windows screenshot file names, which are local Eastern time (UTC-05:00). UTC is five hours later. The screenshots themselves have no clock in the frame, except where the AWS page shows event times (files 05 and 06).

| File | Captured (ET) | Captured (UTC) | What it shows |
|---|---|---|---|
| `01-ses-identity-authorization-tab.png` | 11:27:29 | 16:27:29 | SES identity `aws.arl.psu.edu`, Authorization tab: one policy, `AllowApprovedSenderRoles` |
| `02-ses-identity-policy-json.png` | 11:27:51 | 16:27:51 | The "View policy" popup for that policy. The right edge is cut off, so see the full text below |
| `03-scp-content.png` | 11:29:16 | 16:29:16 | Service control policy `ARL-Deny-SES-Send-Except-Approved`, Content tab |
| `04-scp-targets.png` | 11:29:52 | 16:29:52 | The same policy, Targets tab: attached only to `ARL-ITS-Sandbox` (882729674333) |
| `05-cloudtrail-ses-createemailidentitypolicy.png` | 11:31:56 | 16:31:56 | CloudTrail event history, filtered to `ses.amazonaws.com`: `CreateEmailIdentityPolicy` by `jh.jbt8@arl.psu.edu`, 2026-11-23 10:23:14 (UTC-05:00) |
| `06-cloudtrail-trail-details.png` | 11:32:39 | 16:32:39 | Trail `arl-compliance-BaselineCloudTrail`: logging on, multi-region, log file validation enabled, last log file delivered 11:30:56 (UTC-05:00) |
| `07-sandbox-send-tests.md` | n/a | 15:49 to 15:58 UTC (test times) | Text record of the sandbox deny test, the control, and the allow test, with commands, output, and the CloudTrail events. Not a screenshot |

## Which request each file supports

| Request from Cybersecurity | Files |
|---|---|
| Only approved services and roles can send | 01, 02, 03, 04, 07, and the policy text below |
| Logging and monitoring (CloudTrail) | 05, 06 |
| SES is outbound only | None. Not covered by these screenshots |

## What the screenshots do and do not show

- **Identity status shows "Error".** That is expected. The domain is not verified until the DNS records in the ticket are created, so nothing can send through it yet.
- **File 02 is cut off** on the right edge. The `Resource` line and the role-name pattern are not fully visible. The complete policy, read back from AWS, is below.
- **Files 03 and 04** were viewed from the `arl-its` account, not the management account. The policy ARN shows it belongs to the management account (117021256943).
- **File 06 shows two things a reviewer may ask about:** "Apply trail to my organization" is Not enabled (this is an account-level trail), and "Log file SSE-KMS encryption" is Not enabled.
- **Files 01 to 04 have no clock in the frame.** The times above are the file names' times.

## Policy text as stored in AWS

Read back with the AWS CLI on 2026-11-23 at 16:34:27 UTC.

SES identity policy `AllowApprovedSenderRoles` on `aws.arl.psu.edu` (account `arl-its`, 890884507059):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowApprovedSenderRoles",
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "arn:aws-us-gov:ses:us-gov-west-1:890884507059:identity/aws.arl.psu.edu",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalOrgID": "o-uwpj5760j5"
        },
        "ArnLike": {
          "aws:PrincipalArn": "arn:aws-us-gov:iam::*:role/ARL-SES-Sender-*"
        }
      }
    }
  ]
}
```

Service control policy `ARL-Deny-SES-Send-Except-Approved` (policy ID `p-iyjam8nn`, management account), attached to `ARL-ITS-Sandbox` only:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenySESSendingExceptApprovedRoles",
      "Effect": "Deny",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail",
        "ses:SendTemplatedEmail",
        "ses:SendBulkEmail",
        "ses:SendBulkTemplatedEmail",
        "ses:SendBounce",
        "ses:SendCustomVerificationEmail"
      ],
      "Resource": "*",
      "Condition": {
        "ArnNotLike": {
          "aws:PrincipalArn": "arn:aws-us-gov:iam::*:role/ARL-SES-Sender-*"
        }
      }
    }
  ]
}
```

The same SCP text is exported in `scps/ARL-Deny-SES-Send-Except-Approved.json`, and the identity policy source is `ses/identity-policy-aws.arl.psu.edu.json`.
