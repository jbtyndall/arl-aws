# Sandbox send tests for the SES service control policy, 2026-11-23

Tests of `ARL-Deny-SES-Send-Except-Approved` (policy ID `p-iyjam8nn`), which is attached to `ARL-ITS-Sandbox` (882729674333) only. Run by John Tyndall as `jh.jbt8@arl.psu.edu` in region `us-gov-west-1`.

This is a record of command output copied from the terminal at the time. Account IDs in the output were replaced with `<acct>` when it was captured. In the sandbox tests `<acct>` is 882729674333. In the control test it is 663684808208 (GIDS-Nimbus). Times are UTC. The AWS-side record of the role activity is in CloudTrail (see the last section).

## What was tested

The same `SendEmail` call, from the same account, by two different callers:

1. An administrator role whose name does not match `ARL-SES-Sender-*`. The SCP should deny it.
2. A role named `ARL-SES-Sender-Test`, created for the test. The SCP should let it through authorization.

The sender address `test@aws.arl.psu.edu` and the recipient `jbt8@arl.psu.edu` are not verified in the sandbox account, so a call that passes authorization should stop with `MessageRejected`. No email was sent in any test.

## Test 1: administrator role, SCP attached (deny)

Run began 15:49:15 UTC. Caller:

```
arn:aws-us-gov:sts::<acct>:assumed-role/AWSReservedSSO_AdministratorAccess_9bac68ac2e15f074/jh.jbt8@arl.psu.edu
```

Command:

```
aws sesv2 send-email --from-email-address test@aws.arl.psu.edu --destination ToAddresses=jbt8@arl.psu.edu --content 'Simple={Subject={Data=SCP deny test},Body={Text={Data=test}}}' --profile arl-its-sandbox-govcloud
```

Result:

```
aws: [ERROR]: An error occurred (AccessDeniedException) when calling the SendEmail operation: User 'arn:aws-us-gov:sts::<acct>:assumed-role/AWSReservedSSO_AdministratorAccess_9bac68ac2e15f074/jh.jbt8@arl.psu.edu' is not authorized to perform 'ses:SendEmail' on resource 'arn:aws-us-gov:ses:us-gov-west-1:<acct>:identity/test@aws.arl.psu.edu'
exit=254
```

## Control: administrator role, no SCP attached

Same run, a few seconds later. This is a different account (`GIDS-Nimbus`) that does not have the SCP. It shows what the same kind of call does without the guardrail.

Command:

```
aws sesv2 send-email --from-email-address test@aws.arl.psu.edu --destination ToAddresses=jbt8@arl.psu.edu --content 'Simple={Subject={Data=SCP control test},Body={Text={Data=test}}}' --profile gids-nimbus-govcloud
```

Result:

```
aws: [ERROR]: An error occurred (MessageRejected) when calling the SendEmail operation: Email address is not verified. The following identities failed the check in region US-GOV-WEST-1: test@aws.arl.psu.edu, jbt8@arl.psu.edu
```

## Test 2: role named `ARL-SES-Sender-Test`, SCP attached (allow)

The role was created in the sandbox through `OrganizationAccountAccessRole`. The role trusted only the administrator role and allowed `ses:SendEmail` and `ses:SendRawEmail`. It was deleted right after the test.

| Time (UTC) | Step |
|---|---|
| 15:57:45 | Assumed `OrganizationAccountAccessRole` in the sandbox (session `ses-scp-test`, 15 minutes) |
| 15:57:51 | Created role `ARL-SES-Sender-Test` with an inline `AllowSesSend` policy |
| 15:58:07 | Assumed `ARL-SES-Sender-Test` as the administrator role and sent |
| 15:58:12 | Deleted the inline policy and the role |
| 15:58:26 | Confirmed the role was gone (`NoSuchEntity`) |

Caller during the send:

```
arn:aws-us-gov:sts::<acct>:assumed-role/ARL-SES-Sender-Test/allow-test
```

Command:

```
aws sesv2 send-email --from-email-address test@aws.arl.psu.edu --destination ToAddresses=jbt8@arl.psu.edu --content 'Simple={Subject={Data=SCP allow test},Body={Text={Data=test}}}'
```

Result:

```
aws: [ERROR]: An error occurred (MessageRejected) when calling the SendEmail operation: Email address is not verified. The following identities failed the check in region US-GOV-WEST-1: jbt8@arl.psu.edu, test@aws.arl.psu.edu
send exit=254
```

Cleanup check at 15:58:26 UTC:

```
aws: [ERROR]: An error occurred (NoSuchEntity) when calling the GetRole operation: The role with name ARL-SES-Sender-Test cannot be found.
```

## Results

| Caller | Account | SCP attached | Result |
|---|---|---|---|
| Administrator role (not approved) | `ARL-ITS-Sandbox` | Yes | `AccessDeniedException` |
| `ARL-SES-Sender-Test` (approved name) | `ARL-ITS-Sandbox` | Yes | `MessageRejected` (passed authorization, stopped at unverified identity) |
| Administrator role (control) | `GIDS-Nimbus` | No | `MessageRejected` |

## CloudTrail record of the role activity

Checked at 16:09 UTC through the CLI (`cloudtrail lookup-events`, sandbox account). Times are shown as recorded, UTC-05:00:

| Event | Time | Caller |
|---|---|---|
| `CreateRole` | 2026-11-23 10:57:53 | session `ses-scp-test` |
| `PutRolePolicy` | 2026-11-23 10:57:55 | session `ses-scp-test` |
| `DeleteRolePolicy` | 2026-11-23 10:58:14 | session `ses-scp-test` |
| `DeleteRole` | 2026-11-23 10:58:16 | session `ses-scp-test` |

The SCP's own creation and attachment are in CloudTrail in the management account: `CreatePolicy` at 10:45:37 and `AttachPolicy` at 10:45:39 (UTC-05:00), by `jh.jbt8@arl.psu.edu`.
