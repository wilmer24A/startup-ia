"""
RAG con Pinecone como base vectorial persistente.
Los embeddings se guardan en la nube y persisten entre reinicios.
"""
import os
import json
from pathlib import Path
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()


class PineconeRAG:
    """
    RAG con base vectorial persistente en Pinecone.
    Los embeddings se generan una sola vez y se reutilizan.
    """

    def __init__(self, knowledge_dir: str = "data/knowledge"):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = os.getenv("PINECONE_INDEX", "techhelper-docs")
        self.index = self.pc.Index(self.index_name)
        self.knowledge_dir = knowledge_dir

    def _dividir_en_chunks(self, texto: str, tamano: int = 400) -> list[dict]:
        """Divide el texto en chunks por secciones."""
        chunks = []
        seccion_actual = {"titulo": "General", "contenido": ""}
        for linea in texto.split("\n"):
            if linea.isupper() and len(linea) > 3:
                if seccion_actual["contenido"].strip():
                    chunks.append(seccion_actual.copy())
                seccion_actual = {"titulo": linea.strip(), "contenido": ""}
            else:
                seccion_actual["contenido"] += linea + "\n"
        if seccion_actual["contenido"].strip():
            chunks.append(seccion_actual)
        return chunks

    def indexar_documentos(self) -> int:
        """
        Lee los documentos de knowledge_dir y los sube a Pinecone.
        Solo indexa si Pinecone está vacío.
        """
        # Verifica si ya hay vectores en Pinecone
        stats = self.index.describe_index_stats()
        total_vectores = stats.total_vector_count

        if total_vectores > 0:
            print(f"Pinecone ya tiene {total_vectores} vectores — saltando indexación")
            return total_vectores

        # Carga y procesa documentos
        ruta = Path(self.knowledge_dir)
        archivos = list(ruta.glob("*.txt"))
        if not archivos:
            print("No se encontraron documentos")
            return 0

        todos_chunks = []
        for archivo in archivos:
            texto = archivo.read_text(encoding="utf-8")
            chunks = self._dividir_en_chunks(texto)
            for chunk in chunks:
                texto_completo = f"[{chunk['titulo']}]\n{chunk['contenido'].strip()}"
                todos_chunks.append(texto_completo)

        print(f"Generando embeddings para {len(todos_chunks)} chunks...")

        # Genera embeddings
        respuesta = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=todos_chunks
        )

        # Sube a Pinecone
        vectores = []
        for i, (chunk, embedding) in enumerate(zip(todos_chunks, respuesta.data)):
            vectores.append({
                "id": f"chunk_{i}",
                "values": embedding.embedding,
                "metadata": {"texto": chunk[:500]}
            })

        self.index.upsert(vectors=vectores)
        print(f"Indexados {len(vectores)} chunks en Pinecone")
        return len(vectores)

    def buscar(self, consulta: str, top_k: int = 2) -> list[str]:
        """Busca los chunks más relevantes en Pinecone."""
        respuesta = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=[consulta]
        )
        embedding_consulta = respuesta.data[0].embedding

        resultados = self.index.query(
            vector=embedding_consulta,
            top_k=top_k,
            include_metadata=True
        )

        return [match.metadata["texto"] for match in resultados.matches]


if __name__ == "__main__":
    print("=== Demo Pinecone RAG ===\n")

    rag = PineconeRAG()

    print("Indexando documentos...")
    total = rag.indexar_documentos()
    print(f"Total vectores en Pinecone: {total}\n")

    consultas = [
        "Como instalo TechHelper en Mac?",
        "Que incluye el plan Pro?",
        "Como configuro Slack?",
    ]

    for consulta in consultas:
        print(f"Consulta: {consulta}")
        resultados = rag.buscar(consulta, top_k=2)
        for i, r in enumerate(resultados):
            print(f"  Resultado {i+1}: {r[:100]}...")
        print()
