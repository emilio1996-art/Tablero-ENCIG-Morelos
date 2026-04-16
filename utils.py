import streamlit as st
import os

def mostrar_logo_inegi():
    """
    Inserta el logo de INEGI desde la carpeta local assets.
    """
    ruta_logo = os.path.join("assets", "INEGI_Logotipo_8.png")

    aplicar_estilo_navegacion()
    
    with st.sidebar:
        if os.path.exists(ruta_logo):
            st.image(ruta_logo, use_container_width=True)
        else:
            st.error(f"No se encontró el logo en: {ruta_logo}")
        
        st.markdown("""
            <div style='text-align: center; margin-top: -15px;'>
                <p style='color: #004b8d; font-weight: bold; font-size: 14px; margin-bottom: 5px;'>
                    Sistema de Información Estadística
                </p>
                <p style='color: #7d7d7d; font-size: 12px;'>
                    Estado de Morelos
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()

def aplicar_estilo_navegacion():
    """
    Inyecta CSS para que los botones de navegación del menú lateral
    se vean institucionales y uniformes.
    """
    st.markdown("""
        <style>
            /* Cambiar el fondo de la opción seleccionada */
            [data-testid="stSidebarNavItems"] li div a span {
                color: #f0f2f6 !important; /* Texto claro */
                font-weight: 500;
            }
            
            /* Estilo para los botones (links) del menú lateral */
            [data-testid="stSidebarNavItems"] a {
                background-color: transparent;
                border-radius: 5px;
                margin-bottom: 5px;
                transition: all 0.3s ease;
            }

            /* Estilo cuando pasas el ratón (hover) */
            [data-testid="stSidebarNavItems"] a:hover {
                background-color: rgba(255, 255, 255, 0.1) !important;
                color: #ffffff !important;
            }

            /* Estilo de la página activa */
            [data-testid="stSidebarNavItems"] a[aria-current="page"] {
                background-color: #004b8d !important; /* Azul institucional INEGI */
                color: white !important;
                border-left: 5px solid #ffca28; /* Detalle amarillo para resaltar */
            }

            # /* Ocultar el texto "A" o el icono por defecto si prefieres algo más limpio */
            [data-testid="stSidebarNavSeparator"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
