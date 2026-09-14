---
name: check_ticket_status
track: team_bonus
kind: local_read
provider: mock_ticket_store
requires_env: []
inputs: [ticket_id]
outputs: [ticket]
side_effect: false
---
# check_ticket_status

Looks up an existing helpdesk ticket by its ticket ID and returns its current
status, priority, assignment, and timeline. Reads from the mock ticket store
and any tickets created by `create_ticket` during the session.

This is a read-only tool with no side effects. A valid ticket ID (e.g.
INC-1042, CHG-221, LAB-xxxxxxxx) is required.
