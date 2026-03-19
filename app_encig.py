# ======================================================
# TABLERO ENCIG 2023 – ESTADO DE MORELOS (OPTIMIZADO)
# Alineado a Metodología INEGI - Vista Panel Única
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
    # Carga de hojas
    df_principal = pd.read_excel("Consolidado_Morelos_Bases_Final.xlsx", sheet_name=0)
    df_sec6 = pd.read_excel("Consolidado_Morelos_Bases_Final.xlsx", sheet_name="encig2023_03_sec_6")
    df_sec7 = pd.read_excel("Consolidado_Morelos_Bases_Final.xlsx", sheet_name="encig2023_04_sec_7")
    
    # 1. Personas únicas (1 fila = 1 persona)
    df_sec6_u = df_sec6[["ID_VIV", "ID_PER", "P6_1"]].drop_duplicates(subset=["ID_VIV", "ID_PER"])
    df_gen = pd.merge(df_principal, df_sec6_u, on=["ID_VIV", "ID_PER"], how="left")
    
    # 2. Registros de trámites (múltiples filas por persona)
    df_tramites = pd.merge(
        df_gen[["ID_VIV", "ID_PER", "FAC_P18", "P6_1"]], 
        df_sec7[["ID_VIV", "ID_PER", "P7_3"]], 
        on=["ID_VIV", "ID_PER"], 
        how="inner"
    )
    
    # Limpieza numérica centralizada
    datasets = [df_gen, df_tramites]
    for d in datasets:
        if "FAC_P18" in d.columns:
            d["FAC_P18"] = pd.to_numeric(d["FAC_P18"], errors="coerce").fillna(0)
        for c in ["P6_1", "P7_3"]:
            if c in d.columns:
                d[c] = pd.to_numeric(d[c], errors="coerce")
            
    return {"general": df_gen, "tramites": df_tramites}

data = load_data()
df = data["general"]
df_t = data["tramites"]

# ------------------------------------------------------
# FUNCIONES DE CÁLCULO
# ------------------------------------------------------

def fac_total(df):
    return df["FAC_P18"].sum()

def principal_problema(df):
    problemas = {
        "P3_1_05": "Inseguridad y delincuencia", "P3_1_03": "Corrupción",
        "P3_1_01": "Mal desempeño del gobierno", "P3_1_04": "Desempleo",
        "P3_1_02": "Pobreza", "P3_1_06": "Mala aplicación de la ley",
        "P3_1_07": "Desastres naturales", "P3_1_08": "Baja calidad de la educación pública",
        "P3_1_09": "Mala atención en centros de salud", "P3_1_10": "Falta de coordinación gubernamental",
        "P3_1_11": "Falta de rendición de cuentas"
    }
    total_pob = fac_total(df)
    res = []
    for col, nombre in problemas.items():
        if col in df.columns:
            pob = df[df[col] == 1]["FAC_P18"].sum()
            res.append({"Problema": nombre, "Porcentaje": (pob / total_pob * 100) if total_pob > 0 else 0})
    
    tabla = pd.DataFrame(res).sort_values("Porcentaje", ascending=False)
    main_prob = tabla.iloc[0] if not tabla.empty else {"Problema": "N/A", "Porcentaje": 0}
    return main_prob, tabla

def corrupcion_frecuente(df):
    df_v = df[df["P3_2"].isin([1, 2, 3, 4])]
    total = df_v["FAC_P18"].sum()
    pob = df_v[df_v["P3_2"].isin([1, 2])]["FAC_P18"].sum()
    return (pob / total * 100) if total > 0 else 0

def satisfaccion_8a10(df, col):
    if col not in df.columns: return 0
    total_pob = df["FAC_P18"].sum()
    v = pd.to_numeric(df[col], errors="coerce")
    satisfechos = df[v.isin([8, 9, 10])]["FAC_P18"].sum()
    return (satisfechos / total_pob * 100) if total_pob > 0 else 0

def satisfaccion_promedio_servicios(df):
    cols = ["P4_1B","P4_2B","P4_3B","P4_4B","P4_5B"]
    valores = [satisfaccion_8a10(df, c) for c in cols]
    return sum(valores) / len(valores) if valores else 0

