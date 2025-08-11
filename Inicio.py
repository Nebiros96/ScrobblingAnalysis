import streamlit as st
from core.data_loader import load_user_data, clear_cache, unique_metrics
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
    color: #D51007 !important; /* Cambia este color si quieres otro */
}
</style>
""", unsafe_allow_html=True)


# --- Título---
st.title("🎵 Last.fm Scrobblings Dashboard")
st.markdown("#### Explore Your Last.fm Activity")

# --- 🧪 Formulario de búsqueda de usuario ---
with st.form("user_search_form"):
    input_user = st.text_input("Enter your Last.fm user:", placeholder="ej. Brenoritvrezork")

    checkpoint_file = None
    resume_option = True

    # Si el usuario ya escribió algo, verificamos si hay checkpoint
    if input_user:
        checkpoint_file = os.path.join("temp_checkpoints", f"{input_user}_checkpoint.parquet")
        if os.path.exists(checkpoint_file):
            st.info(f"🔄 Progress found for **{input_user}**.")
            choice = st.radio(
                "What do you want to do?",
                ["Continue from last progress", "Restart from scratch"],
                index=0
            )
            resume_option = (choice == "Continue from last progress")

    # 👇 Siempre al final del form
    submitted = st.form_submit_button("Load Lastfm data")

if submitted and input_user:
    # Si elige reiniciar, borramos el checkpoint
    if not resume_option and checkpoint_file and os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

    st.session_state.clear()
    clear_cache(input_user)
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

        # Pasamos resume_option a load_user_data
        df = load_user_data(input_user, progress_callback, resume=resume_option)

        if df is not None and not df.empty:
            st.session_state["df_user"] = df
            st.session_state["data_loaded_successfully"] = True
            status_container.update(
                label=f"✅ Data extracted successfully! **{len(df):,}** scrobbings were found for the user **{input_user}**",
                state="complete",
                expanded=False
            )
            time.sleep(2)
            message_placeholder.empty()
        else:
            st.session_state["data_loaded_successfully"] = False
            status_container.update(label="❌ Data loading failed", state="error", expanded=True)
            st.error("❌ Data could not be loaded. Please check the username or try again.")


# --- Lógica de renderizado de las pestañas ---
if "current_user" in st.session_state and st.session_state.get("data_loaded_successfully"):
    st.success(f"Data extracted successfully! **{len(st.session_state['df_user']):,}** scrobbings were found for the user **{st.session_state['current_user']}**")

    # Pre-cálculo de datos que se usarán en varias pestañas
    user = st.session_state["current_user"]
    df_user = st.session_state["df_user"]
    metrics = unique_metrics(user=user, df=df_user)
    
    # Define las pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Statistics", "📊 Overview", "🎵 Top Artists", "ℹ️ Info"])

    # Llama a la función de cada pestaña
    with tab1:
        tab_statistics(user, df_user, metrics)
    with tab2:
        tab_overview(user, df_user, metrics)
    with tab3:
        tab_top_artists(user, df_user, metrics)
    with tab4:
        tab_info()
