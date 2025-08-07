import streamlit as st

st.set_page_config(page_title="Last.fm Scrobblings Dashboard", layout="wide")

# Custom CSS to remove white banner and create elegant navigation
st.markdown("""
<style>
/* Remove white banner noise */
.main .block-container {
    padding-top: 1rem;
}

/* Remove default Streamlit padding */
.main .block-container {
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 1200px;
}

/* Make info boxes clickable */
.clickable-info {
    cursor: pointer;
    transition: all 0.3s ease;
}

.clickable-info:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# Main content - Welcome page
st.title("🎵 Last.fm Scrobblings Dashboard")

# Read and display help.md content in main area
with open("help.md", "r", encoding="utf-8") as f:
    help_content = f.read()
st.markdown(help_content)

# Quick stats as clickable info boxes
st.markdown("### 🚀 Navegación rápida")
col1, col2, col3 = st.columns(3)

with col1:
    # Create clickable container for Visión General
    with st.container():
        st.info("📊 **Visión General**\n\nAnaliza tendencias y patrones de escucha")
        if st.button("Ir a Visión General", key="nav_vision", help="Ir a la página de Visión General"):
            st.switch_page("pages/1_📊_Visión_General.py")

with col2:
    # Create clickable container for Top Artistas
    with st.container():
        st.info("🎵 **Top Artistas**\n\nDescubre los artistas favoritos")
        if st.button("Ir a Top Artistas", key="nav_artists", help="Ir a la página de Top Artistas"):
            st.switch_page("pages/2_🎵_Top_Artistas.py")

#with col3:
#    # Help info box (not clickable since help is already on this page)
#    st.info("❓ **Ayuda**\n\nConsulta la guía completa en esta página")
