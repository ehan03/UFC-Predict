# standard library imports

# third party imports
import streamlit as st

# local imports

st.set_page_config(page_title="Info", page_icon="🗿")

st.markdown("""# 🗿 Info""")
st.markdown("""_About this project + FAQ minus the F_""")
st.divider()

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
