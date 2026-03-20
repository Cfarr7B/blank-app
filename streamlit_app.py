import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="7BREW | Financial Performance Dashboard",
    page_icon="coffee",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit default UI for a clean dashboard experience
st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            max-width: 100% !important;
        }
        iframe {
            border: none !important;
        }
        .stApp {
            background-color: #0D0D0D;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Read the HTML dashboard file
html_path = Path(__file__).parent / "dashboard.html"
html_content = html_path.read_text(encoding="utf-8")

# Render the full HTML dashboard inside Streamlit
st.components.v1.html(html_content, height=2000, scrolling=True)
