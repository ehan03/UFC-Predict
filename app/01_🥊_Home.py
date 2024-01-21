# standard library imports
import sqlite3

# third party imports
import streamlit as st

# local imports
from .utils import add_socials

st.set_page_config(page_title="UFC-Predict", page_icon="🥊")

st.markdown("""# 🥊 UFC-Predict""")
st.markdown("""_Applying machine learning and optimization techniques to the UFC_""")
st.divider()

st.markdown("""### Upcoming""")
st.info("Last updated: TBA")

st.divider()
st.markdown("""### Socials""")
add_socials()
