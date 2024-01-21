# standard library imports

# third party imports
import streamlit as st

# local imports

st.set_page_config(page_title="Methodology", page_icon="🤓")

st.markdown("""# 🤓 Methodology""")
st.markdown("""_A whole lot of yapping_""")
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
