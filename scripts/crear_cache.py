content = '''"""
Caché de respuestas con Redis (Upstash).
Evita llamadas repetidas al LLM para preguntas frecuentes.
"""
import os
import hashlib
import json
from dotenv import load_dotenv

load_dotenv()

TTL_SEGUNDOS = 3600  # 1 hora


class CacheRespuestas:
    """
    Guarda respuestas del agente en Redis.
    Preguntas idénticas devuelven la respuesta cacheada sin llamar al LLM.
    """

    def __init__(self):
        self._cliente = None

    def _get_cliente(self):
        if self._cliente is None:
            from upstash_redis import Redis
            self._cliente = Redis(
                url=os.getenv("UPSTASH_REDIS_REST_URL"),
                token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
            )
        return self._cliente

    def generar_clave(self, pregunta: str) -> str:
        """Genera una clave única basada en el hash de la pregunta."""
        hash_pregunta = hashlib.md5(pregunta.lower().strip().encode()).hexdigest()
        return f"cache:respuesta:{hash_pregunta}"

    def obtener(self, pregunta: str) -> str | None:
        """Busca la respuesta en caché. Devuelve None si no existe."""
        try:
            clave = self.generar_clave(pregunta)
            cliente = self._get_cliente()
            valor = cliente.get(clave)
            if valor:
                datos = json.loads(valor)
                print(f"[Cache] HIT — {pregunta[:50]}")
                return datos.get("respuesta")
            print(f"[Cache] MISS — {pregunta[:50]}")
            return None
        except Exception as e:
            print(f"[Cache] Error al obtener: {e}")
            return None

    def guardar(self, pregunta: str, respuesta: str, categoria: str = "") -> bool:
        """Guarda la respuesta en caché con TTL de 1 hora."""
        try:
            clave = self.generar_clave(pregunta)
            cliente = self._get_cliente()
            datos = json.dumps({"respuesta": respuesta, "categoria": categoria})
            cliente.setex(clave, TTL_SEGUNDOS, datos)
            print(f"[Cache] Guardado — {pregunta[:50]}")
            return True
        except Exception as e:
            print(f"[Cache] Error al guardar: {e}")
            return False

    def invalidar(self, pregunta: str) -> bool:
        """Elimina una respuesta del caché."""
        try:
            clave = self.generar_clave(pregunta)
            self._get_cliente().delete(clave)
            return True
        except Exception as e:
            print(f"[Cache] Error al invalidar: {e}")
            return False


# Instancia global
cache_respuestas = CacheRespuestas()


if __name__ == "__main__":
    print("=== Demo Caché de Respuestas ===\\n")

    cache = CacheRespuestas()

    # Simula guardar una respuesta
    pregunta = "Cuanto cuesta el plan Pro?"
    respuesta_llm = "El plan Pro cuesta $29/mes e incluye proyectos ilimitados y 50GB de almacenamiento."

    print("1. Intentando obtener del caché (primera vez)...")
    resultado = cache.obtener(pregunta)
    print(f"   Resultado: {resultado}\\n")

    print("2. Guardando respuesta en caché...")
    cache.guardar(pregunta, respuesta_llm, "facturacion")
    print()

    print("3. Intentando obtener del caché (segunda vez)...")
    resultado = cache.obtener(pregunta)
    print(f"   Resultado: {resultado[:80]}...\\n")

    print("4. Probando con variante de la pregunta (diferente hash)...")
    resultado2 = cache.obtener("cuanto cuesta el plan pro")
    print(f"   Resultado: {resultado2}\\n")

    print("Demo completada")
'''

with open('src/middleware/cache_respuestas.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Archivo creado correctamente")