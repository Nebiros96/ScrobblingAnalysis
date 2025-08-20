import streamlit as st
from core.data_loader import load_user_data, clear_cache, calculate_all_metrics, get_df_hash, load_user_data_incremental
from core.ui_tabs import tab_statistics, tab_overview, tab_top_artists, tab_info
import time 
import os
import pandas as pd
import logging
import traceback
from typing import Optional, Dict, Any, Tuple
from functools import wraps
from contextlib import contextmanager

# =====================================================
# SISTEMA DE LOGGING Y CONFIGURACIÓN
# =====================================================

def setup_logging():
    """Configura el sistema de logging basado en el entorno"""
    # Auto-detectar entorno
    is_development = (
        os.getenv('STREAMLIT_ENV', 'development').lower() == 'development' or
        os.getenv('ENVIRONMENT', '').lower() != 'production'
    )
    
    log_level = logging.DEBUG if is_development else logging.WARNING
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger('lastfm_app')
    logger.setLevel(log_level)
    
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger

# Inicializar logger global
logger = setup_logging()

def handle_errors(user_message: str = "An unexpected error has occurred", 
                 show_success: bool = False,
                 success_message: str = "Operation completed successfully"):
    """Decorador para manejo de errores elegante"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                logger.debug(f"✅ {func.__name__} successfully executed")
                
                if show_success:
                    st.success(success_message)
                    
                return result
                
            except Exception as e:
                logger.error(f"❌ Error in {func.__name__}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                st.error(user_message)
                
                # Solo mostrar detalles técnicos en desarrollo
                is_dev = os.getenv('STREAMLIT_ENV', 'development').lower() == 'development'
                if is_dev:
                    with st.expander("🔧 Detalles técnicos (desarrollo)"):
                        st.code(f"Error: {str(e)}")
                        st.code(f"Función: {func.__name__}")
                
                return None
                
        return wrapper
    return decorator

def validate_dataframe(df: Any, name: str = "DataFrame") -> bool:
    """Valida un DataFrame y registra el resultado"""
    try:
        if df is None:
            logger.error(f"🔍 {name} is None")
            return False
            
        if hasattr(df, 'empty') and df.empty:
            logger.error(f"🔍 {name} is empty")
            return False
            
        if hasattr(df, 'shape'):
            logger.info(f"🔍 {name} validated: {df.shape[0]:,} rows, {df.shape[1]} columns")
            return True
        
        logger.warning(f"🔍 {name} does not appear to be a valid DataFrame")
        return False
        
    except Exception as e:
        logger.error(f"🔍 Error validating {name}: {str(e)}")
        return False

def validate_required_columns(df: Any, required_columns: list, name: str = "DataFrame") -> bool:
    """Valida que el DataFrame tenga las columnas requeridas"""
    try:
        if not hasattr(df, 'columns'):
            logger.error(f"🔍 {name} has no 'columns' attribute")
            return False
            
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"🔍 {name} - Missing columns: {missing_columns}")
            return False
        else:
            logger.info(f"🔍 {name} - All required columns present")
            return True
            
    except Exception as e:
        logger.error(f"🔍 Error validating columns of {name}: {str(e)}")
        return False

@contextmanager
def performance_timer(operation_name: str):
    """Context manager para medir tiempo de ejecución"""
    start_time = time.time()
    try:
        yield
    finally:
        execution_time = time.time() - start_time
        logger.info(f"⏱️ {operation_name} completed in {execution_time:.2f} seconds")

# =====================================================
# FUNCIONES DE VALIDACIÓN REFACTORIZADAS
# =====================================================

@handle_errors(
    user_message="Error validating user data",
    show_success=False
)
def validate_user_session_data() -> Optional[Tuple[str, pd.DataFrame]]:
    """Valida y retorna los datos del usuario desde session_state"""
    
    # Validar session state básico
    if "current_user" not in st.session_state:
        logger.warning("🔍 User not found in session_state")
        return None
        
    if not st.session_state.get("data_loaded_successfully"):
        logger.warning("🔍 Data not loaded successfully")
        return None
        
    if st.session_state.get("loading_data", False):
        logger.info("🔍 Data in process of loading")
        return None
    
    user = st.session_state["current_user"]
    df_user = st.session_state["df_user"]
    
    # Validar DataFrame
    if not validate_dataframe(df_user, "df_user"):
        logger.error("🔍 df_user failed basic validation")
        return None
    
    # Validar columnas requeridas
    required_columns = ['datetime_utc', 'artist', 'album', 'track', 'user']
    if not validate_required_columns(df_user, required_columns, "df_user"):
        logger.error("🔍 df_user has no required columns")
        return None
    
    logger.info(f"✅ User data validated: {user} - {len(df_user):,} scrobbles")
    return user, df_user

@handle_errors(
    user_message="Error processing metrics",
    show_success=False
)
def get_or_calculate_metrics_safe(user: str, df_user: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """Obtiene métricas del cache o las calcula de forma segura"""
    
    # Intentar usar cache primero
    if "all_metrics_cache" in st.session_state:
        logger.info("🔄 Using metrics from cache")
        return st.session_state["all_metrics_cache"]
    
    # Calcular métricas con spinner
    logger.info("📊 Calculating metrics...")
    
    with st.spinner("Calculating metrics..."):
        with performance_timer("Cálculo de métricas"):
            all_metrics = calculate_all_metrics(user=user, df=df_user)
    
    # Validar resultado
    if all_metrics is None:
        logger.error("📊 calculate_all_metrics returned None")
        return None
        
    if isinstance(all_metrics, dict) and len(all_metrics) == 0:
        logger.error("📊 calculate_all_metrics returned and empty dictionary")
        return None
    
    # Guardar en cache
    st.session_state["all_metrics_cache"] = all_metrics
    logger.info(f"📊 Metrics calculated successfully: {len(all_metrics)} keys")
    
    return all_metrics

@handle_errors(
    user_message="Error processing CSV file",
    show_success=False
)
def process_uploaded_csv(uploaded_file) -> Optional[Dict[str, Any]]:
    """Procesa el archivo CSV subido de forma segura"""
    
    logger.info("📁 Processing uploaded CSV file")
    
    # Leer CSV
    df_uploaded = pd.read_csv(uploaded_file, sep=None, encoding='utf-8-sig', engine='python')
    
    # Validar columnas requeridas
    required_columns = ['user', 'datetime_utc', 'artist', 'album', 'track', 'url']
    missing_columns = [col for col in required_columns if col not in df_uploaded.columns]
    
    if missing_columns:
        logger.error(f"📁Missing columns in CSV file: {missing_columns}")
        st.error(f"Missing required columns: {missing_columns}")
        return None
    
    # Convertir datetime
    df_uploaded['datetime_utc'] = pd.to_datetime(df_uploaded['datetime_utc'])
    
    # Obtener información
    uploaded_user = df_uploaded['user'].iloc[0]
    last_timestamp = df_uploaded['datetime_utc'].max()
    total_scrobbles = len(df_uploaded)
    
    logger.info(f"📁 Processed CSV: {uploaded_user} - {total_scrobbles:,} scrobbles")
    
    return {
        'dataframe': df_uploaded,
        'user': uploaded_user,
        'last_timestamp': last_timestamp,
        'total_scrobbles': total_scrobbles
    }

# =====================================================
# FUNCIONES DE INTERFAZ LIMPIAS
# =====================================================

def render_dashboard_content():
    """Renderiza el contenido principal del dashboard de forma limpia"""
    
    # Validar datos del usuario
    validation_result = validate_user_session_data()
    if validation_result is None:
        # Los errores ya fueron manejados y mostrados al usuario
        return
    
    user, df_user = validation_result
    
    # Obtener o calcular métricas
    all_metrics = get_or_calculate_metrics_safe(user, df_user)
    if all_metrics is None:
        # Los errores ya fueron manejados y mostrados al usuario
        return
    
    # Si llegamos aquí, todo está OK
    logger.info("🚀 Dashboard loaded successfully")
    
    # Success message and download button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.success(f"Data extracted successfully! **{len(df_user):,}** scrobblings were found for the user **{user}**")
    
    with col2:
        csv_data = df_user.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"{user}.csv",
            mime="text/csv",
            help="Download your complete scrobbling data as CSV file (utf-8-sig encoding)",
            use_container_width=True
        )
    
    # Render tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Statistics", "📊 Overview", "🎵 Top Artists", "ℹ️ Info & FAQ"])
    
    with tab1:
        tab_statistics(user, df_user, all_metrics)
    with tab2:
        tab_overview(user, df_user, all_metrics)
    with tab3:
        tab_top_artists(user, df_user, all_metrics)
    with tab4:
        tab_info()

# =====================================================
# APLICACIÓN PRINCIPAL
# =====================================================

st.set_page_config(page_title="Last.fm Scrobblings Dashboard", layout="wide")

# Custom CSS 
st.markdown("""
<style>
.main .block-container {
    padding-top: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 100%;
    width: 100%;
}

