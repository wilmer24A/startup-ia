"""
Prompt dinámico para maximizar la personalización.
Le dice explícitamente al LLM qué hechos del usuario usar en cada respuesta.
"""
import os
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from src.agents.memoria_usuario import MemoriaUsuario
from src.agents.rag_avanzado import RAGAvanzado
from src.agents.agente_multinivel import ClasificadorContexto, CONTEXTOS_ESPECIALIZADOS

load_dotenv()


class PromptDinamico:
    """
    Construye instrucciones específicas sobre qué hechos del usuario
    usar en cada respuesta según el tipo de pregunta.
    """

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def construir(self, pregunta: str, hechos: list[str], categoria: str) -> str:
        """
        Genera instrucciones dinámicas para el LLM sobre cómo personalizar
        la respuesta usando los hechos del usuario.
        """
        if not hechos:
            return ""

        hechos_texto = "\n".join(f"- {h}" for h in hechos)

        respuesta = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en personalización de respuestas de IA. Responde SOLO con JSON válido."
                },
                {
                    "role": "user",
                    "content": f"""Pregunta del usuario: {pregunta}
Categoría: {categoria}
Hechos conocidos del usuario:
{hechos_texto}

Genera instrucciones específicas para personalizar la respuesta.
¿Qué hechos son relevantes para esta pregunta específica y cómo usarlos?

Responde SOLO con JSON:
{{"instrucciones": "instrucción específica de máximo 2 oraciones sobre cómo usar los hechos relevantes en la respuesta"}}"""
                }
            ]
        )

        try:
            datos = json.loads(respuesta.choices[0].message.content)
            instrucciones = datos.get("instrucciones", "")
            if instrucciones:
                return f"\n\n## INSTRUCCIÓN DE PERSONALIZACIÓN\n{instrucciones}"
            return ""
        except Exception:
            return ""


class AgentePromptDinamico:
    """
    Agente con prompt dinámico que maximiza la personalización.
    Genera instrucciones específicas por pregunta sobre qué hechos usar.
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
        self.prompt_dinamico = PromptDinamico()
        self.historial = []
        self.claude_md_base = Path("CLAUDE.md").read_text(encoding="utf-8")

    def _construir_contexto(self, mensaje: str) -> tuple[str, str]:
        """
        Contexto con prompt dinámico:
        1. CLAUDE.md base
        2. Contexto especializado
        3. RAG avanzado
        4. Prompt dinámico con instrucciones específicas de personalización
        """
        categoria = self.clasificador.clasificar(mensaje)

        # 1. CLAUDE.md base
        contexto = self.claude_md_base

        # 2. Contexto especializado
        archivo_esp = CONTEXTOS_ESPECIALIZADOS.get(categoria)
        if archivo_esp and Path(archivo_esp).exists():
            contexto += f"\n\n{Path(archivo_esp).read_text(encoding='utf-8')}"

        # 3. RAG avanzado
        docs = self.rag.buscar(mensaje, top_k=2)
        if docs:
            contexto += f"\n\n## Documentación técnica relevante\n" + "\n\n".join(docs)

        # 4. Prompt dinámico — instrucciones específicas de personalización
        instrucciones = self.prompt_dinamico.construir(
            mensaje, self.memoria.hechos, categoria
        )
        contexto += instrucciones

        return contexto, categoria

    def chat(self, mensaje: str) -> dict:
        """Responde con prompt dinámico de personalización."""
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
    print("=== Agente con Prompt Dinámico ===\n")

    agente = AgentePromptDinamico(usuario_id="alexander_123")
    print(f"Hechos del usuario: {len(agente.memoria.hechos)}\n")

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