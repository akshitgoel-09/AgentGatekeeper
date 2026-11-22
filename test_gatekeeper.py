"""
Automated Test Suite for Amazon Agent Gatekeeper
Tests all 8 authorization rules, agent management, and edge cases.
Uses Pytest for automated execution.
Academic Prototype - University Project Simulation.
"""

import os
import pytest
from core.gatekeeper import evaluate_request
from core.data_manager import (
    register_agent,
    revoke_agent,
    reactivate_agent,
    delete_agent,
    get_agent,
    load_agents,
    update_audit_log_outcome,
    load_audit_log_df
)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure standard active and revoked test agents exist before each test."""
    agents = load_agents()

    # Ensure Agent-Alice is active
    if "Agent-Alice" not in agents:
        register_agent("Agent-Alice", "Alice Support", "Customer Support Specialist")
    else:
        reactivate_agent("Agent-Alice")

    # Ensure Agent-Bob is revoked
    if "Agent-Bob" not in agents:
        register_agent("Agent-Bob", "Bob Fulfillment", "Fulfillment Assistant")
    revoke_agent("Agent-Bob", "Test Revocation Policy")

    yield


# =====================================================================
# Core 6 Specification Tests
# =====================================================================

def test_rule_1_unknown_agent():
    """
    Test 1: Unknown agent attempts to view an order -> BLOCK, R1.
    """
    res = evaluate_request(
        customer="Priya Sharma",
        agent_id="Agent-Ghost-999",
        action="View Order",
        amount=0.0,
        persist_log=False
    )
    assert res["decision"] == "BLOCK"
    assert res["rule_number"] == "R1"
    assert "Unknown Agent" in res["reason"]
    assert res["final_outcome"] == "BLOCKED"


def test_rule_1_typed_unknown_agent_999():
    """
    Test: Explicitly verify that typing 'Unknown-Agent-999' on a valid request returns BLOCK under Rule R1.
    """
    res = evaluate_request(
        customer="Priya Sharma",
        agent_id="Unknown-Agent-999",
        action="Place Order",
        amount=750.0,
        persist_log=False
    )
    assert res["decision"] == "BLOCK"
    assert res["rule_number"] == "R1"
    assert "Unknown Agent" in res["reason"]
    assert "Unknown-Agent-999" in res["reason"]
    assert res["final_outcome"] == "BLOCKED"


def test_registered_agent_mode_allows_valid_order():
    """
    Test: Selecting a registered active agent (Agent-Alice) on a routine order returns ALLOW under Rule R4.
    """
    res = evaluate_request(
        customer="Priya Sharma",
        agent_id="Agent-Alice",
        action="Place Order",
        amount=750.0,
        persist_log=False
    )
    assert res["decision"] == "ALLOW"
    assert res["rule_number"] == "R4"
    assert res["final_outcome"] == "EXECUTED"


def test_rule_2_revoked_agent():
    """
    Test 2: Revoked agent attempts to place an order -> BLOCK, R2.
    """
    res = evaluate_request(
        customer="Rahul Verma",
        agent_id="Agent-Bob",
        action="Place Order",
        amount=500.0,
        persist_log=False
    )
    assert res["decision"] == "BLOCK"
    assert res["rule_number"] == "R2"
    assert "Revoked Agent" in res["reason"]
    assert res["final_outcome"] == "BLOCKED"


def test_rule_3_registered_agent_view_order():
    """
    Test 3: Registered agent views an order -> ALLOW, R3.
    """
    res = evaluate_request(
        customer="Amit Kumar",
        agent_id="Agent-Alice",
        action="View Order",
        amount=0.0,
        persist_log=False
    )
    assert res["decision"] == "ALLOW"
    assert res["rule_number"] == "R3"
    assert res["final_outcome"] == "EXECUTED"


def test_rule_4_low_value_order():
    """
    Test 4: Registered agent places an order worth ₹800 (<= ₹1,000) -> ALLOW, R4.
    """
    res = evaluate_request(
        customer="Sneha Patel",
        agent_id="Agent-Alice",
        action="Place Order",
        amount=800.0,
        persist_log=False
    )
    assert res["decision"] == "ALLOW"
    assert res["rule_number"] == "R4"
    assert "Low-value purchase" in res["reason"]
    assert res["final_outcome"] == "EXECUTED"


def test_rule_5_high_value_order():
    """
    Test 5: Registered agent places an order worth ₹2,000 (> ₹1,000) -> ASK CUSTOMER, R5.
    """
    res = evaluate_request(
        customer="Vikram Malhotra",
        agent_id="Agent-Alice",
        action="Place Order",
        amount=2000.0,
        persist_log=False
    )
    assert res["decision"] == "ASK CUSTOMER"
    assert res["rule_number"] == "R5"
    assert "High-value purchase" in res["reason"]
    assert res["customer_approval"] == "PENDING"
    assert res["final_outcome"] == "PENDING"


def test_rule_7_refund():
    """
    Test 6: Registered agent requests a refund -> ASK CUSTOMER, R7.
    """
    res = evaluate_request(
        customer="Deepak Joshi",
        agent_id="Agent-Alice",
        action="Refund",
        amount=1500.0,
        persist_log=False
    )
    assert res["decision"] == "ASK CUSTOMER"
    assert res["rule_number"] == "R7"
    assert "Refund request" in res["reason"]
    assert res["customer_approval"] == "PENDING"
    assert res["final_outcome"] == "PENDING"


# =====================================================================
# Additional Comprehensive Tests (R6, R8, Agent Ops, Edge Cases)
# =====================================================================

def test_rule_6_return_product():
    """
    Test: Return product requires customer confirmation -> ASK CUSTOMER, R6.
    """
    res = evaluate_request(
        customer="Ananya Iyer",
        agent_id="Agent-Alice",
        action="Return Product",
        amount=0.0,
        persist_log=False
    )
    assert res["decision"] == "ASK CUSTOMER"
    assert res["rule_number"] == "R6"
    assert "Product return initiated" in res["reason"]
    assert res["customer_approval"] == "PENDING"


def test_rule_8_missing_customer_name():
    """
    Test: Missing customer name triggers Rule R8 -> BLOCK.
    """
    res = evaluate_request(
        customer="   ",
        agent_id="Agent-Alice",
        action="Place Order",
        amount=500.0,
        persist_log=False
    )
    assert res["decision"] == "BLOCK"
    assert res["rule_number"] == "R8"
    assert "Customer name is required" in res["reason"]


def test_rule_8_missing_agent_id():
    """
    Test: Missing agent ID triggers Rule R8 -> BLOCK.
    """
    res = evaluate_request(
        customer="Priya Sharma",
        agent_id="",
        action="View Order",
        amount=0.0,
        persist_log=False
    )
    assert res["decision"] == "BLOCK"
    assert res["rule_number"] == "R8"
    assert "Agent ID is required" in res["reason"]


def test_rule_8_invalid_action():
    """
    Test: Unrecognized action triggers Rule R8 -> BLOCK.
    """
    res = evaluate_request(
        customer="Priya Sharma",
        agent_id="Agent-Alice",
        action="Delete Customer Account",
        amount=0.0,
        persist_log=False
    )
    assert res["decision"] == "BLOCK"
    assert res["rule_number"] == "R8"
    assert "Invalid action" in res["reason"]


def test_rule_8_invalid_amount_negative():
    """
    Test: Negative amount triggers Rule R8 -> BLOCK.
    """
    res = evaluate_request(
        customer="Priya Sharma",
        agent_id="Agent-Alice",
        action="Place Order",
        amount=-250.0,
        persist_log=False
    )
    assert res["decision"] == "BLOCK"
    assert res["rule_number"] == "R8"
    assert "Transaction amount cannot be negative" in res["reason"]


def test_rule_8_zero_amount_on_order():
    """
    Test: Place Order with zero amount triggers Rule R8 -> BLOCK.
    """
    res = evaluate_request(
        customer="Priya Sharma",
        agent_id="Agent-Alice",
        action="Place Order",
        amount=0.0,
        persist_log=False
    )
    assert res["decision"] == "BLOCK"
    assert res["rule_number"] == "R8"
    assert "Amount must be a positive number" in res["reason"]


def test_agent_registration_and_duplicate_prevention():
    """
    Test: Register a new agent and verify duplicate registration is blocked.
    """
    test_agent_id = "Agent-Test-Unique-01"
    delete_agent(test_agent_id)

    try:
        success, msg = register_agent(test_agent_id, "Test Agent", "Quality Assurance")
        assert success is True
        assert "successfully registered" in msg

        # Duplicate check
        dup_success, dup_msg = register_agent(test_agent_id, "Duplicate Agent", "QA")
        assert dup_success is False
        assert "already exists" in dup_msg
    finally:
        delete_agent(test_agent_id)


def test_agent_revocation_and_timestamps():
    """
    Test: Revoking an agent records timestamp and reason, and prevents actions.
    """
    test_agent_id = "Agent-To-Revoke"
    delete_agent(test_agent_id)

    try:
        register_agent(test_agent_id, "Temp Agent", "Temporary")
        
        # Revoke
        rev_ok, rev_msg = revoke_agent(test_agent_id, "Audit Compliance Fail")
        assert rev_ok is True
        assert "REVOKED" in rev_msg

        # Verify agent state
        agent = get_agent(test_agent_id)
        assert agent["status"] == "REVOKED"
        assert agent["revoked_at"] is not None
        assert agent["revocation_reason"] == "Audit Compliance Fail"

        # Verify action is blocked under R2
        eval_res = evaluate_request("Test User", test_agent_id, "View Order", 0.0, persist_log=False)
        assert eval_res["decision"] == "BLOCK"
        assert eval_res["rule_number"] == "R2"
    finally:
        delete_agent(test_agent_id)


def test_customer_confirmation_audit_update():
    """
    Test: Customer confirmation updates audit log properly.
    """
    eval_res = evaluate_request(
        customer="Customer Confirmation Test",
        agent_id="Agent-Alice",
        action="Place Order",
        amount=3500.0,
        persist_log=True
    )
    req_id = eval_res["request_id"]
    assert eval_res["decision"] == "ASK CUSTOMER"
    assert eval_res["final_outcome"] == "PENDING"

    # Simulate customer clicking confirm
    update_ok = update_audit_log_outcome(req_id, "APPROVED", "EXECUTED")
    assert update_ok is True

    # Verify in audit log DF
    df = load_audit_log_df()
    row = df[df["request_id"] == req_id].iloc[0]
    assert row["customer_approval"] == "APPROVED"
    assert row["final_outcome"] == "EXECUTED"
