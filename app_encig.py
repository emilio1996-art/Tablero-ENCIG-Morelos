# ======================================================
# TABLERO ENCIG 2023 – ESTADO DE MORELOS (CORREGIDO)
# Alineado a Metodología INEGI
# ======================================================

import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ------------------------------------------------------

st.set_page_config(
    page_title="ENCIG 2023 – Morelos",
    layout="wide"
)

st.markdown("""
<style>
.plot-container { 
    padding: 15px; border-radius: 10px; 
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border: 1px solid rgba(128,128,128,0.2);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------
# CARGA Y LIMPIEZA DE DATOS
# ------------------------------------------------------

@st.cache_data
def load_data():
    # Asegúrate de que el archivo Excel esté en la misma carpeta que este script
    df = pd.read_excel("Consolidado_Morelos_Bases_Final.xlsx")
    
    # Conversión crítica a numérico para evitar errores de cálculo
    df["FAC_P18"] = pd.to_numeric(df["FAC_P18"], errors="coerce").fillna(0)
    
    # Limpiamos columnas de servicios preventivamente
    cols_check = ["P4_1B","P4_2B","P4_3B","P4_4B","P4_5B","P4_6B","P4_7B","P4_8B", "P3_2"]
    for col in cols_check:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

df = load_data()

# ------------------------------------------------------
# FUNCIONES DE CÁLCULO (Lógica INEGI)
# ------------------------------------------------------

def fac_total(df):
    return df["FAC_P18"].sum()

def principal_problema(df):
    problemas = {
        "P3_1_05": "Inseguridad y delincuencia",
        "P3_1_03": "Corrupción",
        "P3_1_01": "Mal desempeño del gobierno",
        "P3_1_04": "Desempleo",
        "P3_1_02": "Pobreza",
        "P3_1_06": "Mala aplicación de la ley",
        "P3_1_07": "Desastres naturales",
        "P3_1_08": "Baja calidad de la educación pública",
        "P3_1_09": "Mala atención en centros de salud y hospitales públicos",
        "P3_1_10": "Falta de coordinación entre diferentes niveles de gobierno",
        "P3_1_11": "Falta de rendición de cuentas"
    }
    total_pob = fac_total(df)
    res = []
    for col, nombre in problemas.items():
        if col in df.columns:
            # INEGI cuenta si marcaron la opción (1)
            pob = df[df[col] == 1]["FAC_P18"].sum()
            res.append({
                "Problema": nombre,
                "Porcentaje": (pob / total_pob * 100) if total_pob > 0 else 0
            })
    tabla = pd.DataFrame(res).sort_values("Porcentaje", ascending=False)
    return (tabla.iloc[0] if not tabla.empty else {"Problema": "N/A", "Porcentaje": 0}), tabla

def corrupcion_frecuente(df):
    # P3_2: 1=Muy frecuente, 2=Frecuente. Excluimos el 9 (No sabe)
    df_v = df[df["P3_2"].isin([1, 2, 3, 4])]
    total = df_v["FAC_P18"].sum()
    pob = df_v[df_v["P3_2"].isin([1, 2])]["FAC_P18"].sum()
    return (pob / total * 100) if total > 0 else 0

def satisfaccion_8a10(df, col):
    """Denominador: Población Total Morelos -> Resultado esperado: 51.7%"""
    if col not in df.columns: return 0
    total_pob = df["FAC_P18"].sum()
    v = pd.to_numeric(df[col], errors="coerce")
    # INEGI cuenta 8, 9 y 10 como satisfactorio
    satisfechos = df[v.isin([8, 9, 10])]["FAC_P18"].sum()
    return (satisfechos / total_pob * 100) if total_pob > 0 else 0

def satisfaccion_promedio_servicios(df):
    # Servicios básicos clave para el KPI general
    cols = ["P4_1B","P4_2B","P4_3B","P4_4B","P4_5B"]
    valores = [satisfaccion_8a10(df, c) for c in cols]
    return sum(valores) / len(valores) if valores else 0

def interaccion_gob(df):
    # Personas que interactuaron con al menos un servicio/trámite digital o presencial
    cols = ["P10_1_2","P10_1_3","P10_1_4","P10_1_5","P10_1_6"]
    for c in cols: df[c] = pd.to_numeric(df[c], errors="coerce")
    df_d = df[df[cols].eq(1).any(axis=1)]
    return (df_d["FAC_P18"].sum() / fac_total(df) * 100) if fac_total(df) > 0 else 0

def tabla_atributos(df, atributos):
    """Denominador: Población Total Morelos -> Resultado esperado: 79.2%, 71.6%, etc."""
    filas = []
    total_pob = df["FAC_P18"].sum()
    for col, nombre in atributos.items():
        if col in df.columns:
            v = pd.to_numeric(df[col], errors="coerce")
            # Solo contamos el 'Sí' (valor 1)
            total_si = df[v == 1]["FAC_P18"].sum()
            filas.append({
                "Característica": nombre,
                "Porcentaje": (total_si / total_pob * 100) if total_pob > 0 else 0
            })
    return pd.DataFrame(filas).sort_values("Porcentaje", ascending=True)

def tarjeta_servicio(df, nombre, cfg, altura=300): # Subí la altura base a 380
    with st.container():
        st.subheader(nombre)
        # Calculamos la métrica de satisfacción (8-10)
        st.metric("Satisfacción (8–10)", f"{satisfaccion_8a10(df, cfg['calif']):.1f}%")
        
        # Generamos la tabla con las 7 categorías
        df_plot = tabla_atributos(df, cfg["atributos"])
        
        fig = px.bar(
            df_plot,
            x="Porcentaje",
            y="Característica",
            orientation="h",
            text_auto=".1f",
            color_discrete_sequence=[cfg["color"]]
        )
        # Ajustamos márgenes para que los nombres largos (como "pozo comunitario") se lean bien
        fig.update_layout(
            height=altura, 
            xaxis_title="%", 
            yaxis_title="",
            margin=dict(l=150, r=20, t=20, b=20) 
        )
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------
# DICCIONARIO DE CONFIGURACIÓN
# ------------------------------------------------------

SERVICIOS_BASICOS = {
    "Agua potable": {
        "calif": "P4_1B", 
        "color": "#0077B6",
        "atributos": {
            "P4_1_1": "Suministro constante",
            "P4_1_2": "Agua clara",
            "P4_1_3": "Agua bebible",
            "P4_1_4": "Reparación de fugas",
            "P4_1_5": "Red pública",
            "P4_1_6": "Proviene de pozo comunitario",
            "P4_1_7": "Proviene de pozo particular",
        }
    },
    "Drenaje y alcantarillado": {
        "calif": "P4_2B", "color": "#52B788",
        "atributos": {"P4_2_1": "Conexión y descarga adecuada", "P4_2_2": "Mantenimiento frecuente", "P4_2_3": "Limpieza constante", "P4_2_4": "Fuga de aguas residuales"}
    },
    "Alumbrado público": {
        "calif": "P4_3B", "color": "#FFB703",
        "atributos": {"P4_3_1": "Iluminación adecuada", "P4_3_2": "Mantenimiento", "P4_3_3": "Atención inmediata de fallas"}
    },
    "Recolección de basura": {
        "calif": "P4_5B", "color": "#2D6A4F",
        "atributos": {"P4_5_1": "Oportuno", "P4_5_2": "Gratuito", "P4_5_3": "Solicitan separación de residuos"}
    },
    "Policía": {
        "calif": "P4_6B", "color": "#003049",
        "atributos": {"P4_6_1": "Brinda seguridad", "P4_6_2": "Dispuesta a ayudar"}
    },
    "Parques y jardines": {
        "calif": "P4_4B", "color": "#40916C",
        "atributos": {"P4_4_1": "Horarios Accesibles", "P4_4_3": "Limpios", "P4_4_4": "Seguros"}
    }
}

# ------------------------------------------------------
# SIDEBAR – NAVEGACIÓN
# ------------------------------------------------------

with st.sidebar:
    st.title("ENCIG 2023 - Morelos")
    categoria = st.selectbox("Sección:", ["Pantalla principal", "Servicios Públicos Básicos"])

    if categoria == "Servicios Públicos Básicos":
        modo = st.radio("Visualización:", ["Vista tipo panel", "Vista individual"])
        if modo == "Vista individual":
            servicio = st.selectbox("Servicio:", list(SERVICIOS_BASICOS.keys()))

# ------------------------------------------------------
# CONTENIDO PRINCIPAL
# ------------------------------------------------------

if categoria == "Pantalla principal":
    st.markdown("## 📊 Panorama General – Morelos")
    c1, c2, c3, c4 = st.columns(4)

    pp, tabla = principal_problema(df)

    c1.metric("Principal problema", pp["Problema"], f"{pp['Porcentaje']:.1f}%")
    c2.metric("Corrupción frecuente", f"{corrupcion_frecuente(df):.1f}%")
    c3.metric("Satisfacción servicios", f"{satisfaccion_promedio_servicios(df):.1f}%")
    c4.metric("Interacción gobierno", f"{interaccion_gob(df):.1f}%")

    st.markdown("### Percepción de problemas en la entidad")
    fig = px.bar(tabla, x="Porcentaje", y="Problema", orientation="h", text_auto=".1f",
                 color_discrete_sequence=["#C0392B"])
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---") # Línea divisoria visual
    
    # Contenedor expandible para no saturar la vista inicial
    with st.expander("ℹ️ Notas Metodológicas y Glosario de Indicadores"):
        st.markdown("""
        ### **Precisiones Metodológicas**
        Los datos presentados corresponden exclusivamente al estado de **Morelos** y han sido procesados utilizando el **Factor de Expansión (FAC_P18)** de la ENCIG 2023.
        
        * **Cálculo de Porcentajes:** Siguiendo la metodología de los boletines de prensa de INEGI, el denominador utilizado para todos los indicadores es la **población total de 18 años y más**, permitiendo una comparativa directa con las gráficas oficiales nacionales.
        
        ---
        ### **Definición de Indicadores**
        
        * **Principal Problema:** Identifica el fenómeno que la población percibe como la mayor afectación en su entorno inmediato (Inseguridad, Corrupción, etc.).
            
        * **Corrupción Frecuente:** Porcentaje de adultos que consideran que los actos de corrupción ocurren de manera "Muy frecuente" o "Frecuente" en las instituciones de gobierno.
            
        * **Satisfacción con Servicios:** Mide el porcentaje de personas que califican con **8, 9 o 10** la calidad de los servicios básicos (promedio de los servicios analizados).
            
        * **Interacción con el Gobierno:** Mide la población que tuvo al menos un contacto con servidores públicos o plataformas digitales para realizar trámites, pagos o solicitudes.
        
        **Fuente:** Elaboración propia con datos de la Encuesta Nacional de Calidad e Impacto Gubernamental (ENCIG) 2023, INEGI.
        """)

elif categoria == "Servicios Públicos Básicos":
    if modo == "Vista tipo panel":
        st.markdown("## 🧩 Servicios Públicos Básicos")
        cols = st.columns(2)
        for i, (nombre, cfg) in enumerate(SERVICIOS_BASICOS.items()):
            with cols[i % 2]:
                tarjeta_servicio(df, nombre, cfg)
    else:
        st.markdown(f"## {servicio}")
        tarjeta_servicio(df, servicio, SERVICIOS_BASICOS[servicio], altura=400)

st.caption("Fuente: ENCIG 2023, INEGI. Procesamiento con Factor de Expansión FAC_P18.")
