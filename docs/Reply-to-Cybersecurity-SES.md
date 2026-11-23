Damian,

Here is the evidence for the three items. The SES identity `aws.arl.psu.edu` is in the ARL-ITS AWS account (890884507059), GovCloud region us-gov-west-1. Times are Eastern with UTC in parentheses.

**1. Access control in AWS IAM so only approved services and roles can send**

- **SES identity policy** on `aws.arl.psu.edu`, applied 2026-11-23 10:23 (15:23 UTC). It allows `ses:SendEmail` and `ses:SendRawEmail` only for IAM roles named `ARL-SES-Sender-*` in our AWS Organization.
- **Service control policy** `ARL-Deny-SES-Send-Except-Approved`. It denies every SES send action for any principal that is not an `ARL-SES-Sender-*` role, including administrators. It is currently attached to the ARL-ITS-Sandbox account only.
- **Test of the SCP** in that account, same call, 2026-11-23:

| Caller | Result |
|---|---|
| Administrator role (not an approved role) | `AccessDeniedException` |
| Role named `ARL-SES-Sender-Test` (approved name), since deleted | Passed authorization and stopped at `MessageRejected` (sender address not verified) |

Evidence: files 01 to 04 and 07.

**2. SES is only used for outbound mail**

The only MX record in the DNS request is on `bounce.aws.arl.psu.edu`, pointing to `feedback-smtp.us-gov-west-1.amazonses.com`. That is Amazon's endpoint for bounce and complaint notices on mail we send. No MX record is requested for `aws.arl.psu.edu` itself.

**3. Logging and monitoring of SES activity (CloudTrail)**

CloudTrail trail `arl-compliance-BaselineCloudTrail` is enabled in ARL-ITS: logging on, multi-region, log file validation on, management events (read and write), delivered to the central log archive bucket. It records SES API calls, for example `CreateEmailIdentityPolicy` on 2026-11-23 at 10:23:14 (15:23:14 UTC) by `jh.jbt8@arl.psu.edu`.

Evidence: files 05 and 06.

**Attached:** `evidence/2026-11-23/` (files 01 to 07 and the index).

John
