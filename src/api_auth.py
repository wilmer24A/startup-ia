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
from src.database.supabase_client import UsuariosDB, ConversacionesDB

load_dotenv()

# Seguridad HTTP Bearer
security = HTTPBearer()
clerk_auth = ClerkAuth()


# =====================
# DEPENDENCIA DE AUTENTICACIÓN
# =====================

async def verificar_usuario(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UsuarioAutenticado:
    """
    Dependencia de FastAPI que verifica el token JWT de Clerk.
    Se inyecta en cada endpoint protegido.
    Si el token es inválido devuelve 401.
    """
    token = credentials.credentials

    # Para desarrollo: acepta el clerk_user_id directamente como token
    # En producción esto sería un JWT real de Clerk
    if token.startswith("user_"):
        usuario_clerk = clerk_auth.obtener_usuario(token)
        if usuario_clerk:
            return UsuarioAutenticado(
                clerk_user_id=usuario_clerk["clerk_user_id"],
                email=usuario_clerk["email"],
            )

    # Verifica token JWT real
    usuario = clerk_auth.verificar_token(token)
    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado"
        )
    return usuario


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
async def mi_perfil(usuario: UsuarioAutenticado = Depends(verificar_usuario)):
    """
    Devuelve el perfil del usuario autenticado.
    Requiere token válido de Clerk.
    """
    usuarios_db = UsuariosDB()
    usuario_db = usuarios_db.buscar_por_email(usuario.email)

    return {
        "clerk_user_id": usuario.clerk_user_id,
        "email": usuario.email,
        "plan": usuario_db.get("plan", "free") if usuario_db else "free",
        "en_supabase": usuario_db is not None,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    usuario: UsuarioAutenticado = Depends(verificar_usuario)
):
    """
    Endpoint de chat protegido.
    El agente responde solo si el usuario está autenticado.
    """
    global agente_global

    if not agente_global:
        raise HTTPException(status_code=503, detail="Agente no inicializado")

    # Inicia sesión con el usuario autenticado
    agente_global.iniciar_sesion(usuario.email, "pro")

    respuesta = agente_global.chat(request.mensaje)

    return ChatResponse(
        respuesta=respuesta,
        usuario_id=usuario.clerk_user_id,
    )


@app.get("/mis-conversaciones")
async def mis_conversaciones(
    usuario: UsuarioAutenticado = Depends(verificar_usuario)
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