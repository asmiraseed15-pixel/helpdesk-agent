# Email Not Syncing

Category: Software
Severity: Medium
Keywords: email, sync, not receiving, not sending, mailbox, outbox, delay

## Symptoms
- New emails are not arriving.
- Sent emails stay in the Outbox.

## Troubleshooting Steps
1. Check the internet connection.
2. Check that Outlook is not in "Work Offline" mode.
3. Press Send/Receive (F9).
4. Check that the mailbox is not full.
5. Restart Outlook, then restart the laptop.
6. Check email on the web version (Outlook Web) to confirm the mailbox is working.

## Permitted Actions
- check_service_status("email")
- create_ticket(category="Software")

## When to Escalate
- Emails arrive in the web version but not in the Outlook app after a new profile.
- Mail server status is "down".