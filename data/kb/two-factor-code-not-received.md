# Two-factor code not received
Category: Security
Keywords: otp, 2fa, mfa, code not coming
Severity: Medium

## Symptoms
SMS or app code does not arrive.

## Troubleshooting Steps
1. Check phone signal and the correct number.
2. Wait 60 seconds and request a new code.
3. Check the time on your phone is set to automatic.
4. Use a backup code or another method.

## Permitted Actions
- reset_mfa_method(user_id)
- create_ticket(category="Security")

## When to Escalate
- Phone is lost or the number has changed.
