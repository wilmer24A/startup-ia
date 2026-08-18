content = open('src/api_auth.py', 'r', encoding='utf-8').read()

old = '''from src.auth.clerk_auth import ClerkAuth, UsuarioAutenticado
from src.database.supabase_client import UsuariosDB, ConversacionesDB'''

new = '''from src.auth.clerk_auth import ClerkAuth, UsuarioAutenticado
from src.auth.usuario_sync import SincronizadorUsuarios
from src.database.supabase_client import UsuariosDB, ConversacionesDB'''

content = content.replace(old, new)

old2 = '''# Seguridad HTTP Bearer
security = HTTPBearer()
clerk_auth = ClerkAuth()'''

new2 = '''# Seguridad HTTP Bearer
security = HTTPBearer()
clerk_auth = ClerkAuth()
sincronizador = SincronizadorUsuarios()'''

content = content.replace(old2, new2)

old3 = '''async def verificar_usuario(
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
    return usuario'''

new3 = '''class UsuarioCompleto(UsuarioAutenticado):
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
    )'''

content = content.replace(old3, new3)

old4 = '''@app.post("/chat", response_model=ChatResponse)
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
    )'''

new4 = '''@app.post("/chat", response_model=ChatResponse)
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
    )'''

content = content.replace(old4, new4)

old5 = '''@app.get("/mis-conversaciones")
async def mis_conversaciones(
    usuario: UsuarioAutenticado = Depends(verificar_usuario)
):'''

new5 = '''@app.get("/mis-conversaciones")
async def mis_conversaciones(
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):'''

content = content.replace(old5, new5)

old6 = '''@app.get("/mi-perfil")
async def mi_perfil(usuario: UsuarioAutenticado = Depends(verificar_usuario)):'''

new6 = '''@app.get("/mi-perfil")
async def mi_perfil(usuario: UsuarioCompleto = Depends(verificar_usuario)):'''

content = content.replace(old6, new6)

old7 = '''    usuarios_db = UsuariosDB()
    usuario_db = usuarios_db.buscar_por_email(usuario.email)

    return {
        "clerk_user_id": usuario.clerk_user_id,
        "email": usuario.email,
        "plan": usuario_db.get("plan", "free") if usuario_db else "free",
        "en_supabase": usuario_db is not None,
    }'''

new7 = '''    return {
        "clerk_user_id": usuario.clerk_user_id,
        "email": usuario.email,
        "plan": usuario.plan,
        "supabase_id": usuario.supabase_id,
        "en_supabase": bool(usuario.supabase_id),
    }'''

content = content.replace(old7, new7)

with open('src/api_auth.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("API actualizada con multi-tenancy")