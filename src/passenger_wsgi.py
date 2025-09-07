# passenger_wsgi.py
import sys
import os

# Ruta absoluta a la carpeta public_html (donde está src/)
PROJECT_ROOT = '/home/skuradar/public_html'

# Añadir al path
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# Variables de entorno
os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

def application(environ, start_response):
    from streamlit.web import bootstrap
    sys.argv = [
        "streamlit", "run", os.path.join(PROJECT_ROOT, "src", "dashboard.py"),
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--browser.gatherUsageStats=false"
    ]
    return bootstrap.load_app(environ, start_response)