content = '''"""
Rate limiting con Redis (Upstash).
Limita el número de peticiones por usuario por minuto.
"""
import os
import time
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

# Configuración
LIMITE_POR_MINUTO = {
    "free": 5,
    "pro": 20,
    "enterprise": 100,
}

VENTANA_SEGUNDOS = 60


class RateLimiter:
    """
    Controla el número de peticiones por usuario usando Redis.
    Usa el patrón sliding window con TTL automático.
    """

    def __init__(self):
        self._cliente = None

    def _get_cliente(self):
        """Crea el cliente de Redis de Upstash de forma lazy."""
        if self._cliente is None:
            from upstash_redis import Redis
            self._cliente = Redis(
                url=os.getenv("UPSTASH_REDIS_REST_URL"),
                token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
            )
        return self._cliente

    def verificar_limite(self, usuario_id: str, plan: str = "free") -> dict:
        """
        Verifica si el usuario puede hacer una petición.
        Devuelve info del estado actual del rate limit.
        """
        limite = LIMITE_POR_MINUTO.get(plan, LIMITE_POR_MINUTO["free"])
        clave = f"ratelimit:{usuario_id}:{int(time.time() // VENTANA_SEGUNDOS)}"

        try:
            cliente = self._get_cliente()

            # Incrementa el contador
            contador = cliente.incr(clave)

            # Establece TTL solo en la primera petición
            if contador == 1:
                cliente.expire(clave, VENTANA_SEGUNDOS)

            permitido = contador <= limite
            restantes = max(0, limite - contador)

            return {
                "permitido": permitido,
                "contador": contador,
                "limite": limite,
                "restantes": restantes,
                "plan": plan,
            }

        except Exception as e:
            # Si Redis falla, permite la petición (fail open)
            print(f"Rate limiter error: {e} — permitiendo petición")
            return {
                "permitido": True,
                "contador": 0,
                "limite": limite,
                "restantes": limite,
                "plan": plan,
            }

    def estado_usuario(self, usuario_id: str, plan: str = "free") -> dict:
        """Devuelve el estado actual del rate limit sin incrementar."""
        limite = LIMITE_POR_MINUTO.get(plan, LIMITE_POR_MINUTO["free"])
        clave = f"ratelimit:{usuario_id}:{int(time.time() // VENTANA_SEGUNDOS)}"

        try:
            cliente = self._get_cliente()
            contador = cliente.get(clave)
            contador = int(contador) if contador else 0
            return {
                "contador": contador,
                "limite": limite,
                "restantes": max(0, limite - contador),
                "plan": plan,
            }
        except Exception:
            return {"contador": 0, "limite": limite, "restantes": limite, "plan": plan}


# Instancia global compartida
rate_limiter = RateLimiter()


if __name__ == "__main__":
    print("=== Demo Rate Limiter ===\\n")

    # Simula peticiones de un usuario Free (límite: 5/min)
    usuario_test = "test_user_123"

    print(f"Límites por plan: {LIMITE_POR_MINUTO}")
    print(f"\\nSimulando 7 peticiones de usuario Free (límite: 5):\\n")

    for i in range(7):
        resultado = rate_limiter.verificar_limite(usuario_test, "free")
        estado = "✅ PERMITIDA" if resultado["permitido"] else "❌ BLOQUEADA"
        print(f"  Petición {i+1}: {estado} | Contador: {resultado['contador']}/{resultado['limite']} | Restantes: {resultado['restantes']}")

    print(f"\\nEstado actual del usuario:")
    estado = rate_limiter.estado_usuario(usuario_test, "free")
    print(f"  {estado}")
'''

with open('src/middleware/rate_limiter.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Rate limiter creado correctamente")