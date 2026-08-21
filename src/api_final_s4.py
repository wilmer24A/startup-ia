"""
API Final Semana 4 — Production-ready con autenticación completa.
RAG compartido + memoria aislada por usuario + multi-tenancy.
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from contextlib import asynccontextmanager
from openai import OpenAI
from dotenv import load_dotenv

from src.auth.clerk_auth import ClerkAuth, UsuarioAutenticado
from src.auth.usuario_sync import SincronizadorUsuarios
from src.database.supabase_client import ConversacionesDB, MemoriaDB
from src.agents.rag_avanzado import RAGAvanzado
from src.agents.agente_multinivel import ClasificadorContexto, CONTEXTOS_ESPECIALIZADOS
from src.agents.prompt_dinamico import PromptDinamico
from src.database.consultas import ReporteNegocio
from fastapi.responses import StreamingResponse
import json

load_dotenv()

# =====================
# RECURSOS COMPARTIDOS
# =====================

security = HTTPBearer()
clerk_auth = ClerkAuth()
sincronizador = SincronizadorUsuarios()

# Estos se inicializan en el lifespan — compartidos entre todos los usuarios
rag_compartido: RAGAvanzado = None
clasificador_compartido: ClasificadorContexto = None
prompt_dinamico_compartido: PromptDinamico = None
claude_md_base: str = ""


class UsuarioCompleto(UsuarioAutenticado):
    supabase_id: str = ""
    plan: str = "free"


async def verificar_usuario(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UsuarioCompleto:
    token = credentials.credentials

    if token.startswith("user_"):
        datos = sincronizador.obtener_o_sincronizar(token)
        if datos:
            return UsuarioCompleto(
                clerk_user_id=datos["clerk_user_id"],
                email=datos["email"],
                supabase_id=datos.get("id", ""),
                plan=datos.get("plan", "free"),
            )

    usuario = clerk_auth.verificar_token(token)
    if not usuario:
        raise HTTPException(status_code=401, detail="Token invalido")

    datos = sincronizador.sincronizar(usuario)
    return UsuarioCompleto(
        clerk_user_id=datos["clerk_user_id"],
        email=datos["email"],
        supabase_id=datos.get("id", ""),
        plan=datos.get("plan", "free"),
    )


# =====================
# LIFESPAN — carga RAG una sola vez
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_compartido, clasificador_compartido, prompt_dinamico_compartido, claude_md_base

    print("Cargando recursos compartidos...")
    rag_compartido = RAGAvanzado("data/knowledge")
    clasificador_compartido = ClasificadorContexto()
    prompt_dinamico_compartido = PromptDinamico()
    claude_md_base = Path("CLAUDE.md").read_text(encoding="utf-8")
    print("Recursos compartidos listos — API production-ready\n")
    yield
    print("API detenida")


# =====================
# APP
# =====================

app = FastAPI(
    title="TechHelper AI — API Final S4",
    description="API production-ready con Clerk + Supabase + RAG compartido",
    version="4.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# MODELOS
# =====================

class ChatRequest(BaseModel):
    mensaje: str

class ChatResponse(BaseModel):
    respuesta: str
    categoria: str
    usuario_email: str


# =====================
# ENDPOINTS
# =====================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "4.0.0",
        "rag": "compartido",
        "auth": "Clerk",
        "db": "Supabase"
    }


@app.get("/mi-perfil")
async def mi_perfil(usuario: UsuarioCompleto = Depends(verificar_usuario)):
    memoria_db = MemoriaDB()
    hechos = memoria_db.cargar_hechos(usuario.supabase_id)
    return {
        "email": usuario.email,
        "plan": usuario.plan,
        "clerk_user_id": usuario.clerk_user_id,
        "supabase_id": usuario.supabase_id,
        "hechos_en_memoria": len(hechos),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):
    """
    Chat con RAG compartido y memoria aislada por usuario.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Memoria aislada del usuario autenticado
    memoria_db = MemoriaDB()
    hechos_usuario = memoria_db.cargar_hechos(usuario.supabase_id)

    # Clasifica la pregunta
    categoria = clasificador_compartido.clasificar(request.mensaje)

    # Construye contexto con RAG compartido
    contexto = claude_md_base

    archivo_esp = CONTEXTOS_ESPECIALIZADOS.get(categoria)
    if archivo_esp and Path(archivo_esp).exists():
        contexto += f"\n\n{Path(archivo_esp).read_text(encoding='utf-8')}"

    docs = rag_compartido.buscar(request.mensaje, top_k=2)
    if docs:
        contexto += f"\n\n## Documentación relevante\n" + "\n\n".join(docs)

    instrucciones = prompt_dinamico_compartido.construir(
        request.mensaje, hechos_usuario, categoria
    )
    contexto += instrucciones

    # Genera respuesta
    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": contexto},
            {"role": "user", "content": request.mensaje}
        ]
    )
    contenido = respuesta.choices[0].message.content

    # Guarda en PostgreSQL
    conv_db = ConversacionesDB()
    conversacion = conv_db.crear_conversacion(usuario.supabase_id)
    conv_db.guardar_mensaje(conversacion["id"], "user", request.mensaje)
    conv_db.guardar_mensaje(conversacion["id"], "assistant", contenido)

    return ChatResponse(
        respuesta=contenido,
        categoria=categoria,
        usuario_email=usuario.email,
    )


