def load_css():
    css = """
    <style>
    /* 1. Global Typography & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }
    
    .stApp {
        background-color: #f8fafc; /* light background */
        color: #0f172a;
    }

    /* 2. Header (Top Navigation) */
    header[data-testid="stHeader"] {
        background-color: #ffffff;
        border-bottom: 1px solid #e2e8f0;
        box-shadow: none;
    }
    /* Hide the top colored line from Streamlit */
    .stApp > header {
        background-image: none !important;
    }

    /* 3. Left Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        color: #f8fafc;
        border-right: 1px solid #1e293b;
    }
    /* Sidebar text color overrides */
    section[data-testid="stSidebar"] .css-17lntkn,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f8fafc !important;
    }
    
    /* Sidebar labels and small caps */
    .sidebar-section-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-top: 24px;
        margin-bottom: 8px;
        font-weight: 600;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 4px;
    }

    /* 4. Input Boxes */
    .stSelectbox label, .stTextInput label, .stTextArea label {
        font-weight: 500;
        color: #475569;
        font-size: 13px !important;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }
    .stSelectbox > div > div > div, .stTextInput > div > div > input, .stTextArea > div > textarea {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
        color: #0f172a !important;
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace !important;
        font-size: 14px;
    }
    
    /* 5. Buttons */
    .stButton > button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 16px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }

    /* 6. Tabs to Step Indicators */
    div[data-testid="stTabs"] {
        margin-top: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 12px;
        padding-bottom: 12px;
        border-bottom: 2px solid transparent !important;
        background-color: transparent !important;
        color: #64748b !important;
        font-weight: 500;
        font-size: 15px;
        border-radius: 0 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #2563eb !important;
        border-bottom: 2px solid #2563eb !important;
        font-weight: 600;
    }

    /* 7. Card Layout for Main Content */
    /* Wrap the active tab content in a card */
    div[data-testid="stTab"] > div {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 32px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        margin-top: 16px;
        transition: box-shadow 0.3s ease;
    }
    div[data-testid="stTab"] > div:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* Headers inside cards */
    div[data-testid="stTab"] h1, div[data-testid="stTab"] h2, div[data-testid="stTab"] h3 {
        color: #0f172a;
        margin-top: 0;
    }
    div[data-testid="stTab"] h2 {
        font-size: 20px;
        font-weight: 600;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 12px;
        margin-bottom: 24px;
    }

    /* 8. Badges for Metadata */
    .metadata-badge {
        display: inline-block;
        background-color: #f1f5f9;
        color: #334155;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 12px;
        border: 1px solid #e2e8f0;
    }
    .metadata-badge.accent {
        background-color: #e0f2fe;
        color: #0369a1;
        border-color: #bae6fd;
    }

    /* Remove top margin of the main block to tighten up */
    .block-container {
        padding-top: 2rem !important;
        max-width: 1200px !important;
    }
    
    /* Top Bar Component */
    .top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
    }
    .top-bar h1 {
        font-size: 24px;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
    }
    .top-bar-status {
        font-size: 12px;
        color: #14b8a6;
        background-color: #ccfbf1;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    </style>
    """
    return css
