# standard library imports
import sqlite3

# third party imports
import streamlit as st

# local imports

st.set_page_config(page_title="Results", page_icon="📊")

st.markdown("""# 📊 Results""")
st.markdown("""_Past predictions and bets + profit/loss stats_""")
st.divider()
st.info("Last updated: TBA")

# Set fixed width sidebar
st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"]{
        min-width: 244px;
        max-width: 244px;
    }
    """,
    unsafe_allow_html=True,
)
