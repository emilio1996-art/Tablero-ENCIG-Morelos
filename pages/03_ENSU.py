import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np

# 1. Configuración de página
st.set_page_config(page_title="ENSU - Morelos", layout="wide")

# 2. Encabezado
st.title("🏙️ Percepción de Seguridad Pública Urbana (ENSU)")
st.caption("Fuente: Microdatos de INEGI - Análisis específico para el Estado de Morelos")
st.markdown("---")

def limpiar_columnas_inegi(df_input, lista_columnas):
    df_result = df_input.copy()
    for col in lista_columnas:
        if col in df_result.columns:
            # Normalización total: a string, quitar .0 y espacios
            df_result[col] = df_result[col].astype(str).str.replace('.0', '', regex=False).str.strip()
            df_result[col] = df_result[col].replace('nan', np.nan)
    return df_result

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

df_raw = cargar_data() # Cargamos los datos originales

if df_raw is not None:
    # Listamos TODAS las columnas que usaremos en cualquier pestaña que sean códigos (1, 2, 3...)
    cols_control = [
        'BP1_1', 'BP1_3', 'BP1_2_01', 'BP1_2_02', 'BP1_2_03', 'BP1_2_04', 
        'BP1_2_05', 'BP1_2_06', 'BP1_2_07', 'BP1_2_08', 'BP1_2_09', 'BP1_2_10', 
        'BP1_2_11', 'BP1_2_12', 'BP1_4_1', 'BP1_4_2', 'BP1_4_3', 'BP1_4_4', 
        'BP1_4_5', 'BP1_4_6', 'BP1_4_7', 'BP1_4_8', 'BP1_5_1', 'BP1_5_2', 
        'BP1_5_3', 'BP1_5_4', 'BP1_5_5'
    ]
    
    # Aquí creamos el 'df' final que usará todo tu script
    df = limpiar_columnas_inegi(df_raw, cols_control)

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
    
    # 1. Lógica para detectar el último trimestre del último año
    if df_filtrado is not None and not df_filtrado.empty:
        # 1. Identificar el último periodo disponible
        map_orden = {"1er Trim": 1, "2do Trim": 2, "3er Trim": 3, "4to Trim": 4}
        df_temp_reciente = df_filtrado.copy()
        df_temp_reciente['orden'] = df_temp_reciente['TRIMESTRE'].map(map_orden)
        
        # Obtenemos el registro más reciente
        ultimo_anio = df_temp_reciente['ANIO'].max()
        ultimo_trim = df_temp_reciente[df_temp_reciente['ANIO'] == ultimo_anio].sort_values('orden')['TRIMESTRE'].iloc[-1]
        
        # 2. Filtrar y limpiar (Forzamos a STRING para evitar el 0.0%)
        df_reciente = df_temp_reciente[(df_temp_reciente['ANIO'] == ultimo_anio) & 
                                       (df_temp_reciente['TRIMESTRE'] == ultimo_trim)].copy()
        
        # LIMPIEZA CRUCIAL: Convertir a string y quitar posibles decimales .0
        df_reciente['BP1_3'] = df_reciente['BP1_3'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        # 3. Cálculo con FAC_SEL
        pob_total_exp = df_reciente['FAC_SEL'].sum()
        
        # Filtramos categorías de pesimismo (3 y 4)
        pob_igual_mal = df_reciente[df_reciente['BP1_3'] == '3']['FAC_SEL'].sum()
        pob_empeorara = df_reciente[df_reciente['BP1_3'] == '4']['FAC_SEL'].sum()
        pob_mejorara = df_reciente[df_reciente['BP1_3'] == '1']['FAC_SEL'].sum()

        if pob_total_exp > 0:
            pct_igual_mal = (pob_igual_mal / pob_total_exp) * 100
            pct_empeorara = (pob_empeorara / pob_total_exp) * 100
            pct_mejorara = (pob_mejorara / pob_total_exp) * 100
        else:
            pct_igual_mal = pct_empeorara = pct_mejorara = 0.0

        # 4. Mostrar Tarjetas
        st.markdown(f"#### 📊 Expectativas sobre las condiciones de seguridad pública para los próximos 12 meses ")
        k1, k2, k3 = st.columns(3)
        
        with k1:
            st.metric("Seguirá igual de MAL", f"{pct_igual_mal:.1f}%")
        with k2:
            st.metric("EMPEORARÁ", f"{pct_empeorara:.1f}%", delta=f"{(pct_igual_mal + pct_empeorara):.1f}% Total Negativo", delta_color="inverse")
        with k3:
            st.metric("MEJORARÁ", f"{pct_mejorara:.1f}%")

    # 5. DEFINICIÓN DE SECCIONES (TABS)
    tab1, tab2, tab3, tab4 = st.tabs([
        "🛡️ Percepción de Seguridad", 
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
                    indices_validos = df_temp_col[df_temp_col.isin(['1', '2', '3', '9'])].index
                    
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

            st.markdown("---")
        st.subheader("🔊 Incidencias y Conductas Antisociales en el Entorno")
        st.caption("Porcentaje de la población que ha presenciado estas situaciones en los alrededores de su vivienda.")

        if not df_filtrado.empty:
            # 1. Definición del catálogo de conductas según INEGI
            dict_conductas = {
                'BP1_4_1': 'Vandalismo',
                'BP1_4_2': 'Consumo de alcohol en las calles',
                'BP1_4_3': 'Robos o asaltos',
                'BP1_4_4': 'Bandas violentas',
                'BP1_4_5': 'Venta o consumo de drogas',
                'BP1_4_6': 'Disparos frecuentes',
                'BP1_4_7': 'Huiachicol',
                'BP1_4_8': 'Tomas irregulares de luz'
            }

            lista_conductas = []

            # 2. Procesamiento masivo
            for col, nombre in dict_conductas.items():
                if col in df_filtrado.columns:
                    # Iteramos por los trimestres seleccionados para la comparativa
                    for trim in trim_sel:
                        df_t = df_filtrado[df_filtrado['TRIMESTRE'] == trim].copy()
                        
                        # Limpieza de la columna actual
                        df_t[col] = df_t[col].astype(str).str.replace('.0', '', regex=False).str.strip()
                        
                        # Denominador: quienes respondieron Sí (1) o No (2)
                        df_val = df_t[df_t[col].isin(['1', '2'])]
                        
                        if not df_val.empty:
                            pob_si = df_val[df_val[col] == '1']['FAC_SEL'].sum()
                            pob_total_c = df_val['FAC_SEL'].sum()
                            
                            lista_conductas.append({
                                'Conducta': nombre,
                                'Trimestre': trim,
                                'Porcentaje': (pob_si / pob_total_c) * 100
                            })

            if lista_conductas:
                df_c = pd.DataFrame(lista_conductas)
                
                # 3. Gráfica de Barras Agrupadas Horizontales
                # Usamos horizontales porque los nombres de las conductas son largos
                fig_conductas = px.bar(
                    df_c,
                    x='Porcentaje',
                    y='Conducta',
                    color='Trimestre',
                    barmode='group',
                    orientation='h',
                    text=df_c['Porcentaje'].apply(lambda x: f'{x:.1f}%'),
                    title="Atestiguación de Conductas Antisociales por Trimestre",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )

                fig_conductas.update_layout(
                    xaxis_range=[0, 110],
                    height=600,
                    yaxis={'categoryorder':'total ascending'},
                    legend_title="Periodo"
                )
                
                fig_conductas.update_traces(textposition='outside', textfont_size=10)
                
                st.plotly_chart(fig_conductas, use_container_width=True)
            else:
                st.warning("No se encontraron datos para las conductas seleccionadas.")

            # --- SECCIÓN: CAMBIO DE HÁBITOS POR TEMOR AL DELITO (BP1_5_1 a BP1_5_5) ---
        st.markdown("---")
        st.subheader("🚶 Cambio de Hábitos por Inseguridad")
        
        if df_filtrado is not None and not df_filtrado.empty:
            dict_habitos = {
                'BP1_5_1': 'Llevar cosas de valor',
                'BP1_5_2': 'Caminar en los alrederores despúes de las 8 PM',
                'BP1_5_3': 'Visitar parientes/amigos',
                'BP1_5_4': 'Menores salgan de casa',
                'BP1_5_5': 'Otro'
            }

            lista_habitos = []

            for col, nombre in dict_habitos.items():
                if col in df_filtrado.columns:
                    for trim in trim_sel:
                        # 1. Filtramos por trimestre
                        df_t = df_filtrado[df_filtrado['TRIMESTRE'] == trim].copy()
                        
                        if not df_t.empty:
                            # 2. LIMPIEZA AGRESIVA IN-SITU (Esto asegura el dibujo)
                            # Convertimos a string y forzamos que sea solo el primer carácter 
                            # (por si acaso hay '1.0' o espacios)
                            serie_limpia = df_t[col].astype(str).str.strip().str.get(0)
                            
                            # 3. Calculamos usando la serie limpia
                            pob_si = df_t[serie_limpia == '1']['FAC_SEL'].sum()
                            pob_total_h = df_t[serie_limpia.isin(['1', '2'])]['FAC_SEL'].sum()
                            
                            if pob_total_h > 0:
                                lista_habitos.append({
                                    'Hábito': nombre,
                                    'Trimestre': trim,
                                    'Porcentaje': (pob_si / pob_total_h) * 100
                                })

            if lista_habitos:
                df_h = pd.DataFrame(lista_habitos)
                fig_habitos = px.bar(
                    df_h, x='Porcentaje', y='Hábito', color='Trimestre',
                    barmode='group', orientation='h',
                    text=df_h['Porcentaje'].apply(lambda x: f'{x:.1f}%'),
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_habitos.update_layout(xaxis_range=[0, 110], height=450)
                st.plotly_chart(fig_habitos, use_container_width=True)
                
                # Nota interpretativa
                st.info("""**Nota de análisis:** Los cambios en hábitos como 'Caminar de noche' o 'Permitir que menores salgan' suelen ser los indicadores más sensibles 
                        al aumento de la percepción de inseguridad en Morelos.""")
            else:
                st.warning("No hay datos suficientes para las variables de cambio de hábitos.")

    # --- SECCIÓN 2: Desempeño Gubernamental ---
    with tab2:
        st.header("Desempeño Gubernamental")
        st.info("Evaluación de la efectividad del gobierno para resolver problemas en la ciudad.")

    # --- SECCIÓN 3: Acoso y Violencia ---
    with tab3:
        st.header("Acoso y Violencia")
        st.info("Prevalencia de situaciones de acoso personal y violencia en el entorno urbano.")

    # --- SECCIÓN 4: Confianza en Administración Pública ---
    with tab4:
        st.header("Confianza en la Administración Pública")
        st.info("Nivel de confianza en las diversas instituciones de seguridad (Marina, Sedena, Policía).")

    # --- NOTA METODOLÓGICA (Alineada con los TABS) ---
    st.markdown("---") # Una línea divisoria antes del expander
    with st.expander("📝 Nota Metodológica y Precisión Estadística"):
        st.markdown(f"""
        **¿Por qué existen variaciones respecto a los tabulados oficiales?**
        
        Los resultados presentados en este tablero se calculan mediante el procesamiento directo de los microdatos de la **ENSU**, aplicando el factor de expansión `FAC_SEL`. 
        
        Las pequeñas variaciones (típicamente entre 1% y 2%) frente a los comunicados de prensa del INEGI se deben a:
        1. **Coeficiente de Variación (CV):** Según la metodología de INEGI, las estimaciones tienen niveles de precisión:
            * 🟢 **Alto:** CV entre 0 y 15%.
            * 🟡 **Moderado:** CV entre 15 y 30%.
            * 🔴 **Bajo:** CV superior al 30%.
        2. **Redondeo y Agregación:** Este tablero utiliza la base de datos cruda para permitir filtros dinámicos.
        
        *Última actualización de datos: Diciembre 2025.*
        """)

else: # Este else está alineado con el 'if df is not None' del inicio
    st.warning("⚠️ El sistema está listo, pero el archivo 'Master_ENSU_Morelos.parquet' no se encuentra.")
