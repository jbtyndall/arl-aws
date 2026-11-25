# arl-aws: Project Context

## Accounts

| Name | Account ID | Partition | Role |
|---|---|---|---|
| arlpsu | 193147501194 | Commercial | Organizations management account and master payer. Owns the IAM Identity Center (IDC) instance. Root email: aws+arlpsu@arl.psu.edu |
| arlpsu-govcloud | 117021256943 | GovCloud | Linked GovCloud account of arlpsu. Separate partition and separate IDC. |
| arl-its | 808000717462 | Commercial | Delegated administrator for the org (sso, guardduty, securityhub, fms, access-analyzer, servicecatalog, StackSets). |

- AWS Marketplace exists only in the commercial partition. GovCloud bills through the paired commercial account.
- The user (John Tyndall) is the Cloud Architect for ARL at Penn State. Do not suggest he "just do it himself" when he says someone else (e.g., the CFO) must perform an action.

## AWS CLI Profiles

- Profiles live in `~/.aws/config`. Do not run bare `aws` commands. The default profile has no credentials. Always pass `--profile`.
- Commercial profiles all share `sso-session arlpsu-commercial` (start URL `https://arlpsu.awsapps.com/start`). One `aws sso login --profile arlpsu-commercial` covers every commercial profile.
- GovCloud profiles all share `sso-session arlpsu-govcloud` (start URL `https://start.us-gov-home.awsapps.com/directory/arlpsu`, region `us-gov-west-1`). It is a separate login from commercial.
- When a token is expired, tell John to run `! aws sso login --profile <name>`. Do not try to work around it.
- A backup of the config from before the commercial consolidation is at `~/.aws/config.bak-20261125`.

## IAM Identity Center

- Instance: `arn:aws:sso:::instance/ssoins-72239915bfbe637d`, identity store `d-9066270627`, region us-east-1. Owned by 193147501194.
- Existing permission sets: `SecurityAudit`, `AdministratorAccess`, `ProjectAdmin`, `ViewOnlyAccess`. Session duration is 4 hours (8 for ViewOnly).
- Groups are synced from Entra. Naming: `AWS-Global-*` for org-wide groups and `AWS-<Project>-Admins` for project groups.
- Permission sets are defined outside this repo. John believes they are managed through the arl-its account (808000717462, a delegated admin for `sso.amazonaws.com`). Expect AWS to require some actions on the management account itself to be done from arlpsu. Verify before assuming.
- When passing the instance ARN in shell commands, spell it out. Piping it through `xargs` mangled it once.

## In-Progress Work: CFO Marketplace Approver Role

Request: Red Hat is issuing a private offer through AWS Marketplace for the ARL subscription renewal. The CFO must log in to arlpsu (193147501194) and accept the agreement. She should have Marketplace accept/deny plus full billing and Cost Explorer, and nothing else.

Planned design (not yet built):

- Permission set `BillingMarketplaceApprover`, 4-hour session.
- Entra group `AWS-Global-BillingApprovers`, containing the CFO and one backup. Assign only to account 193147501194.
- Policies (names verified to exist unless noted):
  - `AWSMarketplaceManageSubscriptions`
  - `AWSMarketplaceRead-only`
  - `AWSLicenseManagerConsumptionPolicy` (not `ConsumerPolicy`, which does not exist)
  - Billing access: `job-function/Billing` is NOT yet verified. `AWSBillingReadOnlyAccess` exists.
- Do not use `AWSMarketplaceFullAccess` or `AWSPrivateMarketplaceRequests`.
- Still to verify: that "IAM user and role access to Billing information" is activated in the management account, and that Entra enforces MFA for the CFO.
- Still to verify: that the offer is addressed to 193147501194 and when it expires, and that the account's billing and tax setup is complete.

## Working Rules for This Repo

- John performs all `git add` and `git commit`. Provide the commands and message, but never run them.
- SCPs are in `scps/`. The management account is not affected by SCPs. The only SCP on it is `FullAWSAccess`.
- The `aws-mcp` MCP server has failed to connect in past sessions. Fall back to the CLI profiles.
- Do not add Claude attribution lines to commit messages, per John's global instructions.
