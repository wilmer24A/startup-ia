content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = 'rag_compartido: RAGAvanzado = None'
new = 'rag_compartido: PineconeRAG = None'

content = content.replace(old, new)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Anotación de tipo corregida")