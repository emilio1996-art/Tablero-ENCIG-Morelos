import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Tablero ENCIG Morelos", layout="wide")

# 2. Estilo Visual Adaptativo
st.markdown("""
    <style>
    .plot-container { 
        padding: 20px; border-radius: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 25px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .metric-card { 
        padding: 15px; border-radius: 10px; border-top: 4px solid #004b8d; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;
        background-color: rgba(128, 128, 128, 0.05); margin-bottom: 10px;
    }
    .leyenda-satisfaccion { text-align: center; font-weight: bold; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES MAESTRAS ---

def procesar_y_graficar(df, mapeo, titulo, color="#8E24AA", altura=500, es_problema=False):
    res = []
    df['FAC_P18'] = pd.to_numeric(df['FAC_P18'], errors='coerce').fillna(0)
    total_pob_estado = df['FAC_P18'].sum()
    
    for col, nombre in mapeo.items():
        if col in df.columns:
            val_col = pd.to_numeric(df[col], errors='coerce')
            if es_problema:
                pob_si = df[val_col == 1]['FAC_P18'].sum()
                porc = (pob_si / total_pob_estado * 100) if total_pob_estado > 0 else 0
            else:
                df_v = df[val_col.isin([1, 2, 9])]
                total_servicio = df_v['FAC_P18'].sum()
                palabras_negativas = ['fuga', 'falla', 'mantenimiento', 'bache', 'saturación', 'deficiencia']
                exito = 2 if any(p in nombre.lower() for p in palabras_negativas) else 1
                pob_si = df_v[val_col == exito]['FAC_P18'].sum()
                porc = (pob_si / total_servicio * 100) if total_servicio > 0 else 0
            res.append({'Concepto': nombre, 'Porcentaje': porc})
    
    df_plot = pd.DataFrame(res).sort_values(by='Porcentaje', ascending=True)
    st.markdown(f"### {titulo}")
    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
    fig = px.bar(df_plot, x='Porcentaje', y='Concepto', orientation='h', text_auto='.1f', color_discrete_sequence=[color])
    fig.update_layout(height=max(300, altura), xaxis_range=[0, 105], xaxis_title="%", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def renderizar_satisfaccion(df, col_sat, titulo, color, umbral=8, filtro_col=None):
    df[col_sat] = pd.to_numeric(df[col_sat], errors='coerce')
    df_base = df[df[filtro_col] == 1] if filtro_col else df
    df_v = df_base[(df_base[col_sat] >= 0) & (df_base[col_sat] <= 10)]
    total = df_v['FAC_P18'].sum()
    porc = (df_v[df_v[col_sat] >= umbral]['FAC_P18'].sum() / total * 100) if total > 0 else 0
    
    col_t, col_m = st.columns([2, 1])
    with col_t: st.title(titulo)
    with col_m: st.metric("Satisfacción (%)", f"{porc:.1f}%")
    
    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
    fig = px.bar(pd.DataFrame({'C':['Satisfechos'], 'V':[porc]}), x='V', y='C', 
                 orientation='h', range_x=[0,100], text_auto='.1f', color_discrete_sequence=[color])
    fig.update_layout(height=150, xaxis_title="%", yaxis_title="", margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def calcular_sat_salud(df, col_sat):
    df[col_sat] = pd.to_numeric(df[col_sat], errors='coerce')
    df_v = df[(df[col_sat] >= 0) & (df[col_sat] <= 10)]
    total = df_v['FAC_P18'].sum()
    return (df_v[df_v[col_sat] >= 9]['FAC_P18'].sum() / total * 100) if total > 0 else 0

def graficar_frecuencia_corrupcion(df):
    """Grafica la percepción de frecuencia de corrupción (P3_2)"""
    mapeo_etiquetas = {1: 'Muy Frecuente', 2: 'Frecuente', 3: 'Poco Frecuente', 4: 'Nunca', 9: 'No sabe / No responde'}
    df['P3_2'] = pd.to_numeric(df['P3_2'], errors='coerce')
    df['FAC_P18'] = pd.to_numeric(df['FAC_P18'], errors='coerce').fillna(0)
    
    df_v = df[df['P3_2'].isin(mapeo_etiquetas.keys())]
    total_pob = df_v['FAC_P18'].sum()
    
    datos = []
    for cod, etiqueta in mapeo_etiquetas.items():
        pob_cat = df_v[df_v['P3_2'] == cod]['FAC_P18'].sum()
        porc = (pob_cat / total_pob * 100) if total_pob > 0 else 0
        datos.append({'Frecuencia': etiqueta, 'Porcentaje': porc})
    
    st.markdown("### Percepción sobre la frecuencia de corrupción en la entidad")
    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
    fig = px.bar(pd.DataFrame(datos), x='Frecuencia', y='Porcentaje', text_auto='.1f', color_discrete_sequence=['#8E24AA'])
    fig.update_layout(xaxis_title="", yaxis_title="%", yaxis_range=[0, 100], height=450)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def graficar_percepcion_sectores(df):
    """Grafica la percepción de corrupción por sectores (P3_3_01 a P3_3_23)"""
    sectores_map = {
        'P3_3_01': 'Universidades públicas',
        'P3_3_02': 'Policías',
        'P3_3_03': 'Hospitales públicos',
        'P3_3_04': 'Presidencia de la República y Secretarías de Estado',
        'P3_3_05': 'Empresarios(as)',
        'P3_3_06': 'Gubernatura del estado o Jefatura de Gobierno',
        'P3_3_08': 'Presidencias municipales o Alcaldías',
        'P3_3_10': 'Sindicatos',
        'P3_3_12': 'Cámaras de Diputados y Senadores',
        'P3_3_13': 'Medios de comunicación',
        'P3_3_14': 'Institutos electorales',
        'P3_3_15': 'Comisiones de derechos humanos',
        'P3_3_16': 'Escuelas públicas de nivel básico',
        'P3_3_17': 'Jueces(ezas) y Magistrados(as)',
        'P3_3_19': 'Partidos políticos',
        'P3_3_20': 'Guardia Nacional',
        'P3_3_21': 'Ejército y Marina',
        'P3_3_22': 'Ministerio Público o Fiscalía Estatal',
        'P3_3_23': 'Servidores(as) públicos(as) o empleados(as) de gobierno'
    }

    res_sectores = []
    df['FAC_P18'] = pd.to_numeric(df['FAC_P18'], errors='coerce').fillna(0)
    
    for col, nombre in sectores_map.items():
        if col in df.columns:
            val_col = pd.to_numeric(df[col], errors='coerce')
            df_v = df[val_col.isin([1, 2, 3, 4, 9])]
            total_sector = df_v['FAC_P18'].sum()
            # Suma de "Muy frecuente" (1) y "Frecuente" (2)
            pob_frecuente = df_v[val_col.isin([1, 2])]['FAC_P18'].sum()
            porc = (pob_frecuente / total_sector * 100) if total_sector > 0 else 0
            res_sectores.append({'Sector': nombre, 'Porcentaje': porc})

    df_plot = pd.DataFrame(res_sectores).sort_values(by='Porcentaje', ascending=True)

    st.markdown("### Percepción de frecuencia de corrupción por sectores e instituciones")
    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
    fig = px.bar(df_plot, x='Porcentaje', y='Sector', orientation='h', 
                 text_auto='.1f', color_discrete_sequence=['#E67E22'])
    fig.update_layout(height=700, xaxis_range=[0, 105], xaxis_title="Porcentaje (Muy frecuente + Frecuente)", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_excel('Consolidado_Morelos_Bases_Final.xlsx')

# --- LÓGICA DE NAVEGACIÓN ---

try:
    df = load_data()
    st.markdown("<div style='text-align: center;'><h1>ENCIG 2023 - Estado de Morelos</h1></div>", unsafe_allow_html=True)

    with st.sidebar:
        st.title("Navegación")
        categoria = st.selectbox("Categoría:", 
                                ["1. Servicios Públicos Básicos", 
                                 "2. Experiencias de Corrupción", 
                                 "3. Servicios Públicos Bajo Demanda"])
        
        if categoria == "1. Servicios Públicos Básicos":
            tematica = st.radio("Temática:", ["Agua potable", "Drenaje y alcantarillado", "Alumbrado público", "Recolección de Basura", "Policía", "Parques y jardines", "Calles y avenidas", "Carreteras"])
        elif categoria == "2. Experiencias de Corrupción":
            tematica = st.radio("Temática:", ["Problemas Importantes en la Entidad", "Frecuencia de actos de corrupción", "Frecuencia por Sectores e Instituciones"])
        else:
            tematica = st.radio("Temática:", ["Comparativa de Salud", "Energía Eléctrica"])

    if categoria == "1. Servicios Públicos Básicos":
        config = {
            "Agua potable": ('P4_1B', ['P4_1_1','P4_1_2','P4_1_3','P4_1_4','P4_1_5'], ['Suministro Constante','Agua Clara','Bebible','Sin Fugas','Red Pública'], '#0077B6', 7, 'P4_1_5'),
            "Drenaje y alcantarillado": ('P4_2B', ['P4_2_1','P4_2_3','P4_2_4'], ['Conexión Red','Sin Fugas','Mantenimiento'], '#52B788', 8, None),
            "Alumbrado público": ('P4_3B', ['P4_3_1','P4_3_2','P4_3_3'], ['Iluminación Adecuada','Mantenimiento','Sin Fallas'], '#FFB703', 8, None),
            "Recolección de Basura": ('P4_5B', ['P4_5_1','P4_5_2','P4_5_3'], ['Oportuna','Gratuita','Frecuencia'], '#2D6A4F', 8, None),
            "Policía": ('P4_6B', ['P4_6_1','P4_6_2'], ['Disposición a Ayudar','Sensación de Seguridad'], '#003049', 8, None),
            "Parques y jardines": ('P4_4B', ['P4_4_1','P4_4_2','P4_4_3','P4_4_4'], ['Horarios','Cercanía','Limpieza','Seguridad'], '#2D6A4F', 8, None),
            "Calles y avenidas": ('P4_7B', ['P4_7_1','P4_7_2','P4_7_3'], ['En buen estado','Reparación de baches','Semáforos'], '#495057', 8, None),
            "Carreteras": ('P4_8B', ['P4_8_1','P4_8_2','P4_8_3'], ['Sin Baches','Seguridad','Comunicación'], '#212529', 8, None)
        }
        c = config[tematica]
        renderizar_satisfaccion(df, c[0], f"Servicio: {tematica}", c[3], umbral=8, filtro_col=c[5])
        procesar_y_graficar(df, dict(zip(c[1], c[2])), "Evaluación de Atributos", color="#168AAD")

    elif categoria == "2. Experiencias de Corrupción":
        if tematica == "Problemas Importantes en la Entidad":
            problemas_map = {'P3_1_01': 'Inseguridad y delincuencia', 'P3_1_02': 'Corrupción', 'P3_1_03': 'Mal desempeño del gobierno', 'P3_1_04': 'Desempleo', 'P3_1_05': 'Pobreza', 'P3_1_06': 'Mala atención en salud', 'P3_1_07': 'Mala aplicación de la ley', 'P3_1_08': 'Falta coordinación gubernamental', 'P3_1_09': 'Baja calidad educación pública', 'P3_1_10': 'Falta rendición de cuentas', 'P3_1_11': 'Desastres naturales'}
            procesar_y_graficar(df, problemas_map, "🚨 Problemas más importantes percibidos", color="#C0392B", altura=600, es_problema=True)
        elif tematica == "Frecuencia de actos de corrupción":
            graficar_frecuencia_corrupcion(df)
        elif tematica == "Frecuencia por Sectores e Instituciones":
            graficar_percepcion_sectores(df)

    elif categoria == "3. Servicios Públicos Bajo Demanda":
        if tematica == "Comparativa de Salud":
            st.title("Comparativa de Servicios de Salud")
            st.markdown("<p class='leyenda-satisfaccion'>Porcentaje de satisfacción</p>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("IMSS", f"{calcular_sat_salud(df, 'P5_4B'):.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("ISSSTE", f"{calcular_sat_salud(df, 'P5_5B'):.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Salud Estatal", f"{calcular_sat_salud(df, 'P5_7B'):.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            
            inst_config = {'P5_4': 'IMSS', 'P5_5': 'ISSSTE', 'P5_7': 'Salud Estatal'}
            atributos = {'_01': 'Trato respetuoso', '_02': 'Limpieza', '_03': 'Sin cobros extras', '_04': 'Información oportuna', '_05': 'Médicos capacitados', '_06': 'Equipo necesario', '_07': 'Médicos suficientes', '_08': 'Atención inmediata', '_09': 'Medicamentos', '_10': 'Sin deficiencias', '_11': 'Sin saturación'}
            datos_c = []
            for suf, nom in atributos.items():
                for pref, inst_n in inst_config.items():
                    col_name = f"{pref}{suf}"
                    if col_name in df.columns:
                        val = pd.to_numeric(df[col_name], errors='coerce')
                        df_v = df[val.isin([1, 2, 9])]
                        total_n = df_v['FAC_P18'].sum()
                        exito_n = 2 if suf in ['_10', '_11'] else 1
                        porc_n = (df_v[val == exito_n]['FAC_P18'].sum() / total_n * 100) if total_n > 0 else 0
                        datos_c.append({'Atributo': nom, 'Institución': inst_n, 'Porcentaje': porc_n})
            
            st.markdown('<div class="plot-container">', unsafe_allow_html=True)
            fig_c = px.bar(pd.DataFrame(datos_c), x='Atributo', y='Porcentaje', color='Institución', barmode='group', text_auto='.1f', color_discrete_map={'IMSS': '#8E24AA', 'ISSSTE': '#1C3D6E', 'Salud Estatal': '#D81B60'})
            fig_c.update_layout(height=550, xaxis_tickangle=-45, yaxis_range=[0, 110])
            st.plotly_chart(fig_c, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        elif tematica == "Energía Eléctrica":
            # 1. Indicador de Satisfacción General para Energía Eléctrica (P5_8B)
            renderizar_satisfaccion(df, 'P5_8B', "Servicio: Energía Eléctrica", "#F1C40F", umbral=8)

            # 2. Evaluación de Atributos Específicos
            # P5_8_1: Suministro sin apagones constantes
            # P5_8_2: Mantenimiento oportuno
            # P5_8_3: Atención inmediata de fallas
            atributos_luz = {
                'P5_8_1': 'Suministro sin apagones',
                'P5_8_2': 'Mantenimiento oportuno',
                'P5_8_3': 'Atención rápida de fallas'
            }
            
            # Reutilizamos la función procesar_y_graficar con color representativo (Amarillo/Dorado)
            procesar_y_graficar(df, atributos_luz, "Evaluación de Atributos del Servicio", color="#F39C12")

    st.markdown("---")
    st.caption("📌 Fuente: ENCIG 2023, INEGI.")

except Exception as e:
    st.error(f"Error: {e}")
