# Commercial Payer Account and IAM Identity Center

Last updated: 2026-11-25

This document records how ARL's commercial AWS footprint is set up, how to sign in to it from the command line, and the status of the CFO billing and Marketplace access work.

## 1. Accounts

| Name | Account ID | Partition | Role |
|---|---|---|---|
| arlpsu | 193147501194 | Commercial | Organizations management account and master payer. Owns the IAM Identity Center (IDC) instance. Root email: aws+arlpsu@arl.psu.edu |
| arlpsu-govcloud | 117021256943 | GovCloud | Linked GovCloud account of arlpsu. Separate partition and separate IDC. |
| arl-its | 808000717462 | Commercial | Delegated administrator for the org (sso, guardduty, securityhub, fms, access-analyzer, servicecatalog, StackSets). |

- AWS Marketplace exists only in the commercial partition. GovCloud bills through the paired commercial account.
- SCPs do not apply to the management account. The only SCP attached to arlpsu is `FullAWSAccess`.

## 2. AWS CLI profiles

- Profiles live in `~/.aws/config`. The default profile has no credentials, so every command needs `--profile`.
- All commercial profiles share `sso-session arlpsu-commercial` (start URL `https://arlpsu.awsapps.com/start`). One `aws sso login --profile arlpsu-commercial` covers all of them.
- All GovCloud profiles share `sso-session arlpsu-govcloud` (start URL `https://start.us-gov-home.awsapps.com/directory/arlpsu`, region `us-gov-west-1`). It is a separate login from commercial.
- On 2026-11-25 the `arl-its-commercial`, `arl-its-sandbox-commercial`, and `gids-nimbus-commercial` profiles were moved onto the shared commercial session. The previous config is at `~/.aws/config.bak-20261125`. The old per-profile `[sso-session ...]` blocks are still in the file and are unused.

## 3. IAM Identity Center

- Instance: `arn:aws:sso:::instance/ssoins-72239915bfbe637d`. Identity store: `d-9066270627`. Region: us-east-1. Owned by arlpsu (193147501194).
- arl-its (808000717462) is a delegated administrator for `sso.amazonaws.com`.
- Permission sets that existed before this work: `SecurityAudit`, `AdministratorAccess`, `ProjectAdmin`, `ViewOnlyAccess`. Session duration is 4 hours, except ViewOnly at 8.
- Groups are synced from Entra. Existing naming includes `AWS-Global-*` and `AWS-<Project>-Admins`. New role groups use `APP-AWSCommercial-Role-<PermissionSetName>`.
- Permission sets are not defined in this repo. They exist only in AWS.
- A permission set that targets the management account was created in arlpsu itself. Whether arl-its could have created and assigned it was not tested.

## 4. CFO billing and Marketplace access

### 4.1 Why

Red Hat is issuing a private offer for the ARL subscription renewal through AWS Marketplace. Someone has to sign in to arlpsu and accept it. The CFO must be that person. She needs full billing access (including Cost Explorer) and the ability to accept or reject Marketplace agreements, and nothing else.

### 4.2 Design

The CFO is not an AWS user. She gets one role that does everything she needs, so she sees one choice in the sign-in portal. IAM Identity Center does not combine permission sets on the same account. Two assigned sets would show up as two separate roles.

| Entra group | Permission set | ARN suffix | Assigned to arlpsu |
|---|---|---|---|
| `APP-AWSCommercial-Role-FinanceAdministrator` | `FinanceAdministrator` | `ps-722333e97265b882` | Yes (2026-11-25) |

The IDC group ID is `9498b4c8-b0b1-706a-9069-147e9155a5b3`. The session duration is 4 hours.

**Scope: everything money-related.** `FinanceAdministrator` attaches:

- `job-function/Billing`. This is write-capable: payments, payment methods, tax registrations, purchase orders, invoicing, budgets, cost and usage reports, and `billing:UpdateIAMAccessPreference`. IAM billing access is enabled on the account, confirmed by a successful Cost Explorer query from the admin role.
- `AWSMarketplaceManageSubscriptions`, which includes `AcceptAgreementRequest`, `GetOffer`, and `Subscribe`.
- `AWSMarketplaceRead-only`.
- `AWSSupportAccess` (`support:*` only), so she can open and read billing questions with AWS Support. The account is on Basic support, so the Support API is unavailable and cases go through the console.
- An inline policy named `LicenseManagerGrantReview` allowing `ListReceivedGrants`, `ListReceivedGrantsForOrganization`, `ListReceivedLicenses`, `GetGrant`, `GetLicense`, `AcceptGrant`, and `RejectGrant`.

**Delegation.** If the CFO wants someone else to approve Marketplace agreements, create a Marketplace-only permission set. Attach `AWSMarketplaceManageSubscriptions`, `AWSMarketplaceRead-only`, and the same inline `LicenseManagerGrantReview` policy, with no billing. Create a new Entra group, assign it to the IDC enterprise app, let it sync, and assign it to 193147501194. A `BillingMarketplaceApprover` set was built for this and deleted on 2026-11-25 because nobody was using it.

### 4.3 Decisions and corrections

- One role for the CFO, named for its scope. It was first `BillingAdministrator`, then renamed `FinanceAdministrator` because it also covers Marketplace approval and support. IDC cannot rename a permission set, so the old one was deleted after the new group assignment succeeded. The Entra group kept its object ID through the rename, so the IDC group and its ID did not change.
- Two permission sets on one account appear as two roles in the portal. That was rejected as a poor experience for a non-technical user, and the Marketplace accept flow can touch billing and tax setup.
- The role does not include buying Savings Plans or Reserved Instances. Those are EC2 and Savings Plans actions with no approval workflow, and project admins buy their own with AdministratorAccess.
- She does not need to see accounts or resources. Cost Explorer spend data is enough, so there is no ViewOnlyAccess or Organizations read policy.
- `AWSMarketplaceFullAccess` and `AWSPrivateMarketplaceRequests` were left out on purpose. The accept path does not need them.
- `AWSLicenseManagerConsumptionPolicy` was considered and rejected. It only allows `CheckoutLicense`, `CheckInLicense`, `ExtendLicenseConsumption`, and `GetLicense`, which is for workloads consuming a license, not for a person accepting a grant.

### 4.4 Status

Done:

- `FinanceAdministrator` exists with its policies and is assigned to account 193147501194 for the CFO's group.
- Members at assignment: the CFO (`gaf121`) and John's standard account (`jbt8`, for testing).

Not done:

- Confirm the Entra group rename (`...FinanceAdministrator`) has propagated to IDC. The IDC group still showed the old display name when last checked. This is cosmetic. Assignments use the group ID.
- Add a backup approver to the group in Entra. John is asking the CFO.
- Remove `jbt8` from the group in Entra when testing is finished. Membership is managed in Entra and synced over SCIM, so do not change it in AWS.
- Have the CFO sign in and open the Marketplace console, Private offers page, before the offer arrives.

### 4.5 Open questions

- The inline License Manager actions are untested against a real grant. If she gets an access error while accepting, start there.
- Confirm Entra enforces MFA for the CFO.
- Confirm the offer is addressed to account 193147501194, and find out when it expires.
- Confirm the account's billing and tax profile is complete. First-time Marketplace buyers often get stuck here.
