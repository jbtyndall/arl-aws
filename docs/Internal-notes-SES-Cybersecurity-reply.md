# Internal notes: SES reply to Cybersecurity (do not send)

Companion to `Reply-to-Cybersecurity-SES.md`. The reply answers Damian's three questions and nothing else. This file holds everything that was deliberately left out, why, and what to do about it. Written 2026-11-23.

## Decisions before you send

1. **The SCP is attached to the sandbox only.** The reply says so in one sentence, because "only approved roles can send" would be misleading without it. Your options:
   - Send as written. Damian may reply "so it is not enforced yet."
   - Attach it to Root first, then send. The 2026-11-23 survey found no SES identities and no sending in any of the 20 accounts (both GovCloud regions), so it should not break an existing sender. Attaching it also means nobody can send until a sender role exists, and you have not decided onboarding (see below).
2. **Item 3 is worded to claim only what is verified.** It says CloudTrail is on and records SES API calls (the screenshot shows `CreateEmailIdentityPolicy`). It does not claim CloudTrail records individual sent messages. I believe it does not, but I could not confirm that against AWS docs (web search is blocked in this environment, and the sandbox has never successfully sent, so there was nothing to look for). If Damian meant "log each send," expect a follow-up, and the answer would be SES event publishing to CloudWatch, which is not set up.
3. **Item 2 states only the MX facts.** I did not claim "inbound receiving does not exist in GovCloud." The only evidence is that `aws ses describe-active-receipt-rule-set` returned `InvalidAction` in us-gov-west-1. I do not know why. If you want a stronger answer, confirm in the SES GovCloud documentation, or confirm no receiving was ever configured, and add one sentence. The statement that the bounce MX is Amazon's feedback endpoint is standard SES behavior for a custom MAIL FROM domain, but I also have not checked it against docs.

## What was cut from the reply, and where it lives now

| Cut | Why it is not in the reply | Where to find it |
|---|---|---|
| Org-wide survey (20 accounts, both regions, no SES anywhere) | Not asked | `docs/Centralized-SES-Email-Sending.md`, Section 4.1 |
| Offer to turn on SES event publishing | Not asked, and it invites scope | Section 9 of the design doc |
| Known gaps: DMARC `p=none`, SES sandbox, two leftover test identities, account-level trail | Not asked | Section 9 |
| Plan to attach the SCP org-wide | Not asked | Section 5 |
| Exact limits of the SCP test (denial message does not name the SCP, cross-account send untested) | Not asked | Below, and `docs/Centralized-SES-Email-Sending.md`, Section 8.1 |
| `[VERIFY]` notes | Internal | Above |

## What Damian could ask next, and what is true

- **"Does this stop someone with admin from sending?"** The SCP is written to, and the sandbox test shows an administrator role denied. The denial message does not name the SCP, so it is strong evidence, not proof. Detaching the SCP from the sandbox and repeating the call (expect `MessageRejected`) would make it conclusive. It is a quick write and I would re-attach immediately.
- **"Has a role in another account actually sent through the shared identity?"** No. The domain is not verified until the DNS records exist, so that path is untested.
- **"Who can change the SCP?"** Not fully known. `ARL-ITS` can read the org's SCPs and the console showed Edit, Delete, and Attach buttons, but Organizations is not in `ARL-ITS`'s delegated services and no delegation policy was found. Design doc, open item 14. Settle this before sending if you can.
- **"Does the trail cover the other 19 accounts, and is it encrypted?"** The trail is account-level, not an organization trail (screenshot 06 shows "Apply trail to my organization: Not enabled"), and log file SSE-KMS is "Not enabled" (also in 06). Whether member accounts deliver to the central bucket is unconfirmed. Design doc, open items 8 and 15.
- **"Why does the identity show Error?"** The DNS records are not in place, which is what the ticket is for.
- **"What were the failed attempts at 10:51 ET in CloudTrail under your name?"** My first role-creation script had a malformed trust policy (`CreateRole` failed, nothing changed), and `PutRolePolicy` was denied by `ARL-Guardrails-Global` (`ProtectRoles`). Both changed nothing. I deleted my test role afterward, and the role activity ran through `OrganizationAccountAccessRole` (session `ses-scp-test`).

## Things the evidence shows that the reply does not mention

- Screenshot 04 shows the SCP attached to one account.
- Screenshots 01 and 02 show the identity status as Error.
- Screenshot 02 is cut off on the right edge. The evidence index has the full text of both policies.
- Screenshot 06 shows the trail is account-level and not KMS-encrypted.
- Screenshots 03 and 04 are viewed from the `arl-its` account, not the management account (see open item 14).

None of that is hidden. It is in the images you are attaching. It is just not commentary in the reply.

## Onboarding is not decided

`ProtectRoles` in `ARL-Guardrails-Global` stops the SSO administrator role from attaching permissions to `ARL-*` roles. So creating `ARL-SES-Sender-*` roles needs `OrganizationAccountAccessRole` (worked in the sandbox) or a StackSet from `ARL-ITS` (untested). Do not promise researchers a process until you have tested it. Not something to tell Damian.
