from __future__ import annotations

import json
from typing import Any

from tools._shared import ROOT, err


TICKET_FILE = ROOT / "helpdesk_data" / "tickets.json"
LIVE_TICKET_DIR = ROOT / "tickets"


def check_ticket_status(ticket_id: str = "") -> dict[str, Any]:
    """Look up an existing helpdesk ticket by its ticket ID.

    Searches both the mock ticket store and any tickets created during the
    current session (via create_ticket). Returns ticket details including
    status, priority, assignment, and timeline.
    """
    wanted_id = (ticket_id or "").strip().upper()
    if not wanted_id:
        return {"tool": "check_ticket_status", "error": "missing_ticket_id",
                "message": "A ticket ID is required (e.g. INC-1042, CHG-221)."}

    try:
        # Search in mock ticket store
        if TICKET_FILE.exists():
            data = json.loads(TICKET_FILE.read_text(encoding="utf-8"))
            for ticket in data.get("tickets", []):
                if ticket.get("ticket_id", "").upper() == wanted_id:
                    return {
                        "tool": "check_ticket_status",
                        "ticket_id": ticket["ticket_id"],
                        "ticket": {
                            "ticket_id": ticket["ticket_id"],
                            "summary": ticket.get("summary", ""),
                            "priority": ticket.get("priority", "unknown"),
                            "status": ticket.get("status", "unknown"),
                            "asset_id": ticket.get("asset_id"),
                            "assigned_to": ticket.get("assigned_to"),
                            "created_at": ticket.get("created_at"),
                            "updated_at": ticket.get("updated_at"),
                            "resolved_at": ticket.get("resolved_at"),
                            "related_service": ticket.get("related_service"),
                            "notes": ticket.get("notes", ""),
                        },
                        "source": "mock_ticket_store",
                        "snapshot_at": data.get("snapshot_at"),
                    }

        # Search in live tickets created by create_ticket
        if LIVE_TICKET_DIR.exists():
            for ticket_file in LIVE_TICKET_DIR.glob("*.json"):
                try:
                    ticket = json.loads(ticket_file.read_text(encoding="utf-8"))
                    if ticket.get("ticket_id", "").upper() == wanted_id:
                        return {
                            "tool": "check_ticket_status",
                            "ticket_id": ticket["ticket_id"],
                            "ticket": {
                                "ticket_id": ticket["ticket_id"],
                                "summary": ticket.get("summary", ""),
                                "priority": ticket.get("priority", "unknown"),
                                "status": "open",
                                "asset_id": ticket.get("asset_id"),
                                "assigned_to": None,
                                "created_at": ticket.get("created_at"),
                                "updated_at": ticket.get("created_at"),
                                "resolved_at": None,
                                "related_service": None,
                                "notes": "Newly created ticket.",
                            },
                            "source": "live_session",
                        }
                except (json.JSONDecodeError, KeyError):
                    continue

        return {
            "tool": "check_ticket_status",
            "ticket_id": wanted_id,
            "error": "ticket_not_found",
            "message": f"No ticket found with ID {wanted_id}.",
        }

    except Exception as exc:
        return err("check_ticket_status", exc)
