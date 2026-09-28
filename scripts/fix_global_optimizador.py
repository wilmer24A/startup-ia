content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_compartido, clasificador_compartido, prompt_dinamico_compartido, claude_md_base'''

new = '''@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_compartido, clasificador_compartido, prompt_dinamico_compartido, optimizador_compartido, claude_md_base'''

content = content.replace(old, new)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Global optimizador añadido")