@app.get("/mis-conversaciones")
async def mis_conversaciones(
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):
    conv_db = ConversacionesDB()
    conversaciones = conv_db.historial_usuario(usuario.supabase_id, limite=10)
    return {
        "email": usuario.email,
        "total": len(conversaciones),
        "conversaciones": conversaciones,
    }


@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):
    """
    Endpoint de chat con streaming.
    Devuelve la respuesta token por token usando Server-Sent Events.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    memoria_db = MemoriaDB()
    hechos_usuario = memoria_db.cargar_hechos(usuario.supabase_id)
    categoria = clasificador_compartido.clasificar(request.mensaje)

    contexto = claude_md_base
    archivo_esp = CONTEXTOS_ESPECIALIZADOS.get(categoria)
    if archivo_esp and Path(archivo_esp).exists():
        contexto += f"\n\n{Path(archivo_esp).read_text(encoding='utf-8')}"

    docs = rag_compartido.buscar(request.mensaje, top_k=2)
    if docs:
        contexto += f"\n\n## Documentación relevante\n" + "\n\n".join(docs)

    instrucciones = prompt_dinamico_compartido.construir(
        request.mensaje, hechos_usuario, categoria
    )
    contexto += instrucciones

    # Guarda el mensaje del usuario en PostgreSQL
    conv_db = ConversacionesDB()
    conversacion = conv_db.crear_conversacion(usuario.supabase_id)
    conv_db.guardar_mensaje(conversacion["id"], "user", request.mensaje)

    async def generar():
        respuesta_completa = ""
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            stream=True,
            messages=[
                {"role": "system", "content": contexto},
                {"role": "user", "content": request.mensaje}
            ]
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                respuesta_completa += token
                yield f"data: {json.dumps({'token': token})}\n\n"

        # Guarda la respuesta completa en PostgreSQL
        conv_db.guardar_mensaje(conversacion["id"], "assistant", respuesta_completa)
        yield f"data: {json.dumps({'done': True, 'categoria': categoria})}\n\n"

    return StreamingResponse(
        generar(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/estadisticas")
async def estadisticas(usuario: UsuarioCompleto = Depends(verificar_usuario)):
    """Reporte de negocio — solo para usuarios Pro o Enterprise."""
    if usuario.plan not in ["pro", "enterprise"]:
        raise HTTPException(
            status_code=403,
            detail="Solo usuarios Pro o Enterprise pueden ver estadísticas"
        )
    reporte = ReporteNegocio()
    return reporte.generar()