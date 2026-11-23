# SES evidence for Cybersecurity, 2026-11-23

AWS account `arl-its` (890884507059), region US-Gov-West (`us-gov-west-1`) unless noted. Console pages were captured while signed in as `AdministratorAccess/jh.jbt8@arl.psu.edu`.

Capture times come from the file names (local Eastern time, UTC-05:00).

| File | Captured (ET) | Captured (UTC) | What it shows |
|---|---|---|---|
| `01-ses-identity-authorization-tab.png` | 11:27:29 | 16:27:29 | SES identity `aws.arl.psu.edu`, Authorization tab: policy `AllowApprovedSenderRoles` |
| `02-ses-identity-policy-json.png` | 11:27:51 | 16:27:51 | The policy text. The right edge is cut off, so the full text is below |
| `03-scp-content.png` | 11:29:16 | 16:29:16 | Service control policy `ARL-Deny-SES-Send-Except-Approved`, Content tab |
| `04-scp-targets.png` | 11:29:52 | 16:29:52 | The same policy, Targets tab |
| `05-cloudtrail-ses-createemailidentitypolicy.png` | 11:31:56 | 16:31:56 | CloudTrail event history filtered to `ses.amazonaws.com`: `CreateEmailIdentityPolicy`, 2026-11-23 10:23:14 (UTC-05:00) |
| `06-cloudtrail-trail-details.png` | 11:32:39 | 16:32:39 | Trail `arl-compliance-BaselineCloudTrail` details |
| `07-sandbox-send-tests.md` | n/a | 15:49 to 15:58 | Text record of the sandbox send tests |

## Which request each file supports

| Request | Files |
|---|---|
| Only approved services and roles can send | 01, 02, 03, 04, 07, and the policy text below |
| Logging and monitoring (CloudTrail) | 05, 06 |

## Policy text as stored in AWS

Read back with the AWS CLI on 2026-11-23 at 16:34:27 UTC.

SES identity policy `AllowApprovedSenderRoles` on `aws.arl.psu.edu`:

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

Service control policy `ARL-Deny-SES-Send-Except-Approved` (policy ID `p-iyjam8nn`, management account):

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
