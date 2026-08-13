"""
RAG avanzado con chunking estratégico y reranking.
Recupera documentos más precisos que el RAG básico.
"""
import os
import json
import numpy as np
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ChunkerEstrategico:
    """
    Divide documentos por secciones lógicas en lugar de por tamaño fijo.
    Cada chunk contiene una idea completa.
    """

    def dividir(self, texto: str) -> list[dict]:
        """
        Divide el texto por secciones marcadas con ## o títulos en mayúsculas.
        Devuelve lista de {titulo, contenido}.
        """
        chunks = []
        seccion_actual = {"titulo": "Introducción", "contenido": ""}

        for linea in texto.split("\n"):
            # Detecta títulos de sección
            if linea.isupper() and len(linea) > 3:
                if seccion_actual["contenido"].strip():
                    chunks.append(seccion_actual.copy())
                seccion_actual = {"titulo": linea.strip(), "contenido": ""}
            else:
                seccion_actual["contenido"] += linea + "\n"

        if seccion_actual["contenido"].strip():
            chunks.append(seccion_actual)

        return chunks

    def chunks_con_contexto(self, chunks: list[dict]) -> list[str]:
        """
        Añade el título al inicio de cada chunk para dar contexto.
        """
        return [
            f"[{c['titulo']}]\n{c['contenido'].strip()}"
            for c in chunks
            if c["contenido"].strip()
        ]


class Reranker:
    """
    Usa el LLM para reordenar chunks por relevancia real.
    Después de recuperar por similitud coseno, el LLM decide cuáles son mejores.
    """

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def reordenar(self, pregunta: str, chunks: list[str], top_k: int = 2) -> list[str]:
        """
        Reordena los chunks por relevancia para la pregunta.
        Devuelve solo los top_k más relevantes.
        """
        if len(chunks) <= top_k:
            return chunks

        chunks_texto = "\n\n".join([
            f"Chunk {i+1}:\n{chunk[:300]}"
            for i, chunk in enumerate(chunks)
        ])

        respuesta = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en recuperación de información. Responde SOLO con JSON válido."
                },
                {
                    "role": "user",
                    "content": f"""Pregunta del usuario: {pregunta}

Chunks disponibles:
{chunks_texto}

¿Cuáles son los {top_k} chunks más relevantes para responder la pregunta?
Responde SOLO con JSON: {{"indices": [N, N]}} donde N son los números de chunk (1-indexed)."""
                }
            ]
        )

        try:
            datos = json.loads(respuesta.choices[0].message.content)
            indices = [i - 1 for i in datos["indices"] if 0 < i <= len(chunks)]
            return [chunks[i] for i in indices[:top_k]]
        except Exception:
            return chunks[:top_k]


class RAGAvanzado:
    """
    RAG con chunking estratégico por secciones y reranking con LLM.
    Más preciso que el RAG básico por tamaño fijo.
    """

    def __init__(self, carpeta: str = "data/knowledge"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chunker = ChunkerEstrategico()
        self.reranker = Reranker()
        self.chunks: list[str] = []
        self.embeddings: list[list[float]] = []
        self._cargar(carpeta)

    def _cargar(self, carpeta: str) -> None:
        """Carga documentos con chunking estratégico."""
        ruta = Path(carpeta)
        archivos = list(ruta.glob("*.txt"))
        if not archivos:
            print("No se encontraron documentos")
            return

        todos_chunks = []
        for archivo in archivos:
            texto = archivo.read_text(encoding="utf-8")
            chunks_raw = self.chunker.dividir(texto)
            chunks_con_ctx = self.chunker.chunks_con_contexto(chunks_raw)
            todos_chunks.extend(chunks_con_ctx)
            print(f"Documento '{archivo.name}': {len(chunks_con_ctx)} secciones")

        self.chunks = todos_chunks
        print(f"Generando embeddings para {len(self.chunks)} secciones...")

        respuesta = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=self.chunks
        )
        self.embeddings = [e.embedding for e in respuesta.data]
        print(f"RAG avanzado listo: {len(self.chunks)} secciones indexadas\n")

    def buscar(self, consulta: str, top_k: int = 2) -> list[str]:
        """
        Busca por similitud coseno y luego aplica reranking.
        """
        if not self.chunks:
            return []

        # Paso 1: similitud coseno — recupera top 5
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
        candidatos = [self.chunks[i] for _, i in similitudes[:5]]

        # Paso 2: reranking con LLM — devuelve top_k
        return self.reranker.reordenar(consulta, candidatos, top_k)


if __name__ == "__main__":
    print("=== RAG Avanzado con Chunking Estratégico y Reranking ===\n")

    rag = RAGAvanzado()

    consultas = [
        "Como instalo TechHelper en Mac con error de seguridad?",
        "Que incluye el plan Pro?",
        "Como configuro Slack paso a paso?",
        "Puerto 3000 en uso, como lo soluciono?",
    ]

    for consulta in consultas:
        print(f"Consulta: {consulta}")
        resultados = rag.buscar(consulta, top_k=2)
        for i, doc in enumerate(resultados):
            print(f"  Resultado {i+1}: {doc[:100]}...")
        print()