import streamlit as st

st.set_page_config(page_title="Info - Last.fm Dashboard", layout="wide")

st.title("ℹ️ Information")
st.subheader("Learn about this Last.fm dashboard and how to use it")

# Leer y mostrar la documentación
with open("help.md", "r", encoding="utf-8") as f:
    help_content = f.read()

st.markdown(help_content)

# Agregar información adicional sobre el dashboard
st.markdown("---")
st.markdown("### 🛠️ Technical Information")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Data Source:**")
    st.markdown("- Last.fm API")
    st.markdown("- Real-time data extraction")
    st.markdown("- Complete user scrobblings history")
    
    st.markdown("**Features:**")
    st.markdown("- Cached data for fast navigation")
    st.markdown("- Multiple time period views")
    st.markdown("- Interactive visualizations")
    st.markdown("- Progress tracking during data loading")

with col2:
    st.markdown("**Technologies:**")
    st.markdown("- Streamlit (Web framework)")
    st.markdown("- Plotly (Interactive charts)")
    st.markdown("- Pandas (Data processing)")
    st.markdown("- Python (Backend logic)")
    
    st.markdown("**Data Processing:**")
    st.markdown("- Automatic time zone conversion")
    st.markdown("- Monthly/Quarterly/Yearly aggregation")
    st.markdown("- Real-time metrics calculation")
    st.markdown("- Error handling and validation")

# Botón para volver a la página principal
st.markdown("---")
if st.button("🏠 Back to Main Page"):
    st.switch_page("Inicio.py")
