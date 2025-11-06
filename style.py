# style.py
import streamlit as st

def apply_theme(title: str = "GeoShield", hide_sidebar: bool = True, layout: str = "wide"):
    # Call set_page_config ONLY once per page
    if not st.session_state.get("_pg_cfg"):
        st.set_page_config(page_title=title, layout=layout)
        st.session_state["_pg_cfg"] = True

    # Global CSS: warm sand / cream + optional sidebar hide
    st.markdown(f"""
    <style>
      :root {{
        --gs-bg: #FFFAEE;          /* app background (soft cream) */
        --gs-card: #EBDCC7;        /* containers (light beige)   */
        --gs-accent: #8F7B66;      /* buttons & highlights        */
        --gs-accent-strong:#6F5F4F;/* hover/darker accent         */
        --gs-text:#2B2B2B;         /* text color                  */
        --gs-sand:#BBAB8C;         /* border sand                 */
      }}

      .stApp {{
        background: var(--gs-bg) !important;
        color: var(--gs-text) !important;
      }}
      .block-container {{ padding-top: 1rem; }}

      /* “Cards” look for top-level blocks */
      [data-testid="stVerticalBlock"] > div {{
        background: var(--gs-card);
        border: 1px solid var(--gs-sand);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
      }}

      /* Inputs */
      input, textarea, select, .stTextInput > div > div > input {{
        background: #F7EEDC !important;
        color: var(--gs-text) !important;
        border: 1px solid var(--gs-sand) !important;
        border-radius: 10px !important;
      }}

      /* Buttons */
      .stButton > button {{
        background: var(--gs-accent) !important;
        color: #FFFFFF !important;
        border: 0 !important;
        border-radius: 12px !important;
        padding: 0.5rem 1rem !important;
        box-shadow: 0 2px 0 rgba(0,0,0,0.08);
      }}
      .stButton > button:hover {{ background: var(--gs-accent-strong) !important; }}

      /* Metrics */
      [data-testid="stMetricValue"] {{ color: var(--gs-accent-strong) !important; }}

      /* DataFrame shell */
      .stDataFrame {{ border-radius: 10px; overflow: hidden; }}

      /* Optional: fully hide the sidebar + toggles (robust selectors) */
      {"section[data-testid='stSidebar'] { display:none !important; }" if hide_sidebar else ""}
      {"div[data-testid='stSidebarNav'] { display:none !important; }" if hide_sidebar else ""}
      {"button[kind='header'] { display:none !important; }" if hide_sidebar else ""}  /* top-right menu */
      {"div[data-testid='collapsedControl'] { display:none !important; }" if hide_sidebar else ""}

      /* Remove left gutter space that appears when sidebar is hidden */
      {"[data-testid='stAppViewContainer'] > .main { padding-left: 1rem !important; }" if hide_sidebar else ""}
    </style>
    """, unsafe_allow_html=True)
