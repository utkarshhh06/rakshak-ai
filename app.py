import pandas as pd
import streamlit as st
from detector import analyze_transaction
from scenarios import SCENARIOS, build_scenario

st.set_page_config(page_title="Rakshak AI | Transaction Safety", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
/* Main canvas */
.stApp {
    background: #0b1220;
    color: #edf4ff;
}

.block-container {
    padding-top: 1.4rem;
    padding-bottom: 3rem;
    max-width: 1440px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #101b2d;
    border-right: 1px solid #24364d;
}

[data-testid="stSidebar"] h2 {
    color: #f3f7fb;
    letter-spacing: -0.3px;
}

/* Hero banner */
.hero {
    padding: 1.6rem 1.7rem;
    border: 1px solid #2b4960;
    border-radius: 18px;
    background: linear-gradient(120deg, #14243a 0%, #10313c 100%);
    margin-bottom: 1.2rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.16);
}

.hero h1 {
    margin: 0;
    color: #f3f7fb;
    font-size: 2.35rem;
    font-weight: 750;
    letter-spacing: -1px;
}

.hero p {
    margin: 0.55rem 0 0;
    color: #b8c8d9;
    font-size: 1.02rem;
    line-height: 1.6;
}

.small-muted {
    color: #a8bad0;
    font-size: 0.9rem;
    line-height: 1.55;
}

/* Section headings */
h2, h3 {
    letter-spacing: -0.35px;
}

/* Summary metric cards */
[data-testid="stMetric"] {
    background: #111c2d;
    border: 1px solid #293d54;
    border-radius: 14px;
    padding: 1rem 1.1rem;
}

[data-testid="stMetricLabel"] {
    color: #b8c8d9;
}

[data-testid="stMetricValue"] {
    color: #f3f7fb;
}

/* Explainable-rule cards */
.rule-card {
    padding: 1rem 1.1rem;
    border: 1px solid #2b4058;
    border-radius: 13px;
    margin: 0.65rem 0;
    background: linear-gradient(135deg, #111c2d, #132338);
    line-height: 1.65;
}

.rule-card strong {
    color: #f3f7fb;
}

/* Data table */
[data-testid="stDataFrame"] {
    border: 1px solid #293d54;
    border-radius: 12px;
    overflow: hidden;
}

/* Buttons */
.stButton > button,
.stFormSubmitButton > button {
    border-radius: 10px;
    font-weight: 650;
    min-height: 2.7rem;
    transition: border-color 0.15s ease, transform 0.15s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    border-color: #4fd1c5;
    transform: translateY(-1px);
}

/* Inputs */
[data-testid="stNumberInput"] input {
    border-radius: 9px;
}

/* Alerts and expanders */
[data-testid="stAlert"] {
    border-radius: 12px;
}

[data-testid="stExpander"] {
    border: 1px solid #293d54;
    border-radius: 12px;
}

/* Small-screen spacing */
@media (max-width: 768px) {
    .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero {
        padding: 1.2rem;
    }

    .hero h1 {
        font-size: 1.8rem;
    }
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🛡️ Rakshak AI")
    st.caption("DEMO CONTROL PANEL")
    scenario_name = st.selectbox("Synthetic scenario", list(SCENARIOS.keys()))
    typical_amount = st.number_input("Typical transaction amount (₹)", min_value=1, max_value=1_000_000, value=1000, step=100)
    st.markdown("---")
    st.markdown("### Privacy by design")
    st.write("Use fictional scenarios only. Do not enter real customer details, account numbers, UPI IDs, or confidential bank data.")
    st.markdown("---")
    st.caption("Prototype build · Rule-based · No live payment integration")

st.markdown("<div class='hero'><h1>🛡️ Rakshak AI</h1><p>Explainable UPI scam-pattern analysis · Understand the warning, not just the score.</p></div>", unsafe_allow_html=True)
st.warning("Synthetic-data demonstration only. This app does not connect to UPI, banks, or payment systems. A score is not a probability or proof of fraud.")


st.divider()
st.subheader("🧪 Manual Transaction Analyzer")
st.caption(
    "Enter fictional transaction details to test the existing detection rules. "
    "This analysis is separate from the predefined scenario selector."
)

with st.form("manual_transaction_form"):
    manual_col1, manual_col2 = st.columns(2)

    with manual_col1:
        manual_amount = st.number_input(
            "Transaction amount (₹)",
            min_value=1,
            max_value=1_000_000,
            value=8000,
            step=100,
            key="manual_amount",
        )
        manual_typical_amount = st.number_input(
            "Typical transaction amount (₹)",
            min_value=1,
            max_value=1_000_000,
            value=1000,
            step=100,
            key="manual_typical_amount",
        )
        manual_is_new = st.checkbox(
            "New beneficiary",
            value=True,
            key="manual_is_new",
        )

    with manual_col2:
        manual_transfers = st.number_input(
            "Transfers in the last 10 minutes",
            min_value=1,
            max_value=100,
            value=3,
            step=1,
            key="manual_transfers",
        )
        manual_urgency = st.checkbox(
            "Urgency or impersonation reported",
            value=True,
            key="manual_urgency",
        )

    manual_submitted = st.form_submit_button(
        "Analyze manual transaction",
        type="primary",
        use_container_width=True,
    )

if manual_submitted:
    try:
        manual_result = analyze_transaction(
            amount=float(manual_amount),
            typical_amount=float(manual_typical_amount),
            is_new_beneficiary=manual_is_new,
            transfers_in_10m=int(manual_transfers),
            urgency_or_impersonation_reported=manual_urgency,
        )

        st.markdown("#### Manual analysis result")

        result_col1, result_col2, result_col3 = st.columns(3)
        result_col1.metric(
            "Illustrative score",
            f"{manual_result['score']} / 100",
        )
        result_col2.metric(
            "Risk band",
            manual_result["risk_band"],
        )
        result_col3.metric(
            "Amount / typical amount",
            f"{manual_result['amount_ratio']:.2f}×",
        )

        if manual_result["risk_band"] == "High":
            st.error(
                f"High warning level — "
                f"{manual_result['score']}/100. "
                "This is an illustrative result, not proof of fraud."
            )
        elif manual_result["risk_band"] == "Medium":
            st.warning(
                f"Medium warning level — "
                f"{manual_result['score']}/100."
            )
        else:
            st.info(
                f"Low warning level under these demo rules — "
                f"{manual_result['score']}/100. "
                "A low score does not guarantee safety."
            )

        st.markdown("#### Why these rules triggered")

        if manual_result["triggered_rules"]:
            for rule in manual_result["triggered_rules"]:
                st.markdown(
                    f"<div class='rule-card'>"
                    f"<strong>{rule['rule_id']} · {rule['name']}</strong><br>"
                    f"<span class='small-muted'>{rule['evidence']}</span><br>"
                    f"<strong>+{rule['points']} points</strong>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info(
                "No configured warning signals were triggered "
                "for these manual inputs."
            )

        st.markdown("#### Suggested next step")
        st.write(manual_result["guidance"])

    except ValueError as exc:
        st.error(f"Please check your entries: {exc}")

    st.caption(
        "Manual analysis uses the same existing detector rules as the "
        "predefined scenarios. It does not contact a bank, verify a "
        "beneficiary, or initiate, block, or reverse a payment."
    )

st.divider()


cfg = SCENARIOS[scenario_name]
st.subheader("Scenario overview")
st.write(cfg["description"])
df = build_scenario(scenario_name, typical_amount)
results = []
for _, row in df.iterrows():
    results.append(analyze_transaction(amount=float(row["amount_inr"]), typical_amount=float(typical_amount),
        is_new_beneficiary=bool(row["is_new_beneficiary"]), transfers_in_10m=int(row["transfers_in_10m"]),
        urgency_or_impersonation_reported=bool(row["urgency_or_impersonation_reported"])))
latest = results[-1]

# Scenario risk summary
st.markdown("### Risk at a glance")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Illustrative score",
        f"{latest['score']} / 100",
        help="A rule-based warning score, not a probability of fraud.",
    )

with c2:
    st.metric(
        "Risk band",
        latest["risk_band"],
        help="Low, Medium, or High based on the configured demo thresholds.",
    )

with c3:
    st.metric(
        "Transfers in scenario",
        len(df),
        help="Number of fictional transactions in the selected scenario.",
    )

with c4:
    st.metric(
        "Rules triggered",
        len(latest["triggered_rules"]),
        help="Number of warning rules triggered by the latest transaction.",
    )

st.caption(
    "Summary reflects the latest transaction in the selected synthetic scenario. "
    "Scores are illustrative and do not establish whether fraud occurred."
)

st.markdown("### Transaction timeline")
timeline = df.copy()
timeline["time"] = timeline["time"].dt.strftime("%H:%M:%S")
timeline["amount_inr"] = timeline["amount_inr"].map(lambda x: f"₹{x:,.0f}")
timeline["New beneficiary"] = timeline["is_new_beneficiary"].map({True: "Yes", False: "No"})
timeline["Urgency reported"] = timeline["urgency_or_impersonation_reported"].map({True: "Yes", False: "No"})
timeline["Risk score"] = [r["score"] for r in results]
timeline["Risk band"] = [r["risk_band"] for r in results]
timeline = timeline[["time", "amount_inr", "beneficiary_label", "New beneficiary", "transfers_in_10m", "Urgency reported", "Risk score", "Risk band"]]
timeline.columns = ["Time", "Amount", "Fictional beneficiary", "New beneficiary", "Transfers in 10 min", "Urgency reported", "Score", "Band"]

st.dataframe(
    timeline,
    use_container_width=True,
    hide_index=True,
    height=220,
    column_config={
        "Time": st.column_config.TextColumn("Time"),
        "Amount": st.column_config.TextColumn("Amount"),
        "Fictional beneficiary": st.column_config.TextColumn(
            "Fictional beneficiary",
            width="medium",
        ),
        "New beneficiary": st.column_config.TextColumn("New beneficiary"),
        "Transfers in 10 min": st.column_config.NumberColumn(
            "Transfers in 10 min",
            help="Transactions counted in the inclusive 10-minute window.",
        ),
        "Urgency reported": st.column_config.TextColumn("Urgency reported"),
        "Score": st.column_config.NumberColumn(
            "Score",
            help="Illustrative rule-based score, capped at 100.",
        ),
        "Band": st.column_config.TextColumn("Risk band"),
    },
)


st.markdown("### Explainable alert")
st.caption(
    "See which signals contributed to the latest transaction's score "
    "and why each rule was triggered."
)

if latest["risk_band"] == "High":
    st.error(
        f"High warning level · {latest['score']}/100",
        icon="🚨",
    )
elif latest["risk_band"] == "Medium":
    st.warning(
        f"Medium warning level · {latest['score']}/100",
        icon="⚠️",
    )
else:
    st.info(
        f"Low warning level · {latest['score']}/100",
        icon="🛡️",
    )

triggered_rules = latest["triggered_rules"]

if triggered_rules:
    st.markdown(f"**Triggered signals: {len(triggered_rules)}**")

    
    for rule in triggered_rules:
        with st.container(border=True):
            title_col, points_col = st.columns([4, 1])

            with title_col:
                st.markdown(
                    f"**{rule['rule_id']} · {rule['name']}**"
                )

            with points_col:
                st.markdown(f"**+{rule['points']} pts**")

            if rule.get("evidence"):
                st.caption(str(rule["evidence"]))

else:
    st.success(
        "No configured warning signals were triggered for the latest transaction."
    )


st.markdown("### Suggested next steps")
st.write(latest["guidance"])
st.write("If you suspect an actual scam, do not use contact details supplied in the suspicious message. Use independently obtained official bank/payment-provider channels.")

with st.expander("How the illustrative score works"):
    st.markdown("""
    - **R-01:** New beneficiary — +20
    - **R-02:** Exactly 2 transfers in 10 minutes — +15
    - **R-03:** 3 or more transfers in 10 minutes — +30 (replaces R-02)
    - **R-04:** Amount ≥2× and <3× typical amount — +15
    - **R-05:** Amount ≥3× typical amount — +25 (replaces R-04)
    - **R-06:** User-reported urgency/impersonation indicator — +25

    The rules are manually selected demonstration heuristics, not learned or calibrated from real fraud outcomes. Low scores do not establish that a payment is safe. False positives and false negatives are possible.
    """)

with st.expander("Prototype checks and limitations"):
    st.markdown("""
    - Inputs are fictional and scenario-based.
    - No live UPI/bank integration or payment action is available.
    - A warning should support human review, not make a final fraud determination.
    - Real deployment would require authorized representative data, privacy/security review, threshold validation, and monitored evaluation.
    """)
st.caption("Rakshak AI · Hackathon prototype · Synthetic data only · No payment is blocked, reversed, or authorized.")
