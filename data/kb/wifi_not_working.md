# Wi-Fi Not Working

Category: Network
Severity: Medium
Keywords: wifi, wireless, no internet, network, disconnected

## Symptoms
- Wi-Fi icon shows "No internet" or the network is not listed.
- Connection keeps dropping.

## Troubleshooting Steps
1. Turn Wi-Fi off and on again.
2. Turn Airplane mode on for 10 seconds, then off.
3. Forget the network and reconnect with the password.
4. Restart the laptop.
5. Check whether other devices connect to the same Wi-Fi.
6. Run Windows Network Troubleshooter.

## Permitted Actions
- check_service_status("wifi")
- create_ticket(category="Network")

## When to Escalate
- Other devices also cannot connect (router or access point issue).
