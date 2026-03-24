import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ENVIPE Morelos - Comparativa", layout="wide")
st.title("🛡️ Análisis de Seguridad (ENVIPE) - Morelos")

import unicodedata # Añade esta importación al inicio de tu archivo

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

try:
    df_per = load_persona_data()

    # 1. Filtro Multiselect de Años en la Sidebar
    st.sidebar.header("Configuración del Análisis")
    anios_disponibles = sorted(df_per['ANIO_ESTADISTICO'].unique())
    anios_sel = st.sidebar.multiselect(
        "Seleccione los años para comparar:",
        options=anios_disponibles,
        default=anios_disponibles[-2:] # Por defecto los últimos dos años
    )

    # ==========================================
    # NUEVO BLOQUE: FILTRO DE MUNICIPIO (INSERTAR AQUÍ)
    # ==========================================
    st.sidebar.divider()
    st.sidebar.subheader("📍 Filtro Geográfico")
    
    # Al estar normalizados a .title(), la lista saldrá limpia y sin duplicados
    municipios_lista = sorted(df_per['NOM_MUN'].unique().tolist())
    
    muni_sel = st.sidebar.selectbox(
        "Seleccione un Municipio:",
        options=["Todo el Estado"] + municipios_lista
    )

    # Filtrado Global
    df_filtrado = df_per[df_per['ANIO_ESTADISTICO'].isin(anios_sel)].copy()

    if muni_sel != "Todo el Estado":
        df_filtrado = df_filtrado[df_filtrado['NOM_MUN'] == muni_sel]
    # ==========================================

    if not anios_sel:
        st.warning("⚠️ Por favor, seleccione al menos un año en el menú lateral.")
    else:
        # ==============================================================================
        # SECCIÓN 1: PREVALENCIA DELICTIVA EN HOGARES (NUEVA)
        # ==============================================================================
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
        # Definimos las variables necesarias para la nota fuera del bucle
        if not df_prev_h.empty:
            ultimo_dato = df_prev_h.iloc[-1] # Toma el último año de la lista analizada
            
            with st.expander("📝 Nota Metodológica sobre el cálculo de Prevalencia"):
                st.markdown(f"""
                **Consideraciones sobre los datos presentados:**
                
                1. **Fuente de Datos:** Este cálculo utiliza la base de datos de integrantes (`TPer_Vic1`) de la ENVIPE.
                2. **Universo de Estudio:** Se identificaron **{int(ultimo_dato['Base_Total']):,}** hogares estimados en Morelos para el año {ultimo_dato['Año']}, cifra que coincide con el marco muestral oficial de INEGI.
                3. **Variación en la Tasa:** La tasa calculada en este tablero ({ultimo_dato['Porcentaje']:.1f}%) presenta una variación respecto al boletín de prensa oficial (30.2%) debido a que el INEGI integra validaciones adicionales provenientes del **Módulo de Delitos (Tabla TVic)**.
                4. **Criterio de Identificación:** Se considera un hogar víctima aquel cuya entrevista fue clasificada con resultado **'A' (Con Victimización)** en la variable `RESUL_H`.
                5. **Años con datos nulos:** Algunas ediciones de la ENVIPE no consideran la totalidad de los municipios de la Entidad, por lo que al aplicar el fltro de "Municipio habrá algunos años que no muestren datos en las gráficas".
                
                *Este tablero prioriza la tendencia histórica y la comparativa entre años utilizando una metodología consistente sobre la base de integrantes.*
                """)

        st.markdown("---")
        st.header("🛡️ Percepciones de Principales Problemas en Morelos")
        st.caption(f"Mostrando datos de: **{muni_sel}**")

        # ==============================================================================
        # SECCIÓN 2: PREOCUPACIONES CIUDADANAS
        # ==============================================================================
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
            total_ele = df_year['FAC_ELE'].sum() # Preocupaciones usa FAC_ELE (Personas)
            
            for col_id, nombre in dict_preocupaciones.items():
                if col_id in df_year.columns:
                    df_year[col_id] = pd.to_numeric(df_year[col_id], errors='coerce').fillna(0)
                    suma_expandida = df_year[df_year[col_id] == 1]['FAC_ELE'].sum()
                    porcentaje = (suma_expandida / total_ele) * 100 if total_ele > 0 else 0
                    
                    lista_comparativa.append({
                        'Año': str(anio),
                        'Tema': nombre,
                        'Porcentaje': porcentaje
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
                df_comp,
                x='Porcentaje',
                y='Tema',
                color='Año',
                barmode='group',
                orientation='h',
                text=df_comp['Porcentaje'].apply(lambda x: f'{x:.1f}%'),
                labels={'Porcentaje': 'Porcentaje de la Población (%)', 'Tema': 'Problemática'},
                color_discrete_sequence=px.colors.qualitative.Safe,
                category_orders={"Tema": orden_final}
            )

            fig.update_layout(
                height=800,
                yaxis={'categoryorder':'array', 'categoryarray': orden_final},
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=200)
            )
            
            fig.update_traces(textposition='outside', textfont_size=11)
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("Ver tabla comparativa detallada"):
                tabla_pivot = df_comp.pivot(index='Tema', columns='Año', values='Porcentaje')
                st.dataframe(tabla_pivot.style.format("{:.1f}%"))

        # ==============================================================================
        # SECCIÓN 3: ACCIONES REALIZADAS POR EL MUNICIPIO
        # ==============================================================================
        st.markdown("---")
        st.header("🏢 Percepción de Acciones Municipales")
        st.caption(f"Mostrando datos de: **{muni_sel}**")
        st.markdown("""
            Esta sección analiza el porcentaje de la población que **sabe** o percibe 
            que su municipio ha realizado acciones específicas para mejorar la seguridad.
        """)

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
            # CAMBIO CRÍTICO: Usar df_filtrado en lugar de df_per
            df_year = df_filtrado[df_filtrado['ANIO_ESTADISTICO'] == anio].copy()
            
            total_ele = df_year['FAC_ELE'].sum()
            
            for col_id, nombre_accion in dict_acciones.items():
                if col_id in df_year.columns:
                    # Aseguramos que los datos sean numéricos
                    df_year[col_id] = pd.to_numeric(df_year[col_id], errors='coerce').fillna(0)
                    
                    # Filtramos donde la respuesta es 1 (Sí sabe) y sumamos el factor de expansión
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
                labels={'Porcentaje': 'Población que percibe la Acción (%)', 'Acción': 'Tipo de Acción Municipal'},
                color_discrete_sequence=px.colors.qualitative.Prism,
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
        # SECCIÓN 4: INSEGURIDAD EN ESPACIOS PÚBLICOS Y PRIVADOS
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
            # Usamos df_filtrado para que respete el municipio seleccionado
            df_year = df_filtrado[df_filtrado['ANIO_ESTADISTICO'] == anio].copy()
            total_ele = df_year['FAC_ELE'].sum()
            
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
            # Ordenar por el año más reciente para ver qué lugar es el más crítico
            anio_max_esp = str(max(anios_sel))
            orden_lugares = df_esp[df_esp['Año'] == anio_max_esp].sort_values(by='Porcentaje', ascending=True)['Lugar'].tolist()

            fig_esp = px.bar(
                df_esp,
                x='Porcentaje',
                y='Lugar',
                color='Año',
                barmode='group',
                orientation='h',
                text=df_esp['Porcentaje'].apply(lambda x: f'{x:.1f}%'),
                title=f"¿Qué tan inseguros se sienten en {muni_sel}?",
                labels={'Porcentaje': 'Población que se siente Insegura (%)', 'Lugar': 'Espacio Físico'},
                color_discrete_sequence=px.colors.qualitative.Bold,
                category_orders={"Lugar": orden_lugares}
            )

            fig_esp.update_layout(height=700, margin=dict(l=200))
            fig_esp.update_traces(textposition='outside')
            st.plotly_chart(fig_esp, use_container_width=True)
            
            with st.expander("Ver datos detallados por lugar"):
                st.dataframe(df_esp.pivot(index='Lugar', columns='Año', values='Porcentaje').style.format("{:.1f}%"))

except Exception as e:
    st.error(f"Error en la comparativa: {e}")
