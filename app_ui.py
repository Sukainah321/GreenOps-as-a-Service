import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="GreenOps-aaS", layout="wide")

st.title("🌱 GreenOps-as-a-Service")
st.write("X-as-a-Service: Cloud Sustainability & Optimiser")

BACKEND_URL = "http://127.0.0.1:5000"

tab1, tab2 = st.tabs(["Optimisation Service", "Research Library"])

with tab1:
    code_input = st.text_area("Paste Python code for analysis:", height=250,
        placeholder="# Paste your Python code here...")

    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        analyse = st.button("Analyze Code", type="primary")
    with col_info:
        st.caption("Singapore Grid GEF: 0.42 kg CO₂/kWh")

    if analyse:
        if not code_input.strip():
            st.warning("Please paste some Python code ...")
        else:
            with st.spinner("AI Service Optimising…"):
                try:
                    res = requests.post(
                        f"{BACKEND_URL}/audit",
                        json={"code": code_input}
                    )
                except requests.exceptions.ConnectionError:
                    st.error(
                        "**Backend offline.** Start app.py first:\n\n"
                        "```\npython app.py\n```"
                    )
                    st.stop()
 
            if res.status_code != 200:
                try:
                    err = res.json().get("error", res.text)
                except Exception:
                    err = res.text
                st.error(f"**API Error:** {err}")
                st.stop()
 
            data   = res.json()
            report = data.get("report", {})
            ai_on  = data.get("ai_powered", False)
 
            if not report:
                st.error("Received an empty report from the backend.")
                st.stop()
 
            # ── AI badge ──
            if ai_on:
                st.success("✅ AI-powered audit complete")
            else:
                st.warning("⚙️ AST fallback audit (Gemini unavailable — check your API key)")
 
            st.divider()
 
            # ── 1. Key metrics ──
            st.subheader("Results")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Green Score", f"{report.get('green_score', 0)} / 100")
            c2.metric("AI Powered", "Yes (Gemini)" if ai_on else "No (AST)")
            c3.metric("CO₂ Saved / Run", f"{report.get('total_co2_grams_per_run', 0):.4f} g")
            c4.metric("vCPU Hours Saved",f"{report.get('total_vcpu_hours_saved', 0):.4f} h")
 
            # ── 2. Summary ──
            st.info(f"**AI Summary:** {report.get('summary', 'No summary provided.')}")
 
            # ── 3. Formula breakdown ──
            with st.expander("📐 Sustainability Formula Breakdown"):
                st.write("**Carbon Calculation Logic (Singapore Grid)**")
                st.latex(r"\text{Energy}_{kWh} = \text{Hours}_{saved} \times 0.0021\,kW")
                st.latex(r"\text{Carbon}_{g} = \text{Energy}_{kWh} \times 0.42\,\frac{kg}{kWh} \times 1000")
                st.write(f"- vCPU Hours saved: **{report.get('total_vcpu_hours_saved', 0):.4f} h**")
                st.write(f"- Singapore Grid Emission Factor: **0.42 kg CO₂/kWh**")
                st.write(f"- CO₂ reduction: **{report.get('total_co2_grams_per_run', 0):.4f} g per run**")
 
            # ── 4. Efficiency score bars ──
            st.subheader("Efficiency Scores")
            scores = report.get("scores", {})
            if scores:
                cols = st.columns(len(scores))
                for idx, (k, v) in enumerate(scores.items()):
                    label = k.replace("_", " ").title()
                    color = "normal" if v >= 70 else ("off" if v < 40 else "normal")
                    cols[idx].metric(label, f"{v}/100")
                    cols[idx].progress(int(v) / 100)
            else:
                st.write("No score breakdown available.")
 
            st.divider()
 
            # ── 5. Issues + Improved code side-by-side ──
            col_l, col_r = st.columns(2)
 
            with col_l:
                st.subheader("Issues Detected")
                issues = report.get("issues", [])
                if issues:
                    for iss in issues:
                        sev = iss.get("severity", "low")
                        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sev, "⚪")
                        with st.expander(f"{icon} [{sev.upper()}] {iss.get('pattern', 'Unknown')}  —  {iss.get('line_hint', '')}"):
                            st.write(f"**Fix:** {iss.get('fix', '')}")
                            st.write(f"**Impact:** {iss.get('impact', '')}")
                            st.write(f"**Est. hours saved:** {iss.get('estimated_hours_saved', 0):.2f} h/run")
                else:
                    st.success("No issues found — code is already efficient!")
 
            with col_r:
                st.subheader("Improved Code")
                improved = report.get("improved_code", "")
                if improved.strip():
                    st.code(improved, language="python")
                else:
                    st.info("No optimisation needed.")
 
with tab2:
    st.subheader("Crowdsourced Research Library")
    st.write(
        "Dual-Utility: Anonymized data used for Green Cloud Computing research."
    )
 
    col_refresh, _ = st.columns([1, 4])
    with col_refresh:
        refresh = st.button("Refresh Library")
 
    if refresh:
        try:
            lib_res = requests.get(f"{BACKEND_URL}/library")
            lib = lib_res.json()
        except requests.exceptions.ConnectionError:
            st.error("Backend offline. Start app.py first.")
            lib = []
        except Exception as e:
            st.error(f"Library fetch error: {e}")
            lib = []
 
        if lib:
            df = pd.DataFrame(lib)
 
            st.metric("Total Audits Logged", len(df))
 
            # Green Score trend chart
            st.write("**Green Score**")
            if "timestamp" in df.columns and "green_score" in df.columns:
                chart_df = df.set_index("timestamp")[["green_score"]]
                st.line_chart(chart_df)
 
            # CO2 saved trend
            if "co2_saved" in df.columns:
                st.write("**Estimated Carbon Reduction**")
                st.bar_chart(df.set_index("timestamp")["co2_saved"])
 
            # Raw table
            st.write("**All Audit Records**")
            st.dataframe(df, width="stretch")
 
            # Summary stats
            st.write("**Summary Statistics**")
            numeric_df = df.select_dtypes(include="number")
            if not numeric_df.empty:
                st.dataframe(numeric_df.describe(), width="stretch")
        else:
            st.info("No audit data yet.")

 