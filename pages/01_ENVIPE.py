import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata

# 1. Configuración de la página
st.set_page_config(page_title="ENVIPE Morelos - Comparativa", layout="wide")

# 2. Función de carga de datos con normalización (Mantenida intacta)
@st.cache_data
def load_persona_data():
    ruta = "data/MAESTRA_TPer_Vic1_MORELOS_2021_2025.csv"
    df = pd.read_csv(ruta, low_memory=False)
    df.columns = [c.upper() for c in df.columns]
    
    # --- FUNCIÓN INTERNA PARA LIMPIAR TEXTO ---
    def normalizar_texto(texto):
        if pd.isna(texto): return texto
        # 1. Convertir a string y quitar espacios
        texto = str(texto).strip()
        # 2. Eliminar acentos (Normalización NFD y filtrado de diacríticos)
        texto = "".join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )
        # 3. Regresar en formato Título (Ej: MIACATLAN -> Miacatlan)
        return texto.title()

    # --- APLICAR LIMPIEZA TOTAL ---
    if 'NOM_MUN' in df.columns:
        df['NOM_MUN'] = df['NOM_MUN'].apply(normalizar_texto)
    
    return df

# 3. Inicialización de datos
try:
    df_per = load_persona_data()
except Exception as e:
    st.error(f"Error al cargar la base de datos: {e}")

