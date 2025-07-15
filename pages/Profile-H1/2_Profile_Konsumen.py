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
            query = text("""
                SELECT
                l.local_id,
                l.fixdate AS tgl_nd, 
                fn.TGL_MOHON AS tgl_faktur_md,
                l."NO.MEMO" as no_espk, 
                l."NO.INVOICE" no_nd, 
                l."NO.SURATJALAN(SJ)" AS no_sj_nd, 
                l.NAMAKONSUMEN,
                fn.TGL_LAHIR,
                fn.PEKERJAAN as pekerjaan_kons,
                fn.PENGELUARAN as pengeluaran_kons,
                fn.DIGUNAKAN as gunakan_kons,
                fn.MTRSBL as kons_mtrsbl,
                fn.JENIS_SKR as kons_jnsskr,
                fn.KD_PEMAKAI as kons_kdpmkai,
                l.ALAMATKONSUMEN, 
                l.KELURAHAN, 
                l.KECAMATAN, 
                l."KOTA/KAB", 
                l.NAMASALESFORCE, 
                l.JABATAN, 
                l.GC, 
                l.SEGMENT, 
                l.SERIES, 
                l.SALESTYPE, 
                l.TIPEUNIT, 
                l.WARNAUNIT, 
                l."NO.MESIN", 
                l."NO.RANGKA", 
                l.TIPEPEMBAYARAN, 
                l.LEASING,
                fn.UANG_MUKA as cr_dp,
                fn.TENOR as cr_tenor,
                l.DiskonCustomer, 
                l.DiskonMd, 
                l.DiskonSCP, 
                l.totaldiskon, 
                l.SOURCECHANNEL,
                fn.last_sync_at
                FROM LAPJUAL l
                LEFT JOIN faktur_net fn ON fn.NO_RANGKA = l."NO.RANGKA"
            """)
            result_set = conn.execute(query)
            rows = result_set.fetchall()
            # For SQLAlchemy Result object, use .keys() to get column names
            df = pd.DataFrame(rows, columns=result_set.keys())
        # Ensure tgl_nd is datetime and drop NaT
        df["tgl_nd"] = pd.to_datetime(df["tgl_nd"], errors="coerce")
        df = df.dropna(subset=["tgl_nd"])
        # Manually create year, month, and day columns from tgl_nd
        # as they are no longer in the SQL query.
        df["year"] = df["tgl_nd"].dt.strftime('%Y')
        df["month"] = df["tgl_nd"].dt.strftime('%m')
        df["day"] = df["tgl_nd"].dt.day

        return df
    except Exception as e:
        st.error(f"Failed to connect or query database: {e}")
        st.stop()
