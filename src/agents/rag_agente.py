"""
Agente RAG con Context Engineering completo.
Combina CLAUDE.md + memoria del usuario + documentos del producto.
"""
import os
import json
import numpy as np
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from src.agents.memoria_usuario import MemoriaUsuario

load_dotenv()


class BaseConocimiento:
    """
    Indexa documentos del producto y los busca por similitud semántica.
    """

    def __init__(self, carpeta: str = "data/knowledge"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chunks: list[str] = []
        self.embeddings: list[list[float]] = []
        self._cargar_documentos(carpeta)

    def _dividir_en_chunks(self, texto: str, tamano: int = 400) -> list[str]:
        """Divide el texto en chunks por párrafos."""
        parrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
        chunks = []
        chunk_actual = ""
        for parrafo in parrafos:
            if len(chunk_actual) + len(parrafo) < tamano:
                chunk_actual += parrafo + "\n\n"
            else:
                if chunk_actual:
                    chunks.append(chunk_actual.strip())
                chunk_actual = parrafo + "\n\n"
        if chunk_actual:
            chunks.append(chunk_actual.strip())
        return chunks

    def _cargar_documentos(self, carpeta: str) -> None:
        """Carga todos los archivos .txt y genera embeddings."""
        ruta = Path(carpeta)
        archivos = list(ruta.glob("*.txt"))
        if not archivos:
            print("No se encontraron documentos en la base de conocimiento")
            return

        print(f"Cargando {len(archivos)} documentos...")
        todos_chunks = []
        for archivo in archivos:
            texto = archivo.read_text(encoding="utf-8")
            chunks = self._dividir_en_chunks(texto)
            todos_chunks.extend(chunks)

        self.chunks = todos_chunks
        print(f"Generando embeddings para {len(self.chunks)} chunks...")

        respuesta = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=self.chunks
        )
        self.embeddings = [e.embedding for e in respuesta.data]
        print(f"Base de conocimiento lista: {len(self.chunks)} fragmentos indexados")

    def buscar(self, consulta: str, top_k: int = 3) -> list[str]:
        """Busca los chunks más relevantes para la consulta."""
        if not self.chunks:
            return []

        respuesta = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=[consulta]
        )
        embedding_consulta = np.array(respuesta.data[0].embedding)

        similitudes = []
        for i, emb in enumerate(self.embeddings):
            vec = np.array(emb)
            similitud = float(np.dot(embedding_consulta, vec) /
                            (np.linalg.norm(embedding_consulta) * np.linalg.norm(vec)))
            similitudes.append((similitud, i))

        similitudes.sort(reverse=True)
        return [self.chunks[i] for _, i in similitudes[:top_k]]


class AgenteRAG:
    """
    Agente con context engineering completo:
    CLAUDE.md + memoria del usuario + RAG de documentos.
    """

    def __init__(
        self,
        claude_md: str = "CLAUDE.md",
        usuario_id: str = "default",
        knowledge_dir: str = "data/knowledge"
    ):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.memoria = MemoriaUsuario(usuario_id)
        self.base_conocimiento = BaseConocimiento(knowledge_dir)
        self.historial = []

        # Contexto base
        self.claude_md = Path(claude_md).read_text(encoding="utf-8")

    def chat(self, mensaje: str) -> str:
        """
        Responde combinando CLAUDE.md + memoria del usuario + documentos relevantes.
        """
        # Busca documentos relevantes para esta pregunta
        docs_relevantes = self.base_conocimiento.buscar(mensaje, top_k=3)
        contexto_docs = "\n\n".join(docs_relevantes)

        # Construye el contexto completo
        contexto_completo = self.claude_md
        contexto_completo += self.memoria.contexto_para_agente()
        contexto_completo += f"\n\n## Documentación relevante\n{contexto_docs}"

        self.historial.append({"role": "user", "content": mensaje})

        respuesta = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {"role": "system", "content": contexto_completo},
                *self.historial
            ]
        )

        contenido = respuesta.choices[0].message.content
        self.historial.append({"role": "assistant", "content": contenido})
        return contenido

    def finalizar_sesion(self) -> None:
        """Extrae hechos del usuario al terminar la sesión."""
        if not self.historial:
            return
        conversacion = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in self.historial
        ])
        self.memoria.extraer_hechos(conversacion)


if __name__ == "__main__":
    print("=== Agente RAG con Context Engineering Completo ===\n")

    agente = AgenteRAG(usuario_id="alexander_123")
    print()

    preguntas = [
        "Como instalo TechHelper en Mac con macOS Ventura?",
        "Que incluye el plan Pro exactamente?",
        "Como configuro la integracion con GitHub?",
        "Me aparece el error puerto 3000 en uso, que hago?",
    ]

    for pregunta in preguntas:
        print(f"Usuario: {pregunta}")
        respuesta = agente.chat(pregunta)
        print(f"Agente: {respuesta}")
        print("-" * 60)
        print()

    agente.finalizar_sesion()