"""
Agente con contexto reordenado para maximizar personalización.
La memoria del usuario aparece PRIMERO en el contexto.
"""
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from src.agents.memoria_usuario import MemoriaUsuario
from src.agents.rag_agente import BaseConocimiento
from src.agents.agente_multinivel import ClasificadorContexto, CONTEXTOS_ESPECIALIZADOS

load_dotenv()


def construir_resumen_usuario(hechos: list[str]) -> str:
    """
    Convierte la lista de hechos en un párrafo natural.
    Más fácil de usar para el LLM que una lista de items.
    """
    if not hechos:
        return ""

    hechos_texto = "\n".join(f"- {h}" for h in hechos)
    return f"""## CONTEXTO DEL USUARIO ACTUAL
Este es el usuario con quien estás hablando ahora mismo. USA esta información en tu respuesta:

{hechos_texto}

IMPORTANTE: Adapta tu respuesta a este usuario específico. Menciona su plan, sistema operativo o integraciones cuando sea relevante."""


class AgentePersonalizado:
    """
    Agente con contexto reordenado:
    1. Memoria usuario (primero — máxima personalización)
    2. CLAUDE.md base
    3. Contexto especializado
    4. RAG documentos
    """

    def __init__(
        self,
        usuario_id: str = "default",
        knowledge_dir: str = "data/knowledge"
    ):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.memoria = MemoriaUsuario(usuario_id)
        self.base_conocimiento = BaseConocimiento(knowledge_dir)
        self.clasificador = ClasificadorContexto()
        self.historial = []
        self.claude_md_base = Path("CLAUDE.md").read_text(encoding="utf-8")

    def _construir_contexto(self, mensaje: str) -> tuple[str, str]:
        """
        Construye el contexto en el orden óptimo para personalización.
        """
        categoria = self.clasificador.clasificar(mensaje)

        # 1. PRIMERO — memoria del usuario como resumen natural
        resumen_usuario = construir_resumen_usuario(self.memoria.hechos)

        # 2. CLAUDE.md base
        contexto = resumen_usuario + "\n\n" + self.claude_md_base

        # 3. Contexto especializado según categoría
        archivo_esp = CONTEXTOS_ESPECIALIZADOS.get(categoria)
        if archivo_esp and Path(archivo_esp).exists():
            contexto_esp = Path(archivo_esp).read_text(encoding="utf-8")
            contexto += f"\n\n{contexto_esp}"

        # 4. Documentos RAG al final
        docs = self.base_conocimiento.buscar(mensaje, top_k=2)
        if docs:
            contexto += f"\n\n## Documentación técnica relevante\n" + "\n\n".join(docs)

        return contexto, categoria

    def chat(self, mensaje: str) -> dict:
        """Responde con el contexto optimizado para personalización."""
        contexto, categoria = self._construir_contexto(mensaje)

        self.historial.append({"role": "user", "content": mensaje})

        respuesta = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {"role": "system", "content": contexto},
                *self.historial
            ]
        )

        contenido = respuesta.choices[0].message.content
        self.historial.append({"role": "assistant", "content": contenido})

        return {
            "respuesta": contenido,
            "categoria": categoria,
        }

    def finalizar_sesion(self) -> None:
        if not self.historial:
            return
        conversacion = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in self.historial
        ])
        self.memoria.extraer_hechos(conversacion)


if __name__ == "__main__":
    print("=== Agente con Contexto Optimizado para Personalización ===\n")

    agente = AgentePersonalizado(usuario_id="alexander_123")
    print(f"Hechos del usuario cargados: {len(agente.memoria.hechos)}")
    print(f"Hechos: {agente.memoria.hechos[:3]}...\n")

    casos = [
        "No puedo instalar TechHelper en Mac, me sale error de seguridad",
        "Cuantos proyectos puedo tener en el plan Pro?",
        "Como configuro la integracion con Slack?",
        "Quiero cambiar del plan Free al Pro",
    ]

    for caso in casos:
        print(f"Usuario: {caso}")
        resultado = agente.chat(caso)
        print(f"[{resultado['categoria']}] {resultado['respuesta']}")
        print("-" * 60)
        print()

    agente.finalizar_sesion()