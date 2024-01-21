# standard library imports

# third party imports
import streamlit as st

# local imports
from ..utils import set_sidebar_fixed_width

st.set_page_config(page_title="Info", page_icon="🗿")

st.markdown("""# 🗿 Info""")
st.markdown("""_About this project + FAQ minus the F_""")
st.divider()

set_sidebar_fixed_width()
