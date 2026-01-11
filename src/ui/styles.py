"""Estilos personalizados para la UI."""

css = """
<style>
/* Import Inter font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

/* Base Styles */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0E1117;
    border-right: 1px solid #262730;
}

/* Metric Cards */
div.css-1r6slb0, div.css-1wivap2 {
    background-color: #262730;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #363945;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

/* Headers */
h1, h2, h3 {
    font-weight: 700;
    color: #FAFAFA;
}

h1 {
    font-size: 2.5rem;
    background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Buttons */
.stButton button {
    background: linear-gradient(45deg, #FF4B4B, #FF914D);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 75, 75, 0.3);
}

/* Plotly Charts */
.js-plotly-plot .plotly .modebar {
    opacity: 0.5 !important;
}

/* Custom Containers */
.custom-card {
    background-color: #1E1E1E;
    padding: 1.5rem;
    border-radius: 10px;
    border: 1px solid #333;
    margin-bottom: 1rem;
}

.metric-label {
    font-size: 0.9rem;
    color: #A0A0A0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #FFFFFF;
}

.metric-delta-pos {
    color: #4CAF50;
    font-size: 0.9rem;
    font-weight: 600;
}

.metric-delta-neg {
    color: #FF5252;
    font-size: 0.9rem;
    font-weight: 600;
}
</style>
"""

def apply_styles():
    import streamlit as st
    st.markdown(css, unsafe_allow_html=True)
