import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np
from utils import mostrar_logo_inegi

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="ENSU - Morelos", layout="wide")

mostrar_logo_inegi()

# Inyectamos CSS para ocultar menús de Streamlit y dar aspecto profesional
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

st.title("🏙️ Percepción de Seguridad Pública Urbana (ENSU)")
st.caption("Fuente: Microdatos de INEGI - Análisis específico para el Estado de Morelos")
st.markdown("---")

# --- 2. FUNCIONES DE APOYO (Lógica de Negocio) ---

def limpiar_columnas_inegi(df_input, lista_columnas):
    df_result = df_input.copy()
    for col in lista_columnas:
        if col in df_result.columns:
            # Convertimos a string, quitamos el .0 y espacios
            df_result[col] = df_result[col].astype(str).str.replace('.0', '', regex=False).str.strip()
            # Tomamos solo el primer carácter para normalizar (evita '1.0' o '1 ')
            df_result[col] = df_result[col].str.get(0)
    return df_result

@st.cache_data
def cargar_data():
    ruta_archivo = os.path.join("data", "Master_ENSU_Morelos.parquet")
    try:
        with st.spinner("Actualizando indicadores estratégicos..."):
            return pd.read_parquet(ruta_archivo) if os.path.exists(ruta_archivo) else None
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

