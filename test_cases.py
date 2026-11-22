"""
Standalone Sample Test Cases Runner for Amazon Agent Gatekeeper
Executes the sample test cases and outputs a clear terminal summary table.
Academic Prototype - University Project Simulation.
"""

from core.gatekeeper import evaluate_request
from core.data_manager import (
    register_agent,
    revoke_agent,
    reactivate_agent,
    delete_agent,
    get_agent,
    load_agents
)


def run_standalone_tests():
    print("=" * 80)
    print(" AMAZON AGENT GATEKEEPER - AUTOMATED TEST SUITE")
    print(" Academic Simulation | Evaluating 8 Authorization Rules & Lifecycle")
    print("=" * 80)

    # Setup environment
    agents = load_agents()
    if "Agent-Alice" not in agents:
        register_agent("Agent-Alice", "Alice Support", "Customer Support Specialist")
    else:
        reactivate_agent("Agent-Alice")

    if "Agent-Bob" not in agents:
        register_agent("Agent-Bob", "Bob Fulfillment", "Fulfillment Assistant")
    revoke_agent("Agent-Bob", "Revocation Test Policy")

    # Define the 11 comprehensive test scenarios
    test_scenarios = [
        {
            "id": "Test 1",
            "name": "Unknown Agent (R1)",
            "customer": "Priya Sharma",
            "agent": "Unknown-Agent-999",
            "action": "View Order",
            "amount": 0.0,
            "expected_decision": "BLOCK",
            "expected_rule": "R1"
        },
        {
            "id": "Test 2",
            "name": "Revoked Agent (R2)",
            "customer": "Rahul Verma",
            "agent": "Agent-Bob",
            "action": "Place Order",
            "amount": 500.0,
            "expected_decision": "BLOCK",
            "expected_rule": "R2"
        },
        {
            "id": "Test 3",
            "name": "Registered Agent Views Order (R3)",
            "customer": "Amit Kumar",
            "agent": "Agent-Alice",
            "action": "View Order",
            "amount": 0.0,
            "expected_decision": "ALLOW",
            "expected_rule": "R3"
        },
        {
            "id": "Test 4",
            "name": "Low-Value Order <= ₹1,000 (R4)",
            "customer": "Sneha Patel",
            "agent": "Agent-Alice",
            "action": "Place Order",
            "amount": 800.0,
            "expected_decision": "ALLOW",
            "expected_rule": "R4"
        },
        {
            "id": "Test 5",
            "name": "High-Value Order > ₹1,000 (R5)",
            "customer": "Vikram Malhotra",
            "agent": "Agent-Alice",
            "action": "Place Order",
            "amount": 2000.0,
            "expected_decision": "ASK CUSTOMER",
            "expected_rule": "R5"
        },
        {
            "id": "Test 6",
            "name": "Refund Request (R7)",
            "customer": "Deepak Joshi",
            "agent": "Agent-Alice",
            "action": "Refund",
            "amount": 1500.0,
            "expected_decision": "ASK CUSTOMER",
            "expected_rule": "R7"
        },
        {
            "id": "Test 7",
            "name": "Return Product (R6)",
            "customer": "Ananya Iyer",
            "agent": "Agent-Alice",
            "action": "Return Product",
            "amount": 0.0,
            "expected_decision": "ASK CUSTOMER",
            "expected_rule": "R6"
        },
        {
            "id": "Test 8",
            "name": "Missing Customer Name (R8)",
            "customer": "",
            "agent": "Agent-Alice",
            "action": "Place Order",
            "amount": 500.0,
            "expected_decision": "BLOCK",
            "expected_rule": "R8"
        },
        {
            "id": "Test 9",
            "name": "Negative Amount (R8)",
            "customer": "Priya Sharma",
            "agent": "Agent-Alice",
            "action": "Place Order",
            "amount": -250.0,
            "expected_decision": "BLOCK",
            "expected_rule": "R8"
        },
        {
            "id": "Test 10",
            "name": "Zero Amount on Order (R8)",
            "customer": "Priya Sharma",
            "agent": "Agent-Alice",
            "action": "Place Order",
            "amount": 0.0,
            "expected_decision": "BLOCK",
            "expected_rule": "R8"
        },
        {
            "id": "Test 11",
            "name": "Unrecognized Action (R8)",
            "customer": "Priya Sharma",
            "agent": "Agent-Alice",
            "action": "Delete Account",
            "amount": 0.0,
            "expected_decision": "BLOCK",
            "expected_rule": "R8"
        }
    ]

    passed_count = 0
    total_count = len(test_scenarios)

    header_fmt = "{:<8} | {:<32} | {:<14} | {:<14} | {:<7}"
    print(header_fmt.format("Test ID", "Scenario", "Expected", "Actual", "Result"))
    print("-" * 80)

    for tc in test_scenarios:
        res = evaluate_request(
            customer=tc["customer"],
            agent_id=tc["agent"],
            action=tc["action"],
            amount=tc["amount"],
            persist_log=False
        )

        is_passed = (res["decision"] == tc["expected_decision"]) and (res["rule_number"] == tc["expected_rule"])
        if is_passed:
            passed_count += 1
            status = "PASS"
        else:
            status = "FAIL"

        exp_str = f"{tc['expected_decision']} ({tc['expected_rule']})"
        act_str = f"{res['decision']} ({res['rule_number']})"
        print(header_fmt.format(tc["id"], tc["name"], exp_str, act_str, status))

    print("-" * 80)
    print(f" Summary: {passed_count}/{total_count} Tests Passed ({(passed_count/total_count)*100:.1f}%)")
    print("=" * 80)


if __name__ == "__main__":
    run_standalone_tests()
