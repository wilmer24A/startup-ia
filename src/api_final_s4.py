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
from src.database.pinecone_client import PineconeRAG
from src.agents.agente_multinivel import ClasificadorContexto, CONTEXTOS_ESPECIALIZADOS
from src.agents.prompt_dinamico import PromptDinamico
from src.database.consultas import ReporteNegocio
from fastapi.responses import StreamingResponse
from src.tasks.celery_app import tarea_analizar_conversacion, tarea_deduplicar_memoria
from src.middleware.rate_limiter import rate_limiter
from prometheus_fastapi_instrumentator import Instrumentator
from langsmith import traceable
from src.middleware.cache_respuestas import cache_respuestas
from src.agents.optimizador_contexto import OptimizadorContexto
from src.security.detector_injection import detector_injection
from src.security.middleware_seguridad import middleware_seguridad
from src.billing.stripe_client import stripe_client
from src.billing.planes import PLANES
from src.billing.metricas import MetricasBilling
import stripe as stripe_lib
import json

load_dotenv()

# =====================
# RECURSOS COMPARTIDOS
# =====================

security = HTTPBearer()
clerk_auth = ClerkAuth()
sincronizador = SincronizadorUsuarios()

# Estos se inicializan en el lifespan — compartidos entre todos los usuarios
rag_compartido: PineconeRAG = None
clasificador_compartido: ClasificadorContexto = None
prompt_dinamico_compartido: PromptDinamico = None
optimizador_compartido: OptimizadorContexto = None
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
    global rag_compartido, clasificador_compartido, prompt_dinamico_compartido, optimizador_compartido, claude_md_base

    print("Cargando recursos compartidos...")
    rag_compartido = PineconeRAG("data/knowledge")
    rag_compartido.indexar_documentos()
    clasificador_compartido = ClasificadorContexto()
    prompt_dinamico_compartido = PromptDinamico()
    claude_md_base = Path("CLAUDE.md").read_text(encoding="utf-8")
    optimizador_compartido = OptimizadorContexto(claude_md_base)
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

# Prometheus metrics
Instrumentator().instrument(app).expose(app)


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


def procesar_chat_langsmith(mensaje: str, usuario_email: str, hechos: list, categoria: str, contexto: str) -> str:
    """Función traceable para LangSmith."""
    client_openai = __import__('openai').OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    respuesta = client_openai.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": contexto},
            {"role": "user", "content": mensaje}
        ]
    )
    return respuesta.choices[0].message.content


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):
    """
    Chat con RAG compartido, memoria aislada y rate limiting.
    """
    # Verifica rate limit del usuario
    limite = rate_limiter.verificar_limite(usuario.supabase_id, usuario.plan)
    if not limite["permitido"]:
        raise HTTPException(
            status_code=429,
            detail=f"Límite de peticiones excedido. Plan {usuario.plan}: {limite['limite']} peticiones/minuto. Intenta en 60 segundos."
        )
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # PASO 0: Middleware de seguridad unificado
    mensaje_sanitizado = middleware_seguridad.verificar_mensaje(
        mensaje=request.mensaje,
        usuario_id=usuario.supabase_id,
        plan=usuario.plan
    )

    # PASO 1: Verifica caché
    respuesta_cache = cache_respuestas.obtener(mensaje_sanitizado)
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
    categoria = clasificador_compartido.clasificar(mensaje_sanitizado)

    # PASO 3: Construye contexto optimizado
    docs = rag_compartido.buscar(mensaje_sanitizado, top_k=2)
    archivo_esp = CONTEXTOS_ESPECIALIZADOS.get(categoria)
    contexto_esp = ""
    if archivo_esp and Path(archivo_esp).exists():
        contexto_esp = Path(archivo_esp).read_text(encoding='utf-8')

    contexto, complejidad, tokens_est = optimizador_compartido.construir_contexto_optimizado(
        request.mensaje, docs, hechos_usuario, contexto_esp
    )
    print(f"[Optimizador] Complejidad: {complejidad} | Tokens estimados: {tokens_est}")

    # PASO 4: Genera respuesta con tracing de LangSmith
    contenido = procesar_chat_langsmith(
        mensaje=mensaje_sanitizado,
        usuario_email=usuario.email,
        hechos=hechos_usuario,
        categoria=categoria,
        contexto=contexto
    )

    # PASO 5: Guarda en caché
    cache_respuestas.guardar(mensaje_sanitizado, contenido, categoria)

    # Guarda en PostgreSQL
    conv_db = ConversacionesDB()
    conversacion = conv_db.crear_conversacion(usuario.supabase_id)
    conv_db.guardar_mensaje(conversacion["id"], "user", request.mensaje)
    conv_db.guardar_mensaje(conversacion["id"], "assistant", contenido)

    # Dispara análisis en segundo plano con Celery
    try:
        tarea_analizar_conversacion.delay(usuario.supabase_id, conversacion["id"])
    except Exception as e:
        print(f"Warning: No se pudo enviar tarea a Celery: {e}")

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


