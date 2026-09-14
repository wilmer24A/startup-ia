content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from src.agents.rag_avanzado import RAGAvanzado
from src.agents.agente_multinivel import ClasificadorContexto, CONTEXTOS_ESPECIALIZADOS
from src.agents.prompt_dinamico import PromptDinamico'''

new = '''from src.database.pinecone_client import PineconeRAG
from src.agents.agente_multinivel import ClasificadorContexto, CONTEXTOS_ESPECIALIZADOS
from src.agents.prompt_dinamico import PromptDinamico'''

content = content.replace(old, new)

old2 = '''    print("Cargando recursos compartidos...")
    rag_compartido = RAGAvanzado("data/knowledge")'''

new2 = '''    print("Cargando recursos compartidos...")
    rag_compartido = PineconeRAG("data/knowledge")
    rag_compartido.indexar_documentos()'''

content = content.replace(old2, new2)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("API actualizada con Pinecone RAG")