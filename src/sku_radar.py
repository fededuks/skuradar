# src/sku_radar.py
import pandas as pd
import requests
from fuzzywuzzy import fuzz

# Configuración
TIPO_CAMBIO_USD = 950  # Puedes actualizarlo desde una API después
COMISION_ML = 0.13      # 13% comisión aproximada en ML
COSTO_ENVIO_ESTIMADO = 800  # En ARS
ML_SITE = "MLA"         # MercadoLibre Argentina

def cargar_proveedores(ruta):
    """Carga y procesa el archivo Excel de proveedores"""
    df = pd.read_excel(ruta)
    # Aseguramos que las columnas clave existan
    if 'Precio USD' in df.columns:
        df['Precio ARS'] = df['Precio USD'] * TIPO_CAMBIO_USD
    elif 'Precio ARS' not in df.columns:
        raise ValueError("Falta columna 'Precio USD' o 'Precio ARS'")
    
    # Normalización
    df['Descripción'] = df['Descripción'].str.lower().str.strip()
    return df

def buscar_en_ml(query):
    """Busca un producto en MercadoLibre usando la API"""
    url = f"https://api.mercadolibre.com/sites/{ML_SITE}/search"
    params = {"q": query, "limit": 1}
    headers = {"User-Agent": "SKUradar/1.0"}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                item = data['results'][0]
                return {
                    'precio_ml': item['price'],
                    'url': item['permalink'],
                    'condicion': item['condition'],
                    'ventas': item.get('sold_quantity', 0),
                    'titulo': item['title']
                }
    except Exception as e:
        print(f"Error al buscar en ML: {e}")
    return None

def calcular_rentabilidad(precio_prov_ars, precio_ml):
    """Calcula diferencial, margen y ganancia neta"""
    if precio_ml <= 0:
        return 0, 0, 0
    
    costo_total = precio_prov_ars + COSTO_ENVIO_ESTIMADO
    comision = precio_ml * COMISION_ML
    ganancia = precio_ml - costo_total - comision
    margen = (ganancia / precio_ml * 100) if precio_ml > 0 else 0
    diferencial = precio_ml - precio_prov_ars
    
    return round(diferencial, 2), round(margen, 2), round(ganancia, 2)

def analizar_catalogo(ruta_archivo):
    """Analiza todo el catálogo de proveedores"""
    try:
        df_prov = cargar_proveedores(ruta_archivo)
    except Exception as e:
        print(f"Error al cargar archivo: {e}")
        return pd.DataFrame()

    resultados = []
    
    for _, row in df_prov.iterrows():
        print(f"🔍 Buscando: {row['Descripción']} (SKU: {row.get('SKU', 'N/A')})")
        
        # Búsqueda inteligente: primero por SKU, luego por descripción
        query = str(row.get('SKU', '')) if pd.notna(row.get('SKU')) else row['Descripción']
        resultado_api = buscar_en_ml(query)
        
        if not resultado_api:
            # Intento secundario con solo la descripción
            resultado_api = buscar_en_ml(row['Descripción'])
        
        if resultado_api:
            diferencial, margen, ganancia = calcular_rentabilidad(
                row['Precio ARS'], resultado_api['precio_ml']
            )
            resultados.append({
                'SKU': row.get('SKU', 'N/D'),
                'Descripción Proveedor': row['Descripción'].title(),
                'Precio Proveedor (ARS)': row['Precio ARS'],
                'Título en ML': resultado_api['titulo'],
                'Precio ML (ARS)': resultado_api['precio_ml'],
                'Ventas Estimadas': resultado_api['ventas'],
                'Condición': 'Nuevo' if resultado_api['condicion'] == 'new' else 'Usado',
                'Diferencial (ARS)': diferencial,
                'Margen (%)': margen,
                'Ganancia Estimada (ARS)': ganancia,
                'URL': resultado_api['url']
            })
        else:
            resultados.append({
                'SKU': row.get('SKU', 'N/D'),
                'Descripción Proveedor': row['Descripción'].title(),
                'Precio Proveedor (ARS)': row['Precio ARS'],
                'Título en ML': 'No encontrado',
                'Precio ML (ARS)': 0,
                'Ventas Estimadas': 0,
                'Condición': '',
                'Diferencial (ARS)': 0,
                'Margen (%)': 0,
                'Ganancia Estimada (ARS)': 0,
                'URL': ''
            })
    
    # Crear DataFrame y ordenar por margen
    df_resultado = pd.DataFrame(resultados)
    df_resultado = df_resultado[df_resultado['Precio ML (ARS)'] > 0]  # Filtrar no encontrados
    df_resultado = df_resultado.sort_values(by='Margen (%)', ascending=False)
    
    # Guardar en la carpeta results
    output_file = f"../results/skuradar_resultados_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx"
    try:
        df_resultado.to_excel(output_file, index=False)
        print(f"✅ Resultados guardados en: {output_file}")
    except Exception as e:
        print(f"❌ No se pudo guardar el archivo: {e}")
    
    return df_resultado