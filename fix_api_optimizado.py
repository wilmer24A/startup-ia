content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from prometheus_fastapi_instrumentator import Instrumentator
from langsmith import traceable
import json'''

new = '''from prometheus_fastapi_instrumentator import Instrumentator
from langsmith import traceable
from src.middleware.cache_respuestas import cache_respuestas
from src.agents.optimizador_contexto import OptimizadorContexto
import json'''

content = content.replace(old, new)

old2 = '''# Estos se inicializan en el lifespan — compartidos entre todos los usuarios
rag_compartido: PineconeRAG = None
clasificador_compartido: ClasificadorContexto = None
prompt_dinamico_compartido: PromptDinamico = None
claude_md_base: str = ""'''

new2 = '''# Estos se inicializan en el lifespan — compartidos entre todos los usuarios
rag_compartido: PineconeRAG = None
clasificador_compartido: ClasificadorContexto = None
prompt_dinamico_compartido: PromptDinamico = None
optimizador_compartido: OptimizadorContexto = None
claude_md_base: str = ""'''

content = content.replace(old2, new2)

old3 = '''    print("Cargando recursos compartidos...")
    rag_compartido = PineconeRAG("data/knowledge")
    rag_compartido.indexar_documentos()
    clasificador_compartido = ClasificadorContexto()
    prompt_dinamico_compartido = PromptDinamico()
    claude_md_base = Path("CLAUDE.md").read_text(encoding="utf-8")
    print("Recursos compartidos listos — API production-ready\\n")'''

new3 = '''    print("Cargando recursos compartidos...")
    rag_compartido = PineconeRAG("data/knowledge")
    rag_compartido.indexar_documentos()
    clasificador_compartido = ClasificadorContexto()
    prompt_dinamico_compartido = PromptDinamico()
    claude_md_base = Path("CLAUDE.md").read_text(encoding="utf-8")
    optimizador_compartido = OptimizadorContexto(claude_md_base)
    print("Recursos compartidos listos — API production-ready\\n")'''

content = content.replace(old3, new3)

old4 = '''    # Memoria aislada del usuario autenticado
    memoria_db = MemoriaDB()
    hechos_usuario = memoria_db.cargar_hechos(usuario.supabase_id)

    # Clasifica la pregunta
    categoria = clasificador_compartido.clasificar(request.mensaje)

    # Construye contexto con RAG compartido
    contexto = claude_md_base

    archivo_esp = CONTEXTOS_ESPECIALIZADOS.get(categoria)
    if archivo_esp and Path(archivo_esp).exists():
        contexto += f"\\n\\n{Path(archivo_esp).read_text(encoding=\'utf-8\')}"

    docs = rag_compartido.buscar(request.mensaje, top_k=2)
    if docs:
        contexto += f"\\n\\n## Documentación relevante\\n" + "\\n\\n".join(docs)

    instrucciones = prompt_dinamico_compartido.construir(
        request.mensaje, hechos_usuario, categoria
    )
    contexto += instrucciones

    # Genera respuesta con tracing de LangSmith
    contenido = procesar_chat_langsmith(
        mensaje=request.mensaje,
        usuario_email=usuario.email,
        hechos=hechos_usuario,
        categoria=categoria,
        contexto=contexto
    )'''

new4 = '''    # PASO 1: Verifica caché
    respuesta_cache = cache_respuestas.obtener(request.mensaje)
    if respuesta_cache:
        return ChatResponse(
            respuesta=respuesta_cache,
            categoria="cache",
            usuario_email=usuario.email,
        )

    # PASO 2: Memoria aislada del usuario autenticado
    memoria_db = MemoriaDB()
    hechos_usuario = memoria_db.cargar_hechos(usuario.supabase_id)

    # Clasifica la pregunta
    categoria = clasificador_compartido.clasificar(request.mensaje)

    # PASO 3: Construye contexto optimizado
    docs = rag_compartido.buscar(request.mensaje, top_k=2)
    archivo_esp = CONTEXTOS_ESPECIALIZADOS.get(categoria)
    contexto_esp = ""
    if archivo_esp and Path(archivo_esp).exists():
        contexto_esp = Path(archivo_esp).read_text(encoding=\'utf-8\')

    contexto, complejidad, tokens_est = optimizador_compartido.construir_contexto_optimizado(
        request.mensaje, docs, hechos_usuario, contexto_esp
    )
    print(f"[Optimizador] Complejidad: {complejidad} | Tokens estimados: {tokens_est}")

    # PASO 4: Genera respuesta con tracing de LangSmith
    contenido = procesar_chat_langsmith(
        mensaje=request.mensaje,
        usuario_email=usuario.email,
        hechos=hechos_usuario,
        categoria=categoria,
        contexto=contexto
    )

    # PASO 5: Guarda en caché
    cache_respuestas.guardar(request.mensaje, contenido, categoria)'''

content = content.replace(old4, new4)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("API optimizada con caché y optimizador de contexto")