# SES evidence for Cybersecurity, 2026-11-23

Internal index. Not part of the upload set. AWS account `arl-its` (890884507059), region US-Gov-West (`us-gov-west-1`) unless noted. Console pages were captured while signed in as `AdministratorAccess/jh.jbt8@arl.psu.edu`.

Screenshot capture times come from the file names (local Eastern time, UTC-05:00).

| File | Captured (ET) | Captured (UTC) | What it is |
|---|---|---|---|
| `01-ses-identity-authorization-tab.png` | 11:27:29 | 16:27:29 | SES identity `aws.arl.psu.edu`, Authorization tab: policy `AllowApprovedSenderRoles` |
| `02-ses-identity-policy-json.png` | 11:27:51 | 16:27:51 | The policy popup. The right edge is cut off, so see file 05 for the full text |
| `03-scp-content.png` | 11:29:16 | 16:29:16 | Service control policy `ARL-Deny-SES-Send-Except-Approved`, Content tab |
| `04-scp-targets.png` | 11:29:52 | 16:29:52 | The same policy, Targets tab |
| `05-ses-identity-policy-aws.arl.psu.edu.json` | n/a | 17:14:24 | SES identity policy `AllowApprovedSenderRoles`, read back from AWS with the CLI |
| `06-scp-ARL-Deny-SES-Send-Except-Approved.json` | n/a | 17:14:24 | Service control policy `ARL-Deny-SES-Send-Except-Approved` (policy ID `p-iyjam8nn`), read back from AWS with the CLI |
| `07-cloudtrail-ses-createemailidentitypolicy.png` | 11:31:56 | 16:31:56 | CloudTrail event history filtered to `ses.amazonaws.com`: `CreateEmailIdentityPolicy`, 2026-11-23 10:23:14 (UTC-05:00) |
| `08-cloudtrail-trail-details.png` | 11:32:39 | 16:32:39 | Trail `arl-compliance-BaselineCloudTrail` details |
| `internal-sandbox-send-tests.md` | n/a | 15:49 to 15:58 | Text record of the sandbox send tests. Not part of the upload set |

## Which request each file supports

| Request | Files |
|---|---|
| Only approved services and roles can send | 01, 02, 03, 04, 05, 06 |
| Logging and monitoring (CloudTrail) | 07, 08 |

Files 05 and 06 are the same policies shown in 01 to 04, as exact text.
