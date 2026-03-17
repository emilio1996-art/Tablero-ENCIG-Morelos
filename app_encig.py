# ======================================================
# TABLERO ENCIG 2023 – ESTADO DE MORELOS
# Pantalla Ejecutiva + Servicios Públicos Básicos
# Vista individual y Vista tipo panel
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
# CARGA DE DATOS
# ------------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_excel("Consolidado_Morelos_Bases_Final.xlsx")
    df["FAC_P18"] = pd.to_numeric(df["FAC_P18"], errors="coerce").fillna(0)
    return df

df = load_data()

# ------------------------------------------------------
# FUNCIONES – KPIs EJECUTIVOS
# ------------------------------------------------------

def fac_total(df):
    return df["FAC_P18"].sum()

def principal_problema(df):
    problemas = {
        "P3_1_05": "Inseguridad y delincuencia",
        "P3_1_03": "Corrupción",
        "P3_1_01": "Mal desempeño del gobierno",
        "P3_1_04": "Desempleo",
        "P3_1_02": "Pobreza"
    }
    total = fac_total(df)
    res = []
    for col, nombre in problemas.items():
        v = pd.to_numeric(df[col], errors="coerce")
        pob = df[v == 1]["FAC_P18"].sum()
        res.append({
            "Problema": nombre,
            "Porcentaje": (pob / total * 100) if total > 0 else 0
        })
    tabla = pd.DataFrame(res).sort_values("Porcentaje", ascending=False)
    return tabla.iloc[0], tabla

def corrupcion_frecuente(df):
    v = pd.to_numeric(df["P3_2"], errors="coerce")
    pob = df[v.isin([1, 2])]["FAC_P18"].sum()
    return pob / fac_total(df) * 100

def satisfaccion_servicios(df):
    cols = ["P4_1B","P4_2B","P4_3B","P4_4B","P4_5B","P4_6B"]
    valores = []
    for col in cols:
        v = pd.to_numeric(df[col], errors="coerce")
        df_v = df[(v >= 1) & (v <= 10)]
        total = df_v["FAC_P18"].sum()
        sat = df_v[v >= 8]["FAC_P18"].sum()
        if total > 0:
            valores.append(sat / total * 100)
    return sum(valores) / len(valores)

def interaccion_gob(df):
    cols = ["P10_1_2","P10_1_3","P10_1_4","P10_1_5","P10_1_6"]
    tmp = df.copy()
    tmp[cols] = tmp[cols].apply(pd.to_numeric, errors="coerce")
    df_d = tmp[tmp[cols].eq(1).any(axis=1)]
    return df_d["FAC_P18"].sum() / fac_total(df) * 100

# ------------------------------------------------------
# FUNCIONES – SERVICIOS BÁSICOS
# ------------------------------------------------------

def satisfaccion_8a10(df, col):
    v = pd.to_numeric(df[col], errors="coerce")
    df_v = df[(v >= 1) & (v <= 10)]
    total = df_v["FAC_P18"].sum()
    sat = df_v[v >= 8]["FAC_P18"].sum()
    return (sat / total * 100) if total > 0 else 0

def tabla_atributos(df, atributos):
    filas = []
    for col, nombre in atributos.items():
        v = pd.to_numeric(df[col], errors="coerce")
        df_v = df[v.isin([1,2])]
        total = df_v["FAC_P18"].sum()
        si = df_v[v == 1]["FAC_P18"].sum()
        filas.append({
            "Característica": nombre,
            "Porcentaje": (si / total * 100) if total > 0 else 0
        })
    return pd.DataFrame(filas).sort_values("Porcentaje")

