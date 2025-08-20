# logging_config.py - Configuración separada para el sistema de logging
import os
from dataclasses import dataclass
from typing import Dict


@dataclass
class LoggingConfig:
    """Configuración centralizada del sistema de logging"""

    # Detección automática del entorno
    environment: str = os.getenv("STREAMLIT_ENV", "development")
    is_development: bool = None

    # Configuración de mensajes
    error_messages: Dict[str, str] = None

    # Configuración de UI
    show_technical_details: bool = None
    show_performance_metrics: bool = None
    show_debug_sidebar: bool = None

    def __post_init__(self):
        # Auto-detectar entorno si no está explícitamente configurado
        if self.environment == "development":
            # Verificar otras variables de entorno para auto-detección
            if (
                os.getenv("ENVIRONMENT") == "production"
                or os.getenv("HEROKU")
                or os.getenv("RAILWAY_ENVIRONMENT")
                or os.getenv("RENDER")
            ):
                self.environment = "production"

        self.is_development = self.environment == "development"

        # Configurar comportamiento basado en el entorno
        if self.show_technical_details is None:
            self.show_technical_details = self.is_development

        if self.show_performance_metrics is None:
            self.show_performance_metrics = self.is_development

        if self.show_debug_sidebar is None:
            self.show_debug_sidebar = self.is_development

        # Configurar mensajes de error si no están definidos
        if self.error_messages is None:
            self.error_messages = {
                "data_validation_error": "Los datos no están disponibles. Por favor, recarga la página.",
                "metrics_calculation_error": "Error al procesar las métricas. Los datos pueden estar incompletos.",
                "csv_processing_error": "Error al procesar el archivo CSV. Verifica el formato.",
                "data_loading_error": "Error al cargar los datos de Last.fm. Intenta nuevamente.",
                "generic_error": "Ha ocurrido un error inesperado.",
                "missing_columns": "El archivo no tiene el formato esperado.",
                "empty_dataframe": "No hay datos para mostrar.",
            }


# Instancia global
config = LoggingConfig()


# Función para configurar el entorno manualmente si es necesario
def set_environment(env: str):
    """
    Configura manualmente el entorno
    Args:
        env: 'development' o 'production'
    """
    global config
    os.environ["STREAMLIT_ENV"] = env
    config = LoggingConfig()


def get_environment_info() -> Dict[str, str]:
    """Obtiene información del entorno actual"""
    return {
        "environment": config.environment,
        "is_development": str(config.is_development),
        "show_technical_details": str(config.show_technical_details),
        "show_debug_sidebar": str(config.show_debug_sidebar),
        "streamlit_env": os.getenv("STREAMLIT_ENV", "not set"),
        "environment_var": os.getenv("ENVIRONMENT", "not set"),
    }
