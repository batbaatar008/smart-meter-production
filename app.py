import streamlit as st
import streamlit.components.v1 as components

# Streamlit-ийн гарчиг
st.set_page_config(layout="wide")

# Миний өгсөн HTML кодыг энд хувьсагчид хадгална
html_code = """
<!DOCTYPE html>
<html>
... (миний өгсөн бүх HTML кодыг энд бүтнээр нь хуулна) ...
</html>
"""

# HTML-ийг Streamlit дотор суулгаж өгөх
components.html(html_code, height=900, scrolling=True)
