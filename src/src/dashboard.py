# src/dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime
from sku_radar import analizar_catalogo
import os

# Asegurar que existan las carpetas
if not os.path.exists("uploads"):
    os.makedirs("uploads")
if not os.path.exists("results"):
    os.makedirs("results")

# Configuración de la página
st.set_page_config(
    page_title="SKUradar",
    page_icon="🔍",
    layout="wide"
)

# Título y descripción
st.title("🔍 SKUradar - Sistema de Oportunidades en MercadoLibre")
st.markdown("""
**Automatiza tu estrategia de ventas** comparando precios de proveedores con MercadoLibre.  
Encuentra productos *winners* con alto margen y potencial de venta.
""")

# Subida de archivo
uploaded_file = st.file_uploader(
    "📤 Sube tu archivo Excel de proveedores (.xlsx)",
    type=["xlsx"],
    help="El archivo debe tener columnas: SKU, Descripción, Precio USD o Precio ARS"
)

if uploaded_file:
    st.success("✅ Archivo cargado correctamente")
    
    # Mostrar vista previa
    df = pd.read_excel(uploaded_file)
    st.write("### 📄 Vista previa del archivo")
    st.dataframe(df.head(10), use_container_width=True)

    # Botón de análisis
    if st.button("🚀 Analizar en MercadoLibre"):
        with st.spinner("🔍 Buscando productos en MercadoLibre... (esto puede tardar)"):
            # Guardar temporalmente
            temp_path = "uploads/temp_proveedores.xlsx"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Ejecutar análisis
            df_resultado = analizar_catalogo(temp_path)
        
        if not df_resultado.empty:
            st.success("✅ Análisis completado")
            st.write("### 🏆 Productos con Mayor Potencial")

            # Mostrar resultados
            st.dataframe(
                df_resultado,
                column_config={
                    "URL": st.column_config.LinkColumn("Ver en ML")
                },
                use_container_width=True
            )

            # Gráfico de top 10
            st.write("### 📊 Top 10 por Margen de Ganancia")
            top10 = df_resultado.head(10)
            st.bar_chart(top10.set_index('SKU')['Margen (%)'])

            # Descarga
            @st.cache_data
            def convert_df_to_excel(df):
                return df.to_excel(index=False).encode('utf-8')

            excel_data = convert_df_to_excel(df_resultado)
            st.download_button(
                label="⬇️ Descargar resultados como Excel",
                data=excel_data,
                file_name=f"skuradar_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No se encontraron productos válidos.")