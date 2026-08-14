"""
Consultas avanzadas a Supabase para análisis del negocio.
Extrae estadísticas y patrones de uso del agente.
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from src.database.supabase_client import get_client

load_dotenv()


class EstadisticasDB:
    """
    Consultas agregadas sobre usuarios, conversaciones y mensajes.
    """

    def __init__(self):
        self.client = get_client()

    def usuarios_por_plan(self) -> dict:
        """Cuenta usuarios por plan."""
        for plan in ["free", "pro", "enterprise"]:
            respuesta = self.client.table("usuarios").select(
                "id", count="exact"
            ).eq("plan", plan).execute()
            yield plan, respuesta.count or 0

    def total_conversaciones(self) -> int:
        """Total de conversaciones en la base de datos."""
        respuesta = self.client.table("conversaciones").select(
            "id", count="exact"
        ).execute()
        return respuesta.count or 0

    def total_mensajes(self) -> int:
        """Total de mensajes guardados."""
        respuesta = self.client.table("mensajes").select(
            "id", count="exact"
        ).execute()
        return respuesta.count or 0

    def mensajes_por_rol(self) -> dict:
        """Cuenta mensajes por rol (user vs assistant)."""
        resultado = {}
        for rol in ["user", "assistant"]:
            respuesta = self.client.table("mensajes").select(
                "id", count="exact"
            ).eq("role", rol).execute()
            resultado[rol] = respuesta.count or 0
        return resultado

    def ultimos_usuarios(self, limite: int = 5) -> list[dict]:
        """Obtiene los últimos N usuarios registrados."""
        respuesta = self.client.table("usuarios").select(
            "email, plan, fecha_registro"
        ).order("fecha_registro", desc=True).limit(limite).execute()
        return respuesta.data or []


class AnalisisMemoria:
    """
    Analiza los hechos de memoria para detectar patrones de uso.
    """

    def __init__(self):
        self.client = get_client()

    def todos_los_hechos(self) -> list[str]:
        """Obtiene todos los hechos de memoria de todos los usuarios."""
        respuesta = self.client.table("memoria_usuario").select("hecho").execute()
        return [r["hecho"] for r in respuesta.data] if respuesta.data else []

    def analizar_patrones(self) -> dict:
        """
        Analiza los hechos para detectar patrones frecuentes.
        """
        hechos = self.todos_los_hechos()

        sistemas = {}
        integraciones = {}
        problemas = {}
        planes = {}

        for hecho in hechos:
            hecho_lower = hecho.lower()

            # Detecta sistemas operativos
            for so in ["macos", "windows", "linux", "mac"]:
                if so in hecho_lower and "sistema" in hecho_lower:
                    sistemas[so] = sistemas.get(so, 0) + 1

            # Detecta integraciones
            for integ in ["slack", "github", "jira", "google drive"]:
                if integ in hecho_lower:
                    integraciones[integ] = integraciones.get(integ, 0) + 1

            # Detecta problemas frecuentes
            if "problema" in hecho_lower or "error" in hecho_lower or "frecuente" in hecho_lower:
                problemas[hecho] = problemas.get(hecho, 0) + 1

            # Detecta planes
            for plan in ["free", "pro", "enterprise"]:
                if plan in hecho_lower and "plan" in hecho_lower:
                    planes[plan] = planes.get(plan, 0) + 1

        return {
            "sistemas_operativos": sistemas,
            "integraciones_usadas": integraciones,
            "problemas_frecuentes": list(problemas.keys())[:5],
            "planes_detectados": planes,
            "total_hechos": len(hechos),
        }


class ReporteNegocio:
    """
    Genera un reporte ejecutivo combinando estadísticas y patrones.
    """

    def __init__(self):
        self.stats = EstadisticasDB()
        self.analisis = AnalisisMemoria()

    def generar(self) -> dict:
        """Genera el reporte completo del negocio."""
        # Usuarios por plan
        planes = {plan: count for plan, count in self.stats.usuarios_por_plan()}

        # Estadísticas generales
        total_conv = self.stats.total_conversaciones()
        total_msg = self.stats.total_mensajes()
        msg_por_rol = self.stats.mensajes_por_rol()
        ultimos = self.stats.ultimos_usuarios(3)

        # Patrones de memoria
        patrones = self.analisis.analizar_patrones()

        return {
            "timestamp": datetime.now().isoformat(),
            "usuarios": {
                "por_plan": planes,
                "total": sum(planes.values()),
                "ultimos_registrados": ultimos,
            },
            "conversaciones": {
                "total": total_conv,
                "mensajes_totales": total_msg,
                "mensajes_usuarios": msg_por_rol.get("user", 0),
                "mensajes_agente": msg_por_rol.get("assistant", 0),
            },
            "patrones": patrones,
        }

    def mostrar(self) -> None:
        """Muestra el reporte en formato legible."""
        reporte = self.generar()

        print("=" * 60)
        print("REPORTE DE NEGOCIO — TECHHELPER AI")
        print(f"Generado: {reporte['timestamp'][:19]}")
        print("=" * 60)

        print("\n📊 USUARIOS")
        for plan, count in reporte["usuarios"]["por_plan"].items():
            print(f"  {plan.capitalize()}: {count}")
        print(f"  Total: {reporte['usuarios']['total']}")

        print("\n💬 CONVERSACIONES")
        print(f"  Total conversaciones: {reporte['conversaciones']['total']}")
        print(f"  Mensajes de usuarios: {reporte['conversaciones']['mensajes_usuarios']}")
        print(f"  Mensajes del agente:  {reporte['conversaciones']['mensajes_agente']}")

        print("\n🔍 PATRONES DE USO")
        patrones = reporte["patrones"]
        print(f"  Total hechos en memoria: {patrones['total_hechos']}")

        if patrones["sistemas_operativos"]:
            print(f"  Sistemas operativos: {patrones['sistemas_operativos']}")

        if patrones["integraciones_usadas"]:
            print(f"  Integraciones: {patrones['integraciones_usadas']}")

        if patrones["planes_detectados"]:
            print(f"  Planes detectados: {patrones['planes_detectados']}")

        if patrones["problemas_frecuentes"]:
            print(f"  Problemas frecuentes:")
            for p in patrones["problemas_frecuentes"]:
                print(f"    - {p}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    reporte = ReporteNegocio()
    reporte.mostrar()