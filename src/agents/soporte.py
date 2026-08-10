"""
Agente de soporte con Context Engineering.
Lee el CLAUDE.md como base del contexto del agente.
"""
from pathlib import Path
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()


def cargar_contexto(ruta: str = "CLAUDE.md") -> str:
    """Carga el archivo CLAUDE.md como contexto del agente."""
    archivo = Path(ruta)
    if not archivo.exists():
        raise FileNotFoundError(f"No se encontró {ruta}")
    return archivo.read_text(encoding="utf-8")


class AgenteContexto:
    """
    Agente que usa CLAUDE.md como su contexto principal.
    Todo lo que sabe, cómo se comporta y qué puede hacer
    viene definido en ese archivo — no en el código.
    """

    def __init__(self, claude_md: str = "CLAUDE.md"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.contexto = cargar_contexto(claude_md)
        self.historial = []

    def chat(self, mensaje: str) -> str:
        """Responde usando el contexto del CLAUDE.md como system prompt."""
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

    def reset(self):
        """Limpia el historial de la conversación."""
        self.historial = []


if __name__ == "__main__":
    print("=== Agente con Context Engineering ===\n")

    agente = AgenteContexto()

    preguntas = [
        "Hola, no puedo instalar TechHelper en mi Mac",
        "Cuántos usuarios permite el plan Pro?",
        "Perdí todos mis datos del proyecto, qué hago?",
        "Tienen integración con Notion?",
    ]

    for pregunta in preguntas:
        print(f"Usuario: {pregunta}")
        respuesta = agente.chat(pregunta)
        print(f"Agente: {respuesta}")
        print("-" * 60)
        print()