def interaccion_gob(df):
    cols = ["P10_1_2","P10_1_3","P10_1_4","P10_1_5","P10_1_6"]
    for c in cols: 
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df_d = df[df[cols].eq(1).any(axis=1)]
    return (df_d["FAC_P18"].sum() / fac_total(df) * 100) if fac_total(df) > 0 else 0

def tabla_atributos(df, atributos):
    filas = []
    total_pob = df["FAC_P18"].sum()
    for col, nombre in atributos.items():
        if col in df.columns:
            v = pd.to_numeric(df[col], errors="coerce")
            total_si = df[v == 1]["FAC_P18"].sum()
            filas.append({"Característica": nombre, "Porcentaje": (total_si / total_pob * 100) if total_pob > 0 else 0})
    return pd.DataFrame(filas).sort_values("Porcentaje", ascending=True)

def calcular_lugares_tramites_morelos_oficial(df_gen, df_tram):
    # Universo: Personas con contacto (1=Sí, 9=No especificado/otros según lógica previa)
    df_universo = df_gen[df_gen["P6_1"].isin([1, 9])].drop_duplicates(subset=["ID_VIV", "ID_PER"])
    total_universo = df_universo["FAC_P18"].sum()
    
    if total_universo == 0: return pd.DataFrame()

    mapa = {
        "Instalaciones de gobierno": [1],
        "Cajero automático o kiosco inteligente": [3, 6], 
        "Internet": [4],
        "Banco, supermercado, tiendas o farmacias": [2],
        "Líneas de atención telefónica": [5]
    }
    
    res = []
    for nombre, codigos in mapa.items():
        ids_medio = df_tram[df_tram["P7_3"].isin(codigos)][["ID_VIV", "ID_PER"]].drop_duplicates()
        pob_medio = pd.merge(ids_medio, df_universo, on=["ID_VIV", "ID_PER"])["FAC_P18"].sum()
        res.append({"Lugar": nombre, "Porcentaje": (pob_medio / total_universo * 100)})
    
    return pd.DataFrame(res).sort_values("Porcentaje", ascending=True)

def calcular_percepcion_corrupcion(df):
    """
    Calcula percepción general sobre el total de la población de 18 años y más.
    """
    total_pob = df["FAC_P18"].sum()
    if total_pob == 0: return pd.DataFrame()

    categorias = {1: "Muy frecuente", 2: "Frecuente", 3: "Poco frecuente", 4: "Nunca"}
    res = []
    for cod, nombre in categorias.items():
        pob_cat = df[df["P3_2"] == cod]["FAC_P18"].sum()
        res.append({"Percepción": nombre, "Porcentaje": (pob_cat / total_pob * 100)})
    
    return pd.DataFrame(res)

def calcular_corrupcion_sectores_morelos(df):
    """
    Calcula el porcentaje de percepción 'Muy Frecuente o Frecuente' por sector
    sobre el TOTAL de la población (incluyendo 'No sabe').
    """
    sectores_map = {
        "P3_3_01": "Universidades públicas", "P3_3_02": "Policías",
        "P3_3_03": "Hospitales públicos", "P3_3_04": "Presidencia de la República",
        "P3_3_05": "Empresarios",
        "P3_3_06": "Gobiernos Estatales",
        "P3_3_07": "Compañeros(as) del trabajo",
        "P3_3_08": "Gobierno Municipal", "P3_3_09": "Familia",
        "P3_3_10": "Sindicatos", "P3_3_11": "Vecinos(as)",
        "P3_3_12": "Cámaras de Diputados y Senadores", "P3_3_13": "Medios de comunicación",
        "P3_3_14": "Institutos electorales", "P3_3_15": "Comisiones de derechos humanos",
        "P3_3_16": "Escuelas públicas de nivel básico", "P3_3_17": "Jueces(ezas) y Magistrados(as)",
        "P3_3_18": "Instituciones religiosas", "P3_3_19": "Partidos políticos",
        "P3_3_20": "Guardia Nacional",
        "P3_3_21": "Ejército y Marina", "P3_3_22": "Ministerio Público o Fiscalía Estatal",
        "P3_3_23": "ONG's", "P3_3_24": "Organismos Públicos Autónomos"
    } 
    
    # Denominador: Población total representada en Morelos (FAC_P18)
    total_pob = df["FAC_P18"].sum()
    if total_pob == 0: return pd.DataFrame()

    res = []
    for col, nombre in sectores_map.items():
        if col in df.columns:
            # Numerador: Personas que respondieron 1 (Muy Frecuente) o 2 (Frecuente)
            pob_freq = df[df[col].isin([1, 2])]["FAC_P18"].sum()
            porcentaje = (pob_freq / total_pob * 100)
            res.append({"Sector": nombre, "Porcentaje": porcentaje})
    
    return pd.DataFrame(res).sort_values("Porcentaje", ascending=False)

