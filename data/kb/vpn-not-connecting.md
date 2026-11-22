# VPN not connecting
Category: Network
Keywords: vpn, connect aagala, remote access
Severity: Medium

## Symptoms
VPN client shows an error or keeps loading.

## Troubleshooting Steps
1. Check that normal internet works.
2. Quit the VPN client and sign in again.
3. Switch the protocol to TCP in settings.
4. Restart the laptop and retry.

## Permitted Actions
- check_service_status("vpn")
- reset_vpn_profile(user_id)
- create_ticket(category="Network")

## When to Escalate
- Still failing after restart.
- The same issue affects multiple users.
