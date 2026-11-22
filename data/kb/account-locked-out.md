# Account locked out
Category: Account
Keywords: locked, account lock, too many attempts
Severity: Medium

## Symptoms
Sign-in fails with an account locked message.

## Troubleshooting Steps
1. Wait 15 minutes for auto-unlock.
2. Use self-service unlock if available.
3. Confirm caps lock is off and retry.
4. Reset the password if still locked.

## Permitted Actions
- unlock_account(user_id)
- create_ticket(category="Account")

## When to Escalate
- Repeated lockouts without user attempts (possible attack).
