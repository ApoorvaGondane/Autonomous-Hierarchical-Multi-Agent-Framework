import streamlit as st
import requests
from streamlit_mermaid import st_mermaid
import os 
import re
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd
st.set_page_config(page_title="Product Development Panel", layout="wide")

st.title("Autonomous Multi-Agent Product Planning")
st.markdown("Enter your product requirements below to trigger the Manager, R&D, Manufacturing, and Marketing agents.")

# Initialize the session state key
if 'query_input' not in st.session_state:
    st.session_state.query_input = "Portable solar-powered outdoor air quality monitor"
    
with st.sidebar:
    st.header("Specifications")
    spec_input = st.text_area("Product Idea", key="query_input")
    budget_input = st.number_input("Maximum Unit Budget ($)", value=65.0)
    generate_btn = st.button("Generate Strategy")

# Initialize a session state list to hold past queries
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

if generate_btn:
    st.session_state.query_history.append(spec_input)
    with st.spinner("Agents are debating constraints and calculating costs... This may take up to 90 seconds."):
        try:
            api_endpoint = os.getenv("API_URL", "http://localhost:8000/api/v1/plan/generate")
            response = requests.post(
                api_endpoint,
                json={"product_spec": spec_input, "budget_usd": budget_input}
            )
            response.raise_for_status()
            data = response.json()
            
            st.success("Strategy Generated Successfully!")
            
            # 1. Target the specific agent tasks for robust extraction
            crew_data = data.get("data", {}) if "data" in data else data
            tasks = crew_data.get("tasks_output", [])
            
            rd_text = tasks[0].get("raw", "") if len(tasks) > 0 else ""
            mfg_text = tasks[1].get("raw", "") if len(tasks) > 1 else ""
            mkt_text = tasks[2].get("raw", "") if len(tasks) > 2 else ""

            # 2. Extract metrics using highly forgiving regex
            raw_cost_match = re.search(r"(?:total|material)[\w\s]*cost[\s:*-]*\$?([0-9.]+)", rd_text + mfg_text, re.IGNORECASE)
            overhead_match = re.search(r"overhead[\w\s:*-]*\$?([0-9.]+)", mfg_text, re.IGNORECASE)
            retail_match = re.search(r"(?:retail|target|selling)[\w\s]*price[\s:*-]*\$?([0-9.]+)", mkt_text, re.IGNORECASE)
            comp_price_match = re.search(r"\$?([0-9.]+)\s*(?:to|-|and)\s*\$?([0-9.]+)", mkt_text, re.IGNORECASE)

            # Fallbacks in case the 8B model hallucinates formatting
            raw_cost = float(raw_cost_match.group(1)) if raw_cost_match else 0.0
            overhead = float(overhead_match.group(1)) if overhead_match else (raw_cost * 0.15)
            final_mfg_cost = raw_cost + overhead
            retail_price = float(retail_match.group(1)) if retail_match else 0.0
            
            # Reconstruct the range string safely
            comp_range = f"${comp_price_match.group(1)} to ${comp_price_match.group(2)}" if comp_price_match else "Data unavailable"

            # 3. Top Level Financial KPIs
            st.subheader("Financial Overview")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Raw Material Cost", f"${raw_cost:.2f}")
            m2.metric("Final Manufacturing Cost", f"${final_mfg_cost:.2f}")
            m3.metric("Target Retail Price", f"${retail_price:.2f}")
            m4.metric("Competitor Range", comp_range)
            
            st.divider()
            
            # --- NEW PLOTLY WATERFALL CHART ---
            st.subheader("Cost & Profit Margins")
            gross_profit = retail_price - final_mfg_cost

            fig_waterfall = go.Figure(go.Waterfall(
                name="Financials", 
                orientation="v",
                measure=["relative", "relative", "total", "relative", "total"],
                x=["Raw Materials", "Assembly Overhead", "Total Mfg Cost", "Gross Profit", "Retail Price"],
                textposition="outside",
                text=[f"${raw_cost:.2f}", f"${overhead:.2f}", f"${final_mfg_cost:.2f}", f"${gross_profit:.2f}", f"${retail_price:.2f}"],
                y=[raw_cost, overhead, final_mfg_cost, gross_profit, retail_price],
                decreasing={"marker": {"color": "#ff4b4b"}},
                increasing={"marker": {"color": "#0068c9"}},
                totals={"marker": {"color": "#29b09d"}}
            ))

            fig_waterfall.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_waterfall, use_container_width=True)
            
            st.divider()
            
            # 4. Detailed Dashboards
            col1, col2 = st.columns([1, 1.2])
            
            with col1:
                st.subheader("Bill of Materials (BOM)")
                # Filter out the conversational fluff, keep only the bullet points
                bom_lines = [line.strip('* -') for line in rd_text.split('\n') if line.strip().startswith('*') or line.strip().startswith('-')]
                
                # --- NEW PANDAS DATAFRAME ---
                if bom_lines:
                    df_bom = pd.DataFrame(bom_lines, columns=["Component Specification"])
                    st.dataframe(df_bom, use_container_width=True, hide_index=True)
                else:
                    st.info(rd_text)
                    
                st.subheader("Market Positioning")
                st.write(mkt_text)
                
            with col2:
                st.subheader("Production Timeline")
                mermaid_match = re.search(r"```mermaid(.*?)```", mfg_text, re.DOTALL)
                
                if mermaid_match:
                    clean_code = mermaid_match.group(1).strip()
                    current_year = str(datetime.now().year)
                    clean_code = clean_code.replace("2023", current_year)
                    if "%%{init" not in clean_code:
                        clean_code = "%%{init: {'theme': 'dark'}}%%\n" + clean_code
                    st_mermaid(clean_code)
                else:
                    st.warning("No Gantt chart formatting detected in the manufacturing response.")

            st.sidebar.divider()
            st.sidebar.subheader("Previous Queries")

            for past_query in reversed(st.session_state.query_history):
                if st.sidebar.button(past_query, use_container_width=True):
                    # Programmatically force the widget's tied key to update
                    st.session_state.query_input = past_query
                    st.rerun()   
                    
        except Exception as e:
            st.error(f"Failed to generate strategy: {str(e)}")