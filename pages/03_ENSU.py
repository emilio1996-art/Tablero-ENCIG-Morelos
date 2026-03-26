import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Configuración de página
st.set_page_config(page_title="ENSU - Morelos", layout="wide")

# 2. Encabezado
st.title("🏙️ Percepción de Seguridad Pública Urbana (ENSU)")
st.caption("Fuente: Microdatos de INEGI - Análisis específico para el Estado de Morelos")
st.markdown("---")

# 3. Carga de Datos (Usando el Parquet generado en la consola)
@st.cache_data
def cargar_data():
    # Construimos la ruta dinámica para que funcione en cualquier PC
    ruta_archivo = os.path.join("data", "Master_ENSU_Morelos.parquet")
    
    try:
        if os.path.exists(ruta_archivo):
            df = pd.read_parquet(ruta_archivo)
            return df
        else:
            st.error(f"❌ No se encontró el archivo en: {ruta_archivo}")
            return None
    except Exception as e:
        st.error(f"Error al leer el archivo Parquet: {e}")
        return None

df = cargar_data()

if df is not None:
    # 4. Filtros Globales en Sidebar
    st.sidebar.header("📅 Filtros de Tiempo")
    
    # Filtro de Año
    anios = sorted(df['ANIO'].unique(), reverse=True)
    anio_sel = st.sidebar.multiselect("Seleccione Año(s)", options=anios, default=anios[0])
    
    # --- NUEVO FILTRO DE TRIMESTRE ---
    # Solo mostramos los trimestres que existen en los años seleccionados
    trims_disponibles = sorted(df[df['ANIO'].isin(anio_sel)]['TRIMESTRE'].unique())
    trim_sel = st.sidebar.multiselect(
        "Seleccione Trimestre(s)", 
        options=trims_disponibles, 
        default=trims_disponibles # Por defecto todos los del año
    )
    
    st.sidebar.markdown("---")
    st.sidebar.header("📍 Ubicación")
    municipios = sorted(df['NOM_MUN'].unique())
    mun_sel = st.sidebar.multiselect("Municipio/Ciudad", options=municipios, default=municipios)

    # ACTUALIZACIÓN DE LA LÓGICA DE FILTRADO
    # Ahora el df_filtrado considera Año, Trimestre y Municipio
    df_filtrado = df[
        (df['ANIO'].isin(anio_sel)) & 
        (df['TRIMESTRE'].isin(trim_sel)) & 
        (df['NOM_MUN'].isin(mun_sel))
    ]

    # 5. DEFINICIÓN DE SECCIONES (TABS)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🛡️ Percepción de Seguridad", 
        "🚫 Conflictos y Antisociales", 
        "🏗️ Desempeño Gubernamental", 
        "⚠️ Acoso y Violencia",
        "🤝 Confianza Pública"
    ])

    # --- SECCIÓN 1: Percepción Sobre Seguridad Pública ---
    with tab1:
        st.header("Percepción Sobre Seguridad Pública")
        
        if df_filtrado is not None and not df_filtrado.empty:
            st.subheader("⚠️ Percepción General de Inseguridad en la Ciudad")
            
            # 1. Preparación de datos con FAC_SEL
            df_g1 = df_filtrado[['ANIO', 'TRIMESTRE', 'BP1_1', 'FAC_SEL']].copy()
            
            # Aseguramos formato texto y limpieza
            df_g1['BP1_1'] = df_g1['BP1_1'].astype(str).str.strip()
            
            # Mapeo oficial
            map_seguridad = {
                '1': '1 Seguro',
                '2': '2 Inseguro',
                '9': '9 No sabe/No responde'
            }
            df_g1['Respuesta'] = df_g1['BP1_1'].map(map_seguridad)
            
            # 2. Agrupación y Cálculo de Porcentajes usando FAC_SEL
            # Sumamos el factor de selección por grupo
            df_grouped = df_g1.groupby(['ANIO', 'TRIMESTRE', 'Respuesta'])['FAC_SEL'].sum().reset_index()
            
            # Calculamos el total expandido por trimestre
            df_grouped['Total_Pob_Trim'] = df_grouped.groupby(['ANIO', 'TRIMESTRE'])['FAC_SEL'].transform('sum')
            
            # Sacamos el porcentaje real
            df_grouped['Porcentaje'] = (df_grouped['FAC_SEL'] / df_grouped['Total_Pob_Trim']) * 100
            
            # Orden cronológico
            map_orden_trim = {"1er Trim": 1, "2do Trim": 2, "3er Trim": 3, "4to Trim": 4}
            df_grouped['orden'] = df_grouped['TRIMESTRE'].map(map_orden_trim)
            df_grouped = df_grouped.sort_values(by=['ANIO', 'orden'])
            
            # 3. Gráfica de Líneas con Plotly
            fig1 = px.line(
                df_grouped,
                x='TRIMESTRE',
                y='Porcentaje',
                color='Respuesta',
                markers=True,
                title="Evolución de la Percepción de Seguridad (Población 18+)",
                labels={'Porcentaje': 'Porcentaje de la Población (%)'},
                color_discrete_map={
                    '1 Seguro': '#4CAF50',
                    '2 Inseguro': '#F44336',
                    '9 No sabe/No responde': '#9E9E9E'
                }
            )
            
            fig1.update_layout(yaxis_range=[0, 100], hovermode="x unified")
            st.plotly_chart(fig1, use_container_width=True)
            
            # Métrica del dato más reciente
            try:
                # Filtramos solo la categoría 'Inseguro' del periodo más reciente
                ultimo_dato = df_grouped[df_grouped['Respuesta'] == '2 Inseguro'].iloc[-1]
                st.metric(
                    label=f"Índice de Inseguridad Percibida ({ultimo_dato['TRIMESTRE']} {ultimo_dato['ANIO']})",
                    value=f"{ultimo_dato['Porcentaje']:.1f}%",
                    delta_color="inverse", # Rojo si sube, verde si baja (opcional si comparamos con el anterior)
                    help="Representa a la población expandida con el factor FAC_SEL."
                )
            except:
                pass

            st.markdown("---")
            st.subheader("📍 ¿En qué lugares se siente más inseguro?")
            
            # 1. Diccionario de Lugares
            dict_lugares = {
                'BP1_2_01': 'Casa', 'BP1_2_02': 'Trabajo', 'BP1_2_03': 'Calle',
                'BP1_2_04': 'Escuela', 'BP1_2_05': 'Mercado', 'BP1_2_06': 'Centro Comercial',
                'BP1_2_07': 'Banco', 'BP1_2_08': 'Cajero Automático', 'BP1_2_09': 'Transporte Público',
                'BP1_2_10': 'Automóvil', 'BP1_2_11': 'Carretera', 'BP1_2_12': 'Parque'
            }

            # 2. Procesamiento (dentro del mismo nivel de indentación)
            lista_resultados = []
            for col, nombre in dict_lugares.items():
                if col in df_filtrado.columns:
                    # Convertimos la columna a string y quitamos espacios para asegurar la comparación
                    df_temp_col = df_filtrado[col].astype(str).str.strip()
                    
                    # Filtro de respuestas válidas (1 y 2) usando el índice del df original para mantener FAC_SEL
                    indices_validos = df_temp_col[df_temp_col.isin(['1', '2'])].index
                    
                    if not indices_validos.empty:
                        # Población que se siente insegura (Respuesta '2')
                        mask_inseguro = df_temp_col.loc[indices_validos] == '2'
                        pob_insegura = df_filtrado.loc[indices_validos][mask_inseguro]['FAC_SEL'].sum()
                        
                        # Población total que frecuenta el lugar (1 + 2)
                        pob_total = df_filtrado.loc[indices_validos]['FAC_SEL'].sum()
                        
                        if pob_total > 0:
                            lista_resultados.append({
                                'Lugar': nombre, 
                                'Porcentaje': (pob_insegura / pob_total) * 100
                            })

            # Solo dibujamos si hay resultados
            lista_comparativa = []
            
            # Iteramos por cada lugar y por cada trimestre presente en el filtro
            for col, nombre in dict_lugares.items():
                if col in df_filtrado.columns:
                    for trim in trim_sel: # Usamos los trimestres seleccionados en el sidebar
                        df_trim = df_filtrado[df_filtrado['TRIMESTRE'] == trim].copy()
                        
                        # Limpieza y filtrado de respuestas válidas (1 y 2)
                        df_trim[col] = df_trim[col].astype(str).str.strip()
                        df_valido = df_trim[df_trim[col].isin(['1', '2'])]
                        
                        if not df_valido.empty:
                            pob_insegura = df_valido[df_valido[col] == '2']['FAC_SEL'].sum()
                            pob_total = df_valido['FAC_SEL'].sum()
                            
                            lista_comparativa.append({
                                'Lugar': nombre,
                                'Trimestre': trim,
                                'Porcentaje': (pob_insegura / pob_total) * 100
                            })

            if lista_comparativa:
                df_comp = pd.DataFrame(lista_comparativa)
                
                # Creamos la gráfica de barras agrupadas
                fig_comp = px.bar(
                    df_comp,
                    x='Porcentaje',
                    y='Lugar',
                    color='Trimestre',
                    barmode='group', # Esto hace que las barras se pongan una al lado de otra
                    orientation='h',
                    text=df_comp['Porcentaje'].apply(lambda x: f'{x:.0f}%'),
                    title="Inseguridad Percibida: Comparativa entre Trimestres",
                    # Usamos una paleta secuencial para que los trimestres se vean relacionados
                    color_discrete_sequence=px.colors.sequential.Reds_r 
                )

                fig_comp.update_layout(
                    xaxis_range=[0, 110],
                    height=700, # Aumentamos el alto para que quepan bien los grupos de barras
                    yaxis={'categoryorder':'total ascending'}, # Ordena por el lugar más inseguro en promedio
                    legend_title="Periodo"
                )
                
                fig_comp.update_traces(textposition='outside', textfont_size=10)
                
                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.warning("No hay datos suficientes para generar la comparativa trimestral.")

    # --- SECCIÓN 2: Conflictos y Conductas Antisociales ---
    with tab2:
        st.header("Conflictos y Conductas Antisociales")
        st.info("Presencia de atestiguación de delitos y conflictos directos con vecinos o autoridades.")

    # --- SECCIÓN 3: Desempeño Gubernamental ---
    with tab3:
        st.header("Desempeño Gubernamental")
        st.info("Evaluación de la efectividad del gobierno para resolver problemas en la ciudad.")

    # --- SECCIÓN 4: Acoso y Violencia ---
    with tab4:
        st.header("Acoso y Violencia")
        st.info("Prevalencia de situaciones de acoso personal y violencia en el entorno urbano.")

    # --- SECCIÓN 5: Confianza en Administración Pública ---
    with tab5:
        st.header("Confianza en la Administración Pública")
        st.info("Nivel de confianza en las diversas instituciones de seguridad (Marina, Sedena, Policía).")

else:
    st.warning("⚠️ El sistema está listo, pero el archivo 'Master_ENSU_Morelos.parquet' no se encuentra. Use la Consola para generarlo.")