def tarjeta_servicio(df, nombre, cfg, altura=260):
    with st.container():
        st.subheader(nombre)
        st.metric("Satisfacción (8–10)", f"{satisfaccion_8a10(df, cfg['calif']):.1f}%")
        df_plot = tabla_atributos(df, cfg["atributos"])
        fig = px.bar(
            df_plot,
            x="Porcentaje",
            y="Característica",
            orientation="h",
            text_auto=".1f",
            color_discrete_sequence=[cfg["color"]]
        )
        fig.update_layout(height=altura, xaxis_title="%", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------
# CONFIGURACIÓN SERVICIOS BÁSICOS
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
            "P4_1_5": "Red pública"
        }
    },
    "Drenaje y alcantarillado": {
        "calif": "P4_2B",
        "color": "#52B788",
        "atributos": {
            "P4_2_1": "Conexión adecuada",
            "P4_2_2": "Mantenimiento",
            "P4_2_3": "Evita inundaciones",
            "P4_2_4": "Sin fugas"
        }
    },
    "Alumbrado público": {
        "calif": "P4_3B",
        "color": "#FFB703",
        "atributos": {
            "P4_3_1": "Iluminación",
            "P4_3_2": "Mantenimiento",
            "P4_3_3": "Atención a fallas"
        }
    },
    "Recolección de basura": {
        "calif": "P4_5B",
        "color": "#2D6A4F",
        "atributos": {
            "P4_5_1": "Oportuno",
            "P4_5_2": "Gratuito",
            "P4_5_3": "Separación"
        }
    },
    "Policía": {
        "calif": "P4_6B",
        "color": "#003049",
        "atributos": {
            "P4_6_1": "Brinda seguridad",
            "P4_6_2": "Dispuesta a ayudar"
        }
    },
    "Parques y jardines": {
        "calif": "P4_4B",
        "color": "#40916C",
        "atributos": {
            "P4_4_1": "Accesibles",
            "P4_4_2": "Cercanos",
            "P4_4_3": "Limpios",
            "P4_4_4": "Seguros"
        }
    },
    "Calles y avenidas": {
        "calif": "P4_7B",
        "color": "#495057",
        "atributos": {
            "P4_7_1": "Buen estado",
            "P4_7_2": "Reparación",
            "P4_7_3": "Semáforos"
        }
    },
    "Carreteras": {
        "calif": "P4_8B",
        "color": "#212529",
        "atributos": {
            "P4_8_1": "Sin baches",
            "P4_8_2": "Seguras",
            "P4_8_3": "Conectividad"
        }
    }
}

# ------------------------------------------------------
# SIDEBAR – NAVEGACIÓN
# ------------------------------------------------------

with st.sidebar:
    st.title("Navegación")
    categoria = st.selectbox(
        "Seleccione sección:",
        ["Pantalla principal", "Servicios Públicos Básicos"]
    )

    if categoria == "Servicios Públicos Básicos":
        modo = st.radio(
            "Modo de visualización:",
            ["Vista tipo panel (todos)", "Vista individual"]
        )

        if modo == "Vista individual":
            servicio = st.radio("Servicio:", list(SERVICIOS_BASICOS.keys()))

# ------------------------------------------------------
# CONTENIDO PRINCIPAL
# ------------------------------------------------------

if categoria == "Pantalla principal":
    st.markdown("## 📊 Panorama General – ENCIG 2023 | Morelos")
    c1, c2, c3, c4 = st.columns(4)

    pp, tabla = principal_problema(df)

    c1.metric("Principal problema", pp["Problema"], f"{pp['Porcentaje']:.1f}%")
    c2.metric("Corrupción frecuente", f"{corrupcion_frecuente(df):.1f}%")
    c3.metric("Satisfacción servicios", f"{satisfaccion_servicios(df):.1f}%")
    c4.metric("Interacción con gobierno", f"{interaccion_gob(df):.1f}%")

    fig = px.bar(
        tabla.sort_values("Porcentaje"),
        x="Porcentaje",
        y="Problema",
        orientation="h",
        text_auto=".1f",
        color_discrete_sequence=["#C0392B"]
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📌 Nota metodológica"):
        st.write("""
        Indicadores calculados con FAC_P18.
        La pregunta de problemas permite hasta tres respuestas por persona.
        """)

elif categoria == "Servicios Públicos Básicos":

    if modo == "Vista tipo panel (todos)":
        st.markdown("## 🧩 Servicios Públicos Básicos")
        cols = st.columns(2)
        i = 0
        for nombre, cfg in SERVICIOS_BASICOS.items():
            with cols[i % 2]:
                tarjeta_servicio(df, nombre, cfg, altura=260)
            i += 1

    else:
        st.markdown(f"## {servicio}")
        cfg = SERVICIOS_BASICOS[servicio]
        tarjeta_servicio(df, servicio, cfg, altura=420)

st.caption("Fuente: Encuesta Nacional de Calidad e Impacto Gubernamental (ENCIG) 2023, INEGI.")
