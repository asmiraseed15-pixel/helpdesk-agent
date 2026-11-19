# Printer Offline

Category: Hardware
Severity: Low
Keywords: printer, offline, cannot print, print queue, stuck

## Symptoms
- Printer shows "Offline" in Windows.
- Print jobs are stuck in the queue.

## Troubleshooting Steps
1. Check that the printer is powered on and connected to the network.
2. Open Settings > Printers and clear all pending print jobs.
3. Restart the printer.
4. Remove the printer and add it again.
5. Restart the Print Spooler service.

## Permitted Actions
- check_service_status("print_spooler")
- create_ticket(category="Hardware")

## When to Escalate
- Printer shows a hardware error (paper jam, toner, display error).
- Nobody in the office can print.
