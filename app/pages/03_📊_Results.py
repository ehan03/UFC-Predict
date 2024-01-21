# standard library imports
import sqlite3

# third party imports
import streamlit as st

# local imports
from ..utils import set_sidebar_fixed_width

st.set_page_config(page_title="Results", page_icon="📊")

st.markdown("""# 📊 Results""")
st.markdown("""_Past predictions and bets + profit/loss stats_""")
st.divider()
st.info("Last updated: TBA")

set_sidebar_fixed_width()
