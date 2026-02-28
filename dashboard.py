import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Wireless Automation Dashboard", page_icon="📱", layout="wide")

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_db_connection():
    # Use environment variables or default to localhost mapping for Docker
    pg_user = os.getenv("PG_USER", "postgres")
    pg_password = os.getenv("PG_PASSWORD", "postgres")
    pg_host = os.getenv("PG_HOST", "localhost")
    pg_port = os.getenv("PG_PORT", "5432")
    pg_db = os.getenv("PG_DB", "postgres")
    
    # SQLAlchemy engine for Pandas
    engine = create_engine(f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}")
    return engine

engine = get_db_connection()

# --- FETCH DATA ---
@st.cache_data(ttl=5) # Refresh data every 5 seconds dynamically
def load_data():
    try:
        # Load tables directly into Pandas DataFrames
        df_results = pd.read_sql("SELECT * FROM results", engine)
        df_devices = pd.read_sql("SELECT * FROM devices", engine)
        return df_results, df_devices
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_results, df_devices = load_data()

# --- DASHBOARD UI ---
st.title("📱 Apple Wireless Automation Dashboard")
st.markdown("Real-time metrics for hardware test execution layers and device statuses.")

if df_results.empty or df_devices.empty:
    st.warning("No data found in PostgreSQL. Please run `python main.py` to generate test data.")
else:
    # --- METRICS ROW ---
    total_tests = len(df_results)
    passed_tests = len(df_results[df_results['status'] == 'PASS'])
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    avg_duration = df_results['duration_sec'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tests Executed", total_tests)
    col2.metric("Passed Tests", passed_tests)
    col3.metric("Pass Rate (%)", f"{pass_rate:.1f}%")
    col4.metric("Avg Duration (s)", f"{avg_duration:.2f}s")
    
    st.markdown("---")
    
    # --- CHARTS ROW ---
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Test Results Status")
        # Plotly Pie Chart mapping pass/fails
        fig_pie = px.pie(
            df_results, 
            names='status', 
            hole=0.4,
            color='status',
            color_discrete_map={'PASS':'#00d26a', 'FAIL':'#f8312f'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_chart2:
        st.subheader("Test Execution Duration by Type")
        # Bar chart comparing duration times across different test types
        duration_avg = df_results.groupby('test_name')['duration_sec'].mean().reset_index()
        fig_bar = px.bar(
            duration_avg, 
            x='test_name', 
            y='duration_sec',
            color='test_name',
            title="Average Execution Time (Seconds)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    st.markdown("---")
    
    # --- DATA TABLES ---
    col_table1, col_table2 = st.columns(2)
    
    with col_table1:
        st.subheader("Live Device Fleet Status")
        # Display the devices dataframe
        st.dataframe(df_devices[['device_id', 'status', 'updated_at']], use_container_width=True, hide_index=True)
        
    with col_table2:
        st.subheader("Recent Test Executions")
        # Display the most recent 10 results
        recent_results = df_results.sort_values(by='timestamp', ascending=False).head(10)
        st.dataframe(recent_results[['test_name', 'device_id', 'status', 'duration_sec']], use_container_width=True, hide_index=True)