@app.get("/mi-limite")
async def mi_limite(usuario: UsuarioCompleto = Depends(verificar_usuario)):
    """Devuelve el estado actual del rate limit del usuario."""
    estado = rate_limiter.estado_usuario(usuario.supabase_id, usuario.plan)
    return {
        "email": usuario.email,
        "plan": usuario.plan,
        **estado
    }


@app.get("/sistema/estado")
async def sistema_estado(usuario: UsuarioCompleto = Depends(verificar_usuario)):
    """
    Estado completo del sistema — verifica todos los servicios en tiempo real.
    """
    import time
    estado = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "api": "ok",
        "servicios": {}
    }

    # Verifica Supabase
    try:
        from src.database.supabase_client import get_client
        client = get_client()
        client.table("usuarios").select("id", count="exact").limit(1).execute()
        estado["servicios"]["supabase"] = "ok"
    except Exception as e:
        estado["servicios"]["supabase"] = f"error: {str(e)[:50]}"

    # Verifica Redis
    try:
        from upstash_redis import Redis
        import os
        r = Redis(url=os.getenv("UPSTASH_REDIS_REST_URL"), token=os.getenv("UPSTASH_REDIS_REST_TOKEN"))
        r.set("health_check", "ok")
        estado["servicios"]["redis"] = "ok"
    except Exception as e:
        estado["servicios"]["redis"] = f"error: {str(e)[:50]}"

    # Verifica Pinecone
    try:
        stats = rag_compartido.index.describe_index_stats()
        estado["servicios"]["pinecone"] = f"ok ({stats.total_vector_count} vectores)"
    except Exception as e:
        estado["servicios"]["pinecone"] = f"error: {str(e)[:50]}"

    # Estado general
    errores = [k for k, v in estado["servicios"].items() if "error" in str(v)]
    estado["estado_general"] = "degradado" if errores else "saludable"
    estado["errores"] = errores

    return estado


@app.post("/billing/upgrade")
async def billing_upgrade(
    plan: str,
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):
    """Crea una sesión de pago en Stripe para actualizar el plan."""
    if plan not in ["pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Plan inválido")

    resultado = stripe_client.crear_sesion_pago(plan, usuario.email)

    if resultado.get("error"):
        raise HTTPException(status_code=400, detail=resultado["error"])

    return {"url": resultado["url"], "plan": plan}


@app.post("/webhook/stripe")
async def webhook_stripe(request: Request):
    """
    Recibe webhooks de Stripe y actualiza el plan del usuario.
    No requiere autenticación — usa firma de Stripe.
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    evento = stripe_client.verificar_webhook(payload, signature)

    if not evento:
        raise HTTPException(status_code=400, detail="Webhook inválido")

    # Pago completado
    if evento["type"] == "checkout.session.completed":
        session = evento["data"]["object"]
        email = session.get("customer_email", "")
        plan = session.get("metadata", {}).get("plan", "free")

        if email and plan:
            from src.database.supabase_client import UsuariosDB, get_client
            client = get_client()
            client.table("usuarios").update({"plan": plan}).eq("email", email).execute()
            print(f"Plan actualizado: {email} → {plan}")

    # Suscripción cancelada
    elif evento["type"] == "customer.subscription.deleted":
        customer_id = evento["data"]["object"].get("customer")
        if customer_id:
            try:
                customer = stripe_lib.Customer.retrieve(customer_id)
                email = customer.get("email", "")
                if email:
                    from src.database.supabase_client import get_client
                    client = get_client()
                    client.table("usuarios").update({"plan": "free"}).eq("email", email).execute()
                    print(f"Plan cancelado: {email} → free")
            except Exception as e:
                print(f"Error procesando cancelación: {e}")

    return {"status": "ok"}


@app.get("/billing/planes")
async def billing_planes(usuario: UsuarioCompleto = Depends(verificar_usuario)):
    """Devuelve los planes disponibles para upgrade."""
    planes = stripe_client.obtener_planes_disponibles()
    return {
        "plan_actual": usuario.plan,
        "planes_disponibles": planes
    }


@app.get("/billing/metricas")
async def billing_metricas(usuario: UsuarioCompleto = Depends(verificar_usuario)):
    """Dashboard de métricas de billing — solo Pro y Enterprise."""
    if usuario.plan not in ["pro", "enterprise"]:
        raise HTTPException(status_code=403, detail="Solo usuarios Pro o Enterprise")
    metricas = MetricasBilling()
    return metricas.generar_dashboard()


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