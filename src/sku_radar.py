# sku_radar.py
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta

# === CONFIGURACIÓN ===
TIPO_CAMBIO_USD = 950  # Actualizar desde API si es necesario
COMISION_ML = 0.13      # 13% comisión aproximada
COSTO_ENVIO_ESTIMADO = 800  # ARS
ML_SITE = "MLA"        # MercadoLibre Argentina

# 🔐 CREDENCIALES DE MERCADOLIBRE (reemplaza con las tuyas)
CLIENT_ID = "6146933985950296"        # Ej: 1234567890123456
CLIENT_SECRET = "VsD3o7jllZSU4u68XnlMMpWCZQAYkSN3"  # Ej: ABC123...xyz

# Archivo para cachear el token
TOKEN_FILE = "ml_token_cache.json"

# === MÓDULO 1: Carga y Conversión de Datos ===
def cargar_proveedores(ruta):
    df = pd.read_excel(ruta)
    df['Precio ARS'] = df['Precio USD'] * TIPO_CAMBIO_USD
    df['Descripción'] = df['Descripción'].str.lower().str.strip()
    return df

# === MÓDULO 2: Gestión de Token de Acceso ===
def obtener_token():
    """Obtiene un access_token válido desde la API de MercadoLibre"""
    # Verificar si hay un token guardado y aún es válido
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                data = pd.read_json(f)
                expires_at = pd.to_datetime(data['expires_at'])
                if expires_at > datetime.now():
                    return data['access_token']
        except:
            pass  # Si falla, se obtiene uno nuevo

    # Si no hay token válido, pedir uno nuevo
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            access_token = data['access_token']
            expires_in = data['expires_in']  # en segundos (normalmente 21600 = 6h)
            expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min antes
            
            # Guardar token en caché
            with open(TOKEN_FILE, 'w') as f:
                pd.DataFrame([{
                    'access_token': access_token,
                    'expires_at': expires_at.isoformat()
                }]).to_json(f, indent=2)
            
            print("✅ Nuevo access_token obtenido y guardado.")
            return access_token
        else:
            print(f"❌ Error al obtener token: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción al obtener token: {e}")
    
    return None

# === MÓDULO 3: Búsqueda en MercadoLibre API (con autenticación) ===
def buscar_en_ml(query, access_token):
    url = f"https://api.mercadolibre.com/sites/{ML_SITE}/search"
    params = {"q": query, "limit": 1}
    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "SKUradar/1.0"
    }
    
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
        elif response.status_code == 401:
            print("⚠️ Token expirado. Intentando renovar...")
            return None  # Para forzar renovación
        else:
            print(f"❌ API ML error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error conexión API: {e}")
    return None

# === MÓDULO 4: Cálculo de Rentabilidad ===
def calcular_rentabilidad(precio_prov_ars, precio_ml):
    if precio_ml <= 0:
        return 0, 0, 0
    costo_total = precio_prov_ars + COSTO_ENVIO_ESTIMADO
    ganancia = precio_ml - costo_total - (precio_ml * COMISION_ML)
    margen = (ganancia / precio_ml * 100) if precio_ml > 0 else 0
    diferencial = precio_ml - precio_prov_ars
    return round(diferencial, 2), round(margen, 2), round(ganancia, 2)

# === MÓDULO 5: Análisis Completo ===
def analizar_catalogo(ruta_archivo):
    df_prov = cargar_proveedores(ruta_archivo)
    resultados = []
    
    # Obtener token válido
    access_token = obtener_token()
    if not access_token:
        print("❌ No se pudo obtener un token de acceso. Verifica tus credenciales.")
        return pd.DataFrame()
    
    print("🔍 Iniciando análisis con API de MercadoLibre...\n")
    
    for idx, row in df_prov.iterrows():
        print(f"Buscando: {row['Descripción']} (SKU: {row['SKU']})")
        
        # Intentar con SKU
        resultado_api = buscar_en_ml(row['SKU'], access_token)
        
        # Si no encuentra, intentar con descripción
        if not resultado_api:
            resultado_api = buscar_en_ml(row['Descripción'], access_token)
        
        if resultado_api:
            diferencial, margen, ganancia = calcular_rentabilidad(
                row['Precio ARS'], resultado_api['precio_ml']
            )
            resultados.append({
                'SKU': row['SKU'],
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
                'SKU': row['SKU'],
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
        
        time.sleep(0.5)  # Evitar demasiadas solicitudes
    
    df_resultado = pd.DataFrame(resultados)
    df_resultado = df_resultado[df_resultado['Precio ML (ARS)'] > 0]
    df_resultado = df_resultado.sort_values(by='Margen (%)', ascending=False)
    
    # Exportar resultados
    output_file = f"results/skuradar_resultados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    df_resultado.to_excel(output_file, index=False)
    print(f"\n✅ Análisis completado. Resultados guardados en: {output_file}")
    
    return df_resultado
