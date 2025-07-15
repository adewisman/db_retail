
import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import calendar
from sqlalchemy import create_engine, text
from urllib.parse import urlparse

# Check authentication status
if not st.session_state.get("authentication_status"):
    st.error("You must be logged in to view this page.")
    st.stop()

@st.cache_data
def load_data():
    """
    Connects to the database, queries all necessary sales data,
    and returns it as a cleaned pandas DataFrame.
    This function is cached to avoid re-running the query on every interaction.
    """
    # Using TURSO_DATABASE_URL from Streamlit secrets.
    db_url = st.secrets["TURSO_DB_URL"]
    auth_token = st.secrets["TURSO_AUTH_TOKEN"]

    if not db_url or not auth_token:
        st.error("TURSO_DB_URL and TURSO_AUTH_TOKEN must be set in .streamlit/secrets.toml.")
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

st.set_page_config(
    page_title="Penjualan By Tipe",
    page_icon="static/logo-icons.jpg",
    layout="wide"  
)
df = load_data()

# --- UI Controls ---
years = sorted(df["year"].unique())
months = [f"{m:02d}" for m in range(1, 13)]

row1_col1, row1_col2, row1_col3 = st.columns([1, 1, 2])

with row1_col1:
    selected_year = st.selectbox("Year", years, index=len(years) - 1)

with row1_col2:
    selected_month = st.selectbox(
        "Month", months, index=datetime.now().month - 1
    )

# Determine the number of days in the selected month
year_int = int(selected_year)
month_int = int(selected_month)
num_days_in_month = calendar.monthrange(year_int, month_int)[1]
day_options = list(range(1, num_days_in_month + 1))

with row1_col3:
    start_day, end_day = st.select_slider(
        "Select Day Range",
        options=day_options,
        value=(1, num_days_in_month)
    )

# --- Filter Data ---
# Filter by year, month, and day range
filtered_df = df[
    (df["year"] == selected_year) &
    (df["month"] == selected_month) &
    (df["day"] >= start_day) &
    (df["day"] <= end_day)
].copy()

# --- Calculations ---
# Create a complete dataframe for the selected day range
all_days_in_range = pd.DataFrame({"day": range(start_day, end_day + 1)})

# Calculate total daily counts
daily_counts = (
    filtered_df.groupby("day")["NO.MEMO"].count().reset_index(name="count")
)
daily_counts = all_days_in_range.merge(
    daily_counts, on="day", how="left"
).fillna(0)
daily_counts["count"] = daily_counts["count"].astype(int)

# Calculate daily counts per series
all_series = filtered_df["SERIES"].unique()
full_series_index = pd.MultiIndex.from_product(
    [range(start_day, end_day + 1), all_series], names=["day", "SERIES"]
)
daily_series_counts = (
    filtered_df.groupby(["day", "SERIES"])
    .size()
    .reset_index(name="count")
    .set_index(["day", "SERIES"])
    .reindex(full_series_index, fill_value=0)
    .reset_index()
)

# Calculate daily counts per segment
all_segment = filtered_df["SEGMENT"].unique()
full_segment_index = pd.MultiIndex.from_product(
    [range(start_day, end_day + 1), all_segment], names=["day", "SEGMENT"]
)
daily_segment_counts = (
    filtered_df.groupby(["day", "SEGMENT"])
    .size()
    .reset_index(name="count")
    .set_index(["day", "SEGMENT"])
    .reindex(full_segment_index, fill_value=0)
    .reset_index()
)

# Calculate daily counts per tipeunit
all_tipeunit = filtered_df["TIPEUNIT"].unique()
full_tipeunit_index = pd.MultiIndex.from_product(
    [range(start_day, end_day + 1), all_tipeunit], names=["day", "TIPEUNIT"]
)
daily_tipeunit_counts = (
    filtered_df.groupby(["day", "TIPEUNIT"])
    .size()
    .reset_index(name="count")
    .set_index(["day", "TIPEUNIT"])
    .reindex(full_tipeunit_index, fill_value=0)
    .reset_index()
)

# --- Heatmap Calculations ---
heatmap_data = filtered_df.groupby(['NAMASALESFORCE', 'SERIES']).size().reset_index(name='count')
heatmap_pivot = heatmap_data.pivot(index='NAMASALESFORCE', columns='SERIES', values='count').fillna(0)

# --- Display Metrics and Charts ---
# Set the plotly template based on the session state theme
plotly_template = "plotly_dark" if st.session_state.get("theme", "light") == "dark" else "plotly_white"

