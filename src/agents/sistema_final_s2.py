"""
Sistema Final Semana 2.
Agente completo con evaluación automática y reporte ejecutivo.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from src.agents.prompt_dinamico import AgentePromptDinamico
from src.agents.evaluador_contexto import EvaluadorContexto
from src.agents.memoria_usuario import MemoriaUsuario

ARCHIVO_EVALUACIONES = Path("data/evaluaciones.json")


class HistorialEvaluaciones:
    """
    Guarda el historial de puntuaciones semana a semana.
    Permite mostrar la progresión del agente.
    """

    def __init__(self):
        self.historial = []
        self._cargar()

    def _cargar(self) -> None:
        if ARCHIVO_EVALUACIONES.exists():
            datos = json.loads(ARCHIVO_EVALUACIONES.read_text(encoding="utf-8"))
            self.historial = datos.get("historial", [])

    def guardar_sesion(self, reporte: dict) -> None:
        entrada = {
            "timestamp": datetime.now().isoformat(),
            "media_global": reporte["media_global"],
            "uso_contexto": reporte["uso_contexto"],
            "personalizacion": reporte["personalizacion"],
            "precision": reporte["precision"],
        }
        self.historial.append(entrada)
        ARCHIVO_EVALUACIONES.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVO_EVALUACIONES.write_text(
            json.dumps({"historial": self.historial}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def progresion(self) -> list[dict]:
        """Devuelve las últimas 5 sesiones para mostrar progresión."""
        return self.historial[-5:]

    def comparar_con_anterior(self, media_actual: float) -> str:
        """Compara con la sesión anterior."""
        if len(self.historial) < 2:
            return "Primera sesión evaluada"
        media_anterior = self.historial[-2]["media_global"]
        diferencia = round(media_actual - media_anterior, 2)
        if diferencia > 0:
            return f"↑ +{diferencia} vs sesión anterior"
        elif diferencia < 0:
            return f"↓ {diferencia} vs sesión anterior"
        else:
            return "= igual que sesión anterior"


class SistemaFinalS2:
    """
    Sistema completo de la Semana 2.
    Agente + evaluación automática + reporte ejecutivo.
    """

    def __init__(self, usuario_id: str = "default"):
        self.agente = AgentePromptDinamico(usuario_id=usuario_id)
        self.evaluador = EvaluadorContexto()
        self.historial_eval = HistorialEvaluaciones()
        self.usuario_id = usuario_id
        self.respuestas_sesion = []

    def chat(self, mensaje: str) -> str:
        """Procesa una pregunta y guarda para evaluación posterior."""
        resultado = self.agente.chat(mensaje)
        self.respuestas_sesion.append({
            "pregunta": mensaje,
            "respuesta": resultado["respuesta"],
            "categoria": resultado["categoria"],
        })
        return resultado["respuesta"]

    def finalizar_y_evaluar(self) -> dict:
        """
        Al finalizar la sesión:
        1. Evalúa todas las respuestas
        2. Extrae hechos del usuario
        3. Genera reporte completo
        """
        hechos_antes = len(self.agente.memoria.hechos)

        # Evalúa cada respuesta de la sesión
        for item in self.respuestas_sesion:
            self.evaluador.evaluar_respuesta(
                pregunta=item["pregunta"],
                respuesta=item["respuesta"],
                contexto_usado=f"CLAUDE.md + {item['categoria']} + RAG + prompt_dinamico",
                categoria=item["categoria"],
            )

        # Extrae hechos nuevos
        self.agente.finalizar_sesion()
        hechos_nuevos = len(self.agente.memoria.hechos) - hechos_antes

        # Reporte del evaluador
        reporte_eval = self.evaluador.reporte_final()

        # Guarda en historial
        self.historial_eval.guardar_sesion(reporte_eval)

        # Comparación con sesión anterior
        comparacion = self.historial_eval.comparar_con_anterior(
            reporte_eval["media_global"]
        )

        # Top 3 feedbacks más útiles
        feedbacks = reporte_eval.get("feedbacks", [])[:3]

        return {
            "preguntas_sesion": len(self.respuestas_sesion),
            "media_global": reporte_eval["media_global"],
            "uso_contexto": reporte_eval["uso_contexto"],
            "personalizacion": reporte_eval["personalizacion"],
            "precision": reporte_eval["precision"],
            "comparacion": comparacion,
            "hechos_nuevos": hechos_nuevos,
            "total_hechos": len(self.agente.memoria.hechos),
            "feedbacks_top3": feedbacks,
            "progresion": self.historial_eval.progresion(),
        }


def mostrar_reporte(reporte: dict) -> None:
    """Muestra el reporte ejecutivo al operador."""
    print("\n" + "=" * 60)
    print("REPORTE EJECUTIVO — SISTEMA FINAL SEMANA 2")
    print("=" * 60)

    print(f"\n📊 PUNTUACIONES DE ESTA SESIÓN")
    print(f"  Media global:     {reporte['media_global']}/5")
    print(f"  Uso del contexto: {reporte['uso_contexto']}/5")
    print(f"  Personalización:  {reporte['personalizacion']}/5")
    print(f"  Precisión:        {reporte['precision']}/5")
    print(f"  {reporte['comparacion']}")

    print(f"\n🧠 MEMORIA DEL USUARIO")
    print(f"  Hechos nuevos aprendidos: {reporte['hechos_nuevos']}")
    print(f"  Total hechos acumulados:  {reporte['total_hechos']}")

    print(f"\n📈 PROGRESIÓN (últimas sesiones)")
    for i, sesion in enumerate(reporte["progresion"], 1):
        fecha = sesion["timestamp"][:10]
        print(f"  Sesión {i} ({fecha}): {sesion['media_global']}/5")

    print(f"\n💡 TOP 3 MEJORAS PARA EL CLAUDE.MD")
    for i, fb in enumerate(reporte["feedbacks_top3"], 1):
        print(f"  {i}. {fb[:100]}...")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("=== Sistema Final Semana 2 ===\n")

    sistema = SistemaFinalS2(usuario_id="alexander_123")
    print()

    preguntas = [
        "No puedo instalar TechHelper en Mac, me sale error de seguridad",
        "Cuantos proyectos puedo tener en el plan Pro?",
        "Como configuro la integracion con Slack?",
        "Quiero cambiar del plan Free al Pro",
    ]

    print("Procesando preguntas...\n")
    for pregunta in preguntas:
        print(f"Usuario: {pregunta}")
        respuesta = sistema.chat(pregunta)
        print(f"Agente: {respuesta[:100]}...")
        print()

    print("Evaluando sesión...")
    reporte = sistema.finalizar_y_evaluar()
    mostrar_reporte(reporte)