# passenger_wsgi.py
import sys
import os

# Añadir directorios al path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Variables de entorno para Streamlit
os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

def application(environ, start_response):
    from streamlit.web import bootstrap
    sys.argv = [
        "streamlit", "run", "src/dashboard.py",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--browser.gatherUsageStats=false"
    ]
    return bootstrap.load_app(environ, start_response)