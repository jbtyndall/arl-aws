# AWS CLI TLS Fix for ARL

Fixes this error when you run any AWS CLI command on the ARL network:

```
SSL validation failed for https://sts.us-gov-west-1.amazonaws.com/ [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain
```

## Why it happens

ARL's firewall inspects HTTPS traffic. It re-signs traffic to AWS with ARL's own certificate authority (`ARL WAN1 Forward Trust CA`, which chains up to `ARL Root CA`). Windows already trusts that authority, so browsers and most tools work. The AWS CLI v2 ships its own list of trusted authorities and ignores the Windows certificate store, so it rejects the connection.

## The fix

Run `Fix-AwsCliTls.bat` (double-click it). It does four things:

1. Finds `ARL Root CA` in the Windows Trusted Root stores. Expired copies are skipped.
2. Builds a CA bundle: the AWS CLI's own CA list plus the ARL root certificate.
3. Sets your user-level `AWS_CA_BUNDLE` environment variable to point at that bundle.
4. Tests TLS against the GovCloud and commercial STS endpoints.

Close and reopen any open terminals and VS Code afterward. They only read environment variables when they start.

### What it does not do

- It does **not** turn off certificate checking. Verification stays on.
- It does **not** need administrator rights.
- It does **not** change anything outside your own user profile.
- Because the AWS CLI's normal CA list stays in the bundle, the CLI keeps working when you are off the ARL network.

Do not work around this error with `--no-verify-ssl`. That turns off the protection TLS is there to give you.

## Requirements

- Windows with AWS CLI v2 installed (the default `C:\Program Files\Amazon\AWSCLIV2` location is detected automatically).
- Windows PowerShell 5.1 or later. It ships with Windows 10 and 11.
- An ARL-managed machine that already trusts `ARL Root CA`.

## Files it creates

| Path | Purpose |
|---|---|
| `%USERPROFILE%\.aws\ca-bundle.pem` | The combined CA bundle |
| `%USERPROFILE%\.aws\ca-bundle.pem.bak-<timestamp>` | Backup of the previous bundle, made when you re-run it |
| `%USERPROFILE%\.aws\fix-awscli-tls.log` | Log of what the script did |

## Options

Run these from PowerShell or Command Prompt in this folder. The `.bat` passes arguments through to the script.

| Option | What it does |
|---|---|
| `-WhatIf` | Shows what would change and writes nothing |
| `-SkipEnvironmentVariable` | Builds and tests the bundle but does not set `AWS_CA_BUNDLE` |
| `-Force` | Replaces an existing `AWS_CA_BUNDLE` that points somewhere else. Without it, the script leaves your value alone and warns you |
| `-BundlePath <path>` | Writes the bundle somewhere other than `%USERPROFILE%\.aws\ca-bundle.pem` |
| `-CertificateSubjectPattern <text>` | Matches a different certificate name. Default is `CN=ARL Root CA` |
| `-AwsCliBundlePath <path>` | Uses a specific AWS CLI `cacert.pem` if auto-detection fails |

Example:

```
Fix-AwsCliTls.bat -WhatIf
```

## When to run it again

- After you upgrade the AWS CLI. The bundle contains a copy of the CLI's CA list from the day you built it, so it slowly goes stale.
- After ARL replaces its root certificate.
- If the errors come back.

Re-running is safe. It backs up the old bundle first.

## Troubleshooting

**"AWS_CA_BUNDLE is already set to ... Not changing it."**
You already had a value, possibly from an earlier workaround. Re-run with `-Force` to replace it. The old value is written to the log.

**"No valid certificate matching 'CN=ARL Root CA' found."**
Your machine may not trust the ARL root, or it may use a different name. In Command Prompt, run `certutil -store Root` and look for the ARL entry (add `| findstr /i ARL` to filter). Pass the exact name you find with `-CertificateSubjectPattern`. If nothing is listed, contact ITS.

**"Could not find the AWS CLI v2 CA list."**
AWS CLI v2 is not installed in the default location. Install it, or pass `-AwsCliBundlePath` pointing at the CLI's `awscli\botocore\cacert.pem`.

**The test passes, but your terminal still fails.**
That terminal was open before the fix. Close it and open a new one. In the new terminal, `echo %AWS_CA_BUNDLE%` (Command Prompt) or `$env:AWS_CA_BUNDLE` (PowerShell) should show the bundle path.

**The test says TLS validation FAILED.**
The certificate your firewall presents is not the one the script found. Check what is presented with `openssl s_client -connect sts.us-gov-west-1.amazonaws.com:443 -showcerts` and look at the last certificate in the chain. Contact ITS if it does not match `ARL Root CA`.

**Other tools still fail (Terraform, Python scripts, Node).**
Each tool picks its own CA source. Most Python tools respect `REQUESTS_CA_BUNDLE`, and Node uses `NODE_EXTRA_CA_CERTS`. This script only sets `AWS_CA_BUNDLE`.

## How to undo it

In PowerShell:

```
[Environment]::SetEnvironmentVariable('AWS_CA_BUNDLE', $null, 'User')
```

Then delete `%USERPROFILE%\.aws\ca-bundle.pem`. Reopen your terminals.

## Security note

The bundle trusts the ARL root in addition to the normal public authorities, so the AWS CLI will accept certificates ARL's firewall issues for AWS endpoints. That matches what browsers on your machine already do. Do not add certificates to this bundle that you do not recognize.

The `.bat` runs the script with `-ExecutionPolicy Bypass` for that one run only. It does not change your machine's execution policy. Read `Fix-AwsCliTls.ps1` before you run it. It is documented at the top of the file, and `-WhatIf` shows what it would do.
