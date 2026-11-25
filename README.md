# arl-aws

Documentation, exports, and tools for ARL's AWS GovCloud organization and its commercial master payer account (arlpsu, 193147501194). This repo exists because the original builder of the environment left without documenting it. Anything learned about how the org works goes here.

Keep this repo private. The SCP export files contain AWS account IDs.

## Layout

| Folder | What is in it |
|---|---|
| `docs/` | Design docs and findings. Start with `Centralized-SES-Email-Sending.md` for GovCloud or `Commercial-Payer-Account-and-IDC.md` for the commercial payer account |
| `scps/` | Exports of the org's Service Control Policies: policy JSON, metadata, and attachment targets |
| `tools/aws-cli-tls-fix/` | Fixes AWS CLI `CERTIFICATE_VERIFY_FAILED` errors caused by ARL TLS inspection. Has its own README |

## Environment facts

- The AWS Organization has 20 accounts, all directly under Root (no OUs). Service Control Policies are enabled.
- Primary region is `us-gov-west-1`. Nothing was found in `us-gov-east-1`.
- Sign-in uses IAM Identity Center at `https://start.us-gov-home.awsapps.com/directory/arlpsu`.
- `ARL-ITS` is the Shared Services account and the delegated administrator for Access Analyzer, GuardDuty, Security Hub, Service Catalog, IAM Identity Center, and service-managed StackSets.
- Kion manages accounts and cloud rules, but **not** the SCPs. Kion's AWS Service Control Policies page is empty. The SCPs live only in AWS Organizations.

See `docs/Centralized-SES-Email-Sending.md`, Section 4.2, for how this was determined and what is still unconfirmed.

## Signing in from the command line

All GovCloud profiles share one SSO session, so one login covers every account:

```
aws sso login --sso-session arlpsu-govcloud
```

Profiles are named `<account-name>-govcloud`, for example `gids-basecamp-govcloud`. These older names were kept:

| Profile | Account |
|---|---|
| `arlpsu-govcloud` | Organization management account |
| `arl-its-govcloud` | ARL-ITS (Shared Services) |
| `arl-its-sandbox-govcloud` | ARL-ITS-Sandbox |
| `gids-nimbus-govcloud` | GIDS-Nimbus |

Profiles live in `%USERPROFILE%\.aws\config` on your machine, not in this repo. To test that a profile works:

```
aws sts get-caller-identity --profile arlpsu-govcloud
```

If every call fails with `CERTIFICATE_VERIFY_FAILED`, see `tools/aws-cli-tls-fix/`.

### Commercial accounts

Commercial accounts use a separate portal and a separate login. All commercial profiles share the `arlpsu-commercial` SSO session:

```
aws sso login --sso-session arlpsu-commercial
```

Commercial profiles are named `<account-name>-commercial`, for example `arlpsu-commercial` (master payer) and `arl-its-commercial`. See `docs/Commercial-Payer-Account-and-IDC.md` for the account list, IAM Identity Center details, and the CFO billing and Marketplace access work.

## Service Control Policies

SCPs are created and edited in the AWS Organizations console (management account), not in Kion. The files in `scps/` are point-in-time exports. Nothing deploys from them.

Each policy has three files:

| File | Contents |
|---|---|
| `<name>.json` | The policy document |
| `<name>.meta.json` | Policy ID, name, description, and whether AWS manages it |
| `<name>.targets.json` | What the policy is attached to |

After changing an SCP, re-export it so this repo stays accurate. To read one policy, use the management account profile:

```
aws organizations describe-policy --policy-id <policy-id> --profile arlpsu-govcloud --query Policy.Content --output text
```

List policy IDs with `aws organizations list-policies --filter SERVICE_CONTROL_POLICY --profile arlpsu-govcloud`.

Current exports (2026-11-23):

| Policy | Attached to |
|---|---|
| `ARL-Guardrails-Global` | Root |
| `ARL-Guardrails-DenyIGW` | Root |
| `FullAWSAccess` | Root and each account |

`ARL-Guardrails-Global` protects logging, CloudWatch resources, `ARL-*` and `CT-*` roles, account settings, and RAM sharing. Be careful with the role protection: SSO administrators are not on its exemption list, so changing `ARL-*` roles may be denied.

## Open work

- GovCloud SES: tracked in `docs/Centralized-SES-Email-Sending.md`, Section 9.
- Commercial CFO billing and Marketplace access: tracked in `docs/Commercial-Payer-Account-and-IDC.md`, Section 4.4.
