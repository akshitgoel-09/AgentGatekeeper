"""
Amazon Agent Gatekeeper - Streamlit Web Application
An AI Agent Authorization and Access Control System
Academic Prototype - University Assignment Simulation
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime

from core.data_manager import (
    load_agents,
    register_agent,
    revoke_agent,
    reactivate_agent,
    load_audit_log_df,
    update_audit_log_outcome,
    get_dashboard_metrics,
    AUDIT_LOG_FILE
)
from core.gatekeeper import (
    evaluate_request,
    RULES_METADATA,
    ALLOWED_ACTIONS,
    SPENDING_THRESHOLD_INR
)

# Set page configuration
st.set_page_config(
    page_title="Amazon Agent Gatekeeper | AI Access Control",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Amazon Navy #232F3E, #131921, Amazon Orange #FF9900, Clean Professional Cards)
st.markdown("""
<style>
    /* Main Theme Variables */
    :root {
        --amazon-navy: #131921;
        --amazon-light-navy: #232F3E;
        --amazon-orange: #FF9900;
        --amazon-orange-hover: #E88B00;
        --text-dark: #0F1111;
        --bg-light: #F7F9FA;
        --card-border: #E3E6E6;
        --success-green: #067D62;
        --danger-red: #BA0933;
        --warning-amber: #B12704;
    }

    /* Header styling */
    .brand-header {
        background: linear-gradient(135deg, #131921 0%, #232F3E 100%);
        color: white;
        padding: 22px 28px;
        border-radius: 10px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }
    .brand-title {
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .brand-accent {
        color: #FF9900;
    }
    .brand-sub {
        font-size: 13px;
        color: #D5D9D9;
        margin-top: 4px;
    }
    .brand-badge {
        background-color: rgba(255, 153, 0, 0.2);
        border: 1px solid #FF9900;
        color: #FFD814;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Academic Disclaimer Banner */
    .disclaimer-banner {
        background-color: #FFF8E7;
        border-left: 4px solid #FF9900;
        padding: 10px 16px;
        border-radius: 6px;
        margin-bottom: 20px;
        font-size: 12.5px;
        color: #553C00;
    }

    /* Metric cards */
    .metric-card {
        background: white;
        border: 1px solid #E3E6E6;
        border-radius: 8px;
        padding: 18px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.04);
        text-align: center;
        transition: transform 0.15s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        margin-top: 6px;
    }
    .metric-label {
        font-size: 12px;
        font-weight: 600;
        color: #565959;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Decision Badges */
    .badge-allow {
        background-color: #E7F4EE;
        color: #067D62;
        border: 1px solid #B6E2CD;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
    }
    .badge-ask {
        background-color: #FFF3E8;
        color: #B12704;
        border: 1px solid #FFD0A8;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
    }
    .badge-block {
        background-color: #FDF0F2;
        color: #BA0933;
        border: 1px solid #F5C6CB;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
    }

    /* Pending Confirmation Card */
    .confirmation-box {
        background: #FFFDF9;
        border: 2px solid #FF9900;
        border-radius: 10px;
        padding: 22px;
        margin-top: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(255, 153, 0, 0.15);
    }
    .confirmation-title {
        color: #B12704;
        font-size: 19px;
        font-weight: 700;
        margin-bottom: 12px;
    }

    /* Enrolment sidebar badge */
    .student-badge-box {
        background: #F0F2F2;
        border: 1px dashed #A6A6A6;
        border-radius: 8px;
        padding: 12px;
        font-size: 12px;
        color: #333;
        margin-bottom: 18px;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# SIDEBAR NAVIGATION & STUDENT ENROLMENT SECTION
# =====================================================================

with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding-bottom: 10px;">
            <h2 style="margin: 0; color: #131921; font-weight: 800; font-size: 22px;">
                amazon <span style="color: #FF9900;">gatekeeper</span>
            </h2>
            <p style="font-size: 11px; color: #666; margin: 2px 0 0 0;">AI Agent Authorization Engine</p>
        </div>
    """, unsafe_allow_html=True)

    # 10. Student & Project Identification (Requirement 1 & 10)
    st.markdown("### 🎓 Academic Project Info")
    
    # Store in session state for persistence
    if "student_name" not in st.session_state:
        st.session_state["student_name"] = "[ENTER YOUR NAME]"
    if "enrolment_number" not in st.session_state:
        st.session_state["enrolment_number"] = "[ENTER YOUR ENROLMENT NUMBER]"

    student_name_input = st.text_input(
        "Student Name:",
        value=st.session_state["student_name"],
        help="Fill in your student name for assignment submission."
    )
    enrolment_input = st.text_input(
        "Enrolment Number:",
        value=st.session_state["enrolment_number"],
        help="Fill in your university enrolment / roll number."
    )

    st.session_state["student_name"] = student_name_input
    st.session_state["enrolment_number"] = enrolment_input

    st.markdown(f"""
        <div class="student-badge-box">
            <b>Company:</b> Amazon (Academic Simulation)<br>
            <b>Project:</b> Agent Gatekeeper<br>
            <b>Student:</b> {st.session_state["student_name"]}<br>
            <b>Enrolment No:</b> <code>{st.session_state["enrolment_number"]}</code>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🧭 Navigation")
    menu = st.radio(
        "Go to Section:",
        [
            "📊 Dashboard",
            "🛡️ Request Evaluation",
            "🤖 Agent Management",
            "📜 Rule Management",
            "📋 Audit Logs",
            "🧪 Testing Centre",
            "💡 Business Insights"
        ],
        index=0
    )

    st.markdown("---")
    st.caption("🔒 **Security Mode:** Zero-Trust Agent Policy")
    st.caption("⚙️ **Engine Version:** 1.0.0 (Python / Streamlit)")


# =====================================================================
# GLOBAL HEADER & ACADEMIC SIMULATION DISCLAIMER
# =====================================================================

st.markdown(f"""
    <div class="brand-header">
        <div>
            <h1 class="brand-title">
                amazon <span class="brand-accent">agent gatekeeper</span>
            </h1>
            <div class="brand-sub">
                Enterprise AI Agent Access Control & Decision Verification System
            </div>
        </div>
        <div style="text-align: right; margin-top: 5px;">
            <span class="brand-badge">Academic Prototype Only</span>
            <div style="font-size: 11px; color: #FFF; margin-top: 5px;">
                Student: <b>{st.session_state['student_name']}</b> | Enrolment: <b>{st.session_state['enrolment_number']}</b>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="disclaimer-banner">
        ⚠️ <b>Academic Simulation Disclaimer:</b> This web application is a university prototype designed for academic study.
        It does <b>NOT</b> connect to real Amazon accounts, query real customer data, place real purchases, or process live financial transactions.
        All thresholds (including the ₹1,000 order threshold) are academic design assumptions for testing human-in-the-loop agent workflows.
    </div>
""", unsafe_allow_html=True)


# =====================================================================
# SECTION 1: DASHBOARD
# =====================================================================

if menu == "📊 Dashboard":
    st.subheader("📊 Executive Overview & Agent Metrics")
    metrics = get_dashboard_metrics()

    # Metric Cards Row 1: Agent Fleet
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Registered Agents</div>
                <div class="metric-value" style="color: #131921;">{metrics['total_agents']}</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Active Agents</div>
                <div class="metric-value" style="color: #067D62;">{metrics['active_agents']}</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Revoked Agents</div>
                <div class="metric-value" style="color: #BA0933;">{metrics['revoked_agents']}</div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Metric Cards Row 2: Request Decisions
    col4, col5, col6, col7 = st.columns(4)
    with col4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Requests</div>
                <div class="metric-value" style="color: #232F3E;">{metrics['total_requests']}</div>
            </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Allowed (R3, R4)</div>
                <div class="metric-value" style="color: #067D62;">{metrics['allowed_requests']}</div>
            </div>
        """, unsafe_allow_html=True)
    with col6:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Ask Customer (R5, R6, R7)</div>
                <div class="metric-value" style="color: #FF9900;">{metrics['ask_requests']}</div>
            </div>
        """, unsafe_allow_html=True)
    with col7:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Blocked (R1, R2, R8)</div>
                <div class="metric-value" style="color: #BA0933;">{metrics['blocked_requests']}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Decision Chart & Activity
    chart_col, act_col = st.columns([1, 1])

    with chart_col:
        st.markdown("#### 📈 Decision Distribution")
        df_log = load_audit_log_df()
        if not df_log.empty and "decision" in df_log.columns:
            counts = df_log["decision"].value_counts().reset_index()
            counts.columns = ["Decision", "Count"]
            st.bar_chart(data=counts.set_index("Decision"), color="#FF9900")
        else:
            st.info("No audit log requests recorded yet.")

    with act_col:
        st.markdown("#### ⚡ Quick Actions & Gatekeeper Status")
        st.info("""
            **Gatekeeper Engine State:** Active & Enforcing Rules R1–R8  
            **Spending Threshold:** ₹1,000.00 (Human-in-the-Loop trigger)  
            **Audit Persistence:** Connected to `data/audit_log.csv`  
            **Agent Registry:** Connected to `data/agents.json`
        """)
        st.markdown("""
            **Core Protection Guarantees:**
            - 🛑 Zero-trust evaluation: Unknown or revoked agents are blocked at Step 1 & 2.
            - 👤 Customer Sovereignty: High-value actions (orders > ₹1,000, returns, refunds) cannot execute without human approval.
            - 📝 Immutable Trail: Every evaluation is timestamped and recorded in the audit log.
        """)

    st.markdown("---")
    st.markdown("#### 🕒 Recent Activity (Latest 5 Requests)")
    if not df_log.empty:
        recent_df = df_log.tail(5).iloc[::-1]  # reverse for latest first
        st.dataframe(
            recent_df[[
                "timestamp", "request_id", "customer", "agent",
                "action", "amount", "decision", "rule_number", "final_outcome"
            ]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No recent activity found.")


# =====================================================================
# SECTION 2: REQUEST EVALUATION
# =====================================================================

elif menu == "🛡️ Request Evaluation":
    st.subheader("🛡️ AI Agent Request Evaluation & Authorization")
    st.write("Submit an AI agent transaction request to evaluate it against the 8 authorization rules in real time.")

    # Load available agents for convenience
    agents_dict = load_agents()
    active_agent_ids = [aid for aid, a in agents_dict.items() if a.get("status") == "ACTIVE"]
    all_agent_ids = list(agents_dict.keys())

    # Agent Selection Mode Toggle (Outside form so it dynamically updates the agent widget immediately)
    st.markdown("##### 👤 Agent Identity Selection Mode")
    agent_input_mode = st.radio(
        "Choose how to specify the Agent ID:",
        ["Select from Registered Agents", "Enter Custom / Unknown Agent ID"],
        horizontal=True,
        key="agent_mode_selector",
        help="Switch to 'Enter Custom / Unknown Agent ID' to test Rule R1 (Unknown Agent) with any arbitrary agent ID like Unknown-Agent-999."
    )

    # Form
    with st.form("evaluation_form"):
        col_c, col_a = st.columns(2)
        with col_c:
            customer_name = st.text_input(
                "Customer Name *",
                value="Priya Sharma",
                placeholder="e.g., Rahul Verma",
                help="Name of the customer on whose behalf the agent is acting."
            )
            action_choice = st.selectbox(
                "Requested Action *",
                ALLOWED_ACTIONS,
                index=1,
                help="Select the operation requested by the AI agent."
            )

        with col_a:
            if agent_input_mode == "Select from Registered Agents":
                agent_id = st.selectbox(
                    "Registered Agent ID *",
                    all_agent_ids,
                    help="Choose an existing registered agent from the registry."
                )
            else:
                agent_id = st.text_input(
                    "Enter Custom / Unknown Agent ID *",
                    value="Unknown-Agent-999",
                    placeholder="e.g., Unknown-Agent-999",
                    help="Type an unknown or custom agent ID to test Gatekeeper Rule R1."
                )

            amount_val = st.number_input(
                "Transaction Amount (₹ INR) *",
                min_value=0.0,
                max_value=1000000.0,
                value=750.0,
                step=50.0,
                format="%.2f",
                help="Amount in Indian Rupees. Routine purchases <= ₹1,000 are auto-allowed."
            )

        description = st.text_input(
            "Optional Request Description / Notes",
            value="Customer requested order assistance via chat assistant.",
            placeholder="Additional context about the request"
        )

        submit_btn = st.form_submit_button("🚀 Submit Request to Gatekeeper", use_container_width=True)

    # Process Form Submission
    if submit_btn:
        evaluation = evaluate_request(
            customer=customer_name,
            agent_id=agent_id,
            action=action_choice,
            amount=amount_val,
            description=description,
            persist_log=True
        )
        st.session_state["latest_evaluation"] = evaluation

        # If ASK CUSTOMER, stage for confirmation
        if evaluation["decision"] == "ASK CUSTOMER":
            st.session_state["pending_confirmation"] = evaluation
        else:
            # Clear any stale pending confirmation
            st.session_state.pop("pending_confirmation", None)

    # Display Evaluation Result
    if "latest_evaluation" in st.session_state:
        eval_res = st.session_state["latest_evaluation"]
        dec = eval_res["decision"]
        rule_num = eval_res["rule_number"]
        reason = eval_res["reason"]
        req_id = eval_res["request_id"]

        st.markdown("### 📋 Gatekeeper Decision")

        if dec == "ALLOW":
            st.success(f"""
                ✅ **DECISION: ALLOW**  
                **Rule Triggered:** `{rule_num}` ({RULES_METADATA.get(rule_num, {}).get('name', 'N/A')})  
                **Reason:** {reason}  
                **Request ID:** `{req_id}` | **Status:** Executed Successfully
            """)
        elif dec == "BLOCK":
            st.error(f"""
                🛑 **DECISION: BLOCK**  
                **Rule Triggered:** `{rule_num}` ({RULES_METADATA.get(rule_num, {}).get('name', 'N/A')})  
                **Reason:** {reason}  
                **Request ID:** `{req_id}` | **Status:** Action Prevented by Gatekeeper
            """)
        elif dec == "ASK CUSTOMER":
            st.warning(f"""
                ⚠️ **DECISION: ASK CUSTOMER (Human Approval Required)**  
                **Rule Triggered:** `{rule_num}` ({RULES_METADATA.get(rule_num, {}).get('name', 'N/A')})  
                **Reason:** {reason}  
                **Request ID:** `{req_id}` | **Status:** Held Pending Customer Confirmation
            """)

    # Interactive Customer Confirmation Workflow (Requirement 6)
    if "pending_confirmation" in st.session_state:
        pending = st.session_state["pending_confirmation"]
        st.markdown("""
            <div class="confirmation-box">
                <div class="confirmation-title">👤 Customer Confirmation Portal (Human-in-the-Loop)</div>
                <p>The Gatekeeper has intercepted this high-impact action. The action will <b>NOT</b> be executed until you confirm it below.</p>
        """, unsafe_allow_html=True)

        col_d1, col_d2, col_d3 = st.columns(3)
        col_d1.metric("Customer Name", pending['customer'])
        col_d2.metric("Requested Action", pending['action'])
        col_d3.metric("Amount (INR)", f"₹{float(pending['amount']):,.2f}")

        st.markdown(f"**Agent:** `{pending['agent']}` | **Request ID:** `{pending['request_id']}`")
        st.markdown(f"**Rule Requirement:** {pending['reason']}")

        st.write("")
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("✅ Confirm & Authorize Action (Customer Approves)", key="btn_confirm", type="primary", use_container_width=True):
                update_audit_log_outcome(pending["request_id"], "APPROVED", "EXECUTED")
                st.session_state.pop("pending_confirmation", None)
                st.success(f"🎉 **Action Confirmed!** Request `{pending['request_id']}` has been authorized by the customer and successfully executed.")
                st.rerun()

        with c_btn2:
            if st.button("❌ Reject & Cancel Action (Customer Denies)", key="btn_reject", use_container_width=True):
                update_audit_log_outcome(pending["request_id"], "REJECTED", "REJECTED")
                st.session_state.pop("pending_confirmation", None)
                st.info(f"🚫 **Action Rejected!** Request `{pending['request_id']}` was cancelled by the customer. No action was performed.")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# =====================================================================
# SECTION 3: AGENT MANAGEMENT
# =====================================================================

elif menu == "🤖 Agent Management":
    st.subheader("🤖 AI Agent Registry & Identity Lifecycle Management")
    st.write("Manage AI agent credentials, register new service agents, or revoke agent access to protect customer accounts.")

    agents = load_agents()

    tab_view, tab_register, tab_revoke = st.tabs([
        "📋 Registered Agents",
        "➕ Register New Agent",
        "🚫 Revoke / Manage Agent Access"
    ])

    # Tab 1: View Agents
    with tab_view:
        st.markdown("#### 📑 Active & Revoked Agent Fleet")
        agent_list = []
        for aid, data in agents.items():
            agent_list.append({
                "Agent ID": aid,
                "Agent Name": data.get("name", "N/A"),
                "Role / Department": data.get("role", "N/A"),
                "Status": data.get("status", "ACTIVE"),
                "Registered At": data.get("registered_at", "N/A"),
                "Revoked At": data.get("revoked_at") if data.get("revoked_at") else "—",
                "Revocation Reason": data.get("revocation_reason") if data.get("revocation_reason") else "—"
            })
        agent_df = pd.DataFrame(agent_list)
        st.dataframe(agent_df, use_container_width=True, hide_index=True)

    # Tab 2: Register New Agent
    with tab_register:
        st.markdown("#### ➕ Register a New AI Agent")
        st.write("Newly registered agents receive `ACTIVE` status and can perform permitted routine actions under Gatekeeper rules.")
        
        with st.form("register_agent_form"):
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                new_agent_id = st.text_input("New Agent ID *", placeholder="e.g., Agent-Evelyn")
                new_agent_name = st.text_input("Agent Display Name *", placeholder="e.g., Evelyn - Logistics Specialist")
            with col_r2:
                new_agent_role = st.selectbox(
                    "Role / Department *",
                    [
                        "Customer Support Specialist",
                        "Fulfillment Assistant",
                        "Returns Specialist",
                        "Senior Order Manager",
                        "Billing & Refunds Coordinator",
                        "General AI Assistant"
                    ]
                )
            reg_submit = st.form_submit_button("Register Agent", use_container_width=True)

            if reg_submit:
                success, msg = register_agent(new_agent_id, new_agent_name, new_agent_role)
                if success:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ Registration Failed: {msg}")

    # Tab 3: Revoke Agent Access
    with tab_revoke:
        st.markdown("#### 🚫 Revoke Agent Access")
        st.write("Revoking an agent instantly blocks all future actions under **Rule R2**, storing an immutable timestamp and reason.")
        
        active_agents = {aid: a for aid, a in agents.items() if a.get("status") == "ACTIVE"}
        revoked_agents = {aid: a for aid, a in agents.items() if a.get("status") == "REVOKED"}

        if active_agents:
            with st.form("revoke_agent_form"):
                agent_to_revoke = st.selectbox(
                    "Select Active Agent to Revoke *",
                    list(active_agents.keys()),
                    format_func=lambda x: f"{x} ({active_agents[x].get('name')})"
                )
                revoke_reason = st.text_input(
                    "Revocation Reason *",
                    value="Routine security credentials rotation",
                    placeholder="Reason for revoking agent permissions"
                )
                revoke_submit = st.form_submit_button("🚫 Revoke Agent Immediately", use_container_width=True)

                if revoke_submit:
                    ok, msg = revoke_agent(agent_to_revoke, revoke_reason)
                    if ok:
                        st.warning(f"⚠️ {msg}")
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info("No active agents available to revoke.")

        st.markdown("---")
        st.markdown("#### 🔄 Reactivate Agent (Testing Convenience)")
        st.caption("Reactivating agents allows instructors and students to easily re-test workflows without manually editing JSON files.")
        if revoked_agents:
            with st.form("reactivate_agent_form"):
                agent_to_reactivate = st.selectbox(
                    "Select Revoked Agent to Reactivate:",
                    list(revoked_agents.keys()),
                    format_func=lambda x: f"{x} (Revoked on {revoked_agents[x].get('revoked_at')})"
                )
                reactivate_submit = st.form_submit_button("Reactivate Agent", use_container_width=True)
                if reactivate_submit:
                    ok, msg = reactivate_agent(agent_to_reactivate)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.caption("No revoked agents currently.")


# =====================================================================
# SECTION 4: RULE MANAGEMENT
# =====================================================================

elif menu == "📜 Rule Management":
    st.subheader("📜 Authorization Rules & Priority Hierarchy")
    st.write("The Amazon Agent Gatekeeper enforces a deterministic, 8-rule security hierarchy to eliminate ambiguous authorization states.")

    st.markdown("""
        <div style="background: white; border: 1px solid #E3E6E6; border-radius: 8px; padding: 18px; margin-bottom: 20px;">
            <h4 style="margin-top: 0; color: #131921;">🎯 Gatekeeper Rule Priority Execution Pipeline</h4>
            <ol style="margin-bottom: 0; line-height: 1.8; color: #333;">
                <li><b>Step 1: Input Validation Check (R8):</b> Ensure customer name, agent ID, valid action, and non-negative amounts exist.</li>
                <li><b>Step 2: Identity Authentication (R1):</b> Verify agent is registered in the persistent registry. If unknown &rarr; <b>BLOCK</b>.</li>
                <li><b>Step 3: Revocation Verification (R2):</b> Check if registered agent has been revoked. If revoked &rarr; <b>BLOCK</b>.</li>
                <li><b>Step 4: Action & Spending Evaluation (R3 – R7):</b>
                    <ul>
                        <li><b>View Order (R3):</b> Read-only safe operation &rarr; <b>ALLOW</b>.</li>
                        <li><b>Place Order &le; ₹1,000 (R4):</b> Routine low-value purchase &rarr; <b>ALLOW</b>.</li>
                        <li><b>Place Order &gt; ₹1,000 (R5):</b> High-value purchase &rarr; <b>ASK CUSTOMER</b>.</li>
                        <li><b>Return Product (R6):</b> Inventory & customer experience impact &rarr; <b>ASK CUSTOMER</b>.</li>
                        <li><b>Refund (R7):</b> Financial balance alteration &rarr; <b>ASK CUSTOMER</b>.</li>
                    </ul>
                </li>
                <li><b>Step 5: Fail-Safe Fallback (R8):</b> Any unhandled edge case or invalid request &rarr; <b>BLOCK</b>.</li>
            </ol>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📖 Complete 8-Rule Specification Table")

    rule_rows = []
    for r_id, r_info in RULES_METADATA.items():
        rule_rows.append({
            "Rule ID": r_id,
            "Rule Name": r_info["name"],
            "Decision": r_info["decision"],
            "Category": r_info["category"],
            "Description": r_info["description"]
        })
    st.dataframe(pd.DataFrame(rule_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("""
        #### 💡 Academic Business Assumption: Why the ₹1,000 Threshold?
        > **Note:** The **₹1,000 threshold** in this project is an academic simulation assumption designed to teach
        > **Human-in-the-Loop (HITL)** governance. It reflects standard e-commerce security patterns:
        > 1. **Frictionless Routine Actions:** Automated agents can complete trivial purchases (under ₹1,000) quickly without fatiguing customers with repetitive prompts.
        > 2. **Financial Safeguard:** Large expenditures (over ₹1,000) introduce higher financial risk. Requiring explicit customer approval prevents accidental agent purchases, prompt injection attacks, or automated ordering loops.
        > 3. **Not Amazon's Real Policy:** This rule is implemented strictly for university prototype demonstration and is not an actual Amazon production policy.
    """)


# =====================================================================
# SECTION 5: AUDIT LOGS
# =====================================================================

elif menu == "📋 Audit Logs":
    st.subheader("📋 Comprehensive Audit Log & Compliance Forensics")
    st.write("All Gatekeeper evaluations and customer confirmation decisions are persistently logged with timestamps and rule details.")

    df_audit = load_audit_log_df()

    if not df_audit.empty:
        # Filtering Controls
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            decision_filter = st.selectbox("Filter by Decision:", ["ALL", "ALLOW", "ASK CUSTOMER", "BLOCK"])
        with col_f2:
            agent_filter = st.selectbox("Filter by Agent:", ["ALL"] + sorted(list(df_audit["agent"].dropna().unique())))
        with col_f3:
            search_query = st.text_input("Search (Customer or Request ID):", "")

        # Apply Filters
        filtered_df = df_audit.copy()
        if decision_filter != "ALL":
            filtered_df = filtered_df[filtered_df["decision"] == decision_filter]
        if agent_filter != "ALL":
            filtered_df = filtered_df[filtered_df["agent"] == agent_filter]
        if search_query.strip():
            q = search_query.strip().lower()
            filtered_df = filtered_df[
                filtered_df["customer"].astype(str).str.lower().str.contains(q) |
                filtered_df["request_id"].astype(str).str.lower().str.contains(q)
            ]

        st.markdown(f"**Showing {len(filtered_df)} of {len(df_audit)} total records:**")
        st.dataframe(filtered_df.iloc[::-1], use_container_width=True, hide_index=True)

        # Download CSV Button
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Audit Log as CSV",
            data=csv_data,
            file_name=f"amazon_agent_gatekeeper_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("The audit log is currently empty.")


# =====================================================================
# SECTION 6: TESTING CENTRE
# =====================================================================

elif menu == "🧪 Testing Centre":
    st.subheader("🧪 Automated Testing Centre & Scenario Verification")
    st.write("Execute automated test scenarios to verify all 8 authorization rules, agent management, and customer confirmation workflows.")

    st.markdown("""
        <div style="background: white; border: 1px solid #E3E6E6; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
            <b>Test Coverage Overview:</b>
            This test suite verifies all mandatory specification test scenarios plus comprehensive edge cases,
            comparing <b>Expected Rule & Decision</b> against <b>Live Evaluated Result</b>.
        </div>
    """, unsafe_allow_html=True)

    # Pre-defined test cases
    TEST_CASES = [
        {
            "id": "TC-01",
            "name": "Unknown Agent Attempts Action",
            "customer": "Priya Sharma",
            "agent": "Unknown-Agent-999",
            "action": "View Order",
            "amount": 0.0,
            "expected_decision": "BLOCK",
            "expected_rule": "R1",
            "description": "Rule R1: Unknown agent must be blocked immediately."
        },
        {
            "id": "TC-02",
            "name": "Revoked Agent Attempts Order",
            "customer": "Rahul Verma",
            "agent": "Agent-Bob",
            "action": "Place Order",
            "amount": 500.0,
            "expected_decision": "BLOCK",
            "expected_rule": "R2",
            "description": "Rule R2: Revoked agent cannot perform actions."
        },
        {
            "id": "TC-03",
            "name": "Registered Agent Views Order",
            "customer": "Amit Kumar",
            "agent": "Agent-Alice",
            "action": "View Order",
            "amount": 0.0,
            "expected_decision": "ALLOW",
            "expected_rule": "R3",
            "description": "Rule R3: Read-only view order is permitted."
        },
        {
            "id": "TC-04",
            "name": "Registered Agent Places Low-Value Order",
            "customer": "Sneha Patel",
            "agent": "Agent-Alice",
            "action": "Place Order",
            "amount": 800.0,
            "expected_decision": "ALLOW",
            "expected_rule": "R4",
            "description": "Rule R4: Routine orders ₹1,000 or less are auto-approved."
        },
        {
            "id": "TC-05",
            "name": "Registered Agent Places High-Value Order",
            "customer": "Vikram Malhotra",
            "agent": "Agent-Alice",
            "action": "Place Order",
            "amount": 2000.0,
            "expected_decision": "ASK CUSTOMER",
            "expected_rule": "R5",
            "description": "Rule R5: Orders above ₹1,000 require customer confirmation."
        },
        {
            "id": "TC-06",
            "name": "Registered Agent Requests Refund",
            "customer": "Deepak Joshi",
            "agent": "Agent-Alice",
            "action": "Refund",
            "amount": 1500.0,
            "expected_decision": "ASK CUSTOMER",
            "expected_rule": "R7",
            "description": "Rule R7: Refunds directly alter balances and require approval."
        },
        {
            "id": "TC-07",
            "name": "Registered Agent Returns Product",
            "customer": "Ananya Iyer",
            "agent": "Agent-Alice",
            "action": "Return Product",
            "amount": 0.0,
            "expected_decision": "ASK CUSTOMER",
            "expected_rule": "R6",
            "description": "Rule R6: Product returns require customer confirmation."
        },
        {
            "id": "TC-08",
            "name": "Missing Customer Name",
            "customer": "   ",
            "agent": "Agent-Alice",
            "action": "Place Order",
            "amount": 500.0,
            "expected_decision": "BLOCK",
            "expected_rule": "R8",
            "description": "Rule R8: Missing required information must be blocked."
        },
        {
            "id": "TC-09",
            "name": "Invalid Negative Amount",
            "customer": "Priya Sharma",
            "agent": "Agent-Alice",
            "action": "Place Order",
            "amount": -250.0,
            "expected_decision": "BLOCK",
            "expected_rule": "R8",
            "description": "Rule R8: Negative transaction amount must be blocked."
        },
        {
            "id": "TC-10",
            "name": "Zero Amount on Place Order",
            "customer": "Priya Sharma",
            "agent": "Agent-Alice",
            "action": "Place Order",
            "amount": 0.0,
            "expected_decision": "BLOCK",
            "expected_rule": "R8",
            "description": "Rule R8: Place order requires amount > ₹0."
        },
        {
            "id": "TC-11",
            "name": "Invalid Action Unrecognized",
            "customer": "Priya Sharma",
            "agent": "Agent-Alice",
            "action": "Transfer Funds Out",
            "amount": 500.0,
            "expected_decision": "BLOCK",
            "expected_rule": "R8",
            "description": "Rule R8: Unrecognized actions must be blocked."
        }
    ]

    if st.button("▶️ Run All Automated Test Scenarios", type="primary", use_container_width=True):
        results = []
        all_passed = True

        for tc in TEST_CASES:
            res = evaluate_request(
                customer=tc["customer"],
                agent_id=tc["agent"],
                action=tc["action"],
                amount=tc["amount"],
                description=tc["description"],
                persist_log=False  # Do not pollute user audit log with test executions
            )

            passed = (res["decision"] == tc["expected_decision"]) and (res["rule_number"] == tc["expected_rule"])
            if not passed:
                all_passed = False

            results.append({
                "Test ID": tc["id"],
                "Scenario Name": tc["name"],
                "Input Agent": tc["agent"],
                "Input Action": tc["action"],
                "Input Amount": f"₹{tc['amount']:,.2f}",
                "Expected Decision": tc["expected_decision"],
                "Actual Decision": res["decision"],
                "Expected Rule": tc["expected_rule"],
                "Actual Rule": res["rule_number"],
                "Status": "✅ PASS" if passed else "❌ FAIL"
            })

        results_df = pd.DataFrame(results)
        
        if all_passed:
            st.success(f"🎉 **All {len(TEST_CASES)} Test Scenarios Passed Successfully! (100% Pass Rate)**")
        else:
            st.error("Some test scenarios failed. Check table below.")

        st.dataframe(results_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("""
        #### 💻 Running Tests via Pytest (Command Line)
        For terminal automated testing, run:
        ```bash
        pytest -v
        ```
        This executes the formal Pytest test suite inside `tests/test_gatekeeper.py`.
    """)


# =====================================================================
# SECTION 7: BUSINESS INSIGHTS
# =====================================================================

elif menu == "💡 Business Insights":
    st.subheader("💡 Strategic Insights: AI Agent Governance & Access Control")
    st.write("Academic analysis on why autonomous AI agents require rigorous authorization layers in enterprise systems.")

    col_b1, col_b2 = st.columns(2)

    with col_b1:
        st.markdown("""
            ### 🤖 Why AI Agents Need Authorization
            As Large Language Models (LLMs) transition from passive chatbots into **autonomous agents** capable of tool calling and API execution, they inherit the ability to affect the real world. Without strict authorization:
            - **Hallucinated Actions:** An agent might incorrectly deduce that a customer requested a full order cancellation or high-value purchase.
            - **Prompt Injection:** Malicious inputs from adversarial web pages or reviews could hijack the agent's instructions (Confused Deputy Problem).
            - **Unchecked API Privileges:** Giving an agent direct API keys without an intermediary gatekeeper exposes backends to unlimited read/write actions.

            ---

            ### 🛡️ Customer Protection & Trust
            - **Predictable Boundary:** Customers must know that an AI assistant cannot spend significant money without their explicit sign-off.
            - **Consent as a Feature:** Human-in-the-Loop (HITL) confirmation creates transparency and peace of mind.
            - **Reversibility & Control:** Providing clear approval/rejection dialogues maintains customer autonomy.
        """)

    with col_b2:
        st.markdown("""
            ### 💰 Financial Risk Reduction & Fraud Prevention
            - **Spending Limits:** The ₹1,000 automated ceiling provides a safe sandbox for mundane purchases while mitigating catastrophic loss.
            - **Revocation Capability:** If an agent's behavioral model deviates or an API key is compromised, revoking the agent immediately neuters its privileges across the entire enterprise.
            - **Anti-Drain Safeguards:** Automated refunds without customer verification could be exploited to drain merchant balances.

            ---

            ### 📜 Forensics & Immutable Audit Logs
            - **Accountability:** When an action occurs, the audit log records exactly *which agent*, *which rule*, and *what timestamp* governed the decision.
            - **Regulatory Compliance:** Auditing supports consumer protection standards and algorithmic accountability frameworks.
            - **Post-Incident Analysis:** If a customer questions an order, logs provide complete visibility into whether it was auto-approved or human-confirmed.
        """)

    st.markdown("---")
    st.markdown("""
        <div style="background: #F0F2F2; padding: 15px; border-radius: 8px; font-size: 13px; color: #444;">
            <b>Academic Takeaway:</b> Autonomous agents should operate with <i>Least Privilege</i>.
            The Amazon Agent Gatekeeper pattern demonstrates that security controls must reside outside the LLM, in deterministic code that cannot be swayed by prompt manipulation.
        </div>
    """, unsafe_allow_html=True)
