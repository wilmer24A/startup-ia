"""
Agente con CLAUDE.md multi-nivel.
Carga contextos especializados según el tipo de problema del usuario.
"""
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from src.agents.memoria_usuario import MemoriaUsuario
from src.agents.rag_agente import BaseConocimiento

load_dotenv()

CONTEXTOS_ESPECIALIZADOS = {
    "instalacion": "CLAUDE_instalacion.md",
    "facturacion": "CLAUDE_facturacion.md",
    "general": None,
}


class ClasificadorContexto:
    """
    Detecta el tipo de problema del usuario y selecciona
    el contexto especializado correcto.
    """

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def clasificar(self, mensaje: str) -> str:
        """
        Clasifica el mensaje en: instalacion, facturacion o general.
        """
        respuesta = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": """Clasifica el mensaje del usuario en una de estas categorías:
- instalacion: problemas para instalar, abrir o configurar la aplicación
- facturacion: preguntas sobre precios, pagos, planes o reembolsos
- general: cualquier otra consulta

Responde SOLO con una palabra: instalacion, facturacion o general"""
                },
                {"role": "user", "content": mensaje}
            ]
        )
        categoria = respuesta.choices[0].message.content.strip().lower()
        if categoria not in CONTEXTOS_ESPECIALIZADOS:
            categoria = "general"
        return categoria


class AgenteMultiNivel:
    """
    Agente que combina contextos múltiples según el tipo de problema.
    Cada respuesta usa el contexto más apropiado para la situación.
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

        # Contexto base siempre activo
        self.claude_md_base = Path("CLAUDE.md").read_text(encoding="utf-8")

    def _construir_contexto(self, mensaje: str) -> tuple[str, str]:
        """
        Construye el contexto completo para el mensaje dado.
        Devuelve (contexto_completo, categoria_detectada).
        """
        # Clasifica el tipo de problema
        categoria = self.clasificador.clasificar(mensaje)

        # Contexto base siempre presente
        contexto = self.claude_md_base

        # Añade contexto especializado si existe
        archivo_especializado = CONTEXTOS_ESPECIALIZADOS.get(categoria)
        if archivo_especializado and Path(archivo_especializado).exists():
            contexto_esp = Path(archivo_especializado).read_text(encoding="utf-8")
            contexto += f"\n\n{contexto_esp}"

        # Añade memoria del usuario
        contexto += self.memoria.contexto_para_agente()

        # Añade documentos relevantes del RAG
        docs = self.base_conocimiento.buscar(mensaje, top_k=2)
        if docs:
            contexto += f"\n\n## Documentación relevante\n" + "\n\n".join(docs)

        return contexto, categoria

    def chat(self, mensaje: str) -> dict:
        """
        Responde usando el contexto multi-nivel apropiado.
        Devuelve la respuesta y la categoría detectada.
        """
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
    print("=== Agente Multi-nivel con Context Engineering ===\n")

    agente = AgenteMultiNivel(usuario_id="alexander_123")
    print()

    casos = [
        "No puedo instalar TechHelper en mi Mac, me da error",
        "Cuanto cuesta el plan Enterprise?",
        "Como funciona la integracion con Jira?",
        "Quiero pedir un reembolso del mes pasado",
    ]

    for caso in casos:
        print(f"Usuario: {caso}")
        resultado = agente.chat(caso)
        print(f"[Categoría detectada: {resultado['categoria']}]")
        print(f"Agente: {resultado['respuesta']}")
        print("-" * 60)
        print()

    agente.finalizar_sesion()