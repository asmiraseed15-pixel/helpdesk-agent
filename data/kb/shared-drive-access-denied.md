# Shared drive access denied
Category: Access
Keywords: shared drive, access denied, permission, folder
Severity: Medium

## Symptoms
Access denied when opening a network folder.

## Troubleshooting Steps
1. Confirm you are on the company network or VPN.
2. Re-map the network drive.
3. Sign out and sign in again.
4. Request access from the folder owner.

## Permitted Actions
- create_access_request(user_id, folder)
- create_ticket(category="Access")

## When to Escalate
- Owner approved but access is still denied.