# ------------------------------------------------------
# VISUALIZACIÓN REUTILIZABLE
# ------------------------------------------------------

def tarjeta_servicio(df, nombre, cfg, altura=350):
    with st.container():
        st.subheader(nombre)
        sat_val = satisfaccion_8a10(df, cfg['calif'])
        st.metric("Satisfacción (8–10)", f"{sat_val:.1f}%")
        df_plot = tabla_atributos(df, cfg["atributos"])
        fig = px.bar(df_plot, x="Porcentaje", y="Característica", orientation="h", text_auto=".1f", color_discrete_sequence=[cfg["color"]])
        fig.update_layout(height=altura, xaxis_title="%", yaxis_title="", margin=dict(l=220, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------
# DICCIONARIOS DE CONFIGURACIÓN
# ------------------------------------------------------

SERVICIOS_BASICOS = {
    "Agua potable": {
        "calif": "P4_1B", "color": "#0077B6",
        "atributos": {
            "P4_1_5": "Proviene de la red pública", "P4_1_2": "Pureza y claridad",
            "P4_1_1": "Suministro constante", "P4_1_6": "Proviene de un pozo comunitario",
            "P4_1_4": "Sin desperdicio por fugas", "P4_1_3": "Potabilidad", "P4_1_7": "Proviene de un pozo particular"
        }
    },
    "Drenaje y alcantarillado": {"calif": "P4_2B", "color": "#52B788", "atributos": {"P4_2_1": "Conexión y descarga adecuados", "P4_2_4": "Sin fugas de aguas negras", "P4_2_3": "Limpieza constante", "P4_2_2": "Mantenimiento frecuente"}},
    "Recolección de basura": {"calif": "P4_5B", "color": "#2D6A4F", "atributos": {"P4_5_1": "Servicio oportuno", "P4_5_2": "Sin cuotas o propinas", "P4_5_3": "Solicita separación de residuos"}},
    "Alumbrado público": {"calif": "P4_3B", "color": "#FFB703", "atributos": {"P4_3_1": "Iluminación adecuada", "P4_3_2": "Buen estado", "P4_3_3": "Atención rápida a fallas"}},
    "Policía": {"calif": "P4_6B", "color": "#003049", "atributos": {"P4_6_1": "Brinda seguridad", "P4_6_2": "Disposición a ayudar"}},
    "Parques y jardines": {"calif": "P4_4B", "color": "#40916C", "atributos": {"P4_4_1": "Horarios Accesibles", "P4_4_3": "Limpios", "P4_4_4": "Seguros"}}
}

# ------------------------------------------------------
# NAVEGACIÓN
# ------------------------------------------------------

with st.sidebar:
    st.title("ENCIG 2023 - Morelos")
    categoria = st.selectbox("Sección:", [
        "Inicio", 
        "Servicios Públicos Básicos", 
        "Experiencias en trámites y solicitudes",
        "Experiencias de corrupción"  # <-- Nueva opción agregada
    ])

if categoria == "Inicio":
    st.markdown("## 📊 Panorama General – Morelos")
    pob_total_18 = fac_total(df)
    st.metric("Población representada (18 años y más)", f"{pob_total_18:,.0f}")
    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    pp, tabla_p = principal_problema(df)
    
    # Métricas principales
    c1.metric("Principal problema", pp["Problema"], f"{pp['Porcentaje']:.1f}%")
    c2.metric("Corrupción frecuente", f"{corrupcion_frecuente(df):.1f}%")
    c3.metric("Satisfacción servicios", f"{satisfaccion_promedio_servicios(df):.1f}%")
    c4.metric("Interacción gobierno", f"{interaccion_gob(df):.1f}%")

    st.markdown("### Percepción de problemas en la entidad")
    fig = px.bar(tabla_p, x="Porcentaje", y="Problema", orientation="h", text_auto=".1f", color_discrete_sequence=["#C0392B"])
    st.plotly_chart(fig, use_container_width=True)

    # --- REINSERCIÓN DE NOTAS METODOLÓGICAS ---
    st.divider()
    with st.expander("📝 Precisiones Metodológicas y Definiciones"):
        st.markdown("""
        ### **Precisiones Metodológicas**
        Los datos corresponden exclusivamente al estado de **Morelos** y han sido procesados utilizando el **Factor de Expansión (FAC_P18)** de la ENCIG 2023.
        * **Población Representada:** Es la suma de los factores de expansión, indicando a cuántos ciudadanos reales equivale la muestra.
        * **Cálculo de Porcentajes:** El denominador utilizado para los indicadores es la **población total de 18 años y más**, permitiendo una comparativa directa con las gráficas oficiales.
        
        ---
        ### **Definición de Indicadores**
        * **Principal Problema:** Identifica el fenómeno que la población percibe como la mayor afectación (Inseguridad, Corrupción, etc.).
        * **Corrupción Frecuente:** Adultos que consideran que la corrupción es "Muy frecuente" o "Frecuente".
        * **Satisfacción con Servicios:** Porcentaje de personas que califican con **8, 9 o 10** la calidad de los servicios.
        * **Interacción con el Gobierno:** Población que tuvo al menos un contacto con servidores públicos o plataformas para trámites.
        
        **Fuente:** Elaboración propia con datos de la Encuesta Nacional de Calidad e Impacto Gubernamental (ENCIG) 2023, INEGI.
        """)

elif categoria == "Servicios Públicos Básicos":
    st.markdown("## 🧩 Servicios Públicos Básicos")
    cols = st.columns(2)
    for i, (nombre, cfg) in enumerate(SERVICIOS_BASICOS.items()):
        with cols[i % 2]:
            tarjeta_servicio(df, nombre, cfg)

elif categoria == "Experiencias en trámites y solicitudes":
    st.markdown("## 📑 Experiencias en trámites y solicitudes")
    df_lugares = calcular_lugares_tramites_morelos_oficial(df, df_t)
    if not df_lugares.empty:
        fig = px.bar(df_lugares, x="Porcentaje", y="Lugar", orientation="h", text_auto=".1f", color_discrete_sequence=["#8E44AD"])
        fig.update_layout(xaxis=dict(range=[0, 70]), margin=dict(l=300, r=50, t=50, b=50), height=500)
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

elif categoria == "Experiencias de corrupción":
    st.markdown("## 🛡️ Experiencias de corrupción")
    # Gráfica 1: Percepción General
    st.markdown("### Percepción sobre la frecuencia de corrupción en Morelos")
    df_perc = calcular_percepcion_corrupcion(df)
    if not df_perc.empty:
        fig1 = px.bar(df_perc, x="Percepción", y="Porcentaje", text_auto=".1f", color_discrete_sequence=["#14213d"])
        fig1.update_layout(yaxis=dict(range=[0, 50]), height=400)
        st.plotly_chart(fig1, use_container_width=True)

    st.divider()

    # Gráfica 2: Por Sectores
    st.markdown("### Percepción sobre la frecuencia de corrupción en diversos sectores")
    st.caption("(Suma de respuestas 'Muy frecuente' y 'Frecuente')")
    df_sect = calcular_corrupcion_sectores_morelos(df)
    if not df_sect.empty:
        fig2 = px.bar(df_sect, x="Porcentaje", y="Sector", orientation="h", text_auto=".1f", color_discrete_sequence=["#fca311"])
        fig2.update_layout(xaxis=dict(range=[0, 100]), margin=dict(l=300), height=800)
        st.plotly_chart(fig2, use_container_width=True)
        
    else:
        st.error("No se encontraron registros válidos para generar la gráfica.")

st.caption("Fuente: ENCIG 2023, INEGI. Procesamiento con Factor de Expansión FAC_P18.")
