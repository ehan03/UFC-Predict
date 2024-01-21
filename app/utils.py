# standard library imports

# third party imports
import streamlit as st

# local imports


def add_socials():
    """Adds social media buttons"""
    st.markdown(
        """
        <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'>
        <style>i {padding-right: 7px;}</style>
        """,
        unsafe_allow_html=True,
    )

    def social_button(url, label, icon):
        button_code = (
            f"<a href='{url}' target=_blank><i class='fa {icon}'></i>{label}</a>"
        )
        return st.markdown(button_code, unsafe_allow_html=True)

    social_button("https://github.com/ehan03", "ehan03", "fa-github")
    social_button("http://linkedin.com/in/e-han", "e-han", "fa-linkedin")
