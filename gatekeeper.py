"""
Gatekeeper Rule Engine for Amazon Agent Gatekeeper
Implements the 8 Authorization Rules and Evaluation Priority.
Academic Prototype - University Project Simulation.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from core.data_manager import get_agent, append_audit_log

# Allowed Actions in the System
ALLOWED_ACTIONS = [
    "View Order",
    "Place Order",
    "Return Product",
    "Refund"
]

# Academic Threshold Definition
SPENDING_THRESHOLD_INR = 1000.0  # ₹1,000 threshold for academic prototype simulation

# Rule Definitions with descriptions and academic rationale
RULES_METADATA = {
    "R1": {
        "name": "UNKNOWN AGENT",
        "decision": "BLOCK",
        "description": "If the agent is not registered in the system, block the request immediately.",
        "category": "Identity & Authentication"
    },
    "R2": {
        "name": "REVOKED AGENT",
        "decision": "BLOCK",
        "description": "If the agent has been revoked, block the request immediately to prevent rogue operations.",
        "category": "Identity & Revocation"
    },
    "R3": {
        "name": "VIEW ORDER",
        "decision": "ALLOW",
        "description": "A registered and active agent requesting to view an order is allowed.",
        "category": "Read-Only Action"
    },
    "R4": {
        "name": "LOW-VALUE ORDER",
        "decision": "ALLOW",
        "description": f"A registered and active agent placing an order worth ₹{SPENDING_THRESHOLD_INR:,.0f} or less is allowed.",
        "category": "Routine Transaction"
    },
    "R5": {
        "name": "HIGH-VALUE ORDER",
        "decision": "ASK CUSTOMER",
        "description": f"A registered and active agent placing an order above ₹{SPENDING_THRESHOLD_INR:,.0f} must receive customer confirmation.",
        "category": "Financial Protection"
    },
    "R6": {
        "name": "RETURN PRODUCT",
        "decision": "ASK CUSTOMER",
        "description": "A product return request impacts inventory and customer experience, requiring customer approval.",
        "category": "Customer Confirmation"
    },
    "R7": {
        "name": "REFUND",
        "decision": "ASK CUSTOMER",
        "description": "A refund request directly alters customer account balances and requires explicit customer approval.",
        "category": "Financial Protection"
    },
    "R8": {
        "name": "INVALID OR MISSING INFORMATION",
        "decision": "BLOCK",
        "description": "If required information (customer name, agent, action, or valid amount) is missing or invalid, block the request.",
        "category": "Data Integrity & Validation"
    }
}


def generate_request_id() -> str:
    """Generate a clean, readable unique request ID."""
    now_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    short_uuid = uuid.uuid4().hex[:4].upper()
    return f"REQ-{now_str}-{short_uuid}"


def evaluate_request(
    customer: str,
    agent_id: str,
    action: str,
    amount: Any,
    description: str = "",
    persist_log: bool = True
) -> Dict[str, Any]:
    """
    Evaluates an AI agent request according to the 8 prioritized authorization rules:
    
    Priority Order:
      1. Validate required information (R8)
      2. Check unknown agent (R1)
      3. Check revoked agent (R2)
      4. Evaluate requested action:
         - View Order (R3) -> ALLOW
         - Place Order <= ₹1,000 (R4) -> ALLOW
         - Place Order > ₹1,000 (R5) -> ASK CUSTOMER
         - Return Product (R6) -> ASK CUSTOMER
         - Refund (R7) -> ASK CUSTOMER
      5. Fallback for unhandled conditions (R8) -> BLOCK
    """
    request_id = generate_request_id()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # -------------------------------------------------------------
    # Step 1: Input Validation (Rule R8)
    # -------------------------------------------------------------
    clean_customer = customer.strip() if isinstance(customer, str) else ""
    clean_agent_id = agent_id.strip() if isinstance(agent_id, str) else ""
    clean_action = action.strip() if isinstance(action, str) else ""

    # Parse numeric amount
    parsed_amount: Optional[float] = None
    if amount is not None and str(amount).strip() != "":
        try:
            parsed_amount = float(amount)
        except (ValueError, TypeError):
            parsed_amount = None

    # Check for missing customer
    if not clean_customer:
        return _build_response(
            request_id=request_id,
            timestamp=timestamp,
            customer=clean_customer,
            agent=clean_agent_id,
            action=clean_action,
            amount=parsed_amount if parsed_amount is not None else 0.0,
            decision="BLOCK",
            rule_number="R8",
            reason="Missing required information: Customer name is required and cannot be blank.",
            customer_approval="N/A",
            final_outcome="BLOCKED",
            description=description,
            persist=persist_log
        )

    # Check for missing agent ID
    if not clean_agent_id:
        return _build_response(
            request_id=request_id,
            timestamp=timestamp,
            customer=clean_customer,
            agent=clean_agent_id,
            action=clean_action,
            amount=parsed_amount if parsed_amount is not None else 0.0,
            decision="BLOCK",
            rule_number="R8",
            reason="Missing required information: Agent ID is required and cannot be blank.",
            customer_approval="N/A",
            final_outcome="BLOCKED",
            description=description,
            persist=persist_log
        )

    # Check for unrecognized action
    if clean_action not in ALLOWED_ACTIONS:
        return _build_response(
            request_id=request_id,
            timestamp=timestamp,
            customer=clean_customer,
            agent=clean_agent_id,
            action=clean_action,
            amount=parsed_amount if parsed_amount is not None else 0.0,
            decision="BLOCK",
            rule_number="R8",
            reason=f"Invalid action '{clean_action}'. Permitted actions are: {', '.join(ALLOWED_ACTIONS)}.",
            customer_approval="N/A",
            final_outcome="BLOCKED",
            description=description,
            persist=persist_log
        )

    # Check for negative amount across all actions
    if parsed_amount is not None and parsed_amount < 0:
        return _build_response(
            request_id=request_id,
            timestamp=timestamp,
            customer=clean_customer,
            agent=clean_agent_id,
            action=clean_action,
            amount=parsed_amount,
            decision="BLOCK",
            rule_number="R8",
            reason=f"Invalid amount (₹{parsed_amount:,.2f}). Transaction amount cannot be negative.",
            customer_approval="N/A",
            final_outcome="BLOCKED",
            description=description,
            persist=persist_log
        )

    # Check for invalid/missing amount where strictly required (Place Order, Refund)
    if clean_action in ["Place Order", "Refund"]:
        if parsed_amount is None or parsed_amount <= 0:
            return _build_response(
                request_id=request_id,
                timestamp=timestamp,
                customer=clean_customer,
                agent=clean_agent_id,
                action=clean_action,
                amount=parsed_amount if parsed_amount is not None else 0.0,
                decision="BLOCK",
                rule_number="R8",
                reason=f"Missing or invalid amount for '{clean_action}'. Amount must be a positive number greater than ₹0.",
                customer_approval="N/A",
                final_outcome="BLOCKED",
                description=description,
                persist=persist_log
            )

    safe_amount = parsed_amount if parsed_amount is not None else 0.0

    # -------------------------------------------------------------
    # Step 2: Check Unknown Agent (Rule R1)
    # -------------------------------------------------------------
    agent_data = get_agent(clean_agent_id)
    if agent_data is None:
        return _build_response(
            request_id=request_id,
            timestamp=timestamp,
            customer=clean_customer,
            agent=clean_agent_id,
            action=clean_action,
            amount=safe_amount,
            decision="BLOCK",
            rule_number="R1",
            reason=f"Unknown Agent: Agent '{clean_agent_id}' is not registered in the system.",
            customer_approval="N/A",
            final_outcome="BLOCKED",
            description=description,
            persist=persist_log
        )

    # -------------------------------------------------------------
    # Step 3: Check Revoked Agent (Rule R2)
    # -------------------------------------------------------------
    if agent_data.get("status") == "REVOKED":
        revoked_at = agent_data.get("revoked_at", "Unknown timestamp")
        rev_reason = agent_data.get("revocation_reason", "No reason provided")
        return _build_response(
            request_id=request_id,
            timestamp=timestamp,
            customer=clean_customer,
            agent=clean_agent_id,
            action=clean_action,
            amount=safe_amount,
            decision="BLOCK",
            rule_number="R2",
            reason=f"Revoked Agent: Agent '{clean_agent_id}' was revoked on {revoked_at} (Reason: {rev_reason}) and cannot perform actions.",
            customer_approval="N/A",
            final_outcome="BLOCKED",
            description=description,
            persist=persist_log
        )

    # -------------------------------------------------------------
    # Step 4: Evaluate Action for Active Registered Agent
    # -------------------------------------------------------------
    # Rule R3: View Order -> ALLOW
    if clean_action == "View Order":
        return _build_response(
            request_id=request_id,
            timestamp=timestamp,
            customer=clean_customer,
            agent=clean_agent_id,
            action=clean_action,
            amount=safe_amount,
            decision="ALLOW",
            rule_number="R3",
            reason=f"Registered active agent '{clean_agent_id}' is permitted to view order details for customer '{clean_customer}'.",
            customer_approval="N/A",
            final_outcome="EXECUTED",
            description=description,
            persist=persist_log
        )

    # Place Order: Evaluate amount threshold
    if clean_action == "Place Order":
        # Rule R4: Order amount ₹1,000 or less -> ALLOW
        if safe_amount <= SPENDING_THRESHOLD_INR:
            return _build_response(
                request_id=request_id,
                timestamp=timestamp,
                customer=clean_customer,
                agent=clean_agent_id,
                action=clean_action,
                amount=safe_amount,
                decision="ALLOW",
                rule_number="R4",
                reason=f"Low-value purchase: Order amount of ₹{safe_amount:,.2f} is within the automated threshold (₹{SPENDING_THRESHOLD_INR:,.0f} or less).",
                customer_approval="N/A",
                final_outcome="EXECUTED",
                description=description,
                persist=persist_log
            )
        # Rule R5: Order amount above ₹1,000 -> ASK CUSTOMER
        else:
            return _build_response(
                request_id=request_id,
                timestamp=timestamp,
                customer=clean_customer,
                agent=clean_agent_id,
                action=clean_action,
                amount=safe_amount,
                decision="ASK CUSTOMER",
                rule_number="R5",
                reason=f"High-value purchase: Order amount of ₹{safe_amount:,.2f} exceeds ₹{SPENDING_THRESHOLD_INR:,.0f}. Customer approval is required before execution.",
                customer_approval="PENDING",
                final_outcome="PENDING",
                description=description,
                persist=persist_log
            )

    # Rule R6: Return Product -> ASK CUSTOMER
    if clean_action == "Return Product":
        return _build_response(
            request_id=request_id,
            timestamp=timestamp,
            customer=clean_customer,
            agent=clean_agent_id,
            action=clean_action,
            amount=safe_amount,
            decision="ASK CUSTOMER",
            rule_number="R6",
            reason=f"Product return initiated by agent '{clean_agent_id}' for customer '{clean_customer}'. Explicit customer confirmation is required.",
            customer_approval="PENDING",
            final_outcome="PENDING",
            description=description,
            persist=persist_log
        )

    # Rule R7: Refund -> ASK CUSTOMER
    if clean_action == "Refund":
        return _build_response(
            request_id=request_id,
            timestamp=timestamp,
            customer=clean_customer,
            agent=clean_agent_id,
            action=clean_action,
            amount=safe_amount,
            decision="ASK CUSTOMER",
            rule_number="R7",
            reason=f"Refund request of ₹{safe_amount:,.2f} impacts customer financial balance. Explicit customer approval is required.",
            customer_approval="PENDING",
            final_outcome="PENDING",
            description=description,
            persist=persist_log
        )

    # -------------------------------------------------------------
    # Step 5: Fallback safety net (Rule R8)
    # -------------------------------------------------------------
    return _build_response(
        request_id=request_id,
        timestamp=timestamp,
        customer=clean_customer,
        agent=clean_agent_id,
        action=clean_action,
        amount=safe_amount,
        decision="BLOCK",
        rule_number="R8",
        reason="Unspecified or unhandled transaction parameters. Request blocked by default.",
        customer_approval="N/A",
        final_outcome="BLOCKED",
        description=description,
        persist=persist_log
    )


def _build_response(
    request_id: str,
    timestamp: str,
    customer: str,
    agent: str,
    action: str,
    amount: float,
    decision: str,
    rule_number: str,
    reason: str,
    customer_approval: str,
    final_outcome: str,
    description: str = "",
    persist: bool = True
) -> Dict[str, Any]:
    """Helper to structure decision dictionary and persist to audit log."""
    response = {
        "request_id": request_id,
        "timestamp": timestamp,
        "customer": customer,
        "agent": agent,
        "action": action,
        "amount": f"{amount:.2f}",
        "decision": decision,
        "rule_number": rule_number,
        "reason": reason,
        "customer_approval": customer_approval,
        "final_outcome": final_outcome,
        "description": description
    }

    if persist:
        append_audit_log(response)

    return response
