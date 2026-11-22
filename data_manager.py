"""
Data Manager Module for Amazon Agent Gatekeeper
Handles persistent storage for Agents (JSON) and Audit Logs (CSV).
Academic Prototype - University Project Simulation.
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
AGENTS_FILE = os.path.join(DATA_DIR, "agents.json")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "audit_log.csv")

AUDIT_LOG_COLUMNS = [
    "request_id",
    "timestamp",
    "customer",
    "agent",
    "action",
    "amount",
    "decision",
    "rule_number",
    "reason",
    "customer_approval",
    "final_outcome"
]

DEFAULT_AGENTS = {
    "Agent-Alice": {
        "agent_id": "Agent-Alice",
        "name": "Alice - Customer Support",
        "role": "Customer Support Specialist",
        "status": "ACTIVE",
        "registered_at": "2026-11-20T10:00:00",
        "revoked_at": None,
        "revocation_reason": None
    },
    "Agent-Bob": {
        "agent_id": "Agent-Bob",
        "name": "Bob - Fulfillment",
        "role": "Fulfillment Assistant",
        "status": "REVOKED",
        "registered_at": "2026-11-18T09:30:00",
        "revoked_at": "2026-11-21T14:15:00",
        "revocation_reason": "Security policy compliance review failure"
    },
    "Agent-Charlie": {
        "agent_id": "Agent-Charlie",
        "name": "Charlie - Returns & Refunds",
        "role": "Returns Specialist",
        "status": "ACTIVE",
        "registered_at": "2026-11-19T11:20:00",
        "revoked_at": None,
        "revocation_reason": None
    },
    "Agent-Diana": {
        "agent_id": "Agent-Diana",
        "name": "Diana - Prime Order Manager",
        "role": "Senior Order Manager",
        "status": "ACTIVE",
        "registered_at": "2026-11-22T08:00:00",
        "revoked_at": None,
        "revocation_reason": None
    }
}

DEFAULT_AUDIT_LOGS = [
    {
        "request_id": "REQ-20261121-143010-001",
        "timestamp": "2026-11-21 14:30:10",
        "customer": "Pooja Verma",
        "agent": "Agent-Alice",
        "action": "View Order",
        "amount": 0.00,
        "decision": "ALLOW",
        "rule_number": "R3",
        "reason": "Registered and active agent is permitted to view order details.",
        "customer_approval": "N/A",
        "final_outcome": "EXECUTED"
    },
    {
        "request_id": "REQ-20261121-151022-002",
        "timestamp": "2026-11-21 15:10:22",
        "customer": "Rohan Mehta",
        "agent": "Agent-Alice",
        "action": "Place Order",
        "amount": 749.00,
        "decision": "ALLOW",
        "rule_number": "R4",
        "reason": "Order amount (₹749.00) is within the automated threshold (₹1,000 or less).",
        "customer_approval": "N/A",
        "final_outcome": "EXECUTED"
    },
    {
        "request_id": "REQ-20261121-164505-003",
        "timestamp": "2026-11-21 16:45:05",
        "customer": "Simran Kaur",
        "agent": "Agent-Bob",
        "action": "Place Order",
        "amount": 500.00,
        "decision": "BLOCK",
        "rule_number": "R2",
        "reason": "Agent 'Agent-Bob' has been revoked on 2026-11-21T14:15:00 and cannot execute actions.",
        "customer_approval": "N/A",
        "final_outcome": "BLOCKED"
    }
]


def ensure_data_directory():
    """Ensure data directory and persistent files exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(AGENTS_FILE):
        with open(AGENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_AGENTS, f, indent=2)
    if not os.path.exists(AUDIT_LOG_FILE):
        with open(AUDIT_LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=AUDIT_LOG_COLUMNS)
            writer.writeheader()
            for row in DEFAULT_AUDIT_LOGS:
                writer.writerow(row)


# --- Agent Management Functions ---

