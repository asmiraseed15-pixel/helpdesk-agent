# Software installation request
Category: Software
Keywords: install, software request, need app
Severity: Low

## Symptoms
User needs an approved application installed.

## Troubleshooting Steps
1. Check the approved software list.
2. Open the company software portal.
3. Request the app and wait for approval.
4. Install it from the portal.

## Permitted Actions
- create_install_request(user_id, app_name)
- create_ticket(category="Software")

## When to Escalate
- Software is not on the approved list (needs security approval).
- Admin rights or a paid license is required.
