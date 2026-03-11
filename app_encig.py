import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Tablero ENCIG Morelos", layout="wide")

# 2. Estilo Visual Personalizado
st.markdown("""
    <style>
    .stApp { background-color: #F4F7F9; }
    [data-testid="stMetricValue"] { font-size: 32px; color: #004b8d; font-weight: bold; }
    .plot-container { background-color: white; padding: 20px; border-radius: 10px; 
                      box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px; }
    h1 { color: #004b8d !important; border: none !important; }
    .metric-card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 10px; 
        border-top: 4px solid #004b8d; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES MAESTRAS (Definidas al inicio para evitar errores de importación) ---

def procesar_y_graficar(df, mapeo, titulo, color="#8E24AA", altura=500, es_problema=False):
    """Calcula porcentajes usando factor de expansión y genera gráficas horizontales."""
    res = []
    df['FAC_P18'] = pd.to_numeric(df['FAC_P18'], errors='coerce').fillna(0)
    total_pob_estado = df['FAC_P18'].sum()
    
    for col, nombre in mapeo.items():
        if col in df.columns:
            val_col = pd.to_numeric(df[col], errors='coerce')
            if es_problema:
                # Población que considera eso un problema (valor 1)
                pob_si = df[val_col == 1]['FAC_P18'].sum()
                porc = (pob_si / total_pob_estado * 100) if total_pob_estado > 0 else 0
            else:
                # Población usuaria satisfecha
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
    """Métrica de satisfacción general con barra de progreso."""
    df[col_sat] = pd.to_numeric(df[col_sat], errors='coerce')
    df_base = df[df[filtro_col] == 1] if filtro_col else df
    df_v = df_base[(df_base[col_sat] >= 0) & (df_base[col_sat] <= 10)]
    total = df_v['FAC_P18'].sum()
    porc = (df_v[df_v[col_sat] >= umbral]['FAC_P18'].sum() / total * 100) if total > 0 else 0
    
    col1, col2 = st.columns([2, 1])
    with col1: st.title(titulo)
    with col2: st.metric("Satisfacción (%)", f"{porc:.1f}%")
    
    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
    fig = px.bar(pd.DataFrame({'C':['Satisfechos'], 'V':[porc]}), x='V', y='C', 
                 orientation='h', range_x=[0,100], text_auto='.1f', color_discrete_sequence=[color])
    fig.update_layout(height=150, xaxis_title="%", yaxis_title="", margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def calcular_sat_kpi(df, col_sat):
    """Retorna solo el número de satisfacción para las tarjetas de salud."""
    df[col_sat] = pd.to_numeric(df[col_sat], errors='coerce')
    df_v = df[(df[col_sat] >= 0) & (df[col_sat] <= 10)]
    total = df_v['FAC_P18'].sum()
    return (df_v[df_v[col_sat] >= 8]['FAC_P18'].sum() / total * 100) if total > 0 else 0

@st.cache_data
def load_data():
    return pd.read_excel('Consolidado_Morelos_Bases_Final.xlsx')

# --- LÓGICA DE NAVEGACIÓN Y RENDERIZADO ---

try:
    df = load_data()
    
    # Título Principal
    st.markdown("<div style='text-align: center;'><h1>ENCIG 2023 - Estado de Morelos</h1></div>", unsafe_allow_html=True)

    with st.sidebar:
        st.title("Navegación")
        categoria = st.selectbox("Seleccione Categoría:", 
                                ["1. Servicios Públicos Básicos", 
                                 "2. Problemas Importantes", 
                                 "3. Servicios Públicos Bajo Demanda"])
        
        if categoria == "1. Servicios Públicos Básicos":
            tematica = st.radio("Temática:", ["Agua potable", "Drenaje y alcantarillado", "Alumbrado público", "Recolección de Basura", "Policía", "Parques y jardines", "Calles y avenidas", "Carreteras"])
        elif categoria == "2. Problemas Importantes":
            tematica = "Principales Problemas"
        else:
            tematica = st.radio("Temática:", ["Comparativa de Salud"])

    # --- RENDERIZADO DE SECCIONES ---

    if categoria == "1. Servicios Públicos Básicos":
        # Diccionario de configuración para restaurar la funcionalidad de básicos
        config_basicos = {
            "Agua potable": ('P4_1B', ['P4_1_1','P4_1_2','P4_1_3','P4_1_4','P4_1_5'], ['Suministro Constante','Agua Clara','Bebible','Sin Fugas','Red Pública'], '#0077B6', 7, 'P4_1_5'),
            "Drenaje y alcantarillado": ('P4_2B', ['P4_2_1','P4_2_3','P4_2_4'], ['Conexión Red','Sin Fugas','Mantenimiento'], '#52B788', 8, None),
            "Alumbrado público": ('P4_3B', ['P4_3_1','P4_3_2','P4_3_3'], ['Iluminación Adecuada','Mantenimiento','Sin Fallas'], '#FFB703', 8, None),
            "Recolección de Basura": ('P4_5B', ['P4_5_1','P4_5_2','P4_5_3'], ['Oportuna','Gratuita','Frecuencia Adecuada'], '#2D6A4F', 8, None),
            "Policía": ('P4_6B', ['P4_6_1','P4_6_2'], ['Disposición a Ayudar','Sensación de Seguridad'], '#003049', 8, None),
            "Parques y jardines": ('P4_4B', ['P4_4_1','P4_4_2','P4_4_3','P4_4_4'], ['Horarios Accesibles','Cercanía','Limpieza','Seguridad'], '#2D6A4F', 8, None),
            "Calles y avenidas": ('P4_7B', ['P4_7_1','P4_7_2','P4_7_3'], ['En buen estado','Reparación de baches','Semáforos funcionales'], '#495057', 8, None),
            "Carreteras": ('P4_8B', ['P4_8_1','P4_8_2','P4_8_3'], ['Sin Baches','Seguridad','Señalización/Comunicación'], '#212529', 8, None)
        }
        
        c = config_basicos[tematica]
        renderizar_satisfaccion(df, c[0], f"{tematica}", c[3], c[4], c[5])
        procesar_y_graficar(df, dict(zip(c[1], c[2])), "Evaluación de Atributos del Servicio", color="#168AAD")

    elif categoria == "2. Problemas Importantes":
        problemas_map = {
            'P3_1_01': 'Mal desempeño del gobierno', 'P3_1_02': 'Pobreza', 
            'P3_1_03': 'Corrupción', 'P3_1_04': 'Desempleo', 
            'P3_1_05': 'Inseguridad y delincuencia', 'P3_1_06': 'Mala aplicación de la ley', 
            'P3_1_07': 'Desastres naturales', 'P3_1_08': 'Baja calidad de la educación pública', 
            'P3_1_09': 'Mala atención en centros de salud y hospitales públicos', 'P3_1_10': 'Falta de coordinación entre niveles de gobierno', 
            'P3_1_11': 'Falta de Rendición de Cuentas'
        }
        procesar_y_graficar(df, problemas_map, "🚨 Problemas más importantes percibidos en la entidad", color="#C0392B", altura=600, es_problema=True)

    elif categoria == "3. Servicios Públicos Bajo Demanda":
        if tematica == "Comparativa de Salud":
            st.title("Comparativa de Servicios de Salud")
            
            # Leyenda única para las tres tarjetas
            st.markdown("<p style='text-align: center; color: #666; font-weight: bold; margin-bottom: -10px;'>Porcentaje de satisfacción</p>", unsafe_allow_html=True)
            
            # Tarjetas de Satisfacción (KPIs)
            col1, col2, col3 = st.columns(3)
            with col1: 
                st.markdown(f'<div class="metric-card"><p style="margin:0; color:#666; font-size: 14px;">IMSS</p><h3 style="margin:0;">{calcular_sat_kpi(df, "P5_4B"):.1f}%</h3></div>', unsafe_allow_html=True)
            with col2: 
                st.markdown(f'<div class="metric-card"><p style="margin:0; color:#666; font-size: 14px;">ISSSTE</p><h3 style="margin:0;">{calcular_sat_kpi(df, "P5_5B"):.1f}%</h3></div>', unsafe_allow_html=True)
            with col3: 
                st.markdown(f'<div class="metric-card"><p style="margin:0; color:#666; font-size: 14px;">Estatal</p><h3 style="margin:0;">{calcular_sat_kpi(df, "P5_7B"):.1f}%</h3></div>', unsafe_allow_html=True)
            
            # ... resto del código de la gráfica de barras ...
            
            # Atributos Comparativos (11 columnas)
            inst_config = {'P5_4': 'IMSS', 'P5_5': 'ISSSTE', 'P5_7': 'Salud Estatal'}
            atributos = {
                '_01': 'Atención inmediata', '_02': 'Trato Respetuoso', '_03': 'Información Oportuna', 
                '_04': 'Instalaciones Adecuadas y Equipo Necesario', '_05': 'Instalaciones Limpias y Ordenadas', '_06': 'Disposición de Medicamentos', 
                '_07': 'Atención Sin Requerir Materiales o Medicamentos', '_08': 'Médicos suficientes', '_09': 'Médicos capacitados', 
                '_10': 'Sin saturación', '_11': 'Sin deficiencias'
            }
            
            datos_c = []
            for suf, nom in atributos.items():
                for pref, inst_n in inst_config.items():
                    col_name = f"{pref}{suf}"
                    if col_name in df.columns:
                        val = pd.to_numeric(df[col_name], errors='coerce')
                        df_v = df[val.isin([1, 2, 9])]
                        total_n = df_v['FAC_P18'].sum()
                        # Lógica: Éxito es 2 para deficiencias/saturación, 1 para el resto
                        exito_n = 2 if suf in ['_10', '_11'] else 1
                        porc_n = (df_v[val == exito_n]['FAC_P18'].sum() / total_n * 100) if total_n > 0 else 0
                        datos_c.append({'Atributo': nom, 'Institución': inst_n, 'Porcentaje': porc_n})
            
            st.markdown('<div class="plot-container">', unsafe_allow_html=True)
            fig_c = px.bar(pd.DataFrame(datos_c), x='Atributo', y='Porcentaje', color='Institución', 
                           barmode='group', text_auto='.1f',
                           color_discrete_map={'IMSS': '#8E24AA', 'ISSSTE': '#1C3D6E', 'Salud Estatal': '#D81B60'})
            fig_c.update_layout(height=550, xaxis_tickangle=-45, yaxis_range=[0, 110])
            st.plotly_chart(fig_c, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption("📌 Nota: Los resultados utilizan el factor de expansión poblacional (FAC_P18). Fuente: ENCIG 2023, INEGI.")

except Exception as e:
    st.error(f"Hubo un problema al cargar el tablero: {e}")
