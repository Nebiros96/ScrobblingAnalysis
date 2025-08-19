import streamlit as st
from core.data_loader import load_user_data, clear_cache, calculate_all_metrics, get_df_hash
from core.ui_tabs import tab_statistics, tab_overview, tab_top_artists, tab_info
import time 
import os


st.set_page_config(page_title="Last.fm Scrobblings Dashboard", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
.main .block-container {
    padding-top: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 100%;
    width: 100%;
}

/* Cambiar tamaño de texto en las tabs */
button[data-baseweb="tab"] {
    font-size: 18 !important;
}

/* Negrita y color en la tab activa */
button[data-baseweb="tab"][aria-selected="true"] {
    font-weight: bold !important;
    color: #D51007 !important; 
}
</style>
""", unsafe_allow_html=True)

# --- Título---
st.title("Last.fm Scrobblings Dashboard")
st.markdown("### Explore Your Last.fm Activity")

# --- 🧪 Formulario de búsqueda de usuario ---
with st.form("user_search_form"):
    input_user = st.text_input("Enter your Last.fm user:", placeholder="ej. my_username")

    checkpoint_file = None
    resume_option = True  # Siempre reanudar si hay checkpoint

    resume_placeholder = st.empty()  # 👈 Placeholder para el mensaje de reanudación

    if input_user:
        checkpoint_file = os.path.join("temp_checkpoints", f"{input_user}_checkpoint.parquet")

        # Mostrar solo si hay checkpoint y NO estamos cargando
        if os.path.exists(checkpoint_file) and not st.session_state.get("loading_data", False):
            resume_placeholder.info(f"📄 Resuming from saved progress for **{input_user}**.")
            resume_option = True

    submitted = st.form_submit_button("Load Lastfm data")

if submitted and input_user:
    st.session_state["loading_data"] = True  # Ocultar mensaje durante la descarga
    resume_placeholder.empty()  # 👈 Oculta el mensaje apenas inicia la carga

    if not resume_option and checkpoint_file and os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

    # Limpiar datos previos
    for key in ["df_user", "data_loaded_successfully", "all_metrics_cache"]:
        st.session_state.pop(key, None)
        
    # Limpiar caché de Streamlit para el nuevo usuario
    st.cache_data.clear()

    st.session_state["current_user"] = input_user

    message_placeholder = st.empty()

    with message_placeholder.status(f"🔄 Loading data for user **{input_user}**... (It may take several minutes)", expanded=True) as status_container:
        progress_bar = st.progress(0)
        progress_text = st.empty()

        def progress_callback(page, total_pages, total_tracks, progress_info=None):
            progress_percent = page / total_pages if total_pages > 0 else 0
            progress_bar.progress(progress_percent)
            progress_text.markdown(
                f"📊 Page {page}/{total_pages} ({progress_percent:.2%}) - {total_tracks:,} scrobbles."
            )

        try:
            df = load_user_data(input_user, progress_callback, resume=resume_option)

            if isinstance(df, dict) and df.get("incomplete"):
                # Fallo → volver a mostrar mensaje de reanudación
                resume_placeholder.info(f"📄 Resuming from saved progress for **{input_user}**.")
                st.warning("⚠️ Connection lost. Download can be resumed later.")
                st.session_state["loading_data"] = False
            elif df is not None and not df.empty:
                st.session_state["df_user"] = df
                st.session_state["data_loaded_successfully"] = True
                
                # Pre-calcular métricas una sola vez y guardarlas en caché
                with st.spinner("🔄 Calculating metrics..."):
                    all_metrics = calculate_all_metrics(user=input_user, df=df)
                    st.session_state["all_metrics_cache"] = all_metrics
                
                status_container.update(
                    label=f"✅ Data extracted successfully! **{len(df):,}** scrobbles found for **{input_user}**",
                    state="complete",
                    expanded=False
                )
                time.sleep(2)
                message_placeholder.empty()
                st.session_state["loading_data"] = False
                st.rerun()  # Refrescar para mostrar las pestañas
            else:
                st.session_state["data_loaded_successfully"] = False
                status_container.update(label="❌ Data loading failed", state="error", expanded=True)
                st.error("❌ Data could not be loaded. Please check the username or try again.")
                st.session_state["loading_data"] = False

        except Exception as e:
            st.error(f"Unexpected error: {e}")
            st.session_state["loading_data"] = False


# --- Lógica de renderizado de las pestañas ---
if ("current_user" in st.session_state and 
    st.session_state.get("data_loaded_successfully") and 
    not st.session_state.get("loading_data", False)):
    
    user = st.session_state["current_user"]
    df_user = st.session_state["df_user"]
    
    # Usar métricas pre-calculadas si están disponibles
    if "all_metrics_cache" in st.session_state:
        all_metrics = st.session_state["all_metrics_cache"]
    else:
        # Fallback: calcular métricas si no están en caché
        all_metrics = calculate_all_metrics(user=user, df=df_user)
        st.session_state["all_metrics_cache"] = all_metrics
    
    st.success(f"Data extracted successfully! **{len(df_user):,}** scrobblings were found for the user **{user}**")
    
    # Define las pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Statistics", "📊 Overview", "🎵 Top Artists", "ℹ️ Info & FAQ"])

    # Renderizar pestañas usando las funciones optimizadas
    with tab1:
        tab_statistics(user, df_user, all_metrics)
    with tab2:
        tab_overview(user, df_user, all_metrics)
    with tab3:
        tab_top_artists(user, df_user, all_metrics)
    with tab4:
        tab_info()

# --- Botón para limpiar caché (opcional, solo para desarrollo) ---
#if st.session_state.get("data_loaded_successfully"):
#    if st.sidebar.button("🗑️ Clear Cache"):
#        user = st.session_state.get("current_user")
#        clear_cache(user)
#        st.cache_data.clear()
#        st.sidebar.success("Cache cleared!")
#        st.rerun()

# --- Footer al final ---
st.markdown("""
<style>
/* --- Footer personalizado (no fijo) --- */
footer {visibility: hidden;}
.custom-footer {
    width: 100%;
    background-color: #1e1e1e;
    color: #ffffff;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 12px;
    padding: 20px;
    font-size: 0.9em;
    border-top: 1px solid #171212;
    margin-top: 2rem;
}
.custom-footer img {
    vertical-align: middle;
}
</style>

<div class="custom-footer">
    <span>v0.9.2 © 2025 Julián Gómez. Please support this project on Ko-fi :)</span>
    <a href='https://ko-fi.com/M4M64OI1J' target='_blank'>
        <img height='36' style='border:0px;height:36px;' 
             src='https://storage.ko-fi.com/cdn/kofi6.png?v=6' 
             border='0' alt='Buy Me a Coffee at ko-fi.com' />
    </a>
</div>
""", unsafe_allow_html=True)