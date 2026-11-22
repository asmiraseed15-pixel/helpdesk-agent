# Laptop battery draining fast
Category: Hardware
Keywords: battery, drain, charging, battery low
Severity: Low

## Symptoms
Battery drops quickly or does not charge.

## Troubleshooting Steps
1. Check the charger and cable.
2. Lower screen brightness and enable battery saver.
3. Check which apps use the most battery in Settings.
4. Run: powercfg /batteryreport.

## Permitted Actions
- generate_battery_report(device_id)
- create_ticket(category="Hardware")

## When to Escalate
- Battery health is below 60%.
