"""Estilos premium para Trading Backtester Pro - Tema Dark Fintech."""

css = """
<style>
/* ============================================
   TRADING BACKTESTER PRO - PREMIUM DARK THEME
   ============================================ */

/* Import Premium Fonts */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* CSS Variables for consistency */
:root {
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-card: rgba(17, 24, 39, 0.7);
    --bg-card-hover: rgba(30, 41, 59, 0.8);
    --border-color: rgba(99, 102, 241, 0.2);
    --border-glow: rgba(99, 102, 241, 0.4);
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent-primary: #6366f1;
    --accent-secondary: #8b5cf6;
    --accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
    --success: #10b981;
    --success-glow: rgba(16, 185, 129, 0.3);
    --danger: #ef4444;
    --danger-glow: rgba(239, 68, 68, 0.3);
    --warning: #f59e0b;
    --glass-bg: rgba(15, 23, 42, 0.6);
    --glass-border: rgba(148, 163, 184, 0.1);
}

/* Base Styles */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: var(--bg-primary) !important;
}

/* Main Container Background with subtle pattern */
.main .block-container {
    background: 
        radial-gradient(ellipse at 20% 0%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 100%, rgba(139, 92, 246, 0.06) 0%, transparent 50%),
        var(--bg-primary);
    padding-top: 2rem !important;
}

/* Animated gradient background for header area */
@keyframes gradientFlow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Sidebar - Sleek Dark */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important;
    border-right: 1px solid var(--border-color) !important;
}

section[data-testid="stSidebar"] .stMarkdown {
    color: var(--text-secondary);
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* Headers with gradient */
h1 {
    font-size: 2.8rem !important;
    font-weight: 700 !important;
    background: var(--accent-gradient) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem !important;
}

h2 {
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    border-bottom: 2px solid var(--accent-primary);
    padding-bottom: 0.5rem;
    margin-top: 2rem !important;
}

h3 {
    font-size: 1.2rem !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
}

/* Glassmorphism Cards */
div[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.8rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
}

div[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-weight: 500 !important;
}

div[data-testid="stMetricDelta"] > div {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500 !important;
}

/* Metric card container styling */
div[data-testid="metric-container"] {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 
        0 4px 6px -1px rgba(0, 0, 0, 0.2),
        0 2px 4px -1px rgba(0, 0, 0, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

div[data-testid="metric-container"]:hover {
    border-color: var(--border-glow) !important;
    transform: translateY(-2px) !important;
    box-shadow: 
        0 10px 15px -3px rgba(0, 0, 0, 0.3),
        0 4px 6px -2px rgba(0, 0, 0, 0.15),
        0 0 20px var(--border-glow),
        inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
}

/* Premium Button Styling */
.stButton > button {
    background: var(--accent-gradient) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.75rem 2rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 
        0 4px 14px 0 rgba(99, 102, 241, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    position: relative !important;
    overflow: hidden !important;
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}

.stButton > button:hover {
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 
        0 8px 25px 0 rgba(99, 102, 241, 0.5),
        0 0 30px rgba(139, 92, 246, 0.3) !important;
}

.stButton > button:hover::before {
    left: 100%;
}

.stButton > button:active {
    transform: translateY(-1px) scale(0.98) !important;
}

/* Input fields */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    transition: all 0.2s ease !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div:focus-within,
.stNumberInput > div > div > input:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
}

/* Slider styling */
.stSlider > div > div > div {
    background: var(--accent-gradient) !important;
}

.stSlider > div > div > div > div {
    background: white !important;
    border: 2px solid var(--accent-primary) !important;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4) !important;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

.stTabs [aria-selected="true"] {
    background: var(--accent-gradient) !important;
    color: white !important;
}

.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    background: rgba(99, 102, 241, 0.1) !important;
    color: var(--text-primary) !important;
}

/* DataFrame/Table styling */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--border-color) !important;
}

.stDataFrame [data-testid="stDataFrameResizable"] {
    background: var(--bg-secondary) !important;
}

/* Expander styling */
.streamlit-expanderHeader {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

.streamlit-expanderHeader:hover {
    border-color: var(--border-glow) !important;
}

/* Progress bar */
.stProgress > div > div {
    background: var(--accent-gradient) !important;
    border-radius: 10px !important;
}

/* Success/Error/Warning messages */
.stSuccess {
    background: rgba(16, 185, 129, 0.1) !important;
    border: 1px solid var(--success) !important;
    border-radius: 12px !important;
}

.stError {
    background: rgba(239, 68, 68, 0.1) !important;
    border: 1px solid var(--danger) !important;
    border-radius: 12px !important;
}

.stWarning {
    background: rgba(245, 158, 11, 0.1) !important;
    border: 1px solid var(--warning) !important;
    border-radius: 12px !important;
}

/* Plotly chart background */
.js-plotly-plot .plotly .modebar {
    opacity: 0.6 !important;
    transition: opacity 0.2s !important;
}

.js-plotly-plot .plotly .modebar:hover {
    opacity: 1 !important;
}

/* Custom animated pulse for live indicators */
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.05); }
}

.live-indicator {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Glow effect for positive values */
.positive-glow {
    text-shadow: 0 0 10px var(--success-glow);
    color: var(--success) !important;
}

/* Glow effect for negative values */
.negative-glow {
    text-shadow: 0 0 10px var(--danger-glow);
    color: var(--danger) !important;
}

/* Premium card component */
.premium-card {
    background: var(--glass-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.premium-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
}

.premium-card:hover {
    border-color: var(--border-glow);
    transform: translateY(-4px);
    box-shadow: 
        0 20px 40px -15px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(99, 102, 241, 0.15);
}

/* Stat badge */
.stat-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 20px;
    padding: 0.4rem 1rem;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--accent-primary);
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: var(--accent-primary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent-secondary);
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Responsive adjustments */
@media (max-width: 768px) {
    h1 {
        font-size: 2rem !important;
    }
    
    .premium-card {
        padding: 1rem;
    }
}
</style>
"""


def apply_styles():
    """Apply premium dark theme to Streamlit app."""
    import streamlit as st
    st.markdown(css, unsafe_allow_html=True)


def premium_metric_card(label: str, value: str, delta: str = None, delta_color: str = "normal"):
    """
    Create a premium styled metric card.
    
    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta value
        delta_color: 'normal', 'inverse', or specific color
    """
    import streamlit as st
    
    delta_html = ""
    if delta:
        color = "#10b981" if delta.startswith("+") or delta_color == "inverse" else "#ef4444"
        if delta_color == "inverse":
            color = "#ef4444" if delta.startswith("+") else "#10b981"
        delta_html = f'<div style="color: {color}; font-size: 0.9rem; font-weight: 500; font-family: JetBrains Mono, monospace;">{delta}</div>'
    
    html = f'''
    <div class="premium-card">
        <div style="color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; font-weight: 500;">
            {label}
        </div>
        <div style="color: #f8fafc; font-size: 2rem; font-weight: 700; font-family: JetBrains Mono, monospace; margin-bottom: 0.25rem;">
            {value}
        </div>
        {delta_html}
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def section_header(title: str, icon: str = ""):
    """Create a styled section header."""
    import streamlit as st
    
    html = f'''
    <div style="display: flex; align-items: center; gap: 0.75rem; margin: 2rem 0 1rem 0;">
        <span style="font-size: 1.5rem;">{icon}</span>
        <h2 style="margin: 0; padding: 0; border: none; background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.4rem; font-weight: 600;">
            {title}
        </h2>
        <div style="flex: 1; height: 2px; background: linear-gradient(90deg, rgba(99, 102, 241, 0.4), transparent);"></div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)
