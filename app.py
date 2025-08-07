import streamlit as st
from pages import overview, top_artists

st.set_page_config(page_title="Scrobblings Dashboard", layout="wide")

# Custom CSS to remove white banner and create elegant navigation
st.markdown("""
<style>
/* Remove white banner noise */
.main .block-container {
    padding-top: 1rem;
}

/* Hide any sidebar navigation */
section[data-testid="stSidebar"] {
    display: none !important;
}

/* Hide sidebar if it appears */
.sidebar .sidebar-content {
    display: none !important;
}

/* Elegant navigation panel */
.nav-panel {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    padding: 1.5rem;
    margin: 1rem 0 2rem 0;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    border: 1px solid rgba(255,255,255,0.2);
}

.nav-button {
    background: rgba(255,255,255,0.1);
    color: white;
    padding: 0.8rem 1.5rem;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 10px;
    cursor: pointer;
    margin: 0 0.5rem;
    transition: all 0.3s ease;
    font-weight: 500;
    backdrop-filter: blur(10px);
}

.nav-button:hover {
    background: rgba(255,255,255,0.2);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.nav-button.active {
    background: rgba(255,255,255,0.25);
    border-color: rgba(255,255,255,0.4);
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}

.nav-title {
    color: white;
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1rem;
    text-align: center;
}

/* Remove default Streamlit padding */
.main .block-container {
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 1200px;
}
</style>
""", unsafe_allow_html=True)

# Create elegant navigation panel
st.markdown('<div class="nav-panel">', unsafe_allow_html=True)
st.markdown('<div class="nav-title">🎵 Scrobblings Dashboard</div>', unsafe_allow_html=True)

# Use session state to track current page
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Visión general"

# Navigation buttons in a more elegant layout
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if st.button("📊 Visión general", key="overview_btn", 
                help="Ver estadísticas generales de scrobblings"):
        st.session_state.current_page = "Visión general"

with col2:
    if st.button("🎵 Top Artistas", key="artists_btn", 
                help="Ver los artistas más escuchados"):
        st.session_state.current_page = "Top Artistas"

with col3:
    # Placeholder for future button
    st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)

with col4:
    # Placeholder for future button
    st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Page content
if st.session_state.current_page == "Visión general":
    overview.show()
elif st.session_state.current_page == "Top Artistas":
    top_artists.show()
