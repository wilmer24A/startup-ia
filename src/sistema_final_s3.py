"""
Sistema Final Semana 3.
Pipeline completo: agente + PostgreSQL + deduplicación + reporte.
"""
import os
from src.agents.agente_con_db import AgenteConDB
from src.database.deduplicador import DeduplicadorMemoria
from src.database.consultas import ReporteNegocio
from src.database.supabase_client import UsuariosDB

def mostrar_separador(titulo: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {titulo}")
    print(f"{'=' * 60}\n")


class SistemaFinalS3:
    """
    Pipeline completo de la Semana 3.
    Integra agente, PostgreSQL, deduplicación y reporte.
    """

    def __init__(self, email: str, plan: str = "pro"):
        self.email = email
        self.plan = plan
        self.agente = AgenteConDB()
        self.deduplicador = DeduplicadorMemoria()
        self.reporte = ReporteNegocio()
        self.usuario_id = None

    def iniciar(self) -> None:
        """Inicia sesión y conecta con PostgreSQL."""
        mostrar_separador("INICIANDO SISTEMA")
        usuario = self.agente.iniciar_sesion(self.email, self.plan)
        self.usuario_id = usuario["id"]

    def procesar_preguntas(self, preguntas: list[str]) -> None:
        """Procesa una lista de preguntas con el agente."""
        mostrar_separador("PROCESANDO PREGUNTAS")
        for pregunta in preguntas:
            print(f"Usuario: {pregunta}")
            respuesta = self.agente.chat(pregunta)
            print(f"Agente: {respuesta[:150]}...")
            print()

    def finalizar(self) -> None:
        """
        Finaliza la sesión en el orden correcto:
        1. Extrae hechos nuevos
        2. Deduplica la memoria
        3. Genera el reporte
        """
        mostrar_separador("FINALIZANDO SESIÓN")

        # Paso 1: extrae hechos nuevos
        print("Paso 1: Extrayendo hechos nuevos...")
        self.agente.finalizar_sesion()

        # Paso 2: deduplica
        print("\nPaso 2: Deduplicando memoria...")
        resultado_dedup = self.deduplicador.limpiar_usuario(self.usuario_id)
        print(f"Hechos antes: {resultado_dedup['hechos_antes']}")
        print(f"Eliminados:   {resultado_dedup['eliminados']}")
        print(f"Hechos finales: {resultado_dedup['hechos_despues']}")

        # Paso 3: reporte de negocio
        mostrar_separador("REPORTE DE NEGOCIO")
        self.reporte.mostrar()


if __name__ == "__main__":
    sistema = SistemaFinalS3(
        email="alexander@techhelper.io",
        plan="pro"
    )

    sistema.iniciar()

    preguntas = [
        "Tengo el error de puerto 3000 en uso, como lo soluciono?",
        "Que almacenamiento incluye el plan Pro?",
        "Como sincronizo carpetas con Google Drive?",
    ]

    sistema.procesar_preguntas(preguntas)
    sistema.finalizar()