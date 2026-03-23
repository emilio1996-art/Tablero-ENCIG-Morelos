import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Sistema de Información Morelos",
    page_icon="📊",
    layout="wide"
)

st.title("🏛️ Portal de Datos Estadísticos - Estado de Morelos")
st.markdown("---")

st.markdown("""
### Bienvenido al Centro de Inteligencia Estadística
Este portal transforma los microdatos de INEGI en indicadores estratégicos. 
**¿Qué información necesita para su gestión hoy?**
""")

# Crear las columnas para las tarjetas
col1, col2 = st.columns(2)

with col1:
    st.info("### 🛡️ ENVIPE")
    st.markdown("""
    **Enfoque:** Seguridad Pública y Justicia.
    
    **Utilidad para el funcionario:**
    * Identificar los delitos con mayor incidencia real (incluyendo la **Cifra Negra**).
    * Evaluar la confianza ciudadana en las corporaciones policiales de Morelos.
    * Detectar horarios y lugares críticos para optimizar la estrategia de prevención.
    """)
    if st.button("Analizar Seguridad (ENVIPE)"):
        # Asegúrate de que el nombre del archivo en 'pages' sea exacto
        st.switch_page("pages/01_ENVIPE.py")

with col2:
    st.success("### 🏛️ ENCIG")
    st.markdown("""
    **Enfoque:** Gestión Pública y Corrupción.
    
    **Utilidad para el funcionario:**
    * Medir la satisfacción ciudadana con servicios básicos (agua, luz, vialidades).
    * Identificar trámites con mayor riesgo de corrupción o burocracia.
    * Evaluar el impacto de las políticas de mejora regulatoria en el estado.
    """)
    if st.button("Analizar Gestión (ENCIG)"):
        # Asegúrate de que el nombre del archivo en 'pages' sea app_encig.py o 01_ENCIG.py
        st.switch_page("pages/app_encig.py")

st.markdown("---")
st.caption("Gobierno del Estado de Morelos | Unidad de Análisis y Estadística")