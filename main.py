import os
import libsql
import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import calendar
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
url = os.getenv("TURSO_DB_URL")
auth_token = os.getenv("TURSO_AUTH_TOKEN")

if not url or not auth_token:
    raise EnvironmentError("TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set in environment variables.")

conn = libsql.connect(url, auth_token=auth_token)

# Query all data
query = """
SELECT 
    fixdate, 
    "NO.MEMO",
    STRFTIME('%Y', fixdate) AS year,
    STRFTIME('%m', fixdate) AS month
FROM LAPJUAL
"""
rows = conn.execute(query).fetchall()

# Convert to DataFrame
df = pd.DataFrame(rows, columns=["fixdate", "NO.MEMO", "year", "month"])

# Ensure fixdate is datetime and drop NaT
df["fixdate"] = pd.to_datetime(df["fixdate"], errors="coerce")
df = df.dropna(subset=["fixdate"])

# Streamlit app
st.title("Total Penjualan Daily")

# Generate year and month LOV from data
years = sorted(df["year"].unique())
months = [f"{m:02d}" for m in range(1, 13)]

col1, col2 = st.columns(2)
with col1:
    selected_year = st.selectbox("Select Year", years, index=len(years)-1)
with col2:
    selected_month = st.selectbox("Select Month", months, index=datetime.now().month-1)

# --- Filter Data ---
filtered_df = df[
    (df["year"] == selected_year) &
    (df["month"] == selected_month)
]

# Show total count for the selected month at the top
st.write(f"Total Penjualan {selected_year}-{selected_month}: {filtered_df['NO.MEMO'].count()}")

# st.subheader(f"{selected_year}-{selected_month}")

# Get number of days in selected month/year
year_int = int(selected_year)
month_int = int(selected_month)
num_days = calendar.monthrange(year_int, month_int)[1]

# Create a complete dataframe for all days in the month
all_days = pd.DataFrame({'day': range(1, num_days + 1)})

# Count NO.MEMO per day
daily_counts = filtered_df.groupby(filtered_df["fixdate"].dt.day)["NO.MEMO"].count().reset_index()
daily_counts.rename(columns={"fixdate": "day", "NO.MEMO": "count"}, inplace=True)

# Merge with all days to ensure every day is present
daily_counts = all_days.merge(daily_counts, on="day", how="left").fillna(0)
daily_counts["count"] = daily_counts["count"].astype(int)

# Plotly interactive line chart with tooltips
fig = px.line(
    daily_counts,
    x="day",
    y="count",
    markers=True,
    title=f"Total Penjualan {selected_year}-{selected_month}",
    labels={"day": "Tgl", "count": "Total Jual"},
    template="plotly_dark"
)
fig.update_traces(line_color='deepskyblue', marker=dict(size=8, color='orange'))

st.plotly_chart(fig, use_container_width=True)