def load_agents() -> Dict[str, dict]:
    """Load all agents from the JSON file."""
    ensure_data_directory()
    try:
        with open(AGENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading agents file: {e}")
        return {}


def save_agents(agents: Dict[str, dict]) -> bool:
    """Save agents dictionary persistently to JSON."""
    ensure_data_directory()
    try:
        with open(AGENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(agents, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving agents file: {e}")
        return False


def get_agent(agent_id: str) -> Optional[dict]:
    """Retrieve an agent by ID."""
    agents = load_agents()
    return agents.get(agent_id.strip()) if agent_id else None


def register_agent(agent_id: str, name: str, role: str) -> Tuple[bool, str]:
    """
    Register a new agent with status ACTIVE.
    Prevents duplicate agent IDs.
    """
    if not agent_id or not agent_id.strip():
        return False, "Agent ID cannot be empty."
    if not name or not name.strip():
        return False, "Agent Name cannot be empty."

    clean_id = agent_id.strip()
    agents = load_agents()

    if clean_id in agents:
        return False, f"Agent ID '{clean_id}' already exists. Duplicate registration not permitted."

    now_iso = datetime.now().isoformat(timespec="seconds")
    agents[clean_id] = {
        "agent_id": clean_id,
        "name": name.strip(),
        "role": role.strip() if role else "General Support",
        "status": "ACTIVE",
        "registered_at": now_iso,
        "revoked_at": None,
        "revocation_reason": None
    }

    if save_agents(agents):
        return True, f"Agent '{clean_id}' successfully registered as ACTIVE."
    return False, "Failed to persist new agent to storage."


def revoke_agent(agent_id: str, reason: str = "Administrative revocation") -> Tuple[bool, str]:
    """
    Revoke an active agent, recording timestamp and reason.
    """
    clean_id = agent_id.strip() if agent_id else ""
    agents = load_agents()

    if clean_id not in agents:
        return False, f"Agent '{clean_id}' not found."

    agent = agents[clean_id]
    if agent.get("status") == "REVOKED":
        return False, f"Agent '{clean_id}' is already revoked."

    now_iso = datetime.now().isoformat(timespec="seconds")
    agent["status"] = "REVOKED"
    agent["revoked_at"] = now_iso
    agent["revocation_reason"] = reason.strip() if reason else "Administrative revocation"

    if save_agents(agents):
        return True, f"Agent '{clean_id}' has been REVOKED at {now_iso}."
    return False, "Failed to save revocation status."


def reactivate_agent(agent_id: str) -> Tuple[bool, str]:
    """
    Reactivate a revoked agent (convenience utility for testing and demos).
    """
    clean_id = agent_id.strip() if agent_id else ""
    agents = load_agents()

    if clean_id not in agents:
        return False, f"Agent '{clean_id}' not found."

    agent = agents[clean_id]
    agent["status"] = "ACTIVE"
    agent["revoked_at"] = None
    agent["revocation_reason"] = None

    if save_agents(agents):
        return True, f"Agent '{clean_id}' has been reactivated to ACTIVE status."
    return False, "Failed to update agent status."


def delete_agent(agent_id: str) -> bool:
    """Delete an agent from the JSON file (used for test teardown / cleanup)."""
    clean_id = agent_id.strip() if agent_id else ""
    agents = load_agents()
    if clean_id in agents:
        del agents[clean_id]
        return save_agents(agents)
    return False



# --- Audit Log Functions ---

def load_audit_log_df() -> pd.DataFrame:
    """Load audit log as a pandas DataFrame."""
    ensure_data_directory()
    try:
        df = pd.read_csv(AUDIT_LOG_FILE)
        # Ensure all columns exist
        for col in AUDIT_LOG_COLUMNS:
            if col not in df.columns:
                df[col] = "N/A"
        return df
    except Exception as e:
        print(f"Error loading audit log: {e}")
        return pd.DataFrame(columns=AUDIT_LOG_COLUMNS)


def append_audit_log(entry: dict) -> bool:
    """Append a single request evaluation to the audit log CSV."""
    ensure_data_directory()
    try:
        # Standardize entry keys
        row = {col: entry.get(col, "") for col in AUDIT_LOG_COLUMNS}
        file_exists = os.path.exists(AUDIT_LOG_FILE) and os.path.getsize(AUDIT_LOG_FILE) > 0
        with open(AUDIT_LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=AUDIT_LOG_COLUMNS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        return True
    except Exception as e:
        print(f"Error appending to audit log: {e}")
        return False


def update_audit_log_outcome(request_id: str, customer_approval: str, final_outcome: str) -> bool:
    """
    Update customer confirmation and final outcome for an existing request in the audit log CSV.
    """
    ensure_data_directory()
    try:
        df = pd.read_csv(AUDIT_LOG_FILE)
        mask = df["request_id"] == request_id
        if mask.any():
            df.loc[mask, "customer_approval"] = customer_approval
            df.loc[mask, "final_outcome"] = final_outcome
            df.to_csv(AUDIT_LOG_FILE, index=False)
            return True
        return False
    except Exception as e:
        print(f"Error updating audit log: {e}")
        return False


def get_dashboard_metrics() -> dict:
    """Compute aggregate dashboard metrics from agents and audit log."""
    agents = load_agents()
    total_agents = len(agents)
    active_agents = sum(1 for a in agents.values() if a.get("status") == "ACTIVE")
    revoked_agents = sum(1 for a in agents.values() if a.get("status") == "REVOKED")

    df = load_audit_log_df()
    total_requests = len(df)
    allowed_requests = int((df["decision"] == "ALLOW").sum()) if total_requests > 0 else 0
    ask_requests = int((df["decision"] == "ASK CUSTOMER").sum()) if total_requests > 0 else 0
    blocked_requests = int((df["decision"] == "BLOCK").sum()) if total_requests > 0 else 0

    return {
        "total_agents": total_agents,
        "active_agents": active_agents,
        "revoked_agents": revoked_agents,
        "total_requests": total_requests,
        "allowed_requests": allowed_requests,
        "ask_requests": ask_requests,
        "blocked_requests": blocked_requests
    }
