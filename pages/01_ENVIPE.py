import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ENVIPE Morelos - Comparativa", layout="wide")

st.title("🛡️ Comparativa Interanual de Preocupaciones - Morelos")
st.markdown("---")

@st.cache_data
def load_persona_data():
    ruta = "data/MAESTRA_TPer_Vic1_MORELOS_2021_2025.csv"
    df = pd.read_csv(ruta, low_memory=False)
    df.columns = [c.upper() for c in df.columns]
    return df

try:
    df_per = load_persona_data()

    # 1. Filtro Multiselect de Años
    st.sidebar.header("Configuración del Análisis")
    anios_disponibles = sorted(df_per['ANIO_ESTADISTICO'].unique())
    anios_sel = st.sidebar.multiselect(
        "Seleccione los años para comparar:",
        options=anios_disponibles,
        default=anios_disponibles[-2:] # Por defecto los últimos dos años
    )

    if not anios_sel:
        st.warning("⚠️ Por favor, seleccione al menos un año en el menú lateral.")
    else:
        # 2. Definición de Temas
        dict_preocupaciones = {
            'AP4_2_01': 'Pobreza', 'AP4_2_02': 'Desempleo', 'AP4_2_03': 'Narcotráfico',
            'AP4_2_04': 'Aumento de Precios', 'AP4_2_05': 'Inseguridad', 'AP4_2_06': 'Desastres Naturales',
            'AP4_2_07': 'Escasez de Agua', 'AP4_2_08': 'Corrupción', 'AP4_2_09': 'Educación',
            'AP4_2_10': 'Salud', 'AP4_2_11': 'Falta de Castigo a Delincuentes', 'AP4_2_12': 'Otro',
            'AP4_2_13': 'Ninguno', 'AP4_2_99': 'Sin respuesta'
        }

        # 3. Procesamiento Agrupado por Año
        lista_comparativa = []
        
        for anio in anios_sel:
            df_year = df_per[df_per['ANIO_ESTADISTICO'] == anio].copy()
            total_ele = df_year['FAC_ELE'].sum()
            
            for col_id, nombre in dict_preocupaciones.items():
                if col_id in df_year.columns:
                    df_year[col_id] = pd.to_numeric(df_year[col_id], errors='coerce').fillna(0)
                    # Calculamos el total expandido para este año y este tema
                    suma_expandida = df_year[df_year[col_id] == 1]['FAC_ELE'].sum()
                    porcentaje = (suma_expandida / total_ele) * 100 if total_ele > 0 else 0
                    
                    lista_comparativa.append({
                        'Año': str(anio),
                        'Tema': nombre,
                        'Porcentaje': porcentaje
                    })

        df_comp = pd.DataFrame(lista_comparativa)

        # 4. Procesamiento de Ordenamiento (INVERSIÓN FORZADA)
        if not df_comp.empty:
            # 1. Definimos lo que queremos HASTA ABAJO del gráfico
            categorias_final = ['NS/NR', 'Sin respuesta', 'Ninguno', 'Otro', 'Desastres']
            
            # 2. Obtenemos el resto de los temas (los importantes)
            todos_los_temas = df_comp['Tema'].unique().tolist()
            temas_importantes = [t for t in todos_los_temas if t not in categorias_final]
            
            # 3. Ordenamos los importantes por el porcentaje del año más reciente (de menor a mayor)
            # Al ser de menor a mayor, el más alto quedará al final de esta sub-lista
            anio_max = str(max(anios_sel))
            df_ref = df_comp[df_comp['Año'] == anio_max].sort_values(by='Porcentaje', ascending=True)
            orden_principales = [t for t in df_ref['Tema'].tolist() if t in temas_importantes]
            
            # 4. Procesamiento de Ordenamiento (INVERSIÓN FORZADA)
        if not df_comp.empty:
            # 1. Definimos lo que queremos HASTA ABAJO del gráfico
            categorias_final = ['NS/NR', 'Sin respuesta', 'Ninguno', 'Otro', 'Desastres']
            
            # 2. Obtenemos el resto de los temas (los importantes)
            todos_los_temas = df_comp['Tema'].unique().tolist()
            temas_importantes = [t for t in todos_los_temas if t not in categorias_final]
            
            # 3. Ordenamos los importantes por el porcentaje del año más reciente (de menor a mayor)
            # Al ser de menor a mayor, el más alto quedará al final de esta sub-lista
            anio_max = str(max(anios_sel))
            df_ref = df_comp[df_comp['Año'] == anio_max].sort_values(by='Porcentaje', ascending=True)
            orden_principales = [t for t in df_ref['Tema'].tolist() if t in temas_importantes]
            
            # 4. CONSTRUCCIÓN DEL ORDEN (De abajo hacia arriba)
            # Primero ponemos los de "relleno", luego los importantes (el más alto queda al final = ARRIBA)
            orden_final = [t for t in categorias_final if t in todos_los_temas] + orden_principales

            # 5. Gráfica
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
                category_orders={"Tema": orden_final} # Aplicamos el orden construido
            )

            # --- TRUCO ADICIONAL PARA INVERTIR EL EJE SI FUERA NECESARIO ---
            fig.update_layout(
                height=800,
                yaxis={'categoryorder':'array', 'categoryarray': orden_final},
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=200)
            )
            
            fig.update_traces(textposition='outside', textfont_size=11)
            st.plotly_chart(fig, use_container_width=True)

            # 6. Tabla de datos (Opcional)
            with st.expander("Ver tabla comparativa detallada"):
                tabla_pivot = df_comp.pivot(index='Tema', columns='Año', values='Porcentaje')
                st.dataframe(tabla_pivot.style.format("{:.1f}%"))

except Exception as e:
    st.error(f"Error en la comparativa: {e}")