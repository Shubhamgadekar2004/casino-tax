"""
Risk Dashboard Page — Transparent rule-based risk scoring.
"""
import streamlit as st
import pandas as pd
import json
import plotly.express as px

from models.reconciliation import get_all_risk_scores, get_risk_distribution
from services.risk_service import calculate_risk_score, get_high_risk_individuals
from models.individual import get_all_individuals
from config.settings import RISK_RULES, RISK_THRESHOLDS


def render():
    st.title("⚠️ Risk Dashboard")
    st.caption("Transparent Rule-Based Risk Scoring — No Black Box")

    # ── Risk Rules ─────────────────────────────────────────
    with st.expander("📐 Risk Scoring Rules", expanded=False):
        st.markdown("""
        | Rule | Points |
        |---|---|
        | Winnings not reported in ITR | +40 |
        | Large under-reporting (> ₹50,000) | +30 |
        | Repeated mismatches | +20 |
        | Unusually large cash activity (> ₹2 lakh) | +10 |
        | Frequent high-value transactions | +10 |
        
        **Risk Levels:**
        | Level | Score Range |
        |---|---|
        | 🟢 LOW | 0 – 30 |
        | 🟡 MEDIUM | 31 – 60 |
        | 🟠 HIGH | 61 – 80 |
        | 🔴 CRITICAL | 81 – 100 |
        """)

    st.divider()

    # ── Distribution KPIs ──────────────────────────────────
    risk_dist = get_risk_distribution()
    if risk_dist:
        dist_map = {r["risk_level"]: r["count"] for r in risk_dist}
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🟢 LOW", dist_map.get("LOW", 0))
        c2.metric("🟡 MEDIUM", dist_map.get("MEDIUM", 0))
        c3.metric("🟠 HIGH", dist_map.get("HIGH", 0))
        c4.metric("🔴 CRITICAL", dist_map.get("CRITICAL", 0))

    st.divider()

    # ── Tabs ───────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📊 All Risk Scores", "🔍 Individual Risk", "⚠️ High Risk"])

    with tab1:
        scores = get_all_risk_scores()
        if scores:
            df = pd.DataFrame(scores)
            df["name"] = df["first_name"] + " " + df["last_name"]

            # Parse factors
            def parse_factors(f):
                try:
                    factors = json.loads(f) if isinstance(f, str) else f
                    return "; ".join(factors) if isinstance(factors, list) else str(f)
                except (json.JSONDecodeError, TypeError):
                    return str(f)

            df["factors_text"] = df["factors"].apply(parse_factors)

            display_df = df[[
                "pan", "name", "score", "risk_level", "factors_text",
            ]].copy()
            display_df.columns = ["PAN", "Name", "Score", "Risk Level", "Factors"]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Score": st.column_config.ProgressColumn(
                        min_value=0, max_value=100, format="%d",
                    ),
                },
            )

            # Risk distribution chart
            colors = {"LOW": "#00d97e", "MEDIUM": "#f6c23e", "HIGH": "#fd7e14", "CRITICAL": "#e63757"}
            fig = px.bar(
                df.sort_values("score", ascending=True),
                x="score", y="name", orientation="h",
                color="risk_level",
                color_discrete_map=colors,
                labels={"score": "Risk Score", "name": "Individual"},
            )
            fig.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig, use_container_width=True)

            csv = df.to_csv(index=False)
            st.download_button("📥 Download Risk Scores CSV", csv, "risk_scores.csv", "text/csv")

    with tab2:
        st.subheader("Individual Risk Analysis")
        individuals = get_all_individuals()
        selected_pan = st.selectbox(
            "Select Individual",
            [i["pan"] for i in individuals],
            format_func=lambda x: f"{x} — {next((i['first_name'] + ' ' + i['last_name'] for i in individuals if i['pan'] == x), '')}",
            key="risk_lookup",
        )

        if selected_pan:
            result = calculate_risk_score(selected_pan)
            if result and "error" not in result:
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Risk Score", result["score"])
                    level = result["risk_level"]
                    level_colors = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}
                    st.markdown(f"### {level_colors.get(level, '⚪')} {level}")

                    st.metric("Casino Winnings", f"₹{result['casino_winnings']:,.0f}")
                    st.metric("ITR Declared", f"₹{result['itr_declared']:,.0f}")
                    st.metric("Difference", f"₹{result['difference']:,.0f}")

                with col2:
                    st.markdown("#### Risk Factors")
                    for factor in result["factors"]:
                        st.markdown(f"• {factor}")

                    st.markdown("#### Rules Applied")
                    for rule in result.get("rules_applied", []):
                        points = RISK_RULES.get(rule, 0)
                        st.markdown(f"• `{rule}` → +{points} points")

    with tab3:
        st.subheader("High Risk Individuals")
        high_risk = get_high_risk_individuals()
        if high_risk:
            df_hr = pd.DataFrame(high_risk)
            df_hr["name"] = df_hr["first_name"] + " " + df_hr["last_name"]
            display_hr = df_hr[["pan", "name", "score", "risk_level", "factors"]].copy()
            display_hr["factors"] = display_hr["factors"].apply(
                lambda f: "; ".join(json.loads(f)) if isinstance(f, str) else str(f)
            )
            display_hr.columns = ["PAN", "Name", "Score", "Level", "Factors"]
            st.dataframe(display_hr, use_container_width=True, hide_index=True)
        else:
            st.success("No high-risk individuals detected.")
