import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# 1. Configuración de la página
st.set_page_config(page_title="Tablero ENCIG Morelos", layout="wide")

# 2. Estilo Visual Mejorado
st.markdown("""
    <style>
    .stApp { background-color: #F4F7F9; }
    [data-testid="stMetricValue"] { font-size: 40px; color: #004b8d; font-weight: bold; }
    .plot-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 25px;
    }
    .footer {
        position: fixed;
        bottom: 10px;
        right: 10px;
        font-size: 12px;
        color: #666;
        background: rgba(255,255,255,0.8);
        padding: 5px 10px;
        border-radius: 5px;
    }
    h1 { color: #004b8d !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE APOYO ---

def generar_pdf(tematica, porcentaje, atributos):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado - Usamos Helvetica (estándar en FPDF)
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(0, 75, 141)
    pdf.cell(190, 10, f"Reporte de Satisfaccion: {tematica}", ln=True, align='C')
    
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(100)
    pdf.cell(190, 10, "Fuente: ENCIG 2023 - Estado de Morelos", ln=True, align='C')
    pdf.ln(10)
    
    # Metrica
    pdf.set_fill_color(240, 247, 249)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_text_color(0)
    pdf.cell(190, 15, f"Satisfaccion General del Servicio: {porcentaje:.1f}%", ln=True, fill=True, align='L')
    pdf.ln(5)
    
    # Tabla
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(140, 10, "Atributo Evaluado", border=1, align='C')
    pdf.cell(50, 10, "Cumplimiento (%)", border=1, align='C', ln=True)
    
    pdf.set_font("Helvetica", size=10)
    for item in atributos:
        pdf.cell(140, 8, item['Atributo'], border=1)
        pdf.cell(50, 8, f"{item['Porcentaje']:.1f}%", border=1, ln=True, align='C')
        
    pdf.ln(20)
    pdf.set_font("Helvetica", 'I', 8)
    pdf.multi_cell(190, 5, "Nota: Este reporte fue generado automaticamente a partir de los microdatos de la ENCIG procesados con el factor de expansion FAC_P18.")
    
    return pdf.output()

def renderizar_seccion(df, titulo, col_sat, cols_attr, labels_attr, color_principal, color_barras="#168AAD", umbral=8, filtro_col=None):
    # Cálculos
    df[col_sat] = pd.to_numeric(df[col_sat], errors='coerce')
    df_base = df[df[filtro_col] == 1].copy() if filtro_col else df.copy()
    df_sat_valid = df_base[(df_base[col_sat] >= 0) & (df_base[col_sat] <= 10)].copy()
    
    if not df_sat_valid.empty:
        total_poblacion = df_sat_valid['FAC_P18'].sum()
        pob_satisfecha = df_sat_valid[df_sat_valid[col_sat] >= umbral]['FAC_P18'].sum()
        porcentaje_oficial = (pob_satisfecha / total_poblacion) * 100
    else:
        porcentaje_oficial = 0

    col_t, col_m = st.columns([2, 1])
    with col_t:
        st.title(f"{titulo}")
    with col_m:
        st.metric(label="Satisfacción Oficial (%)", value=f"{porcentaje_oficial:.1f}%")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        st.subheader("📍 Nivel de Satisfacción")
        fig_sat = px.bar(
            pd.DataFrame({'C':['Población Satisfecha'], 'V':[porcentaje_oficial]}), 
            x='V', y='C', orientation='h', range_x=[0,100], text_auto='.1f', 
            color_discrete_sequence=[color_principal]
        )
        fig_sat.update_layout(height=300, xaxis_title="%", yaxis_title="", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_sat, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        st.subheader("✅ Evaluación de Atributos")
        res = []
        for c, n in zip(cols_attr, labels_attr):
            df[c] = pd.to_numeric(df[c], errors='coerce')
            df_v = df[df[c].isin([1, 2, 9])]
            total = df_v['FAC_P18'].sum()
            exito = 2 if any(palabra in n for palabra in ['Fugas', 'Fallas', 'Mantenimiento', 'Baches']) else 1
            pob = df_v[df_v[c] == exito]['FAC_P18'].sum()
            res.append({'Atributo': n, 'Porcentaje': (pob/total)*100 if total > 0 else 0})

        fig_attr = px.bar(pd.DataFrame(res), x='Porcentaje', y='Atributo', orientation='h', text_auto='.1f', color_discrete_sequence=[color_barras])
        fig_attr.update_layout(height=300, xaxis_range=[0,110], margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_attr, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.session_state.ultimos_datos = {
        'titulo': titulo,
        'porcentaje': porcentaje_oficial,
        'atributos': res
    }

@st.cache_data
def load_data():
    return pd.read_excel('Consolidado_Morelos_Bases_Final.xlsx')

# --- EJECUCIÓN PRINCIPAL ---

try:
    df = load_data()

    with st.sidebar:
        st.image("https://www.inegi.org.mx/app/img/logoin_v2.png", width=150)
        st.title("ENCIG 2023")
        categoria = st.selectbox("1. Categoría:", ["1. Servicios Públicos Básicos", "5. Corrupción"])

        if categoria == "1. Servicios Públicos Básicos":
            tematica = st.radio("2. Temática:", 
                ["Agua potable", "Drenaje y alcantarillado", "Alumbrado público", "Recolección de Basura", "Policia", "Parques y jardínes públicos", "Calles y avenidas", "Carreteras y Caminos Libres"])

    if tematica == "Agua potable":
        renderizar_seccion(df, "Agua Potable", 'P4_1B', ['P4_1_1', 'P4_1_2', 'P4_1_3', 'P4_1_4', 'P4_1_5'], ['Suministro Constante', 'Agua Pura', 'Bebible', 'Sin Fugas', 'Red Pública'], '#0077B6', umbral=7, filtro_col='P4_1_5')
    elif tematica == "Drenaje y alcantarillado":
        renderizar_seccion(df, "Drenaje y Alcantarillado", 'P4_2B', ['P4_2_1', 'P4_2_3', 'P4_2_4'], ['Conexión Red', 'Sin Fugas', 'Mantenimiento'], '#52B788', umbral=8)
    elif tematica == "Alumbrado público":
        renderizar_seccion(df, "Alumbrado Público", 'P4_3B', ['P4_3_1', 'P4_3_2', 'P4_3_3'], ['Iluminación Adecuada', 'Mantenimiento', 'Sin Fallas'], '#FFB703', color_barras='#FB8500', umbral=8)
    elif tematica == "Recolección de Basura":
        renderizar_seccion(df, "Recolección de Basura", 'P4_5B', ['P4_5_1', 'P4_5_2', 'P4_5_3'], ['Oportuna', 'Servicio Gratuito', 'Frecuencia Adecuada'], '#2D6A4F', umbral=8)
    elif tematica == "Policia":
        renderizar_seccion(df, "Seguridad Pública (Policía)", 'P4_6B', ['P4_6_1', 'P4_6_2'], ['Disposición Ayuda', 'Sensación Seguridad'], '#003049', umbral=8)
    elif tematica == "Parques y jardínes públicos":
        renderizar_seccion(df, "Parques y Jardines", 'P4_4B', ['P4_4_1', 'P4_4_2', 'P4_4_3', 'P4_4_4'], ['Horarios Accesibles', 'Cercanía', 'Limpieza e Imagen', 'Seguridad'], '#2D6A4F', color_barras='#74C69D', umbral=8)
    elif tematica == "Calles y avenidas":
        renderizar_seccion(df, "Calles y Avenidas", 'P4_7B', ['P4_7_1', 'P4_7_2', 'P4_7_3'], ['En buen estado', 'Reparación de baches', 'Semáforos funcionales'], '#495057', color_barras='#6C757D', umbral=8)
    elif tematica == "Carreteras y Caminos Libres":
        renderizar_seccion(df, "Carreteras y Caminos Libres", 'P4_8B', ['P4_8_1', 'P4_8_2', 'P4_8_3'], ['Sin Baches', 'Seguridad/Delincuencia', 'Comunicación'], '#212529', color_barras='#ADB5BD', umbral=8)

    # Notas al pie
    st.markdown("---")
    col_nota1, col_nota2 = st.columns(2)
    with col_nota1:
        st.caption("📌 **Nota Metodológica:**")
        st.markdown("<div style='font-size: 0.8rem; color: #555;'>La 'Satisfacción Oficial' se calcula sumando las frecuencias expandidas de las categorías aprobatorias...</div>", unsafe_allow_html=True)
    with col_nota2:
        st.caption("🏢 **Fuente de Datos:**")
        st.markdown("<div style='font-size: 0.8rem; color: #555;'>Información obtenida de la <b>ENCIG 2023</b> (INEGI).</div>", unsafe_allow_html=True)

    # Botón PDF en el Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Exportar Resultados")
    if st.sidebar.button("Generar Reporte PDF"):
        if 'ultimos_datos' in st.session_state:
            d = st.session_state.ultimos_datos
            pdf_output = generar_pdf(d['titulo'], d['porcentaje'], d['atributos'])
            st.sidebar.download_button(label="⬇️ Descargar archivo", data=bytes(pdf_output), file_name=f"Reporte_{tematica}.pdf", mime="application/pdf")

except Exception as e:
    st.error(f"Error: {e}")