try:
    df_per = load_persona_data()

    # Diccionario de colores basado en tu imagen
    colores_años = {
        "2021": "#1E8449", # Verde oscuro
        "2022": "#82BF45", # Verde claro
        "2023": "#45B39D", # Turquesa/Cian
        "2024": "#5B2C6F", # Morado
        "2025": "#2471A3"  # Azul
    }

    # ==============================================================================
    # CONFIGURACIÓN DEL MENÚ LATERAL (REESTRUCTURADO)
    # ==============================================================================
    st.sidebar.title("📊 Sistema de Estadísticas")

    # Nivel 1: Gran Tema
    tema_principal = st.sidebar.selectbox(
        "Seleccione el Tema Principal:",
        options=["PRINCIPAL", "ENCIG", "ENVIPE"],
        index=2 # Para que inicie en ENVIPE por defecto
    )

    # Lógica de navegación para ENVIPE
    if tema_principal == "ENVIPE":
        st.sidebar.header("🛡️ Menú ENVIPE")
        
        # Nivel 2: Subtemas
        subtema_envipe = st.sidebar.radio(
            "Seleccione una dimensión:",
            options=[
                "Prevalencia y Víctimas",  
                "Desempeño Institucional"
            ]
        )
        
        st.sidebar.divider()
        st.sidebar.subheader("⚙️ Filtros Globales")
        
        # Selección de años disponibles en la base de datos
        anios_disponibles = sorted(df_per['ANIO_ESTADISTICO'].unique())
        anios_sel = st.sidebar.multiselect(
            "Años a comparar:",
            options=anios_disponibles,
            default=anios_disponibles[-2:]
        )
        
        # Lista de municipios (ya normalizada en la carga de datos)
        municipios_lista = sorted(df_per['NOM_MUN'].unique().tolist())
        muni_sel = st.sidebar.selectbox(
            "Municipio:",
            options=["Todo el Estado"] + municipios_lista
        )

        # --- Lógica de Filtrado Global ---
        df_filtrado = df_per[df_per['ANIO_ESTADISTICO'].isin(anios_sel)].copy()
        if muni_sel != "Todo el Estado":
            df_filtrado = df_filtrado[df_filtrado['NOM_MUN'] == muni_sel]

    # --- Lógica de Navegación del Cuerpo Principal ---
        if not anios_sel:
            st.warning("⚠️ Por favor, seleccione al menos un año en el menú lateral.")
        
        else:
            # ==============================================================================
            # SECCIÓN 1: PREVALENCIA Y VÍCTIMAS
            # ==============================================================================
            if subtema_envipe == "Prevalencia y Víctimas":
                
                # --- SECCIÓN: PREVALENCIA DELICTIVA EN HOGARES ---
                st.markdown("### 🏠 Prevalencia Delictiva en Hogares")
                st.caption(f"Mostrando datos de: **{muni_sel}**")
                st.info("Cálculo basado en el resultado de la entrevista (RESUL_H) y expansión por hogares.")

                lista_prev_hogar = []
                for anio in sorted(anios_sel):
                    df_anio = df_filtrado[df_filtrado['ANIO_ESTADISTICO'] == anio].copy()
                    
                    # 1. FILTRO CRÍTICO: Dejar solo un registro por cada ID de Hogar
                    # Esto es lo que permite que el denominador sea de ~618k y no de millones (personas)
                    df_hogares_unicos = df_anio.drop_duplicates(subset=['ID_HOG'])
                    
                    # 2. Denominador: Suma de FAC_HOG de todos los hogares (Entrevistas A y B)
                    df_completos = df_hogares_unicos[df_hogares_unicos['RESUL_H'].isin(['A', 'B'])]
                    total_hogares_exp = df_completos['FAC_HOG'].sum()
                    
                    # 3. Numerador: Hogares con victimización (Categoría 'A')
                    hogares_vict_exp = df_completos[df_completos['RESUL_H'] == 'A']['FAC_HOG'].sum()
                    
                    # 4. Cálculo de Porcentaje y Tasa
                    porcentaje = (hogares_vict_exp / total_hogares_exp) * 100 if total_hogares_exp > 0 else 0
                    tasa = (hogares_vict_exp / total_hogares_exp) * 100000 if total_hogares_exp > 0 else 0
                    
                    lista_prev_hogar.append({
                        'Año': str(anio),
                        'Porcentaje': porcentaje,
                        'Tasa': tasa,
                        'Estimado': hogares_vict_exp,
                        'Base_Total': total_hogares_exp
                    })

        # --- PROCESAMIENTO Y VISUALIZACIÓN ---
                df_prev_h = pd.DataFrame(lista_prev_hogar)

                # Visualización de Tarjetas (KPIs)
                cols_metrics = st.columns(len(lista_prev_hogar))
                for i, dato in enumerate(lista_prev_hogar):
                    with cols_metrics[i]:
                        st.metric(
                            label=f"Prevalencia {dato['Año']}", 
                            value=f"{dato['Porcentaje']:.1f}%",
                            delta=f"{int(dato['Estimado']):,} hogares víctimas"
                        )
                        st.caption(f"De {int(dato['Base_Total']):,} hogares estimados")

                # 5. Gráfica de Tendencia
                fig_prev = px.line(df_prev_h, x='Año', y='Porcentaje', markers=True, 
                                  text=df_prev_h['Porcentaje'].apply(lambda x: f"{x:.1f}%"),
                                  title="Porcentaje de Hogares Víctima en Morelos (Tendencia)")
                fig_prev.update_traces(textposition="top center", line_color="#E74C3C") 
                st.plotly_chart(fig_prev, use_container_width=True)

                # --- NOTA METODOLÓGICA CORREGIDA ---
                if not df_prev_h.empty:
                    ultimo_dato = df_prev_h.iloc[-1] # Toma el último año de la lista analizada
                    
                    with st.expander("📝 Nota Metodológica sobre el cálculo de Prevalencia"):
                        st.markdown(f"""
                        **Consideraciones sobre los datos presentados:**
                        
                        1. **Fuente de Datos:** Este cálculo utiliza la base de datos de integrantes (`TPer_Vic1`) de la ENVIPE.
                        2. **Universo de Estudio:** Se identificaron **{int(ultimo_dato['Base_Total']):,}** hogares estimados en Morelos para el año {ultimo_dato['Año']}, cifra que coincide con el marco muestral oficial de INEGI.
                        3. **Variación en la Tasa:** La tasa calculada en este tablero ({ultimo_dato['Porcentaje']:.1f}%) presenta una variación respecto al boletín de prensa oficial (30.2%) debido a que el INEGI integra validaciones adicionales provenientes del **Módulo de Delitos (Tabla TVic)**.
                        4. **Criterio de Identificación:** Se considera un hogar víctima aquel cuya entrevista fue clasificada con resultado **'A' (Con Victimización)** en la variable `RESUL_H`.
                        5. **Años con datos nulos:** Algunas ediciones de la ENVIPE no consideran la totalidad de los municipios de la Entidad, por lo que al aplicar el fltro de "Municipio" habrá algunos años que no muestren datos en las gráficas.
                        
                        *Este tablero prioriza la tendencia histórica y la comparativa entre años utilizando una metodología consistente sobre la base de integrantes.*
                        """)

                # --- SUBTEMA 2: PREOCUPACIONES CIUDADANAS (DENTRO DEL IF) ---
                st.markdown("---")
                st.header("🛡️ Percepciones de Principales Problemas en Morelos")
                st.caption(f"Mostrando datos de: **{muni_sel}**")

                dict_preocupaciones = {
                    'AP4_2_01': 'Pobreza', 'AP4_2_02': 'Desempleo', 'AP4_2_03': 'Narcotráfico',
                    'AP4_2_04': 'Aumento de Precios', 'AP4_2_05': 'Inseguridad', 'AP4_2_06': 'Desastres Naturales',
                    'AP4_2_07': 'Escasez de Agua', 'AP4_2_08': 'Corrupción', 'AP4_2_09': 'Educación',
                    'AP4_2_10': 'Salud', 'AP4_2_11': 'Falta de Castigo a Delincuentes', 'AP4_2_12': 'Otro',
                    'AP4_2_13': 'Ninguno', 'AP4_2_99': 'Sin respuesta'
                }

                lista_comparativa = []
                for anio in anios_sel:
                    df_year = df_filtrado[df_filtrado['ANIO_ESTADISTICO'] == anio].copy()
                    total_ele = df_year['FAC_ELE'].sum() 
                    
                    for col_id, nombre in dict_preocupaciones.items():
                        if col_id in df_year.columns:
                            df_year[col_id] = pd.to_numeric(df_year[col_id], errors='coerce').fillna(0)
                            suma_expandida = df_year[df_year[col_id] == 1]['FAC_ELE'].sum()
                            porcentaje = (suma_expandida / total_ele) * 100 if total_ele > 0 else 0
                            
                            lista_comparativa.append({
                                'Año': str(anio), 'Tema': nombre, 'Porcentaje': porcentaje
                            })

                df_comp = pd.DataFrame(lista_comparativa)

                if not df_comp.empty:
                    categorias_final = ['NS/NR', 'Sin respuesta', 'Ninguno', 'Otro', 'Desastres Naturales']
                    todos_los_temas = df_comp['Tema'].unique().tolist()
                    temas_importantes = [t for t in todos_los_temas if t not in categorias_final]
                    
                    anio_max = str(max(anios_sel))
                    df_ref = df_comp[df_comp['Año'] == anio_max].sort_values(by='Porcentaje', ascending=True)
                    orden_principales = [t for t in df_ref['Tema'].tolist() if t in temas_importantes]
                    orden_final = [t for t in categorias_final if t in todos_los_temas] + orden_principales

                    st.subheader("📊 Evolución de las Preocupaciones Ciudadanas")
                    
                    fig = px.bar(
                        df_comp, x='Porcentaje', y='Tema', color='Año',
                        barmode='group', orientation='h',
                        color_discrete_map=colores_años, 
                        text=df_comp['Porcentaje'].apply(lambda x: f'{x:.1f}%'),
                        labels={'Porcentaje': 'Porcentaje (%)', 'Tema': 'Problemática'},
                        category_orders={"Tema": orden_final}
                    )
                    fig.update_layout(height=800, margin=dict(l=200))
                    st.plotly_chart(fig, use_container_width=True)

                    with st.expander("Ver tabla comparativa detallada"):
                        tabla_pivot = df_comp.pivot(index='Tema', columns='Año', values='Porcentaje')
                        st.dataframe(tabla_pivot.style.format("{:.1f}%"))

                # ==============================================================================
                # SUBTEMA 3: INSEGURIDAD EN ESPACIOS PÚBLICOS Y PRIVADOS
                # ==============================================================================
                st.markdown("---")
                st.header("📍 Sensación de Inseguridad por Lugar")
                st.info("Porcentaje de la población que se siente **'Insegura'** en cada espacio específico.")

                dict_espacios = {
                    'AP4_4_01': 'Casa',
                    'AP4_4_02': 'Trabajo',
                    'AP4_4_03': 'Calle',
                    'AP4_4_04': 'Escuela',
                    'AP4_4_05': 'Mercado',
                    'AP4_4_06': 'Centro comercial',
                    'AP4_4_07': 'Banco',
                    'AP4_4_08': 'Cajero automático en vía pública',
                    'AP4_4_09': 'Transporte público',
                    'AP4_4_10': 'Automóvil',
                    'AP4_4_11': 'Carretera',
                    'AP4_4_12': 'Parque'
                }

                lista_espacios = []
                for anio in anios_sel:
                    df_year = df_filtrado[df_filtrado['ANIO_ESTADISTICO'] == anio].copy()
                    
                    for col_id, nombre_lugar in dict_espacios.items():
                        if col_id in df_year.columns:
                            # 1. Convertir a numérico y limpiar
                            df_year[col_id] = pd.to_numeric(df_year[col_id], errors='coerce')
                            
                            # 2. FILTRO CRÍTICO: Seleccionar solo a quienes sí usan/van a ese lugar
                            # (Respuestas 1: Seguro y 2: Inseguro)
                            df_usuarios_lugar = df_year[df_year[col_id].isin([1, 2])]
                            
                            # 3. Nuevo Denominador: Población que acude a ese lugar
                            total_usuarios_exp = df_usuarios_lugar['FAC_ELE'].sum()
                            
                            # 4. Numerador: Solo los que se sienten inseguros (Respuesta 2)
                            inseguros_exp = df_usuarios_lugar[df_usuarios_lugar[col_id] == 2]['FAC_ELE'].sum()
                            
                            # 5. Cálculo final
                            porcentaje = (inseguros_exp / total_usuarios_exp) * 100 if total_usuarios_exp > 0 else 0
                            
                            lista_espacios.append({
                                'Año': str(anio),
                                'Lugar': nombre_lugar,
                                'Porcentaje': porcentaje
                            })

                df_esp = pd.DataFrame(lista_espacios)

                if not df_esp.empty:
                    # Ordenar por el año más reciente
                    anio_max_esp = str(max(anios_sel))
                    df_ref_esp = df_esp[df_esp['Año'] == anio_max_esp].sort_values(by='Porcentaje', ascending=True)
                    orden_lugares = df_ref_esp['Lugar'].tolist()

                    fig_esp = px.bar(
                        df_esp,
                        x='Porcentaje',
                        y='Lugar',
                        color='Año',
                        barmode='group',
                        orientation='h',
                        color_discrete_map=colores_años,
                        text=df_esp['Porcentaje'].apply(lambda x: f'{x:.1f}%'),
                        title=f"¿Qué tan inseguros se sienten en {muni_sel}?",
                        labels={'Porcentaje': 'Población Insegura (%)', 'Lugar': 'Espacio Físico'},
                        category_orders={"Lugar": orden_lugares}
                    )

                    fig_esp.update_layout(height=700, margin=dict(l=200))
                    fig_esp.update_traces(textposition='outside')
                    st.plotly_chart(fig_esp, use_container_width=True)
                    
                    with st.expander("Ver datos detallados por lugar"):
                        tabla_pivot_esp = df_esp.pivot(index='Lugar', columns='Año', values='Porcentaje')
                        st.dataframe(tabla_pivot_esp.style.format("{:.1f}%"))

                # ==============================================================================
                # SUBTEMA 4: CONDUCTAS DELICTIVAS O ANTISOCIALES EN EL ENTORNO
                # ==============================================================================
                st.markdown("---")
                st.header("🔊 Conductas Delictivas y Antisociales")
                st.info("Porcentaje de la población que ha identificado estas conductas en los alrededores de su vivienda.")

                dict_conductas = {
                    'AP4_5_01': 'Consumo de alcohol en la calle',
                    'AP4_5_02': 'Pandillerismo',
                    'AP4_5_03': 'Peleas entre vecinos',
                    'AP4_5_04': 'Venta ilegal de alcohol',
                    'AP4_5_05': 'Venta de piratería',
                    'AP4_5_06': 'Violencia policial contra ciudadanos',
                    'AP4_5_07': 'Invasión de predios',
                    'AP4_5_08': 'Consumo de drogas',
                    'AP4_5_09': 'Robos o asaltos frecuentes',
                    'AP4_5_10': 'Venta de droga',
                    'AP4_5_11': 'Disparos frecuentes',
                    'AP4_5_12': 'Prostitución',
                    'AP4_5_13': 'Secuestros',
                    'AP4_5_14': 'Homicidios',
                    'AP4_5_15': 'Extorsión (cobro de piso)',
                    'AP4_5_16': 'Huachicol',
                    'AP4_5_17': 'Tomas irregulares de luz',
                    'AP4_5_18': 'Ninguna'
                }

                lista_conductas = []
                for anio in anios_sel:
                    df_year = df_filtrado[df_filtrado['ANIO_ESTADISTICO'] == anio].copy()
                    total_ele = df_year['FAC_ELE'].sum()
                    
                    for col_id, nombre_conducta in dict_conductas.items():
                        if col_id in df_year.columns:
                            df_year[col_id] = pd.to_numeric(df_year[col_id], errors='coerce').fillna(0)
                            
                            # Numerador: Personas que respondieron 1 (Sí)
                            si_exp = df_year[df_year[col_id] == 1]['FAC_ELE'].sum()
                            porcentaje = (si_exp / total_ele) * 100 if total_ele > 0 else 0
                            
                            lista_conductas.append({
                                'Año': str(anio),
                                'Conducta': nombre_conducta,
                                'Porcentaje': porcentaje
                            })

                df_cond = pd.DataFrame(lista_conductas)

                if not df_cond.empty:
                    anio_max_cond = str(max(anios_sel))
                    df_ref_cond = df_cond[df_cond['Año'] == anio_max_cond].sort_values(by='Porcentaje', ascending=True)
                    orden_cond = df_ref_cond['Conducta'].tolist()

                    fig_cond = px.bar(
                        df_cond,
                        x='Porcentaje',
                        y='Conducta',
                        color='Año',
                        barmode='group',
                        orientation='h',
                        color_discrete_map=colores_años,
                        text=df_cond['Porcentaje'].apply(lambda x: f'{x:.1f}%'),
                        title=f"Conductas observadas en el entorno de {muni_sel}",
                        labels={'Porcentaje': '% de la Población', 'Conducta': 'Conducta Observada'},
                        category_orders={"Conducta": orden_cond}
                    )

                    fig_cond.update_layout(height=850, margin=dict(l=250))
                    fig_cond.update_traces(textposition='outside')
                    st.plotly_chart(fig_cond, use_container_width=True)
                    
                    with st.expander("Ver tabla de datos (Conductas)"):
                        tabla_pivot_cond = df_cond.pivot(index='Conducta', columns='Año', values='Porcentaje')
                        st.dataframe(tabla_pivot_cond.style.format("{:.1f}%"))

                        
                
            elif subtema_envipe == "Desempeño Institucional":
                
                # --- TÍTULO Y INTRODUCCIÓN GENERAL ---
                st.title("🏢 Desempeño Institucional y Percepción de Autoridades")
                
                st.markdown(f"""
                Esta sección analiza la relación entre la ciudadanía de **{muni_sel}** y las autoridades de seguridad pública y justicia. 
                A través de los siguientes indicadores, se evalúa la legitimidad y eficiencia institucional:
                
                * **Acciones Municipales:** Evaluación de actividades preventivas y de vigilancia local.
                * **Confianza e Identificación:** Nivel de credibilidad de las instituciones (Marina, Ejército, Policías).
                * **Percepción de Corrupción:** Opinión sobre la integridad de los servidores públicos.
                * **Efectividad:** Valoración del desempeño operativo de cada autoridad.
                """)
                
                st.markdown("---")

                dict_acciones = {
                    'AP5_1_01': 'Construcción de parques y canchas',
                    'AP5_1_02': 'Mejorar el alumbrado',
                    'AP5_1_03': 'Mejorar ingreso de las familias',
                    'AP5_1_04': 'Atender el desempleo',
                    'AP5_1_05': 'Atender a jóvenes para disminuir pandillerismo',
                    'AP5_1_06': 'Organización vecinal para seguridad privada',
                    'AP5_1_07': 'Implementar policía de barrio',
                    'AP5_1_08': 'Operativos contra delincuencia',
                    'AP5_1_09': 'Programación de sensibilización para denuncias',
                    'AP5_1_10': 'Mayor patrullaje',
                    'AP5_1_11': 'Combatir la corrupción',
                    'AP5_1_12': 'Combatir el narcotráfico',
                    'AP5_1_13': 'Programas deportivos, culturales, sociales',
                    'AP5_1_14': 'Otra'
                }

                lista_acciones = []
                for anio in anios_sel:
                    df_year = df_filtrado[df_filtrado['ANIO_ESTADISTICO'] == anio].copy()
                    total_ele = df_year['FAC_ELE'].sum()
                    
                    for col_id, nombre_accion in dict_acciones.items():
                        if col_id in df_year.columns:
                            df_year[col_id] = pd.to_numeric(df_year[col_id], errors='coerce').fillna(0)
                            suma_expandida = df_year[df_year[col_id] == 1]['FAC_ELE'].sum()
                            porcentaje = (suma_expandida / total_ele) * 100 if total_ele > 0 else 0
                            
                            lista_acciones.append({
                                'Año': str(anio),
                                'Acción': nombre_accion,
                                'Porcentaje': porcentaje
                            })

                df_acc = pd.DataFrame(lista_acciones)

                if not df_acc.empty:
                    anio_max_acc = str(max(anios_sel))
                    df_ref_acc = df_acc[df_acc['Año'] == anio_max_acc].sort_values(by='Porcentaje', ascending=True)
                    orden_acciones = df_ref_acc['Acción'].tolist()

                    st.subheader("📊 Evolución de la Percepción de Acciones (Respuesta: 'Sí sabe')")
                    
                    fig_acc = px.bar(
                        df_acc,
                        x='Porcentaje',
                        y='Acción',
                        color='Año',
                        barmode='group',
                        orientation='h',
                        text=df_acc['Porcentaje'].apply(lambda x: f'{x:.1f}%'),
                        labels={'Porcentaje': 'Población (%)', 'Acción': 'Acción Municipal'},
                        color_discrete_map=colores_años, # Usamos tus colores definidos
                        category_orders={"Acción": orden_acciones} 
                    )

                    fig_acc.update_layout(
                        height=700,
                        yaxis={'categoryorder': 'array', 'categoryarray': orden_acciones},
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        margin=dict(l=220),
                        xaxis_range=[0, 100]
                    )
                    
                    fig_acc.update_traces(textposition='outside', textfont_size=11)
                    st.plotly_chart(fig_acc, use_container_width=True)

                    with st.expander("Ver tabla de datos detallada (Acciones Municipales)"):
                        tabla_pivot_acc = df_acc.pivot(index='Acción', columns='Año', values='Porcentaje')
                        st.dataframe(tabla_pivot_acc.style.format("{:.1f}%"))
                        st.info("Nota: Los porcentajes corresponden únicamente a la respuesta '1: Sí sabe que se realizó'.")

                # ==============================================================================
                # SECCIÓN 6: CONFIANZA EN LAS AUTORIDADES (NUEVA)
                # ==============================================================================
                st.markdown("---")
                st.header("🛡️ Percepción de Confianza en las Autoridades")
                st.caption(f"Mostrando datos de: **{muni_sel}**")
                st.info("Porcentaje de la población que manifiesta tener **'Mucha'** o **'Algo'** de confianza en cada institución.")

                # Mapeo corregido según el cambio de variables de INEGI
                MAPEO_AUTORIDADES = {
                    "2021": {
                        "AP5_4_01": "Policía de Tránsito Municipal",
                        "AP5_4_02": "Policía Preventiva Municipal",
                        "AP5_4_03": "Policía Estatal",
                        "AP5_4_04": "Policía Ministerial o Judicial",
                        "AP5_4_05": "Guardia Nacional", # En 2021 la GN solía ser la 05
                        "AP5_4_06": "Ministerio Público (MP) y Fiscalías Estatales", 
                        "AP5_4_07": "Fiscalía General de la República(FGR)",
                        "AP5_4_08": "Ejército"
                    },
                    "DEFAULT": { 
                        "AP5_4_01": "Policía de Tránsito Municipal",
                        "AP5_4_02": "Policía Preventiva Municipal",
                        "AP5_4_03": "Policía Estatal",
                        "AP5_4_04": "Guardia Nacional",
                        "AP5_4_05": "Policía Ministerial o Judicial",
                        "AP5_4_06": "Ministerio Público (MP) y Fiscalías Estatales",
                        "AP5_4_07": "Fiscalía General de la República(FGR)",
                        "AP5_4_08": "Ejército"
                    }
                }

                lista_confianza = []
                for anio in anios_sel:
                    df_year = df_filtrado[df_filtrado['ANIO_ESTADISTICO'] == anio].copy()
                    str_anio = str(anio)
                    
                    # Seleccionar el diccionario correcto para este año
                    dict_anio = MAPEO_AUTORIDADES.get(str_anio, MAPEO_AUTORIDADES["DEFAULT"])
                    
                    for col_id, nombre_auth in dict_anio.items():
                        # Generamos la columna de identificación (AP5_3) basada en la de confianza (AP5_4)
                        col_ident = col_id.replace('AP5_4_', 'AP5_3_')
                        
                        if col_id in df_year.columns and col_ident in df_year.columns:
                            df_year[col_id] = pd.to_numeric(df_year[col_id], errors='coerce')
                            df_year[col_ident] = pd.to_numeric(df_year[col_ident], errors='coerce')
                            
                            # Aplicamos el doble filtro (Identifica + Respuesta válida)
                            df_validos = df_year[
                                (df_year[col_ident] == 1) & 
                                (df_year[col_id].isin([1, 2, 3, 4, 9]))
                            ]
                            
                            denominador_real = df_validos['FAC_ELE'].sum()
                            confianza_exp = df_validos[df_validos[col_id].isin([1, 2])]['FAC_ELE'].sum()
                            
                            porcentaje = (confianza_exp / denominador_real) * 100 if denominador_real > 0 else 0
                            
                            lista_confianza.append({
                                'Año': str_anio,
                                'Autoridad': nombre_auth, # Aquí el nombre ya viene corregido por año
                                'Confianza': porcentaje
                            })

                df_conf = pd.DataFrame(lista_confianza)

                if not df_conf.empty:
                    # Ordenar por el año más reciente para ver la autoridad más confiable arriba
                    anio_max_conf = str(max(anios_sel))
                    df_ref_conf = df_conf[df_conf['Año'] == anio_max_conf].sort_values(by='Confianza', ascending=True)
                    orden_confianza = df_ref_conf['Autoridad'].tolist()

                    st.subheader("📊 Evolución del Nivel de Confianza (Tasa de Aceptación)")
                    
                    fig_conf = px.bar(
                        df_conf,
                        x='Confianza',
                        y='Autoridad',
                        color='Año',
                        barmode='group',
                        orientation='h',
                        color_discrete_map=colores_años, # Respetamos tus colores
                        text=df_conf['Confianza'].apply(lambda x: f'{x:.1f}%'),
                        labels={'Confianza': 'Población que Confía (%)', 'Autoridad': 'Institución'},
                        category_orders={"Autoridad": orden_confianza}
                    )

                    fig_conf.update_layout(
                        height=750, 
                        margin=dict(l=220),
                        xaxis_range=[0, 100] # Eje X de 0 a 100%
                    )
                    fig_conf.update_traces(textposition='outside')
                    st.plotly_chart(fig_conf, use_container_width=True)
                    
                    with st.expander("Ver tabla de datos detallada (Confianza Institucional)"):
                        tabla_pivot_conf = df_conf.pivot(index='Autoridad', columns='Año', values='Confianza')
                        st.dataframe(tabla_pivot_conf.style.format("{:.1f}%"))
                        st.info("Nota: La tasa se calcula como (Mucha + Algo de Confianza) / (Total de respuestas válidas 1-4). Se excluyen 'No sabe' y 'Blancos'.")

                    # ==============================================================================
                # SECCIÓN 7: PERCEPCIÓN DE CORRUPCIÓN EN LAS AUTORIDADES
                # ==============================================================================
                st.markdown("---")
                st.header("📉 Percepción de Corrupción")
                st.caption(f"Mostrando datos de: **{muni_sel}**")
                st.info("Porcentaje de la población que considera que la autoridad **SÍ** es corrupta, calculado sobre quienes identifican a la institución.")

                lista_corrupcion = []
                for anio in anios_sel:
                    df_year = df_filtrado[df_filtrado['ANIO_ESTADISTICO'] == anio].copy()
                    str_anio = str(anio)
                    
                    # Usamos el mapeador dinámico que ya definimos para Confianza
                    dict_anio = MAPEO_AUTORIDADES.get(str_anio, MAPEO_AUTORIDADES["DEFAULT"])
                    
                    for col_conf, nombre_auth in dict_anio.items():
                        # Transformamos AP5_4_XX (Confianza) a AP5_5_XX (Corrupción)
                        col_corr = col_conf.replace('AP5_4_', 'AP5_5_')
                        # Transformamos AP5_4_XX (Confianza) a AP5_3_XX (Identificación)
                        col_ident = col_conf.replace('AP5_4_', 'AP5_3_')
                        
                        if col_corr in df_year.columns and col_ident in df_year.columns:
                            # 1. Limpieza de datos
                            df_year[col_corr] = pd.to_numeric(df_year[col_corr], errors='coerce')
                            df_year[col_ident] = pd.to_numeric(df_year[col_ident], errors='coerce')
                            
                            # 2. FILTRO DE IDENTIFICACIÓN Y RESPUESTA VÁLIDA
                            # Solo quienes conocen a la autoridad (1) y respondieron Sí (1) o No (2)
                            df_validos = df_year[
                                (df_year[col_ident] == 1) & 
                                (df_year[col_corr].isin([1, 2, 9]))
                            ]
                            
                            # 3. Denominador: Población que respondió Sí o No
                            total_respuestas_exp = df_validos['FAC_ELE'].sum()
                            
                            # 4. Numerador: Solo los que respondieron "Sí es corrupta" (1)
                            corruptos_exp = df_validos[df_validos[col_corr] == 1]['FAC_ELE'].sum()
                            
                            # 5. Cálculo del porcentaje
                            porcentaje = (corruptos_exp / total_respuestas_exp) * 100 if total_respuestas_exp > 0 else 0
                            
                            lista_corrupcion.append({
                                'Año': str_anio,
                                'Autoridad': nombre_auth,
                                'Percepción de Corrupción': porcentaje
                            })

                df_corr = pd.DataFrame(lista_corrupcion)

                if not df_corr.empty:
                    # Ordenar por el año más reciente (Autoridad percibida como más corrupta arriba)
                    anio_max_corr = str(max(anios_sel))
                    df_ref_corr = df_corr[df_corr['Año'] == anio_max_corr].sort_values(by='Percepción de Corrupción', ascending=True)
                    orden_corrupcion = df_ref_corr['Autoridad'].tolist()

                    st.subheader("📊 ¿Qué autoridades se perciben como más corruptas?")
                    
                    fig_corr = px.bar(
                        df_corr,
                        x='Percepción de Corrupción',
                        y='Autoridad',
                        color='Año',
                        barmode='group',
                        orientation='h',
                        color_discrete_map=colores_años,
                        text=df_corr['Percepción de Corrupción'].apply(lambda x: f'{x:.1f}%'),
                        labels={'Percepción de Corrupción': 'Población que percibe corrupción (%)', 'Autoridad': 'Institución'},
                        category_orders={"Autoridad": orden_corrupcion}
                    )

                    fig_corr.update_layout(
                        height=750, 
                        margin=dict(l=220),
                        xaxis_range=[0, 100]
                    )
                    fig_corr.update_traces(textposition='outside')
                    st.plotly_chart(fig_corr, use_container_width=True)
                    
                    with st.expander("Ver tabla de datos detallada (Percepción de Corrupción)"):
                        tabla_pivot_corr = df_corr.pivot(index='Autoridad', columns='Año', values='Percepción de Corrupción')
                        st.dataframe(tabla_pivot_corr.style.format("{:.1f}%"))
                        st.warning("Nota: Este indicador mide la percepción subjetiva de la población, no necesariamente hechos delictivos comprobados.")

                # ==============================================================================
                # SECCIÓN 8: PERCEPCIÓN DE EFECTIVIDAD EN EL DESEMPEÑO
                # ==============================================================================
                st.markdown("---")
                st.header("📈 Efectividad del Desempeño Institucional")
                st.caption(f"Mostrando datos de: **{muni_sel}**")
                st.info("Porcentaje de la población que considera el desempeño de la autoridad como **'Muy'** o **'Algo'** efectivo.")

                lista_desempeno = []
                for anio in anios_sel:
                    df_year = df_filtrado[df_filtrado['ANIO_ESTADISTICO'] == anio].copy()
                    str_anio = str(anio)
                    
                    # Usamos el mapeador dinámico definido para Confianza (AP5_4)
                    dict_anio = MAPEO_AUTORIDADES.get(str_anio, MAPEO_AUTORIDADES["DEFAULT"])
                    
                    for col_conf, nombre_auth in dict_anio.items():
                        # Transformamos AP5_4_XX (Confianza) a AP5_6_XX (Desempeño)
                        col_des = col_conf.replace('AP5_4_', 'AP5_6_')
                        # Transformamos AP5_4_XX (Confianza) a AP5_3_XX (Identificación)
                        col_ident = col_conf.replace('AP5_4_', 'AP5_3_')
                        
                        if col_des in df_year.columns and col_ident in df_year.columns:
                            # 1. Limpieza de datos
                            df_year[col_des] = pd.to_numeric(df_year[col_des], errors='coerce')
                            df_year[col_ident] = pd.to_numeric(df_year[col_ident], errors='coerce')
                            
                            # 2. FILTRO DE IDENTIFICACIÓN Y RESPUESTA VÁLIDA (1 al 4)
                            # Excluimos 9 (No sabe) y vacíos para el denominador
                            df_validos = df_year[
                                (df_year[col_ident] == 1) & 
                                (df_year[col_des].isin([1, 2, 3, 4]))
                            ]
                            
                            # 3. Denominador: Población con respuesta válida
                            total_validos_exp = df_validos['FAC_ELE'].sum()
                            
                            # 4. Numerador: Muy efectivo (1) + Algo efectivo (2)
                            efectivo_exp = df_validos[df_validos[col_des].isin([1, 2])]['FAC_ELE'].sum()
                            
                            # 5. Cálculo
                            porcentaje = (efectivo_exp / total_validos_exp) * 100 if total_validos_exp > 0 else 0
                            
                            lista_desempeno.append({
                                'Año': str_anio,
                                'Autoridad': nombre_auth,
                                'Efectividad': porcentaje
                            })

                df_des = pd.DataFrame(lista_desempeno)

                if not df_des.empty:
                    # Ordenar por el año más reciente (Autoridad más efectiva arriba)
                    anio_max_des = str(max(anios_sel))
                    df_ref_des = df_des[df_des['Año'] == anio_max_des].sort_values(by='Efectividad', ascending=True)
                    orden_desempeno = df_ref_des['Autoridad'].tolist()

                    st.subheader("📊 Nivel de Efectividad Percibida por Institución")
                    
                    fig_des = px.bar(
                        df_des,
                        x='Efectividad',
                        y='Autoridad',
                        color='Año',
                        barmode='group',
                        orientation='h',
                        color_discrete_map=colores_años,
                        text=df_des['Efectividad'].apply(lambda x: f'{x:.1f}%'),
                        labels={'Efectividad': 'Población que percibe desempeño efectivo (%)', 'Autoridad': 'Institución'},
                        category_orders={"Autoridad": orden_desempeno}
                    )

                    fig_des.update_layout(
                        height=750, 
                        margin=dict(l=220),
                        xaxis_range=[0, 100]
                    )
                    fig_des.update_traces(textposition='outside')
                    st.plotly_chart(fig_des, use_container_width=True)
                    
                    with st.expander("Ver tabla de datos detallada (Efectividad del Desempeño)"):
                        tabla_pivot_des = df_des.pivot(index='Autoridad', columns='Año', values='Efectividad')
                        st.dataframe(tabla_pivot_des.style.format("{:.1f}%"))
                        st.info("Nota: La efectividad se define como la suma de las categorías 'Muy efectivo' y 'Algo efectivo'.")

                # ==============================================================================
                # SECCIÓN 9: CONFIANZA EN CÁRCELES Y RECLUSORIOS
                # ==============================================================================
                st.markdown("---")
                st.header("🏢 Confianza en el Sistema Penitenciario")
                st.caption(f"Mostrando datos de: **{muni_sel}** (Series 2024-2025)")
                st.info("Porcentaje de la población que manifiesta tener **'Mucha'** o **'Algo'** de confianza en las cárceles y reclusorios.")

                lista_carceles = []
                # Filtramos los años seleccionados para que solo procese 2024 y posteriores
                anios_validos_carceles = [a for a in anios_sel if int(a) >= 2024]

                for anio in anios_validos_carceles:
                    df_year = df_filtrado[df_filtrado['ANIO_ESTADISTICO'] == anio].copy()
                    str_anio = str(anio)
                    
                    if 'AP5_9' in df_year.columns:
                        # 1. Limpieza y conversión
                        df_year['AP5_9'] = pd.to_numeric(df_year['AP5_9'], errors='coerce')
                        
                        # 2. Filtro de respuestas válidas (1 al 4)
                        df_validos = df_year[df_year['AP5_9'].isin([1, 2, 3, 4])]
                        
                        # 3. Denominador
                        total_validos_exp = df_validos['FAC_ELE'].sum()
                        
                        # 4. Numerador (Mucha + Alguna)
                        confianza_exp = df_validos[df_validos['AP5_9'].isin([1, 2])]['FAC_ELE'].sum()
                        
                        # 5. Cálculo
                        porcentaje = (confianza_exp / total_validos_exp) * 100 if total_validos_exp > 0 else 0
                        
                        lista_carceles.append({
                            'Año': str_anio,
                            'Confianza': porcentaje
                        })

                df_carc = pd.DataFrame(lista_carceles)

                if not df_carc.empty:
                    st.subheader("📊 Evolución de la confianza en Cárceles (Datos disponibles)")
                    
                    fig_carc = px.bar(
                        df_carc,
                        x='Año',
                        y='Confianza',
                        color='Año',
                        color_discrete_map=colores_años,
                        text=df_carc['Confianza'].apply(lambda x: f'{x:.1f}%'),
                        title=f"Confianza en Sistema Penitenciario - {muni_sel}",
                        labels={'Confianza': '% Confianza', 'Año': 'Año'}
                    )

                    fig_carc.update_layout(
                        yaxis_range=[0, 100], 
                        showlegend=False,
                        height=400 # Gráfica un poco más compacta al ser de menos años
                    )
                    fig_carc.update_traces(textposition='outside')
                    st.plotly_chart(fig_carc, use_container_width=True)
                    
                    with st.expander("Ver detalle técnico (Cárceles)"):
                        st.dataframe(df_carc.set_index('Año').T.style.format("{:.1f}%"))
                else:
                    st.warning("No hay datos disponibles para la variable de cárceles en los años seleccionados (requiere 2024 o 2025).")

except Exception as e:
    st.error(f"Error en la comparativa: {e}")
