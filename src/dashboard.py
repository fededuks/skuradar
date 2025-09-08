# src/dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime
from sku_radar import analizar_catalogo
import os

# === Configuración de carpetas ===
if not os.path.exists("uploads"):
    os.makedirs("uploads")
if not os.path.exists("results"):
    os.makedirs("results")

# === Configuración de la página ===
st.set_page_config(
    page_title="SKUradar",
    page_icon="🔍",
    layout="wide"
)

# === Título y descripción ===
st.title("🔍 SKUradar - Detecta Productos Winners")
st.markdown("""
**Automatiza tu estrategia en MercadoLibre**  
Sube tu lista de proveedores y compara precios con vendedores reales para encontrar **productos con alto margen de ganancia**.
""")

# === Subida de archivo ===
uploaded_file = st.file_uploader(
    "📤 Sube tu archivo Excel de proveedores (.xlsx)",
    type=["xlsx"],
    help="El archivo debe tener columnas: SKU, Descripción, Precio USD"
)

if uploaded_file:
    st.success("✅ Archivo cargado correctamente")

    # Vista previa del archivo
    df = pd.read_excel(uploaded_file)
    st.write("### 📄 Vista previa del archivo")
    st.dataframe(df.head(10), width="stretch")

    # Botón de análisis
    if st.button("🚀 Analizar en MercadoLibre"):
        with st.spinner("🔍 Buscando productos en MercadoLibre... Esto puede tardar unos segundos."):
            # Guardar temporalmente
            temp_path = "uploads/temp_proveedores.xlsx"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Ejecutar análisis
            df_resultado = analizar_catalogo(temp_path)
        
        if not df_resultado.empty:
            st.success("✅ Análisis completado con éxito")
            st.write("### 🏆 Productos con Mayor Potencial")

            # Mostrar resultados
            st.dataframe(
                df_resultado,
                column_config={
                    "URL": st.column_config.LinkColumn("Ver en ML")
                },
                width="stretch"
            )

            # Gráfico: Top 10 por margen
            st.write("### 📊 Top 10 Productos por Margen de Ganancia")
            top10 = df_resultado.head(10).set_index('SKU')['Margen (%)']
            st.bar_chart(top10, width="stretch")

            # Botón de descarga
            @st.cache_data
            def convertir_a_excel(df):
                return df.to_excel(index=False).encode("utf-8")

            excel_datos = convertir_a_excel(df_resultado)
            st.download_button(
                label="⬇️ Descargar resultados como Excel",
                data=excel_datos,
                file_name=f"skuradar_resultados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="full"
            )
        else:
            st.warning("⚠️ No se encontraron productos válidos en MercadoLibre. Verifica los nombres o intenta con otros productos.")
