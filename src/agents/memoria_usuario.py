"""
Memoria dinámica por usuario.
El agente aprende información del usuario y la usa en futuras sesiones.
"""
import json
from pathlib import Path
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

CARPETA_MEMORIA = Path("data/memoria")
CARPETA_MEMORIA.mkdir(parents=True, exist_ok=True)


class MemoriaUsuario:
    """
    Guarda y carga hechos importantes sobre cada usuario.
    La información persiste entre sesiones.
    """

    def __init__(self, usuario_id: str):
        self.usuario_id = usuario_id
        self.ruta = CARPETA_MEMORIA / f"{usuario_id}.json"
        self.hechos: list[str] = []
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._cargar()

    def _cargar(self) -> None:
        """Carga los hechos del usuario desde disco."""
        if self.ruta.exists():
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
            self.hechos = datos.get("hechos", [])
            print(f"Memoria cargada: {len(self.hechos)} hechos para {self.usuario_id}")
        else:
            print(f"Nueva memoria para usuario: {self.usuario_id}")

    def guardar(self) -> None:
        """Guarda los hechos del usuario en disco."""
        datos = {
            "usuario_id": self.usuario_id,
            "hechos": self.hechos
        }
        self.ruta.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def extraer_hechos(self, conversacion: str) -> list[str]:
        """
        Usa el LLM para extraer hechos relevantes del usuario
        de una conversación y los guarda en memoria.
        """
        respuesta = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": """Extrae hechos importantes y durables sobre el usuario de esta conversación de soporte técnico.
Solo incluye hechos útiles para futuras conversaciones: sistema operativo, plan contratado, número de usuarios, integraciones que usa, problemas frecuentes.
NO incluyas: saludos, preguntas genéricas, información temporal.
Responde SOLO con JSON: {"hechos": ["hecho1", "hecho2"]}
Si no hay hechos útiles responde: {"hechos": []}"""
                },
                {"role": "user", "content": f"Conversación:\n{conversacion}"}
            ],
        )

        try:
            datos = json.loads(respuesta.choices[0].message.content)
            nuevos = datos.get("hechos", [])
            for hecho in nuevos:
                if hecho not in self.hechos:
                    self.hechos.append(hecho)
            if nuevos:
                self.guardar()
                print(f"Nuevos hechos guardados: {nuevos}")
            return nuevos
        except Exception as e:
            print(f"Error extrayendo hechos: {e}")
            return []

    def contexto_para_agente(self) -> str:
        """Devuelve los hechos como contexto adicional para el agente."""
        if not self.hechos:
            return ""
        hechos_texto = "\n".join(f"- {h}" for h in self.hechos)
        return f"\n\n## Información conocida del usuario\n{hechos_texto}"


class AgenteConMemoria:
    """
    Agente de soporte que combina CLAUDE.md + memoria del usuario.
    Aprende del usuario y personaliza cada conversación.
    """

    def __init__(self, claude_md: str = "CLAUDE.md", usuario_id: str = "default"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.memoria = MemoriaUsuario(usuario_id)
        self.historial = []

        # Contexto base del CLAUDE.md
        contexto_base = Path(claude_md).read_text(encoding="utf-8")

        # Añade la memoria del usuario al contexto
        self.contexto = contexto_base + self.memoria.contexto_para_agente()

    def chat(self, mensaje: str) -> str:
        """Responde usando CLAUDE.md + memoria del usuario."""
        self.historial.append({"role": "user", "content": mensaje})

        respuesta = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {"role": "system", "content": self.contexto},
                *self.historial
            ]
        )

        contenido = respuesta.choices[0].message.content
        self.historial.append({"role": "assistant", "content": contenido})
        return contenido

    def finalizar_sesion(self) -> None:
        """Al terminar la sesión extrae hechos y los guarda."""
        if not self.historial:
            return

        conversacion = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in self.historial
        ])

        print("\nExtrayendo hechos de la conversación...")
        self.memoria.extraer_hechos(conversacion)


if __name__ == "__main__":
    print("=== Agente con Memoria Dinámica ===\n")

    # Simula primera sesión del usuario
    print("--- SESIÓN 1 ---")
    agente = AgenteConMemoria(usuario_id="alexander_123")

    preguntas_sesion1 = [
        "Hola, tengo un Mac con macOS Ventura y no puedo instalar TechHelper",
        "Estoy en el plan Pro con 12 usuarios en mi equipo",
        "Usamos la integración con Slack todos los días",
    ]

    for pregunta in preguntas_sesion1:
        print(f"Usuario: {pregunta}")
        respuesta = agente.chat(pregunta)
        print(f"Agente: {respuesta}")
        print("-" * 40)

    agente.finalizar_sesion()

    # Simula segunda sesión — el agente ya sabe del usuario
    print("\n--- SESIÓN 2 (el agente recuerda) ---")
    agente2 = AgenteConMemoria(usuario_id="alexander_123")
    print(f"\nContexto adicional del usuario:\n{agente2.memoria.contexto_para_agente()}")

    respuesta = agente2.chat("Tengo un problema con la integración")
    print(f"\nUsuario: Tengo un problema con la integración")
    print(f"Agente: {respuesta}")