button[data-baseweb="tab"] {
    font-size: 18 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    font-weight: bold !important;
    color: #D51007 !important; 
}
</style>
""", unsafe_allow_html=True)

# Título
st.title("Last.fm Scrobblings Dashboard")
st.markdown("### Explore Your Last.fm Activity")

# CSV Upload Section
with st.expander("📁 Upload existing CSV data", expanded=False):
    st.markdown("Upload your previous Last.fm data to continue from where you left off:")
    
    uploaded_file = st.file_uploader(
        "Choose your Last.fm CSV file",
        type=['csv'],
        help="Upload a CSV file with your previous Last.fm data. The app will continue extracting from the last recorded timestamp."
    )
    
    if uploaded_file is not None:
        upload_result = process_uploaded_csv(uploaded_file)
        
        if upload_result:
            st.success("✅ CSV loaded successfully!")
            
            # Store in session state
            st.session_state["uploaded_data"] = upload_result['dataframe']
            st.session_state["uploaded_user"] = upload_result['user']
            st.session_state["last_timestamp"] = upload_result['last_timestamp']

# Formulario de búsqueda de usuario (sin cambios en la lógica, solo limpieza de logs)
with st.form("user_search_form"):
    if "uploaded_data" in st.session_state:
        uploaded_user = st.session_state["uploaded_user"]
        input_user = st.text_input(
            "Enter your Last.fm user:", 
            value=uploaded_user,
            placeholder="ej. my_username",
            help=f"Pre-filled from uploaded CSV. Last scrobble: {st.session_state['last_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        input_user = st.text_input("Enter your Last.fm user:", placeholder="ej. my_username")

    checkpoint_file = None
    resume_option = True

    resume_placeholder = st.empty()

    if input_user:
        checkpoint_file = os.path.join("temp_checkpoints", f"{input_user}_checkpoint.parquet")

        if "uploaded_data" in st.session_state and input_user == st.session_state["uploaded_user"]:
            if not st.session_state.get("loading_data", False):
                resume_placeholder.info(f"📄 Ready to continue from uploaded data. Will fetch new scrobbles since {st.session_state['last_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        elif os.path.exists(checkpoint_file) and not st.session_state.get("loading_data", False):
            resume_placeholder.info(f"📄 Resuming from saved progress for **{input_user}**.")

    submitted = st.form_submit_button("Load Lastfm data")

# Procesamiento del formulario (lógica original con logging mejorado)
if submitted and input_user:
    logger.info(f"🚀 Starting data upload for user: {input_user}")
    
    st.session_state["loading_data"] = True
    resume_placeholder.empty()

    if not resume_option and checkpoint_file and os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

    # Clear previous data
    for key in ["df_user", "data_loaded_successfully", "all_metrics_cache"]:
        st.session_state.pop(key, None)
        
    st.cache_data.clear()
    st.session_state["current_user"] = input_user

    message_placeholder = st.empty()

    use_incremental = (
        "uploaded_data" in st.session_state and 
        input_user == st.session_state["uploaded_user"]
    )

    with message_placeholder.status(f"📄 Loading data for user **{input_user}**... (It may take several minutes)", expanded=True) as status_container:
        progress_bar = st.progress(0)
        progress_text = st.empty()

        def progress_callback(page, total_pages, total_tracks, progress_info=None):
            progress_percent = page / total_pages if total_pages > 0 else 0
            progress_bar.progress(progress_percent)
            if use_incremental:
                existing_count = len(st.session_state["uploaded_data"])
                progress_text.markdown(
                    f"📊 Page {page}/{total_pages} ({progress_percent:.2%}) - {total_tracks:,} new scrobbles + {existing_count:,} existing."
                )
            else:
                progress_text.markdown(
                    f"📊 Page {page}/{total_pages} ({progress_percent:.2%}) - {total_tracks:,} scrobbles."
                )

        try:
            with performance_timer(f"Loading data for {input_user}"):
                if use_incremental:
                    logger.info("📄 Using incremental loading")
                    df = load_user_data_incremental(
                        input_user, 
                        progress_callback, 
                        st.session_state["uploaded_data"],
                        st.session_state["last_timestamp"],
                        resume=resume_option
                    )
                else:
                    logger.info("📄 Using complete load")
                    df = load_user_data(input_user, progress_callback, resume=resume_option)

            if isinstance(df, dict) and df.get("incomplete"):
                logger.warning("⚠️ Incomplete download")
                if use_incremental:
                    resume_placeholder.info(f"📄 Ready to continue from uploaded data.")
                else:
                    resume_placeholder.info(f"📄 Resuming from saved progress for **{input_user}**.")
                st.warning("⚠️ Connection lost. Download can be resumed later.")
                st.session_state["loading_data"] = False
            elif df is not None and not df.empty:
                logger.info(f"✅ Data loaded successfully: {len(df):,} scrobbles")
                
                st.session_state["df_user"] = df
                st.session_state["data_loaded_successfully"] = True
                
                # Pre-calculate metrics
                with st.spinner("📄 Calculating metrics..."):
                    with performance_timer("Pre-cálculo de métricas"):
                        all_metrics = calculate_all_metrics(user=input_user, df=df)
                        st.session_state["all_metrics_cache"] = all_metrics
                
                # Clear uploaded data after successful merge
                for key in ["uploaded_data", "uploaded_user", "last_timestamp"]:
                    st.session_state.pop(key, None)
                
                status_container.update(
                    label=f"✅ Data extracted successfully! **{len(df):,}** scrobbles found for **{input_user}**",
                    state="complete",
                    expanded=False
                )
                time.sleep(2)
                message_placeholder.empty()
                st.session_state["loading_data"] = False
                st.rerun()
            else:
                logger.error("❌ Data could not be loaded")
                st.session_state["data_loaded_successfully"] = False
                status_container.update(label="❌ Data loading failed", state="error", expanded=True)
                st.error("❌ Data could not be loaded. Please check the username or try again.")
                st.session_state["loading_data"] = False

        except Exception as e:
            logger.error(f"❌ Unexpected error during loading: {str(e)}")
            st.error(f"Unexpected error: {e}")
            st.session_state["loading_data"] = False

# Renderizado principal - AQUÍ ES DONDE SE APLICA LA OPTIMIZACIÓN
render_dashboard_content()

# Footer (sin cambios)
st.markdown("""
<style>
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
    <span>v0.9.7 © 2025 Julián Gómez. Please support this project on Ko-fi :)</span>
    <a href='https://ko-fi.com/M4M64OI1J' target='_blank'>
        <img height='36' style='border:0px;height:36px;' 
             src='https://storage.ko-fi.com/cdn/kofi6.png?v=6' 
             border='0' alt='Buy Me a Coffee at ko-fi.com' />
    </a>
</div>
""", unsafe_allow_html=True)