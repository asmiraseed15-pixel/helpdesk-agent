# VPN Not Connecting

Category: Network
Severity: Medium
Keywords: vpn, remote access, connection failed, cannot connect

## Symptoms
- VPN client shows "Connection failed" or "Timeout"
- VPN connects but internal sites do not open

## Troubleshooting Steps
1. Check that the internet is working (open any public website).
2. Close the VPN client completely and reopen it.
3. Verify the username and password are correct.
4. Switch to a different network (for example, mobile hotspot) and retry.
5. Restart the laptop and try again.
6. Update the VPN client to the latest version.

## Permitted Actions
- check_service_status("vpn")
- create_ticket(category="Network")

## When to Escalate
- All steps failed and the VPN server status is "down".
- The same issue affects multiple users.
