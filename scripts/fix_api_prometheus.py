content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from src.database.consultas import ReporteNegocio
from fastapi.responses import StreamingResponse
from src.tasks.celery_app import tarea_analizar_conversacion, tarea_deduplicar_memoria
from src.middleware.rate_limiter import rate_limiter
import json'''

new = '''from src.database.consultas import ReporteNegocio
from fastapi.responses import StreamingResponse
from src.tasks.celery_app import tarea_analizar_conversacion, tarea_deduplicar_memoria
from src.middleware.rate_limiter import rate_limiter
from prometheus_fastapi_instrumentator import Instrumentator
import json'''

content = content.replace(old, new)

old2 = '''app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)'''

new2 = '''app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)'''

content = content.replace(old2, new2)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Prometheus añadido a la API")