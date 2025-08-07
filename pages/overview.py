import streamlit as st
from core.data_loader import load_data
import altair as alt
import plotly.express as px

def show():
    st.title("Visión general del uso de Last.fm")
    st.subheader("Un recorrido a las reproducciones de música realizadas en Last.fm desde octubre de 2014 hasta la actualidad")
    
    scrobblings_by_month = load_data("scrobblings_by_month")
    artists_by_month = load_data("artists_by_month")
    albums_by_month = load_data("albums_by_month")

    # Chart selection buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Selecciona la visualización:")
        chart_type = st.radio(
            "Tipo de gráfica:",
            ["📊 Scrobblings por mes", "🎵 Artistas por mes", "💿 Álbumes por mes"],
            horizontal=True,
            key="chart_selector"
        )

    # Show metrics immediately after chart selection
    if chart_type == "📊 Scrobblings por mes":
        # Metrics right after selection
        st.markdown("### 📊 Métricas de Scrobblings")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Scrobblings", f"{scrobblings_by_month['Scrobblings'].sum():,}")
        with col2:
            st.metric("Promedio mensual", f"{scrobblings_by_month['Scrobblings'].mean():.0f}")
        with col3:
            st.metric("Mes con más scrobblings", scrobblings_by_month.loc[scrobblings_by_month['Scrobblings'].idxmax(), 'Year_Month'])
        
        # Chart after metrics
        fig = px.bar(
            scrobblings_by_month, 
            x="Year_Month", 
            y="Scrobblings", 
            title="Scrobblings por mes",
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(
            xaxis_title="Mes",
            yaxis_title="Número de Scrobblings",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "🎵 Artistas por mes":
        # Metrics right after selection
        st.markdown("### 🎵 Métricas de Artistas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Artistas únicos", f"{artists_by_month['Artists'].sum():,}")
        with col2:
            st.metric("Promedio mensual", f"{artists_by_month['Artists'].mean():.0f}")
        with col3:
            st.metric("Mes con más artistas", artists_by_month.loc[artists_by_month['Artists'].idxmax(), 'Year_Month'])
        
        # Chart after metrics
        fig2 = px.bar(
            artists_by_month, 
            x="Year_Month", 
            y="Artists", 
            title="Artistas únicos por mes",
            color_discrete_sequence=['#ff7f0e']
        )
        fig2.update_layout(
            xaxis_title="Mes",
            yaxis_title="Número de Artistas Únicos",
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    else:  # Álbumes por mes
        # Metrics right after selection
        st.markdown("### 💿 Métricas de Álbumes")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Álbumes únicos", f"{albums_by_month['Albums'].sum():,}")
        with col2:
            st.metric("Promedio mensual", f"{albums_by_month['Albums'].mean():.0f}")
        with col3:
            st.metric("Mes con más álbumes", albums_by_month.loc[albums_by_month['Albums'].idxmax(), 'Year_Month'])
        
        # Chart after metrics
        fig3 = px.bar(
            albums_by_month, 
            x="Year_Month", 
            y="Albums", 
            title="Álbumes únicos por mes",
            color_discrete_sequence=['#2ca02c']
        )
        fig3.update_layout(
            xaxis_title="Mes",
            yaxis_title="Número de Álbumes Únicos",
            showlegend=False
        )
        st.plotly_chart(fig3, use_container_width=True)