st.metric(
    f"Total Penjualan ({selected_year}-{selected_month}, Day {start_day}-{end_day})",
    f"{daily_counts['count'].sum():,}",
)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # Display a message if there is no data, otherwise show the chart
    if daily_counts['count'].sum() == 0:
        st.info("No sales data for the selected period.")
    else:
        # Plotly interactive line chart with tooltips
        fig_daily = px.line(
            daily_counts,
            x="day",
            y="count",
            markers=True,
            title=f"Graphic Penjualan Harian - {selected_year}-{selected_month} (Day {start_day}-{end_day})",
            labels={"day": "Tanggal", "count": "Total Penjualan"},
            template=plotly_template,
        )
        fig_daily.update_traces(line_color="deepskyblue", marker=dict(size=8, color="orange"))
        st.plotly_chart(fig_daily, use_container_width=True)

with chart_col2:
    # --- Stacked Histogram per SERIES ---
    st.header("Penjualan Berdasarkan Series")

    # Filter out series with no sales
    series_total = daily_series_counts.groupby("SERIES")["count"].sum()
    active_series = series_total[series_total > 0].index
    filtered_series_counts = daily_series_counts[daily_series_counts["SERIES"].isin(active_series)]

    # Plotly stacked bar chart
    fig_series = px.bar(
        filtered_series_counts,
        x="day",
        y="count",
        color="SERIES",
        title=f"Stacked Histogram Penjualan per SERIES - {selected_year}-{selected_month} (Day {start_day}-{end_day})",
        labels={"day": "Tanggal", "count": "Total Penjualan"},
        template=plotly_template,
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

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    # --- Stacked Histogram per SEGMENT ---
    st.header("Penjualan Berdasarkan SEGMENT")

    # Filter out segments with no sales
    segment_total = daily_segment_counts.groupby("SEGMENT")["count"].sum()
    active_segments = segment_total[segment_total > 0].index
    filtered_segment_counts = daily_segment_counts[daily_segment_counts["SEGMENT"].isin(active_segments)]

    # Plotly stacked bar chart
    fig_segment = px.bar(
        filtered_segment_counts,
        x="day",
        y="count",
        color="SEGMENT",
        title=f"Stacked Histogram Penjualan per SEGMENT - {selected_year}-{selected_month} (Day {start_day}-{end_day})",
        labels={"day": "Tanggal", "count": "Total Penjualan"},
        template=plotly_template,
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

with chart_col4:
    # --- Stacked Histogram per TIPEUNIT ---
    st.header("Penjualan Berdasarkan TIPEUNIT")

    # Filter out tipeunit with no sales
    tipeunit_total = daily_tipeunit_counts.groupby("TIPEUNIT")["count"].sum()
    active_tipeunits = tipeunit_total[tipeunit_total > 0].index
    filtered_tipeunit_counts = daily_tipeunit_counts[daily_tipeunit_counts["TIPEUNIT"].isin(active_tipeunits)]

    # Plotly stacked bar chart
    fig_tipeunit = px.bar(
        filtered_tipeunit_counts,
        x="day",
        y="count",
        color="TIPEUNIT",
        title=f"Stacked Histogram Penjualan per TIPEUNIT - {selected_year}-{selected_month} (Day {start_day}-{end_day})",
        labels={"day": "Tanggal", "count": "Total Penjualan"},
        template=plotly_template,
    )
    fig_tipeunit.update_layout(barmode="stack")

    # --- Overlay previous daily NO.MEMO total as a line ---
    fig_tipeunit.add_trace(
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
    st.plotly_chart(fig_tipeunit, use_container_width=True)

# --- Heatmap Chart ---
st.header("Salesforce Performance Heatmap")

with st.expander("Filter Salesforce"):
    # Get the list of salespersons for the filter
    salesforce_options = sorted(heatmap_pivot.index.unique())
    selected_salesforce = st.multiselect(
        "Select Salesforce to Display",
        options=salesforce_options,
        default=salesforce_options  # Default to all selected
    )

# Filter the pivot table based on selection
if selected_salesforce:
    filtered_heatmap_pivot = heatmap_pivot.loc[selected_salesforce]
else:
    # If nothing is selected, create an empty dataframe with the same columns
    filtered_heatmap_pivot = pd.DataFrame(columns=heatmap_pivot.columns)

# Hide columns where all values are zero
if not filtered_heatmap_pivot.empty:
    # Only select columns where the sum is not zero
    filtered_heatmap_pivot = filtered_heatmap_pivot.loc[:, (filtered_heatmap_pivot.sum(axis=0) != 0)]

# Display the heatmap only if there is data
if not filtered_heatmap_pivot.empty:
    fig_heatmap = px.imshow(
        filtered_heatmap_pivot,
        text_auto=True,
        aspect="auto",
        labels=dict(x="SERIES", y="NAMASALESFORCE", color="Total Penjualan"),
        title="Heatmap Penjualan per Sales Force dan Series",
        template=plotly_template
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # --- Grand Total Table ---
    st.write("---")
    st.subheader("Grand Total per Series")
    grand_total = filtered_heatmap_pivot.sum().to_frame('Grand Total').T
    st.dataframe(grand_total, use_container_width=True)
else:
    st.warning("No data to display for the selected Salesforce.")
