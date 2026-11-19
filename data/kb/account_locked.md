# Account Locked

Category: Account
Severity: Medium
Keywords: account locked, locked out, too many attempts, login failed, cannot sign in

## Symptoms
- Message "Your account has been locked".
- Login fails after several wrong password attempts.

## Troubleshooting Steps
1. Wait 15 minutes, the account may unlock automatically.
2. Use the self-service portal to unlock the account.
3. Make sure Caps Lock is off and the correct keyboard language is selected.
4. Remove the old saved password from other devices (phone mail app, Wi-Fi) that keep retrying.

## Permitted Actions
- reset_password_request(user_id)
- create_ticket(category="Account")

## When to Escalate
- Account locks again within an hour (possible security issue).
- User suspects someone else tried to log in.