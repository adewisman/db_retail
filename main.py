import os
from dotenv import load_dotenv

# Load environment variables from .env file at the very beginning
# to ensure they are available for all subsequent modules.
load_dotenv()

import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import calendar

url = os.getenv("TURSO_DB_URL")
auth_token = os.getenv("TURSO_AUTH_TOKEN")

    if not db_url or not auth_token:
        st.error("TURSO_DB_URL and TURSO_AUTH_TOKEN must be set in environment variables.")
        st.stop()

    try:
        # The original code constructed the URL incorrectly, leading to the error:
        # "Can't load plugin: sqlalchemy.dialects:sqlite.https"
        # This happens because the connection string becomes "sqlite+https://..."
        # The correct format is "dialect+driver://host".
        # For Turso, the dialect is "sqlite" and the driver is "libsql".
        # We need to extract the hostname from the full URL provided in the env var.
        hostname = urlparse(db_url).netloc

        engine = create_engine(
            f"sqlite+libsql://{hostname}?secure=true",
            connect_args={"auth_token": auth_token},
        )

        with engine.connect() as conn:
            query = text("SELECT * FROM LAPJUAL")
            result_set = conn.execute(query)
            rows = result_set.fetchall()
            # For SQLAlchemy Result object, use .keys() to get column names
            df = pd.DataFrame(rows, columns=result_set.keys())

        # Ensure fixdate is datetime and drop NaT
        df["fixdate"] = pd.to_datetime(df["fixdate"], errors="coerce")
        df = df.dropna(subset=["fixdate"])
        # Manually create year, month, and day columns from fixdate
        # as they are no longer in the SQL query.
        df["year"] = df["fixdate"].dt.strftime('%Y')
        df["month"] = df["fixdate"].dt.strftime('%m')
        df["day"] = df["fixdate"].dt.day

        return df
    except Exception as e:
        st.error(f"Failed to connect or query database: {e}")
        st.stop()

st.set_page_config(layout="wide")

st.title("Dashboard Penjualan")

df = load_data()

# --- UI Controls ---
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
].copy()

# --- Calculations ---
year_int = int(selected_year)
month_int = int(selected_month)
num_days = calendar.monthrange(year_int, month_int)[1]

# Create a complete dataframe for all days in the month
all_days = pd.DataFrame({'day': range(1, num_days + 1)})

# Calculate total daily counts
daily_counts = filtered_df.groupby("day")["NO.MEMO"].count().reset_index(name="count")
daily_counts = all_days.merge(daily_counts, on="day", how="left").fillna(0)
daily_counts["count"] = daily_counts["count"].astype(int)

# Calculate daily counts per series
all_series = filtered_df["SERIES"].unique()

# Count SERIES per day
daily_series_counts = (
    filtered_df.groupby(["day", "SERIES"])
    .size()
    .reset_index(name="count")
)

# Ensure every day and every series is present
full_series_index = pd.MultiIndex.from_product(
    [range(1, num_days + 1), all_series], names=["day", "SERIES"]
)
daily_series_counts = daily_series_counts.set_index(["day", "SERIES"]).reindex(full_series_index, fill_value=0).reset_index()

# Calculate daily counts per segment
all_segment = filtered_df["SEGMENT"].unique()

# Count SEGMENT per day
daily_segment_counts = (
    filtered_df.groupby(["day", "SEGMENT"])
    .size()
    .reset_index(name="count")
)

# Ensure every day and every segment is present data container
full_segment_index = pd.MultiIndex.from_product(
    [range(1, num_days + 1), all_segment], names=["day", "SEGMENT"]
)
daily_segment_counts = daily_segment_counts.set_index(["day", "SEGMENT"]).reindex(full_segment_index, fill_value=0).reset_index()

# --- Display Metrics and Charts ---
st.metric(f"Total Penjualan {selected_year}-{selected_month}", f"{daily_counts['count'].sum():,}")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # Plotly interactive line chart with tooltips
    fig_daily = px.line(
        daily_counts,
        x="day",
        y="count",
        markers=True,
        title=f"Graphic Penjualan Harian - {selected_year}-{selected_month}",
        labels={"day": "Tanggal", "count": "Total Penjualan"},
        template="plotly_dark",
    )
    fig_daily.update_traces(line_color="deepskyblue", marker=dict(size=8, color="orange"))
    st.plotly_chart(fig_daily, use_container_width=True)

with chart_col2:
    # --- Stacked Histogram per SERIES ---
    st.header("Penjualan Berdasarkan Series")

    # Plotly stacked bar chart
    fig_series = px.bar(
        daily_series_counts,
        x="day",
        y="count",
        color="SERIES",
        title=f"Stacked Histogram Penjualan per SERIES {selected_year}-{selected_month}",
        labels={"day": "Tanggal", "count": "Total Penjualan"},
        template="plotly_dark",
    )
    fig_series.update_layout(barmode="stack")

    # --- Overlay previous daily NO.MEMO total as a line ---
    fig_series.add_trace(
        go.Scatter(
            x=daily_counts["day"],
            y=daily_counts["count"],
            mode="lines+markers",
            name="Total NO.MEMO",
            line=dict(color="deepskyblue", width=3),
            marker=dict(size=8, color="orange"),
            yaxis="y",
        )
    )
    st.plotly_chart(fig_series, use_container_width=True)

# --- Stacked Histogram per SEGMENT (on a new row) ---
st.header("Penjualan Berdasarkan SEGMENT")

# Plotly stacked bar chart
fig_segment = px.bar(
    daily_segment_counts,
    x="day",
    y="count",
    color="SEGMENT",
    title=f"Stacked Histogram Penjualan per SEGMENT {selected_year}-{selected_month}",
    labels={"day": "Tanggal", "count": "Total Penjualan"},
    template="plotly_dark",
)
fig_segment.update_layout(barmode="stack")

# --- Overlay previous daily NO.MEMO total as a line ---
fig_segment.add_trace(
    go.Scatter(
        x=daily_counts["day"],
        y=daily_counts["count"],
        mode="lines+markers",
        name="Total NO.MEMO",
        line=dict(color="deepskyblue", width=3),
        marker=dict(size=8, color="orange"),
        yaxis="y",
    )
)
st.plotly_chart(fig_segment, use_container_width=True)