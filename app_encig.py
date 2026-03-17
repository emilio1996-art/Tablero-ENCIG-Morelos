# ======================================================
# TABLERO ENCIG 2023 – ESTADO DE MORELOS
# Pantalla Ejecutiva + Servicios Públicos Básicos
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
    padding: 20px; border-radius: 10px; 
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
# FUNCIÓN GENÉRICA – SERVICIOS BÁSICOS
# ------------------------------------------------------

def grafica_servicio_basico(df, titulo, col_calif, atributos, color):
    st.subheader(titulo)

    # Satisfacción general
    v = pd.to_numeric(df[col_calif], errors="coerce")
    df_v = df[(v >= 1) & (v <= 10)]
    total = df_v["FAC_P18"].sum()
    sat = df_v[v >= 8]["FAC_P18"].sum()
    porc = (sat / total * 100) if total > 0 else 0

    st.metric("Satisfacción (8 a 10)", f"{porc:.1f}%")

    # Atributos
    datos = []
    for col, nombre in atributos.items():
        vals = pd.to_numeric(df[col], errors="coerce")
        df_a = df[vals.isin([1, 2])]
        tot = df_a["FAC_P18"].sum()
        si = df_a[vals == 1]["FAC_P18"].sum()
        datos.append({
            "Característica": nombre,
            "Porcentaje": (si / tot * 100) if tot > 0 else 0
        })

    df_plot = pd.DataFrame(datos).sort_values("Porcentaje")

    fig = px.bar(
        df_plot,
        x="Porcentaje",
        y="Característica",
        orientation="h",
        text_auto=".1f",
        color_discrete_sequence=[color]
    )
    fig.update_layout(xaxis_title="Porcentaje (%)", yaxis_title="", height=420)
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------
# CONFIGURACIÓN – SERVICIOS PÚBLICOS BÁSICOS
# ------------------------------------------------------

SERVICIOS_BASICOS = {
    "Agua potable": {
        "calif": "P4_1B",
        "color": "#0077B6",
        "atributos": {
            "P4_1_1": "Suministro constante",
            "P4_1_2": "Agua clara",
            "P4_1_3": "Agua bebible",
            "P4_1_4": "Reparación rápida de fugas",
            "P4_1_5": "Proviene de red pública"
        }
    },
    "Drenaje y alcantarillado": {
        "calif": "P4_2B",
        "color": "#52B788",
        "atributos": {
            "P4_2_1": "Conexión adecuada",
            "P4_2_2": "Mantenimiento frecuente",
            "P4_2_3": "Evita inundaciones",
            "P4_2_4": "Sin fugas"
        }
    },
    "Alumbrado público": {
        "calif": "P4_3B",
        "color": "#FFB703",
        "atributos": {
            "P4_3_1": "Iluminación adecuada",
            "P4_3_2": "Mantenimiento",
            "P4_3_3": "Atención a fallas"
        }
    },
    "Recolección de basura": {
        "calif": "P4_5B",
        "color": "#2D6A4F",
        "atributos": {
            "P4_5_1": "Servicio oportuno",
            "P4_5_2": "Servicio gratuito",
            "P4_5_3": "Separación de residuos"
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
            "P4_4_1": "Accesibles en horario",
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
            "P4_7_2": "Reparación de baches",
            "P4_7_3": "Semáforos funcionales"
        }
    },
    "Carreteras": {
        "calif": "P4_8B",
        "color": "#212529",
        "atributos": {
            "P4_8_1": "Sin baches",
            "P4_8_2": "Seguras",
            "P4_8_3": "Comunican al estado"
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
        servicio = st.radio(
            "Servicio:",
            list(SERVICIOS_BASICOS.keys())
        )

# ------------------------------------------------------
# CONTENIDO
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
        Resultados calculados con el factor de expansión FAC_P18.
        La pregunta de problemas permite hasta tres respuestas por persona.
        """)

elif categoria == "Servicios Públicos Básicos":
    cfg = SERVICIOS_BASICOS[servicio]
    grafica_servicio_basico(
        df,
        servicio,
        cfg["calif"],
        cfg["atributos"],
        cfg["color"]
    )

st.caption("Fuente: ENCIG 2023, INEGI.")
