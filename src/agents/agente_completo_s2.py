"""
Agente completo Semana 2.
Combina contexto optimizado (Día 1) + RAG avanzado (Día 2).
"""
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from src.agents.memoria_usuario import MemoriaUsuario
from src.agents.rag_avanzado import RAGAvanzado
from src.agents.agente_multinivel import ClasificadorContexto, CONTEXTOS_ESPECIALIZADOS
from src.agents.agente_personalizado import construir_resumen_usuario

load_dotenv()


class AgenteCompletoS2:
    """
    Agente con todas las mejoras de la Semana 2:
    1. Memoria del usuario primero en el contexto
    2. RAG avanzado con chunking estratégico y reranking
    3. Contextos especializados por categoría
    """

    def __init__(
        self,
        usuario_id: str = "default",
        knowledge_dir: str = "data/knowledge"
    ):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.memoria = MemoriaUsuario(usuario_id)
        self.rag = RAGAvanzado(knowledge_dir)
        self.clasificador = ClasificadorContexto()
        self.historial = []
        self.claude_md_base = Path("CLAUDE.md").read_text(encoding="utf-8")

    def _construir_contexto(self, mensaje: str) -> tuple[str, str]:
        """
        Contexto optimizado:
        1. Resumen usuario (primero)
        2. CLAUDE.md base
        3. Contexto especializado
        4. RAG avanzado (más preciso)
        """
        categoria = self.clasificador.clasificar(mensaje)

        # 1. Memoria del usuario — primero
        resumen = construir_resumen_usuario(self.memoria.hechos)

        # 2. CLAUDE.md base
        contexto = resumen + "\n\n" + self.claude_md_base

        # 3. Contexto especializado
        archivo_esp = CONTEXTOS_ESPECIALIZADOS.get(categoria)
        if archivo_esp and Path(archivo_esp).exists():
            contexto += f"\n\n{Path(archivo_esp).read_text(encoding='utf-8')}"

        # 4. RAG avanzado — chunks con reranking
        docs = self.rag.buscar(mensaje, top_k=2)
        if docs:
            contexto += f"\n\n## Documentación técnica relevante\n" + "\n\n".join(docs)

        return contexto, categoria

    def chat(self, mensaje: str) -> dict:
        """Responde con el contexto completo optimizado."""
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
    print("=== Agente Completo Semana 2 ===\n")

    agente = AgenteCompletoS2(usuario_id="alexander_123")
    print()

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