"""
Load testing para TechHelper AI con Locust.
Simula usuarios reales haciendo peticiones a la API.
"""
from locust import HttpUser, task, between

TOKEN = "user_3I59hLkVRqSndxMj9KVIpYnwhDw"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

PREGUNTAS = [
    "Como instalo TechHelper en Mac?",
    "Cuanto cuesta el plan Pro?",
    "Como configuro la integracion con Slack?",
    "Que almacenamiento incluye el plan Enterprise?",
    "Hola necesito ayuda",
    "Como sincronizo con Google Drive?",
    "Tengo un error al instalar en Windows",
    "Cuantos usuarios puedo tener en el plan Free?",
]


class TechHelperUser(HttpUser):
    """
    Usuario virtual que simula el comportamiento real.
    Espera entre 1 y 3 segundos entre peticiones.
    """
    wait_time = between(1, 3)

    @task(3)
    def health_check(self):
        """Petición más frecuente — 3x más que el chat."""
        self.client.get("/health")

    @task(5)
    def chat_pregunta(self):
        """Envía preguntas al chat — la más importante."""
        import random
        pregunta = random.choice(PREGUNTAS)
        self.client.post(
            "/chat",
            json={"mensaje": pregunta},
            headers=HEADERS,
            timeout=30
        )

    @task(1)
    def ver_perfil(self):
        """Consulta el perfil del usuario."""
        self.client.get(
            "/mi-perfil",
            headers=HEADERS
        )

    @task(1)
    def ver_conversaciones(self):
        """Consulta el historial de conversaciones."""
        self.client.get(
            "/mis-conversaciones",
            headers=HEADERS
        )