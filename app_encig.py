import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Tablero ENCIG Morelos", layout="wide")

# 2. Estilo Visual
st.markdown("""
    <style>
    .stApp { background-color: #F4F7F9; }
    [data-testid="stMetricValue"] { font-size: 40px; color: #004b8d; font-weight: bold; }
    .plot-container { background-color: white; padding: 20px; border-radius: 10px; 
                      box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px; }
    h1 { color: #004b8d !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Encabezado Institucional
st.markdown("""
    <div style='text-align: center; padding: 10px; border-bottom: 2px solid #004b8d; margin-bottom: 20px;'>
        <h1 style='margin: 0; font-size: 28px;'>Encuesta Nacional de Calidad e Impacto Gubernamental (ENCIG)</h1>
        <p style='color: #666; font-style: italic;'>Presentación de resultados para el Estado de Morelos</p>
    </div>
    """, unsafe_allow_html=True)

# --- FUNCIONES MAESTRAS ---

def procesar_y_graficar(df, mapeo, titulo, color="#8E24AA", altura=500, es_problema=False):
    """Procesa columnas de la ENCIG y genera la gráfica de barras con lógica corregida."""
    res = []
    df['FAC_P18'] = pd.to_numeric(df['FAC_P18'], errors='coerce').fillna(0)
    total_pob_estado = df['FAC_P18'].sum()
    
    for col, nombre in mapeo.items():
        if col in df.columns:
            val_col = pd.to_numeric(df[col], errors='coerce')
            
            if es_problema:
                # Lógica para incidencia de problemas sobre población total
                pob_si = df[val_col == 1]['FAC_P18'].sum()
                porc = (pob_si / total_pob_estado * 100) if total_pob_estado > 0 else 0
            else:
                # Lógica para servicios (basada en usuarios reales)
                df_v = df[val_col.isin([1, 2, 9])]
                total_servicio = df_v['FAC_P18'].sum()
                # Criterio de éxito: 2 para fallas/saturación/deficiencia, 1 para el resto
                palabras_negativas = ['fuga', 'falla', 'mantenimiento', 'bache', 'saturación', 'deficiencia']
                exito = 2 if any(p in nombre.lower() for p in palabras_negativas) else 1
                pob_si = df_v[val_col == exito]['FAC_P18'].sum()
                porc = (pob_si / total_servicio * 100) if total_servicio > 0 else 0
            
            res.append({'Concepto': nombre, 'Porcentaje': porc})
    
    df_plot = pd.DataFrame(res).sort_values(by='Porcentaje', ascending=True)
    
    st.markdown(f"### {titulo}")
    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
    fig = px.bar(df_plot, x='Porcentaje', y='Concepto', orientation='h', text_auto='.1f', color_discrete_sequence=[color])
    fig.update_layout(height=max(300, altura), xaxis_range=[0, 105], margin=dict(l=0, r=50, t=20, b=20), xaxis_title="%", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def renderizar_satisfaccion(df, col_sat, titulo, color, umbral=8, filtro_col=None):
    """Calcula y muestra la métrica y barra de satisfacción general."""
    df[col_sat] = pd.to_numeric(df[col_sat], errors='coerce')
    df_base = df[df[filtro_col] == 1] if filtro_col else df
    df_v = df_base[(df_base[col_sat] >= 0) & (df_base[col_sat] <= 10)]
    
    total = df_v['FAC_P18'].sum()
    porc = (df_v[df_v[col_sat] >= umbral]['FAC_P18'].sum() / total * 100) if total > 0 else 0
    
    col1, col2 = st.columns([2, 1])
    with col1: st.title(titulo)
    with col2: st.metric("Satisfacción Oficial (%)", f"{porc:.1f}%")
    
    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
    fig = px.bar(pd.DataFrame({'C':['Población Satisfecha'], 'V':[porc]}), x='V', y='C', 
                 orientation='h', range_x=[0,100], text_auto='.1f', color_discrete_sequence=[color])
    fig.update_layout(height=200, xaxis_title="%", yaxis_title="", margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_excel('Consolidado_Morelos_Bases_Final.xlsx')

# --- EJECUCIÓN PRINCIPAL ---

try:
    df = load_data()

    with st.sidebar:
        try: st.image("logo_encig.png", width=200)
        except: st.write("### ENCIG 2023")
        
        st.title("Menú de Navegación")
        categoria = st.selectbox("1. Categoría:", ["1. Servicios Públicos Básicos", "2. Problemas Importantes", "3. Servicios Públicos Bajo Demanda"])
        
        tematica = None
        if categoria == "1. Servicios Públicos Básicos":
            tematica = st.radio("2. Temática:", ["Agua potable", "Drenaje y alcantarillado", "Alumbrado público", "Recolección de Basura", "Policia", "Parques y jardínes públicos", "Calles y avenidas", "Carreteras y Caminos Libres"])
        elif categoria == "3. Servicios Públicos Bajo Demanda":
            tematica = st.radio("2. Temática:", ["Servicios de salud en el IMSS"])

    if categoria == "1. Servicios Públicos Básicos":
        config = {
            "Agua potable": ('P4_1B', ['P4_1_1','P4_1_2','P4_1_3','P4_1_4','P4_1_5'], ['Suministro Constante','Agua Pura','Bebible','Sin Fugas','Red Pública'], '#0077B6', 7, 'P4_1_5'),
            "Drenaje y alcantarillado": ('P4_2B', ['P4_2_1','P4_2_3','P4_2_4'], ['Conexión Red','Sin Fugas','Mantenimiento'], '#52B788', 8, None),
            "Alumbrado público": ('P4_3B', ['P4_3_1', 'P4_3_2', 'P4_3_3'], ['Iluminación Adecuada', 'Mantenimiento', 'Sin Fallas'], '#FFB703', 8, None),
            "Recolección de Basura": ('P4_5B', ['P4_5_1', 'P4_5_2', 'P4_5_3'], ['Oportuna', 'Servicio Gratuito', 'Frecuencia Adecuada'], '#2D6A4F', 8, None),
            "Policia": ('P4_6B', ['P4_6_1', 'P4_6_2'], ['Disposición Ayuda', 'Sensación Seguridad'], '#003049', 8, None),
            "Parques y jardínes públicos": ('P4_4B', ['P4_4_1', 'P4_4_2', 'P4_4_3', 'P4_4_4'], ['Horarios Accesibles', 'Cercanía', 'Limpieza e Imagen', 'Seguridad'], '#2D6A4F', 8, None),
            "Calles y avenidas": ('P4_7B', ['P4_7_1', 'P4_7_2', 'P4_7_3'], ['En buen estado', 'Reparación de baches', 'Semáforos funcionales'], '#495057', 8, None),
            "Carreteras y Caminos Libres": ('P4_8B', ['P4_8_1', 'P4_8_2', 'P4_8_3'], ['Sin Baches', 'Seguridad/Delincuencia', 'Comunicación'], '#212529', 8, None)
        }
        if tematica in config:
            c = config[tematica]
            renderizar_satisfaccion(df, c[0], tematica, c[3], c[4], c[5])
            procesar_y_graficar(df, dict(zip(c[1], c[2])), "Evaluación de Atributos", color="#168AAD")

    elif categoria == "2. Problemas Importantes":
        problemas_map = {
            'P3_1_01': 'Mal desempeño del gobierno', 'P3_1_02': 'Pobreza', 
            'P3_1_03': 'Corrupción', 'P3_1_04': 'Desempleo', 
            'P3_1_05': 'Inseguridad y delincuencia', 'P3_1_06': 'Mala aplicación de la ley', 
            'P3_1_07': 'Desastres naturales', 'P3_1_08': 'Baja calidad de la educación pública', 
            'P3_1_09': 'Mala atención en centros de salud', 'P3_1_10': 'Falta de coordinación entre niveles de gobierno', 
            'P3_1_11': 'Falta de rendición de cuentas'
        }
        procesar_y_graficar(df, problemas_map, "🚨 Problemas más importantes en la entidad", altura=600, es_problema=True)

    elif categoria == "3. Servicios Públicos Bajo Demanda":
        if tematica == "Servicios de salud en el IMSS":
            renderizar_satisfaccion(df, 'P5_4B', "Salud en el IMSS", "#8E24AA")
            salud_map = {
                'P5_4_01': 'Atención Inmediata', 'P5_4_02': 'Trato Respetuoso', 
                'P5_4_03': 'Información oportuna', 'P5_4_04': 'Instalaciones adecuadas', 
                'P5_4_05': 'Limpieza', 'P5_4_06': 'Medicamentos', 
                'P5_4_07': 'Atención sin requerir materiales o medicamentos',
                'P5_4_08': 'Médicos Suficientes', 'P5_4_09': 'Médicos Capacitados', 
                'P5_4_10': 'Hospitales sin saturación', 'P5_4_11': 'Sin deficiencias'
            }
            procesar_y_graficar(df, salud_map, "Evaluación de Atributos del IMSS", color="#8E24AA", altura=600)

    st.markdown("---")
    st.caption("📌 **Nota:** Porcentajes calculados con factor de expansión (FAC_P18). Fuente: ENCIG 2023 (INEGI).")

except Exception as e:
    st.error(f"Error crítico: {e}")
