import streamlit as st
from pages import overview, top_artists

st.set_page_config(page_title="Scrobblings Dashboard", layout="wide")

# Top navigation menu
st.markdown("""
<style>
.nav-container {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 2rem;
}
.nav-button {
    background-color: #4CAF50;
    color: white;
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 0.3rem;
    cursor: pointer;
    margin-right: 0.5rem;
}
.nav-button:hover {
    background-color: #45a049;
}
.nav-button.active {
    background-color: #2E7D32;
}
</style>
""", unsafe_allow_html=True)

# Create top navigation
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    
    # Use session state to track current page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Visión general"
    
    # Navigation buttons
    col_overview, col_artists = st.columns(2)
    
    with col_overview:
        if st.button("📊 Visión general", key="overview_btn", 
                    help="Ver estadísticas generales de scrobblings"):
            st.session_state.current_page = "Visión general"
    
    with col_artists:
        if st.button("🎵 Top Artistas", key="artists_btn", 
                    help="Ver los artistas más escuchados"):
            st.session_state.current_page = "Top Artistas"
    
    st.markdown('</div>', unsafe_allow_html=True)

# Page content
if st.session_state.current_page == "Visión general":
    overview.show()
elif st.session_state.current_page == "Top Artistas":
    top_artists.show()

