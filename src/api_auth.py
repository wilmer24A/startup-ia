"""
API de FastAPI protegida con autenticación de Clerk.
Cada endpoint requiere un token JWT válido.
"""
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from src.auth.clerk_auth import ClerkAuth, UsuarioAutenticado
from src.auth.usuario_sync import SincronizadorUsuarios
from src.database.supabase_client import UsuariosDB, ConversacionesDB

load_dotenv()

# Seguridad HTTP Bearer
security = HTTPBearer()
clerk_auth = ClerkAuth()
sincronizador = SincronizadorUsuarios()


# =====================
# DEPENDENCIA DE AUTENTICACIÓN
# =====================

class UsuarioCompleto(UsuarioAutenticado):
    """Usuario con datos de Clerk y Supabase combinados."""
    supabase_id: str = ""
    plan: str = "free"


async def verificar_usuario(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UsuarioCompleto:
    """
    Verifica el token, sincroniza con Supabase y devuelve usuario completo.
    """
    token = credentials.credentials

    # Para desarrollo: acepta clerk_user_id directamente
    if token.startswith("user_"):
        datos = sincronizador.obtener_o_sincronizar(token)
        if datos:
            return UsuarioCompleto(
                clerk_user_id=datos["clerk_user_id"],
                email=datos["email"],
                supabase_id=datos.get("id", ""),
                plan=datos.get("plan", "free"),
            )

    # Verifica JWT real
    usuario = clerk_auth.verificar_token(token)
    if not usuario:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    # Sincroniza con Supabase
    datos = sincronizador.sincronizar(usuario)
    return UsuarioCompleto(
        clerk_user_id=datos["clerk_user_id"],
        email=datos["email"],
        supabase_id=datos.get("id", ""),
        plan=datos.get("plan", "free"),
    )


# =====================
# MODELOS
# =====================

class ChatRequest(BaseModel):
    mensaje: str


class ChatResponse(BaseModel):
    respuesta: str
    usuario_id: str


# =====================
# LIFESPAN
# =====================

agente_global = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agente_global
    from src.agents.agente_con_db import AgenteConDB
    agente_global = AgenteConDB()
    print("API con autenticación iniciada")
    yield
    print("API detenida")


# =====================
# APP
# =====================

app = FastAPI(
    title="TechHelper AI — API Autenticada",
    description="API protegida con Clerk. Requiere token JWT en Authorization header.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# ENDPOINTS
# =====================

@app.get("/health")
async def health():
    """Endpoint público — no requiere autenticación."""
    return {"status": "ok", "autenticacion": "Clerk"}


@app.get("/mi-perfil")
async def mi_perfil(usuario: UsuarioCompleto = Depends(verificar_usuario)):
    """
    Devuelve el perfil del usuario autenticado.
    Requiere token válido de Clerk.
    """
    return {
        "clerk_user_id": usuario.clerk_user_id,
        "email": usuario.email,
        "plan": usuario.plan,
        "supabase_id": usuario.supabase_id,
        "en_supabase": bool(usuario.supabase_id),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):
    """
    Endpoint de chat con multi-tenancy.
    Cada usuario tiene su propio agente aislado.
    """
    from src.agents.agente_con_db import AgenteConDB

    # Agente independiente por usuario — no compartido
    agente_usuario = AgenteConDB()
    agente_usuario.iniciar_sesion(usuario.email, usuario.plan)

    respuesta = agente_usuario.chat(request.mensaje)

    return ChatResponse(
        respuesta=respuesta,
        usuario_id=usuario.clerk_user_id,
    )


@app.get("/mis-conversaciones")
async def mis_conversaciones(
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):
    """
    Devuelve el historial de conversaciones del usuario autenticado.
    Solo puede ver sus propias conversaciones.
    """
    usuarios_db = UsuariosDB()
    usuario_db = usuarios_db.buscar_por_email(usuario.email)

    if not usuario_db:
        return {"conversaciones": [], "total": 0}

    conv_db = ConversacionesDB()
    conversaciones = conv_db.historial_usuario(usuario_db["id"], limite=10)

    return {
        "usuario": usuario.email,
        "conversaciones": conversaciones,
        "total": len(conversaciones),
    }