# Draft reply to Cybersecurity (DRAFT, not sent)

Review before sending. Items marked **[VERIFY]** are claims I could not confirm against AWS documentation. Either confirm them or cut them. Captured evidence is in `docs/Centralized-SES-Email-Sending.md` (Sections 4, 8, and 10). Screenshots still need to be taken by hand (see the end).

---

Hi Damian,

Thanks for the follow-up. Here is the evidence for the three items. All times are UTC unless noted. The SES identity `aws.arl.psu.edu` is in the ARL-ITS account (GovCloud, us-gov-west-1) and cannot send until the DNS records in the ticket are in place, so nothing can send through it today.

**1. Only approved roles can send**

Two controls:

- **SES identity policy** on `aws.arl.psu.edu` (applied 2026-11-23 15:23). It allows `ses:SendEmail` and `ses:SendRawEmail` only for IAM roles named `ARL-SES-Sender-*` that belong to our AWS Organization. No users, no other roles, and no outside accounts are allowed.
- **Service Control Policy** `ARL-Deny-SES-Send-Except-Approved` (created 2026-11-23 15:45). It denies every SES send action for any principal that is not an `ARL-SES-Sender-*` role, even if that principal has administrator permissions in its own account. It is currently attached to one test account (ARL-ITS-Sandbox). I plan to attach it organization-wide after your review.

I tested the SCP in the sandbox account with the same call, at 15:49 and 15:58:

| Caller | Result |
|---|---|
| Administrator role (not approved) | Denied (`AccessDeniedException`) |
| Role named `ARL-SES-Sender-Test` (approved name), since deleted | Passed authorization, then stopped because the sender address was not verified (`MessageRejected`) |

The denial message does not name the SCP, so I can detach the policy and repeat the test if you want a direct before-and-after. I have not yet tested a send from a role in another account through the shared identity, because that needs the domain verified first.

I also surveyed all 20 accounts in the organization in both GovCloud regions on 2026-11-23. None has an SES identity, none has production access, and none sent anything in the last 24 hours, so this control does not affect any existing senders.

**2. SES is used for outbound mail only**

**[VERIFY]** Inbound receiving is not set up. In us-gov-west-1, the receipt rule set call returns `InvalidAction`, which I believe means inbound receiving is not offered in GovCloud. I have not confirmed that against AWS documentation. I would drop this sentence unless you can confirm it.

About the MX record in the ticket: it is on `bounce.aws.arl.psu.edu` only and points at Amazon's `feedback-smtp` endpoint. It receives bounce and complaint notices for messages we send. It is not a mailbox. There is no MX record on `aws.arl.psu.edu` itself.

**3. Logging and monitoring**

CloudTrail trail `arl-compliance-BaselineCloudTrail` is on for the ARL-ITS account (multi-region, log file validation on, management events read and write, delivering to the central log archive with no errors as of 2026-11-23 16:09). It recorded the changes above, including the SES policy change (`CreateEmailIdentityPolicy`, 15:23:14), the SCP creation and attachment (15:45:37 and 15:45:39), and the sandbox test activity.

**[VERIFY]** I believe CloudTrail records SES configuration and API activity but not each individual message sent. If you need per-message records, I can turn on SES event publishing (send, delivery, bounce, complaint, reject) to CloudWatch. Let me know if you want that before approval. I have not configured it yet, and the SES configuration set currently has no event destination.

**Known gaps**

- DMARC is `p=none` as requested in the ticket. I plan to tighten it after reviewing reports.
- SES is in sandbox mode (200 messages a day, verified recipients only). I will request production access after the domain verifies.
- Two leftover test email identities exist in ARL-ITS (`aws@arl.psu.edu` and `jbt8@arl.psu.edu`). I will remove them.
- The CloudTrail trail is account-level, not an organization trail. I have not yet confirmed that every member account delivers to the central archive.

Once you approve, please add the six DNS records from the original ticket. I can send over the current identity status and the screenshots listed below.

Thanks,
John

---

## Evidence files

The six console screenshots are in `evidence/2026-11-23/`, with an index (`README.md`) that lists when each was captured, what it shows, and the full text of both policies read back from AWS. Attach the six PNGs and paste or attach the index.

`07-sandbox-send-tests.md` is a text record of the sandbox tests (deny at 15:49 UTC, control, allow at 15:58 UTC), with the commands, the output as captured, and the CloudTrail events. Attach it with the screenshots.

Nothing here covers item 2 (outbound only). That one is explained in the reply text.

## Before you send

- Decide on the two **[VERIFY]** items.
- Decide whether you want to tell him about the org-wide attachment plan, or attach it first. I'd tell him the plan and ask.
- The reply is long. Damian asked for three things, so you can shorten it. I kept the survey and gaps because he is likely to ask about them.
