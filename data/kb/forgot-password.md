# Forgot password
Category: Account
Keywords: forgot password, password marandhuten, reset
Severity: Low

## Symptoms
User cannot remember the password.

## Troubleshooting Steps
1. Open the self-service reset page.
2. Verify with the code sent to your phone.
3. Choose a new password with 12+ characters.
4. Sign in again on all devices.

## Permitted Actions
- reset_password_request(user_id)
- create_ticket(category="Account")

## When to Escalate
- User has no access to the registered phone or email.
- Reset link is not received after 15 minutes.
