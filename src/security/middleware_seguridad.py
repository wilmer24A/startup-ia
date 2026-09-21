"""
Middleware de seguridad unificado para TechHelper AI.
Agrupa todas las capas de seguridad en un solo punto de entrada.
"""
from fastapi import HTTPException, Request
from src.security.detector_injection import detector_injection
from src.middleware.rate_limiter import rate_limiter


class MiddlewareSeguridad:
    """
    Aplica todas las capas de seguridad en orden:
    1. Rate limiting
    2. Detección de injection
    3. Sanitización
    """

    def __init__(self):
        self.detector = detector_injection
        self.limiter = rate_limiter

    def verificar_mensaje(self, mensaje: str, usuario_id: str, plan: str) -> str:
        """
        Verifica y sanitiza el mensaje del usuario.
        Devuelve el mensaje sanitizado o lanza HTTPException.
        """
        # Capa 2: Rate limiting
        limite = self.limiter.verificar_limite(usuario_id, plan)
        if not limite["permitido"]:
            raise HTTPException(
                status_code=429,
                detail=f"Límite de peticiones excedido. Plan {plan}: {limite['limite']} req/min"
            )

        # Capa 3: Detección de injection
        resultado = self.detector.detectar(mensaje)
        if resultado.es_ataque:
            raise HTTPException(
                status_code=400,
                detail=f"Mensaje rechazado: {resultado.razon}"
            )

        # Capa 4: Sanitización
        mensaje_limpio = self.detector.sanitizar(mensaje)
        return mensaje_limpio

    def reporte_seguridad(self, usuario_id: str, plan: str) -> dict:
        """Devuelve el estado de seguridad actual del usuario."""
        estado_rate = self.limiter.estado_usuario(usuario_id, plan)
        return {
            "rate_limit": estado_rate,
            "injection_detector": "activo",
            "sanitizacion": "activa",
        }


# Instancia global
middleware_seguridad = MiddlewareSeguridad()
