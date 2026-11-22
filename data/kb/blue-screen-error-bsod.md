# Blue screen error (BSOD)
Category: Hardware
Keywords: blue screen, bsod, crash, restart
Severity: High

## Symptoms
Laptop shows a blue screen and restarts.

## Troubleshooting Steps
1. Note the stop code on the screen.
2. Remove newly connected USB devices.
3. Boot into safe mode and uninstall recent updates or drivers.
4. Run: sfc /scannow.

## Permitted Actions
- collect_crash_logs(device_id)
- create_ticket(category="Hardware")

## When to Escalate
- Blue screen repeats more than twice.
