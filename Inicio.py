import streamlit as st
from core.data_loader import load_user_data, clear_cache, calculate_all_metrics
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
    input_user = st.text_input("Enter your Last.fm user:", placeholder="ej. Brenoritvrezork")

    checkpoint_file = None
    resume_option = True  # Siempre reanudar si hay checkpoint

    if input_user:
        checkpoint_file = os.path.join("temp_checkpoints", f"{input_user}_checkpoint.parquet")

        # Mostrar solo si hay checkpoint y NO estamos cargando
        if os.path.exists(checkpoint_file) and not st.session_state.get("loading_data", False):
            st.info(f"🔄 Resuming from saved progress for **{input_user}**.")
            resume_option = True

    submitted = st.form_submit_button("Load Lastfm data")

if submitted and input_user:
    st.session_state["loading_data"] = True  # Ocultar mensaje durante la descarga

    if not resume_option and checkpoint_file and os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

    # Limpiar datos previos
    for key in ["df_user", "data_loaded_successfully"]:
        st.session_state.pop(key, None)

    st.session_state["current_user"] = input_user

    message_placeholder = st.empty()

    with message_placeholder.status(f"📊 Loading data for user **{input_user}**...", expanded=True) as status_container:
        progress_bar = st.progress(0)
        progress_text = st.empty()

        def progress_callback(page, total_pages, total_tracks):
            progress_percent = page / total_pages if total_pages > 0 else 0
            progress_bar.progress(progress_percent)
            progress_text.markdown(
                f"📊 Page {page}/{total_pages} ({progress_percent:.2%}) - {total_tracks:,} scrobbles."
            )

        try:
            df = load_user_data(input_user, progress_callback, resume=resume_option)

            if isinstance(df, dict) and df.get("incomplete"):
                # Fallo → volver a mostrar mensaje
                st.warning("⚠️ Connection lost. Download can be resumed later.")
                st.session_state["loading_data"] = False
            elif df is not None and not df.empty:
                st.session_state["df_user"] = df
                st.session_state["data_loaded_successfully"] = True
                status_container.update(
                    label=f"✅ Data extracted successfully! **{len(df):,}** scrobbles found for **{input_user}**",
                    state="complete",
                    expanded=False
                )
                time.sleep(2)
                message_placeholder.empty()
                st.session_state["loading_data"] = False
            else:
                st.session_state["data_loaded_successfully"] = False
                status_container.update(label="❌ Data loading failed", state="error", expanded=True)
                st.error("❌ Data could not be loaded. Please check the username or try again.")
                st.session_state["loading_data"] = False

        except Exception as e:
            st.error(f"Unexpected error: {e}")
            st.session_state["loading_data"] = False


# --- Lógica de renderizado de las pestañas ---
if "current_user" in st.session_state and st.session_state.get("data_loaded_successfully"):
    st.success(f"Data extracted successfully! **{len(st.session_state['df_user']):,}** scrobbings were found for the user **{st.session_state['current_user']}**")

    # Pre-cálculo de datos que se usarán en varias pestañas
    user = st.session_state["current_user"]
    df_user = st.session_state["df_user"]
    all_metrics = calculate_all_metrics(user=user, df=df_user)
    
    # Define las pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Statistics", "📊 Overview", "🎵 Top Artists", "ℹ️ Info"])

    # Llama a la función de cada pestaña
    with tab1:
        tab_statistics(user, df_user, all_metrics)
    with tab2:
        tab_overview(user, df_user, all_metrics)
    with tab3:
        tab_top_artists(user, df_user, all_metrics)
    with tab4:
        tab_info()

# --- Footer al final ---
st.markdown("""
<style>
/* --- Footer personalizado (no fijo) --- */
footer {visibility: hidden;}
.custom-footer {
    width: 100%;
    background-color: #242121;
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
    <span>v0.12.1 © 2025 Julián Gómez. Please support this project on Ko-fi :)</span>
    <a href='https://ko-fi.com/M4M64OI1J' target='_blank'>
        <img height='36' style='border:0px;height:36px;' 
             src='https://storage.ko-fi.com/cdn/kofi6.png?v=6' 
             border='0' alt='Buy Me a Coffee at ko-fi.com' />
    </a>
</div>
""", unsafe_allow_html=True)
