# Printer not printing
Category: Hardware
Keywords: printer, print aagala, print stuck
Severity: Low

## Symptoms
Print jobs stay in the queue.

## Troubleshooting Steps
1. Check power, paper and cable or Wi-Fi.
2. Clear the print queue.
3. Restart the Print Spooler service.
4. Remove and re-add the printer.

## Permitted Actions
- check_service_status("print_spooler")
- clear_print_queue(printer_id)
- create_ticket(category="Hardware")

## When to Escalate
- Printer shows a hardware error (paper jam, toner, display error).
- Nobody in the office can print.
