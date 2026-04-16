import streamlit as st
from PIL import Image
import os
from utils import mostrar_logo_inegi

# 1. Configuración de la página
st.set_page_config(
    page_title="Tablero Estadístico - Morelos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

mostrar_logo_inegi()

# 2. Estilos CSS (Mantenemos tu configuración unificada)
st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, p, li {
        font-family: 'Source Sans Pro', sans-serif !important;
    }

    .portal-title {
        color: #1B396A;
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
        padding-top: 10px;
    }

    .bienvenida-text {
        color: #444;
        font-size: 18px;
        text-align: center;
        margin-bottom: 40px;
    }

    div.stButton > button {
        width: 100%;
        height: 55px;
        border-radius: 8px;
        border: none;
        background-color: #1B396A;
        color: white;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s ease;
        margin-top: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    div.stButton > button:hover {
        background-color: #244a85;
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        color: #F8F9F9;
    }

    .encuesta-header {
        font-size: 26px;
        font-weight: bold;
        padding: 12px 20px;
        border-radius: 10px 10px 0px 0px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .header-envipe { background-color: #e3f2fd; color: #1565c0; border-left: 6px solid #1565c0; }
    .header-encig { background-color: #e8f5e9; color: #2e7d32; border-left: 6px solid #2e7d32; }
    .header-ensu { background-color: #fffde7; color: #fbc02d; border-left: 6px solid #fbc02d; }
    
    .section-label {
        font-weight: bold;
        margin-top: 15px;
        color: #1B396A;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Encabezado y Título del Portal
st.markdown("<div class='portal-title'>Sistema de Consulta de Morelos</div>", unsafe_allow_html=True)
st.markdown("<div class='bienvenida-text'>Este portal transforma los microdatos de INEGI en indicadores estratégicos. <b>¿Qué información necesita para su gestión hoy?</b></div>", unsafe_allow_html=True)

st.write("---")

# 4. Grid Informativo
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("<div class='encuesta-header header-envipe'>🛡️ ENVIPE</div>", unsafe_allow_html=True)
    st.markdown("<p class='section-label'>Enfoque:</p> Seguridad Pública y Justicia.", unsafe_allow_html=True)
    st.write("* Identificar delitos con mayor incidencia real.\n* Evaluar confianza ciudadana.\n* Detectar lugares críticos.")
    if st.button("Analizar Seguridad (ENVIPE)"):
        st.switch_page("pages/01_ENVIPE.py")

with col2:
    st.markdown("<div class='encuesta-header header-encig'>🏛️ ENCIG</div>", unsafe_allow_html=True)
    st.markdown("<p class='section-label'>Enfoque:</p> Gestión Pública y Corrupción.", unsafe_allow_html=True)
    st.write("* Medir satisfacción con servicios básicos.\n* Riesgos de corrupción en trámites.\n* Impacto de mejora regulatoria.")
    if st.button("Analizar Gestión (ENCIG)"):
        st.switch_page("pages/app_encig.py")

with col3:
    st.markdown("<div class='encuesta-header header-ensu'>🏙️ ENSU</div>", unsafe_allow_html=True)
    st.markdown("<p class='section-label'>Enfoque:</p> Percepción de Seguridad Urbana.", unsafe_allow_html=True)
    st.write("* Sentimiento de inseguridad en espacios públicos.\n* Efectividad de operativos policiales.\n* Conducta social ante violencia.")
    if st.button("Analizar Percepción (ENSU)"):
        st.switch_page("pages/03_ENSU.py")

st.write("---")

# 5. Sidebar con el Logo de la Carpeta Assets
with st.sidebar:        
    
    st.info("Utilice los botones al pie de cada sección para profundizar en el análisis de microdatos.")