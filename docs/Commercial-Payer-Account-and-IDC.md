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

There are two permission sets and two Entra groups, mapped one to one. They are separate so the CFO can delegate Marketplace approval later without handing over billing.

| Entra group | Permission set | ARN suffix |
|---|---|---|
| `APP-AWSCommercial-Role-BillingAdministrator` | `BillingAdministrator` | `ps-7223635cb848f2eb` |
| `APP-AWSCommercial-Role-BillingMarketplaceApprover` | `BillingMarketplaceApprover` | `ps-72236144b510101f` |

Both permission sets use a 4-hour session and were created in arlpsu on 2026-11-25.

**BillingAdministrator** attaches `job-function/Billing`. That policy is write-capable. It includes payments, payment methods, tax registrations, purchase orders, invoicing, budgets, cost and usage reports, and `billing:UpdateIAMAccessPreference`. IAM billing access is enabled on the account, confirmed by a successful Cost Explorer query from the admin role.

**BillingMarketplaceApprover** attaches:

- `AWSMarketplaceManageSubscriptions`, which includes `AcceptAgreementRequest`, `GetOffer`, and `Subscribe`.
- `AWSMarketplaceRead-only`.
- An inline policy named `LicenseManagerGrantReview` allowing `ListReceivedGrants`, `ListReceivedGrantsForOrganization`, `ListReceivedLicenses`, `GetGrant`, `GetLicense`, `AcceptGrant`, and `RejectGrant`.

### 4.3 Decisions and corrections

- `AWSMarketplaceFullAccess` and `AWSPrivateMarketplaceRequests` were left out on purpose. The accept path does not need them.
- `AWSLicenseManagerConsumptionPolicy` was considered and rejected. It only allows `CheckoutLicense`, `CheckInLicense`, `ExtendLicenseConsumption`, and `GetLicense`, which is for workloads consuming a license, not for a person accepting a grant.
- The Marketplace set was first created as `MarketplaceApprover` and recreated as `BillingMarketplaceApprover` so it matches its group name and sorts next to the billing set. IDC cannot rename a permission set, so the old one was deleted. It had no assignments.

### 4.4 Status

Done:

- Both permission sets exist with their policies.

Not done:

- Create the Entra group `APP-AWSCommercial-Role-BillingMarketplaceApprover`. Put the CFO in both groups.
- Assign both groups to the Entra enterprise app for IAM Identity Center. Unassigned groups do not sync.
- Confirm both groups appear in the identity store, then assign each to account 193147501194 with its matching permission set.
- Have the CFO sign in and open the Marketplace console before the offer arrives.

### 4.5 Open questions

- The inline License Manager actions are untested against a real grant. If she gets an access error while accepting, start there.
- Confirm Entra enforces MFA for the CFO.
- Confirm the offer is addressed to account 193147501194, and find out when it expires.
- Confirm the account's billing and tax profile is complete. First-time Marketplace buyers often get stuck here.
