# standard library imports
import os
import sqlite3

# third party imports
import streamlit as st

# local imports
from utils import add_socials

st.set_page_config(page_title="UFC-Predict", page_icon="🥊")

st.markdown("""# 🥊 UFC-Predict""")
st.markdown("""_Applying machine learning and optimization techniques to the UFC_""")
st.divider()

st.markdown("""### Upcoming""")
st.info("Last updated: TBA")

_left, mid, _right = st.columns([0.2, 0.5, 0.2])
with mid:
    st.image(os.path.join(os.path.dirname(__file__), "images", "cat-crying-ufc.png"))

st.markdown(
    "ignore the above image - this app has no idea of knowing if there's an event this week or not (yet)"
)
st.markdown("i swear this will work in the future, for now enjoy my artwork")

st.divider()
st.markdown("""### Socials""")
add_socials()
