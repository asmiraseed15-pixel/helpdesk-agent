# Wi-Fi connected but no internet
Category: Network
Keywords: wifi, no internet, internet illa
Severity: Medium

## Symptoms
Wi-Fi shows connected but pages do not load.

## Troubleshooting Steps
1. Toggle Wi-Fi off and on.
2. Forget the network and reconnect.
3. Run: ipconfig /release then ipconfig /renew.
4. Restart the router or try another network.

## Permitted Actions
- check_service_status("wifi")
- create_ticket(category="Network")

## When to Escalate
- Other devices also cannot connect (router or access point issue).
