# SKUradar - Sistema de Análisis para MercadoLibre

Aplicación web para detectar productos con alto margen de ganancia en MercadoLibre.

## Instalación en cPanel
1. Sube todos los archivos a `public_html`
2. Ve a "Setup Python App" en cPanel
3. Crea una app con:
   - Python 3.9
   - Ruta: /
   - Startup File: passenger_wsgi.py
4. Instala dependencias: pip install -r requirements.txt
5. Reinicia la app.

Acceso: https://skuradar.com