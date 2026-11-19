# Password Reset

Category: Account
Severity: Low
Keywords: password, forgot password, reset, expired password, cannot login

## Symptoms
- User forgot the password.
- Password expired and login is blocked.

## Troubleshooting Steps
1. Open the company self-service password portal.
2. Click "Forgot Password" and verify identity with the registered phone or email.
3. Create a new password with at least 12 characters, including a number and a symbol.
4. Log in again on all devices with the new password.

## Permitted Actions
- reset_password_request(user_id)

## When to Escalate
- User has no access to the registered phone or email.
- Reset link is not received after 15 minutes.