def crear_grafica_barras(df_plot, x_col, y_col, color_col, titulo, paleta):
    """Función maestra para mantener consistencia visual en todas las gráficas de barras."""
    fig = px.bar(
        df_plot, x=x_col, y=y_col, color=color_col,
        barmode='group', orientation='h',
        text=df_plot[x_col].apply(lambda x: f'{x:.1f}%'),
        title=titulo, color_discrete_sequence=paleta
    )
    fig.update_layout(
        xaxis_range=[0, 110], height=500,
        yaxis={'categoryorder': 'total ascending'},
        legend_title="Periodo", margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.update_traces(textposition='outside', textfont_size=10)
    return fig

# --- 3. PROCESAMIENTO DE DATOS ---
df_raw = cargar_data()

if df_raw is not None:
    cols_control = [
        'BP1_1', 'BP1_3', 'BP1_2_01', 'BP1_2_02', 'BP1_2_03', 'BP1_2_04', 
        'BP1_2_05', 'BP1_2_06', 'BP1_2_07', 'BP1_2_08', 'BP1_2_09', 'BP1_2_10', 
        'BP1_2_11', 'BP1_2_12', 'BP1_4_1', 'BP1_4_2', 'BP1_4_3', 'BP1_4_4', 
        'BP1_4_5', 'BP1_4_6', 'BP1_4_7', 'BP1_4_8', 'BP1_5_1', 'BP1_5_2', 
        'BP1_5_3', 'BP1_5_4', 'BP1_5_5', 'SEXO', 'BP4_1_1', 'BP4_1_2', 'BP4_1_3', 'BP4_1_4', 'BP4_1_5', 
    'BP4_1_6', 'BP4_1_7', 'BP4_1_8', 'BP4_1_9', 'SEXO', 'BP1_7_1', 'BP1_7_2', 'BP1_7_3', 'BP1_7_4', 'BP1_7_5', 'BP1_7_6',
    ]
    df = limpiar_columnas_inegi(df_raw, cols_control)

    # Sidebar: Filtros
    anio_sel = df['ANIO'].unique().tolist()
    
    # 2. El filtro de Trimestre ahora busca en todo el DataFrame
    trims_disponibles = sorted(df['TRIMESTRE'].unique())
    trim_sel = st.sidebar.multiselect("Trimestre(s)", options=trims_disponibles, default=trims_disponibles)
    
    st.sidebar.markdown("---")
    
    # Cambio a Selectbox estilo ENVIPE
    municipios_lista = sorted(df['NOM_MUN'].unique().tolist())
    mun_sel = st.sidebar.selectbox(
        "Municipio/Ciudad", 
        options=["Zona Metro"] + municipios_lista
    )

    mask = (df['ANIO'].isin(anio_sel)) & (df['TRIMESTRE'].isin(trim_sel))
    if mun_sel != "Zona Metro":
        mask &= (df['NOM_MUN'] == mun_sel)
    
    df_filtrado = df[mask]

    # --- 4. DASHBOARD: KPIs SUPERIORES ---
    if not df_filtrado.empty:
        map_orden = {"1er Trim": 1, "2do Trim": 2, "3er Trim": 3, "4to Trim": 4}
        df_temp = df_filtrado.copy()
        df_temp['orden'] = df_temp['TRIMESTRE'].map(map_orden)
        
        ultimo_anio = df_temp['ANIO'].max()
        ultimo_trim = df_temp[df_temp['ANIO'] == ultimo_anio].sort_values('orden')['TRIMESTRE'].iloc[-1]
        df_reciente = df_temp[(df_temp['ANIO'] == ultimo_anio) & (df_temp['TRIMESTRE'] == ultimo_trim)]
        
        pob_total_exp = df_reciente['FAC_SEL'].sum()
        
        if pob_total_exp > 0:
            pct_mal = (df_reciente[df_reciente['BP1_3'] == '3']['FAC_SEL'].sum() / pob_total_exp) * 100
            pct_peor = (df_reciente[df_reciente['BP1_3'] == '4']['FAC_SEL'].sum() / pob_total_exp) * 100
            pct_mejor = (df_reciente[df_reciente['BP1_3'] == '1']['FAC_SEL'].sum() / pob_total_exp) * 100
            
            st.markdown(f"#### 📊 Expectativas de Seguridad (Próximos 12 meses a partir de diciembre)")
            k1, k2, k3 = st.columns(3)
            k1.metric("Seguirá igual de MAL", f"{pct_mal:.1f}%")
            k2.metric("EMPEORARÁ", f"{pct_peor:.1f}%", delta=f"{(pct_mal + pct_peor):.1f}% Negativo", delta_color="inverse")
            k3.metric("MEJORARÁ", f"{pct_mejor:.1f}%")

    # --- 5. SECCIONES (TABS) ---
    tab1, tab2, tab3, tab5 = st.tabs(["🛡️ Percepción", "🏗️ Desempeño y Confianza", "⚠️ Acoso", "🏘️ Victimización"])

    with tab1:
        if not df_filtrado.empty:
            # Gráfica de Evolución (Líneas)
            df_g1 = df_filtrado.groupby(['ANIO', 'TRIMESTRE', 'BP1_1'])['FAC_SEL'].sum().reset_index()
            df_g1['Total'] = df_g1.groupby(['ANIO', 'TRIMESTRE'])['FAC_SEL'].transform('sum')
            df_g1['Porcentaje'] = (df_g1['FAC_SEL'] / df_g1['Total']) * 100
            
            map_seg = {'1': '1 Seguro', '2': '2 Inseguro'}
            df_g1['Respuesta'] = df_g1['BP1_1'].map(map_seg)
            
            fig1 = px.line(df_g1.sort_values(['ANIO', 'TRIMESTRE']), x='TRIMESTRE', y='Porcentaje', color='Respuesta', 
                           markers=True, title="Evolución de la Percepción de Seguridad",
                           color_discrete_map={'1 Seguro': '#4CAF50', '2 Inseguro': '#F44336', '9 No sabe': '#9E9E9E'})
            st.plotly_chart(fig1, use_container_width=True)

            # Diccionarios de Variables
            secciones = {
                "📍 Inseguridad por Lugares": {
                    "dict": {'BP1_2_01': 'Casa', 'BP1_2_02': 'Trabajo', 'BP1_2_03': 'Calle', 'BP1_2_04': 'Escuela', 'BP1_2_05': 'Mercado', 'BP1_2_06': 'Centro Comercial','BP1_2_07': 'Banco', 'BP1_2_08': 'Cajero', 'BP1_2_09': 'Transporte', 'BP1_2_10': 'Automóvil', 'BP1_2_11': 'Carretera', 'BP1_2_12': 'Parque'},
                    "paleta": px.colors.sequential.Reds_r, "filtro": '2'
                },
                "🔊 Conductas Antisociales": {
                    "dict": {'BP1_4_1': 'Vandalismo', 'BP1_4_2': 'Alcohol en calle', 'BP1_4_3': 'Robos', 'BP1_4_4': 'Bandas violentas', 'BP1_4_5': 'Venta o consumo de drogas', 'BP1_4_6': 'Disparos'},
                    "paleta": px.colors.qualitative.Bold, "filtro": '1'
                },
                "🚶 Cambio de Hábitos": {
                    "dict": {'BP1_5_1': 'Llevar cosas valor', 'BP1_5_2': 'Caminar noche', 'BP1_5_3': 'Visitar parientes', 'BP1_5_4': 'Menores solos', 'BP1_5_5': 'Otro'},
                    "paleta": px.colors.qualitative.Safe, "filtro": '1'
                }
            }

            for titulo, config in secciones.items():
                st.markdown("---")
                if "Lugares" in titulo:
                    st.info("Que tan insegura se siente la población por lugar.")
                if "Hábitos" in titulo:
                    st.info("Porcentaje de la población que ha dejado de hacer actividades recurrentes por motivo de inseguridad.")
                if "Antisociales" in titulo:
                    st.info("Porcentaje de la población que ha detectado situaciones de riesgo en su entorno.")
                res_list = []
                for col, nom in config["dict"].items():
                    if col in df_filtrado.columns:
                        for trim in trim_sel:
                            df_t = df_filtrado[df_filtrado['TRIMESTRE'] == trim]
                            df_v = df_t[df_t[col].isin(['1', '2'])]
                            if not df_v.empty:
                                si = df_v[df_v[col] == config["filtro"]]['FAC_SEL'].sum()
                                tot = df_v['FAC_SEL'].sum()
                                res_list.append({titulo.split()[-1]: nom, 'Trimestre': trim, 'Porcentaje': (si/tot)*100})
                
                if res_list:
                    df_p = pd.DataFrame(res_list)
                    st.plotly_chart(crear_grafica_barras(df_p, 'Porcentaje', titulo.split()[-1], 'Trimestre', titulo, config["paleta"]), use_container_width=True)

    # --- SECCIÓN 2: Desempeño y Problemas de la Ciudad ---
    with tab2:
        st.header("📈 Tendencia de Efectividad Gubernamental")
        st.info("Comparativa trimestral: Opinión sobre qué tan efectivo ha sido el gobierno para resolver los principales problemas detectados por la población.")

        lista_efectividad = []

        if not df_filtrado.empty:
            # 1. Procesamiento por cada trimestre seleccionado
            for trim in trim_sel:
                df_t = df_filtrado[df_filtrado['TRIMESTRE'] == trim].copy()
                
                # Limpieza de la columna BP3_2
                df_t['BP3_2'] = df_t['BP3_2'].astype(str).str.replace('.0', '', regex=False).str.strip()
                
                # Cálculo de grupos (Excluyendo '9' No sabe)
                total_valido = df_t[df_t['BP3_2'].isin(['1', '2', '3', '4'])]['FAC_SEL'].sum()
                
                if total_valido > 0:
                    # Grupo Positivo: Muy / Algo efectivo
                    pos_sum = df_t[df_t['BP3_2'].isin(['1', '2'])]['FAC_SEL'].sum()
                    lista_efectividad.append({
                        'Trimestre': trim,
                        'Percepción': 'Positiva (Muy/Algo)',
                        'Porcentaje': (pos_sum / total_valido) * 100
                    })
                    
                    # Grupo Negativo: Poco / Nada efectivo
                    neg_sum = df_t[df_t['BP3_2'].isin(['3', '4'])]['FAC_SEL'].sum()
                    lista_efectividad.append({
                        'Trimestre': trim,
                        'Percepción': 'Negativa (Poco/Nada)',
                        'Porcentaje': (neg_sum / total_valido) * 100
                    })

            if lista_efectividad:
                df_lineas = pd.DataFrame(lista_efectividad)
                
                # Asegurar orden cronológico en el eje X
                orden_trim = ['1er Trim', '2do Trim', '3er Trim', '4to Trim']
                df_lineas['Trimestre'] = pd.Categorical(df_lineas['Trimestre'], categories=orden_trim, ordered=True)
                df_lineas = df_lineas.sort_values('Trimestre')

                # 2. Creación de la gráfica de líneas
                fig_lineas = px.line(
                    df_lineas,
                    x='Trimestre',
                    y='Porcentaje',
                    color='Percepción',
                    markers=True, # Añade puntos en cada trimestre
                    text=df_lineas['Porcentaje'].apply(lambda x: f'{x:.1f}%'),
                    title="Evolución de la Percepción de Efectividad Gubernamental",
                    color_discrete_map={
                        'Positiva (Muy/Algo)': '#2ECC71', # Verde
                        'Negativa (Poco/Nada)': '#E74C3C'  # Rojo
                    },
                    category_orders={"Trimestre": orden_trim}
                )

                fig_lineas.update_traces(textposition="top center")
                fig_lineas.update_layout(
                    yaxis_range=[0, 105], # Escala de 0 a 100
                    xaxis_title=None,
                    yaxis_title="Porcentaje (%)",
                    hovermode="x unified"
                )

                st.plotly_chart(fig_lineas, use_container_width=True)
            else:
                st.warning("No hay datos suficientes para generar la línea de tendencia.")
        
        st.markdown("---")
        st.header("🏙️ Problemática Urbana")
        st.info("Porcentaje de la población que identifica los siguientes temas como los problemas más importantes.")

        dict_problemas = {
            'BP3_1_01': 'Fallas en suministro de agua',
            'BP3_1_02': 'Deficiencias en red de drenaje',
            'BP3_1_03': 'Colaredas tapadas',
            'BP3_1_04': 'Falta de tratamiento de aguas residuales',
            'BP3_1_05': 'Alumbrado público deficiente',
            'BP3_1_06': 'Ineficiencia en servicio de recolección de basura',
            'BP3_1_07': 'Mercados en mal estado',
            'BP3_1_08': 'Embotellamientos frecuentes',
            'BP3_1_09': 'Problemas de salud por mal manejo de rastros',
            'BP3_1_10': 'Baches en calles/avenidas',
            'BP3_1_11': 'Parques y jardines descuidados',
            'BP3_1_12': 'Delincuencia (robos/extorsión)',
            'BP3_1_13': 'Transporte público deficiente',
            'BP3_1_14': 'Hospitales saturados',
        }

        lista_problemas = []

        if not df_filtrado.empty:
            for col, nombre in dict_problemas.items():
                if col in df_filtrado.columns:
                    for trim in trim_sel:
                        df_t = df_filtrado[df_filtrado['TRIMESTRE'] == trim].copy()
                        
                        # Limpieza de datos (Soporta 1, 1.0, "1")
                        respuestas = df_t[col].astype(str).str.replace('.0', '', regex=False).str.strip()
                        
                        si = df_t[respuestas == '1']['FAC_SEL'].sum()
                        tot = df_t['FAC_SEL'].sum()
                        
                        if tot > 0:
                            lista_problemas.append({
                                'Problema': nombre,
                                'Trimestre': trim,
                                'Porcentaje': (si / tot) * 100
                            })

            if lista_problemas:
                df_p_prob = pd.DataFrame(lista_problemas)
                
                # --- LÓGICA DE ORDENAMIENTO DE TRIMESTRES ---
                # Definimos el orden deseado para la leyenda y las barras
                orden_trimestres = ['1er Trim', '2do Trim', '3er Trim', '4to Trim']
                # Convertimos a categoría con el orden específico
                df_p_prob['Trimestre'] = pd.Categorical(df_p_prob['Trimestre'], categories=orden_trimestres, ordered=True)
                
                # Ordenamos el DF: Primero por Problema (alfabético/valor) y luego por Trimestre
                # Nota: Plotly dibuja de abajo hacia arriba según el orden del DF
                df_p_prob = df_p_prob.sort_values(by=['Problema', 'Trimestre'], ascending=[True, False])

                fig_prob = px.bar(
                    df_p_prob,
                    x='Porcentaje',
                    y='Problema',
                    color='Trimestre',
                    barmode='group',
                    orientation='h',
                    text_auto='.1f',
                    title="Principales Problemas Identificados en Morelos",
                    # Usamos una paleta secuencial para que se note la evolución temporal
                    color_discrete_sequence=px.colors.sequential.Blues_r, 
                    height=800,
                    # Forzamos a que la categoría respete el orden definido
                    category_orders={"Trimestre": orden_trimestres}
                )

                fig_prob.update_layout(
                    xaxis_title="Porcentaje de la Población (%)",
                    yaxis_title=None,
                    legend_title="Periodo",
                    # 'total ascending' asegura que el problema más grave esté arriba
                    yaxis={'categoryorder': 'total ascending'} 
                )

                st.plotly_chart(fig_prob, use_container_width=True)
            else:
                st.warning("No se encontraron registros afirmativos ('1') para estos problemas.")
        else:
            st.error("No hay datos cargados en el DataFrame filtrado.")

        # --- SECCIÓN 4: Corrupción (Semestral) ---
    with tab2:
        st.header("⚖️ Incidencia de Corrupción")
        st.info("Comparativa semestral de experiencias de corrupción en trámites y contacto con la policía.")

        lista_corrupcion = []

        if not df_filtrado.empty:
            # Filtramos solo los trimestres que tienen esta información
            trims_corrupcion = [t for t in trim_sel if "2do" in str(t) or "4to" in str(t)]

            for trim in trims_corrupcion:
                df_t = df_filtrado[df_filtrado['TRIMESTRE'] == trim].copy()
                
                # Mapeo de Trimestre a Semestre para la etiqueta
                etiqueta_semestre = "1er Semestre" if "2do" in str(trim) else "2do Semestre"
                
                # Limpieza de columnas
                for c in ['BP3_3', 'BP3_4', 'BP3_5', 'BP3_6']:
                    if c in df_t.columns:
                        df_t[c] = df_t[c].astype(str).str.replace('.0', '', regex=False).str.strip().str.get(0)

                # A. Corrupción en Trámites (Filtro BP3_3 == '1')
                df_tramite = df_t[df_t['BP3_3'] == '1']
                df_v_tramite = df_tramite[df_tramite['BP3_4'].isin(['1', '2'])]
                if not df_v_tramite.empty:
                    si = df_v_tramite[df_v_tramite['BP3_4'] == '1']['FAC_SEL'].sum()
                    tot = df_v_tramite['FAC_SEL'].sum()
                    if tot > 0:
                        lista_corrupcion.append({
                            'Sector': 'Trámites y Servicios',
                            'Temporalidad': etiqueta_semestre,
                            'Porcentaje': (si / tot) * 100
                        })

                # B. Corrupción Policial (Filtro BP3_5 == '1')
                df_policia = df_t[df_t['BP3_5'] == '1']
                df_v_policia = df_policia[df_policia['BP3_6'].isin(['1', '2'])]
                if not df_v_policia.empty:
                    si_p = df_v_policia[df_v_policia['BP3_6'] == '1']['FAC_SEL'].sum()
                    tot_p = df_v_policia['FAC_SEL'].sum()
                    if tot_p > 0:
                        lista_corrupcion.append({
                            'Sector': 'Seguridad Pública',
                            'Temporalidad': etiqueta_semestre,
                            'Porcentaje': (si_p / tot_p) * 100
                        })

            if lista_corrupcion:
                df_p_corr = pd.DataFrame(lista_corrupcion)
                
                # Definimos el orden de los semestres para la gráfica
                orden_sem = ["1er Semestre", "2do Semestre"]
                
                # Gráfica VERTICAL
                fig_corr = px.bar(
                    df_p_corr,
                    x='Sector',
                    y='Porcentaje',
                    color='Temporalidad',
                    barmode='group',
                    text_auto='.1f',
                    title="Prevalencia de Corrupción por Semestre (Morelos)",
                    color_discrete_map={
                        "1er Semestre": "#EF553B", 
                        "2do Semestre": "#B00020"
                    },
                    category_orders={"Temporalidad": orden_sem},
                    height=500
                )
                
                fig_corr.update_layout(
                    yaxis_title="Porcentaje (%)",
                    xaxis_title=None,
                    legend_title="Periodo Semestral"
                )
                
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.warning("No hay datos de corrupción para los periodos seleccionados.")

        st.header("🎖️ Desempeño de Autoridades de Seguridad")
        st.info("Porcentaje de la población que considera 'Muy' o 'Algo Efectivo' el desempeño de la institución (Datos Trimestrales).")

        # 1. Diccionario de Autoridades y sus columnas de Identificación (Filtro) y Desempeño (Métrica)
        # Asegúrate de que el orden sea el que deseas ver en el eje Y
        dict_autoridades = {
            'Policía Municipal':          {'id': 'BP1_7_1', 'perf': 'BP1_8_1'},
            'Policía Estatal':        {'id': 'BP1_7_2', 'perf': 'BP1_8_2'},
            'Guardia Nacional':{'id': 'BP1_7_3', 'perf': 'BP1_8_3'},
            'Ejercito': {'id': 'BP1_7_4', 'perf': 'BP1_8_4'},
            'Fuerza Aérea Mexicana':{'id': 'BP1_7_5', 'perf': 'BP1_8_5'},
            'Marina': {'id': 'BP1_7_6', 'perf': 'BP1_8_6'} # Opcional, pero suele medirse
        }

        lista_desempeño = []

        if not df_filtrado.empty:
            for trim in trim_sel:
                df_t = df_filtrado[df_filtrado['TRIMESTRE'] == trim].copy()
                
                # Pre-limpieza masiva de todas las columnas necesarias
                cols_to_clean = []
                for v in dict_autoridades.values():
                    cols_to_clean.extend([v['id'], v['perf']])
                
                for c in cols_to_clean:
                    if c in df_t.columns:
                        # Limpieza robusta para asegurar comparación textual ('1', '2', etc.)
                        df_t[c] = df_t[c].astype(str).str.replace('.0', '', regex=False).str.strip().str.get(0)

                # Procesamiento por autoridad
                for nombre, cols in dict_autoridades.items():
                    if cols['id'] in df_t.columns and cols['perf'] in df_t.columns:
                        
                        # A. APLICACIÓN DEL FILTRO DE IDENTIFICACIÓN: Solo quienes conocen a la institución (1='Sí')
                        df_identifica = df_t[df_t[cols['id']] == '1']
                        
                        if not df_identifica.empty:
                            # B. METODOLOGÍA DE EFECTIVIDAD: Muy (1) + Algo (2) Efectivo
                            # Denominador: Respuestas válidas (1, 2, 3, 4, 9)
                            df_v = df_identifica[df_identifica[cols['perf']].isin(['1', '2', '3', '4', '9'])]
                            
                            if not df_v.empty:
                                # Numerador: Ponderación de FAC_SEL de quienes dijeron Muy(1) o Algo(2) Efectivo
                                pos_sum = df_v[df_v[cols['perf']].isin(['1', '2'])]['FAC_SEL'].sum()
                                tot_sum = df_v['FAC_SEL'].sum()
                                
                                if tot_sum > 0:
                                    lista_desempeño.append({
                                        'Autoridad': nombre,
                                        'Trimestre': trim,
                                        'Efectividad Positiva': (pos_sum / tot_sum) * 100
                                    })

            if lista_desempeño:
                df_perf = pd.DataFrame(lista_desempeño)
                
                # Pivotar los datos para el formato de Mapa de Calor
                df_pivot = df_perf.pivot(index='Autoridad', columns='Trimestre', values='Efectividad Positiva')

                #Ordenar en modo descendente 
                df_pivot = df_pivot.reindex(df_pivot.mean(axis=1).sort_values(ascending=False).index) 
                
                # Asegurar orden cronológico en el eje X (Trimestres)
                orden_trim = ['1er Trim', '2do Trim', '3er Trim', '4to Trim']
                cols_reindex = [c for c in orden_trim if c in df_pivot.columns]
                df_pivot = df_pivot.reindex(columns=cols_reindex)

                # 2. Creación del Mapa de Calor con Plotly
                fig_perf = px.imshow(
                    df_pivot,
                    labels=dict(x="Periodo", y="Institución", color="Efectividad (%)"),
                    x=df_pivot.columns,
                    y=df_pivot.index,
                    color_continuous_scale='RdYlGn', # Semaforo
                    range_color=[25, 88],
                    text_auto='.1f',
                    title="Percepción de Efectividad en el Desempeño de Autoridades"
                )

                # Ajuste de layout
                fig_perf.update_layout(height=500)
                st.plotly_chart(fig_perf, use_container_width=True)
            else:
                st.warning("No se encontraron registros válidos para calcular la efectividad en los trimestres seleccionados.")
        st.header("🤝 Confianza en las Instituciones")
        st.info("Porcentaje de la población que manifiesta tener 'Mucha' o 'Algo' de confianza en la autoridad (Solo informantes que identifican a la institución).")

        # 1. Diccionario de Autoridades: ID (Filtro identificación) y Trust (Métrica confianza)
        dict_confianza = {
            'Policía Municipal':          {'id': 'BP1_7_1', 'trust': 'BP1_9_1'},
            'Policía Estatal':        {'id': 'BP1_7_2', 'trust': 'BP1_9_2'},
            'Guardia Nacional':{'id': 'BP1_7_3', 'trust': 'BP1_9_3'},
            'Ejército': {'id': 'BP1_7_4', 'trust': 'BP1_9_4'},
            'Fuerza Aérea Mexicana':{'id': 'BP1_7_5', 'trust': 'BP1_9_5'},
            'Marina ': {'id': 'BP1_7_6', 'trust': 'BP1_9_6'}
        }

        lista_confianza = []

        if not df_filtrado.empty:
            for trim in trim_sel:
                df_t = df_filtrado[df_filtrado['TRIMESTRE'] == trim].copy()
                
                # Limpieza de datos
                cols_clean = []
                for v in dict_confianza.values():
                    cols_clean.extend([v['id'], v['trust']])
                
                for c in cols_clean:
                    if c in df_t.columns:
                        df_t[c] = df_t[c].astype(str).str.replace('.0', '', regex=False).str.strip().str.get(0)

                for nombre, cols in dict_confianza.items():
                    if cols['id'] in df_t.columns and cols['trust'] in df_t.columns:
                        
                        # FILTRO: Solo quienes identifican a la autoridad (1='Sí')
                        df_id = df_t[df_t[cols['id']] == '1']
                        
                        if not df_id.empty:
                            # MÉTRICA: Mucha (1) + Algo (2) de confianza
                            # Denominador: Respuestas válidas (1, 2, 3, 4)
                            df_v = df_id[df_id[cols['trust']].isin(['1', '2', '3', '4', '9'])]
                            
                            if not df_v.empty:
                                si_confia = df_v[df_v[cols['trust']].isin(['1', '2'])]['FAC_SEL'].sum()
                                total_resp = df_v['FAC_SEL'].sum()
                                
                                if total_resp > 0:
                                    lista_confianza.append({
                                        'Autoridad': nombre,
                                        'Trimestre': trim,
                                        'Confianza (%)': (si_confia / total_resp) * 100
                                    })

            if lista_confianza:
                df_conf = pd.DataFrame(lista_confianza)
                
                # Pivotar para el Heatmap
                df_pivot_conf = df_conf.pivot(index='Autoridad', columns='Trimestre', values='Confianza (%)')
                
                # Ordenar por nivel de confianza promedio (Mayor arriba)
                orden_nivel = df_conf.groupby('Autoridad')['Confianza (%)'].mean().sort_values(ascending=False).index
                df_pivot_conf = df_pivot_conf.reindex(orden_nivel)

                # Ordenar Trimestres en Eje X
                orden_t = ['1er Trim', '2do Trim', '3er Trim', '4to Trim']
                cols_x = [c for c in orden_t if c in df_pivot_conf.columns]
                df_pivot_conf = df_pivot_conf.reindex(columns=cols_x)

                # 2. Gráfica
                fig_conf = px.imshow(
                    df_pivot_conf,
                    labels=dict(x="Periodo", y="Institución", color="Confianza (%)"),
                    x=df_pivot_conf.columns,
                    y=df_pivot_conf.index,
                    color_continuous_scale='RdYlGn', # Semaforo
                    text_auto='.1f',
                    title="Nivel de Confianza en Autoridades de Seguridad"
                )

                fig_conf.update_layout(height=500)
                st.plotly_chart(fig_conf, use_container_width=True)
            else:
                st.warning("No hay datos suficientes para calcular la confianza en este periodo.")
                    
    # --- SECCIÓN 3: Acoso y Violencia ---
    with tab3:
        st.header("⚠️ Acoso y Violencia Sexual")
        st.info("Nota: Este módulo se divide en primer y segundo semestre del año.")

        # 1. Filtro específico por Sexo (Default ambos para comparativa)
        sexo_opciones = {1: "Hombre", 2: "Mujer"}
        
        c1, c2 = st.columns([1, 2])
        with c1:
            sexo_sel = st.multiselect(
                "Filtrar por sexo:",
                options=[1, 2],
                format_func=lambda x: sexo_opciones[x],
                default=[1, 2], # Aparecen ambos por default
                key="filter_sexo_acoso"
            )

        # 2. Diccionario de variables
        dict_acoso = {
            'BP4_1_1': 'Piropos u ofensas',
            'BP4_1_2': 'Intento de Coerción sexual',
            'BP4_1_3': 'Dinero por actos sexuales',
            'BP4_1_4': 'Acoso sexual por medio de redes',
            'BP4_1_5': 'Violación',
            'BP4_1_6': 'Exhibicionismo',
            'BP4_1_7': 'Manoseos o toqueteos',
            'BP4_1_8': 'Envío de fotos o contenido sexual por redes',
            'BP4_1_9': 'Obligar a observar actos sexuales'
        }

        # Conversión de filtro a string para el DataFrame
        sexo_sel_str = [str(s) for s in sexo_sel]
        df_acoso = df_filtrado[df_filtrado['SEXO'].isin(sexo_sel_str)]

        lista_acoso = []

        if not df_acoso.empty:
            trims_validos = [t for t in trim_sel if "2do" in str(t) or "4to" in str(t)]
            
            for col, nombre in dict_acoso.items():
                if col in df_acoso.columns:
                    for trim in trims_validos:
                        # Iteramos por cada sexo seleccionado para tener la separación en la tabla final
                        for s_val in sexo_sel_str:
                            df_ts = df_acoso[(df_acoso['TRIMESTRE'] == trim) & (df_acoso['SEXO'] == s_val)]
                            df_v = df_ts[df_ts[col].isin(['1', '2'])]
                            
                            if not df_v.empty:
                                si = df_v[df_v[col] == '1']['FAC_SEL'].sum()
                                tot = df_v['FAC_SEL'].sum()
                                
                                if tot > 0:
                                    lista_acoso.append({
                                        'Situación': nombre,
                                        'Trimestre': trim,
                                        'Sexo': sexo_opciones[int(s_val)],
                                        'Porcentaje': (si / tot) * 100
                                    })

            if lista_acoso:
                df_p_acoso = pd.DataFrame(lista_acoso)
                
                # CREACIÓN DE GRÁFICA COMPARATIVA
                # Usamos color='Sexo' para crear las columnas paralelas y barmode='group'
                fig_acoso = px.bar(
                    df_p_acoso,
                    x='Situación',
                    y='Porcentaje',
                    color='Sexo',
                    facet_row='Trimestre', # Esto separa 2do y 4to trimestre en filas para no amontonar
                    barmode='group',
                    text_auto='.1f',
                    title="Comparativa de Acoso por Sexo y Trimestre",
                    color_discrete_map={'Hombre': '#2E59A7', 'Mujer': '#8B42BF'}, # Azul vs Púrpura
                    height=800
                )
                
                fig_acoso.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_acoso, use_container_width=True)
            else:
                st.warning("No hay datos para los trimestres pares seleccionados.")
        else:
            st.warning("Por favor, selecciona al menos un sexo en el filtro.")
            
       #--- SECCIÓN 5: VICTIMIZACIÓN
    with tab5:
        st.subheader("🏠 Impacto Total en Hogares")
        
        if not df_filtrado.empty:
            trims_sem = [t for t in trim_sel if "2do" in str(t) or "4to" in str(t)]
            resumen_hogares = []

            for trim in trims_sem:
                df_t = df_filtrado[df_filtrado['TRIMESTRE'] == trim].copy()
                etiqueta_sem = "1er Semestre" if "2do" in str(trim) else "2do Semestre"
                
                # 1. Identificar columnas de victimización
                cols_v = [f'BP1_6_{i}' for i in range(1, 9)]
                
                # 2. Limpieza rápida para asegurar comparación
                for c in cols_v:
                    if c in df_t.columns:
                        df_t[c] = df_t[c].astype(str).str.replace('.0', '', regex=False).str.strip().str.get(0)
                
                # 3. Lógica de "Hogar Víctima": Si respondió '1' en cualquiera de las columnas
                # Usamos FAC_VIV como solicitaste para el estimado de hogares
                hogares_victima_mask = (df_t[cols_v] == '1').any(axis=1)
                
                total_hogares_victima = df_t[hogares_victima_mask]['FAC_VIV'].sum()
                total_hogares_universo = df_t['FAC_VIV'].sum()
                
                if total_hogares_universo > 0:
                    porcentaje_vic = (total_hogares_victima / total_hogares_universo) * 100
                    resumen_hogares.append({
                        'Semestre': etiqueta_sem,
                        'Absoluto': total_hogares_victima,
                        'Porcentaje': porcentaje_vic
                    })

            # Display de Resultados (Tarjetas para el semestre más reciente seleccionado)
            if resumen_hogares:
                latest = resumen_hogares[-1]
                col1, col2 = st.columns(2)
                
                col1.metric(
                    label=f"Hogares Víctimas ({latest['Semestre']})", 
                    value=f"{latest['Absoluto']:,.0f}",
                    help="Estimado bruto basado en FAC_VIV"
                )
                
                col2.metric(
                    label=f"Tasa de Victimización ({latest['Semestre']})", 
                    value=f"{latest['Porcentaje']:.1f}%",
                    help="Porcentaje del total de hogares que sufrieron al menos un delito"
                )

                # Gráfica de barras simple para comparar semestres si hay más de uno
                if len(resumen_hogares) > 1:
                    df_res = pd.DataFrame(resumen_hogares)
                    fig_res = px.bar(
                        df_res, x='Semestre', y='Porcentaje',
                        text_auto='.1f', title="Evolución de la Tasa de Victimización del Hogar",
                        color='Semestre', color_discrete_sequence=['#34495E', '#AEB6BF']
                    )
                    st.plotly_chart(fig_res, use_container_width=True)
            else:
                st.warning("Selecciona periodos semestrales (2do o 4to Trim) para ver el resumen de hogares.")
                
        st.header("🏡 Victimización en el hogar")
        st.info("Incidencia de delitos sufridos por hogar.")

        # 1. Diccionario de delitos (BP1_6_1 a BP1_6_8)
        dict_delitos = {
            'BP1_6_1': 'Robo total de vehículo',
            'BP1_6_2': 'Robo parcial de vehículo',
            'BP1_6_3': 'Allanamiento de morada',
            'BP1_6_4': 'Robo o asalto en calle/transporte',
            'BP1_6_5': 'Robo en forma distinta a las anteriores',
            'BP1_6_6': 'Extorsión',
            'BP1_6_7': 'Fraude bancario',
            'BP1_6_8': 'Fraude al consumidor'
        }

        lista_victimas = []

        if not df_filtrado.empty:
            # Filtramos trimestres semestrales (2 y 4)
            trims_sem = [t for t in trim_sel if "2do" in str(t) or "4to" in str(t)]

            for col, nombre in dict_delitos.items():
                if col in df_filtrado.columns:
                    for trim in trims_sem:
                        df_t = df_filtrado[df_filtrado['TRIMESTRE'] == trim].copy()
                        
                        # Limpieza y normalización
                        resp = df_t[col].astype(str).str.replace('.0', '', regex=False).str.strip().str.get(0)
                        
                        # Numerador: Al menos un integrante sufrió el delito (1)
                        # Denominador: Respuestas válidas (1 y 2)
                        df_v = df_t[resp.isin(['1', '2'])]
                        
                        if not df_v.empty:
                            si = df_v[resp == '1']['FAC_VIV'].sum()
                            tot = df_v['FAC_VIV'].sum()
                            
                            etiqueta_sem = "1er Sem" if "2do" in str(trim) else "2do Sem"
                            
                            if tot > 0:
                                lista_victimas.append({
                                    'Delito': nombre,
                                    'Semestre': etiqueta_sem,
                                    'Porcentaje': (si / tot) * 100
                                })

            if lista_victimas:
                df_heatmap = pd.DataFrame(lista_victimas)
                
                # --- MEJORA DE ORDENAMIENTO DINÁMICO ---
                # 1. Calculamos el promedio de prevalencia de ambos semestres para cada delito
                df_orden = df_heatmap.groupby('Delito')['Porcentaje'].mean().reset_index()
                # 2. Ordenamos de mayor a menor incidencia
                df_orden = df_orden.sort_values(by='Porcentaje', ascending=False) #Mayor a menor
                delitos_ordenados = df_orden['Delito'].tolist()

                # Pivotar los datos para el formato de Mapa de Calor
                df_pivot = df_heatmap.pivot(index='Delito', columns='Semestre', values='Porcentaje')
                
                # Reindexar el DataFrame pivotado con el orden calculado
                # Asegurar que el reindex no de errores si falta algún delito en los datos
                delitos_reindex = [d for d in delitos_ordenados if d in df_pivot.index]
                df_pivot_ordenado = df_pivot.reindex(delitos_reindex)

                # Definir orden de semestres
                orden_semestres = ["1er Sem", "2do Sem"]
                # Asegurar reindex de columnas
                columnas_reindex = [c for c in orden_semestres if c in df_pivot_ordenado.columns]
                df_pivot_ordenado = df_pivot_ordenado.reindex(columns=columnas_reindex)


                # 2. Creación del Mapa de Calor con Plotly
                fig_heat = px.imshow(
                    df_pivot_ordenado,
                    labels=dict(x="Periodo Semestral", y="Tipo de Delito", color="Prevalencia (%)"),
                    x=df_pivot_ordenado.columns,
                    y=df_pivot_ordenado.index,
                    color_continuous_scale='YlOrRd', # De amarillo a rojo intenso
                    text_auto='.1f',
                    title="Intensidad de Victimización en el Hogar por Semestre"
                )

                fig_heat.update_layout(height=500)
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.warning("Selecciona el 2do o 4to trimestre para visualizar los datos de victimización.")

        st.subheader("🔢 Volumen Absoluto de Delitos Estimados")
        st.info("Cantidad total de incidentes delictivos estimados por tipo de delito (Datos Semestrales).")

        # 1. Diccionario de delitos (Mismo que el heatmap para consistencia)
        dict_delitos = {
            'BP1_6_1': 'Robo total de vehículo',
            'BP1_6_2': 'Robo parcial de vehículo',
            'BP1_6_3': 'Allanamiento de morada',
            'BP1_6_4': 'Robo o asalto en calle/transporte',
            'BP1_6_5': 'Robo en forma distinta a las anteriores',
            'BP1_6_6': 'Extorsión',
            'BP1_6_7': 'Fraude bancario',
            'BP1_6_8': 'Fraude al consumidor'
        }

        lista_volumen_delitos = []

        if not df_filtrado.empty:
            # Filtramos trimestres semestrales (2 y 4)
            trims_sem = [t for t in trim_sel if "2do" in str(t) or "4to" in str(t)]

            for col, nombre in dict_delitos.items():
                if col in df_filtrado.columns:
                    for trim in trims_sem:
                        df_t = df_filtrado[df_filtrado['TRIMESTRE'] == trim].copy()
                        
                        # Limpieza y normalización de la columna de delito
                        df_t[col] = df_t[col].astype(str).str.replace('.0', '', regex=False).str.strip().str.get(0)
                        
                        # --- METODOLOGÍA DE VOLUMEN ABSOLUTO ---
                        # Sumamos el factor de expansión de VIVIENDA (FAC_VIV) 
                        # de cada registro que haya dicho 'Sí' (1) a este delito específico.
                        total_delitos_tipo = df_t[df_t[col] == '1']['FAC_SEL'].sum()
                        
                        etiqueta_sem = "1er Sem" if "2do" in str(trim) else "2do Sem"
                        
                        if total_delitos_tipo > 0:
                            lista_volumen_delitos.append({
                                'Tipo de Delito': nombre,
                                'Temporalidad': etiqueta_sem,
                                'Volumen Absoluto': total_delitos_tipo
                            })

            if lista_volumen_delitos:
                df_volumen = pd.DataFrame(lista_volumen_delitos)
                
                # Ordenar dinámicamente: el delito con mayor volumen absoluto debe quedar arriba
                # Calculamos el volumen promedio para ordenar
                df_orden = df_volumen.groupby('Tipo de Delito')['Volumen Absoluto'].mean().reset_index()
                df_orden = df_orden.sort_values(by='Volumen Absoluto', ascending=False) # Ascending para eje Y invertido
                delitos_ordenados = df_orden['Tipo de Delito'].tolist()

                # Definir orden de semestres para la gráfica
                orden_semestres = ["1er Sem", "2do Sem"]

                # 2. Creación de la gráfica de Barras Horizontales Agrupadas
                fig_volumen = px.bar(
                    df_volumen,
                    x='Volumen Absoluto',
                    y='Tipo de Delito',
                    color='Temporalidad',
                    barmode='group', # Barras agrupadas por semestre
                    orientation='h', # Horizontal para leer bien los nombres largos
                    text_auto='.0s', # Muestra miles como 'k' o millones como 'M'
                    title="Estimado de Volumen Absoluto de Delitos por Tipo",
                    color_discrete_sequence=px.colors.sequential.Tealgrn, # Paleta de verde azulado
                    category_orders={
                        "Tipo de Delito": delitos_ordenados,
                        "Temporalidad": orden_semestres
                    },
                    height=600
                )
                
                # Ajuste de layout para legibilidad
                fig_volumen.update_layout(
                    xaxis_title="Cantidad de Incidentes Estimados",
                    yaxis_title=None,
                    legend_title="Periodo",
                    xaxis_tickformat=',.0f' # Formato de miles en el eje X
                )
                
                st.plotly_chart(fig_volumen, use_container_width=True)
            else:
                st.warning("Selecciona el 2do o 4to trimestre para visualizar el volumen absoluto de delitos.")

    # --- 6. NOTA METODOLÓGICA ---
    st.markdown("---")
    with st.expander("📝 Nota Metodológica y Precisión Estadística"):
        st.markdown("""Resultados calculados con microdatos ENSU y factor `FAC_SEL`. 
                    Variaciones mínimas vs INEGI por Coeficiente de Variación y redondeo dinámico. *Corte: Dic 2025.*""")
else:
    st.warning("⚠️ Archivo 'Master_ENSU_Morelos.parquet' no detectado en la carpeta /data.")
