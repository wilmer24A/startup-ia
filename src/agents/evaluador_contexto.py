"""
Evaluador automático del context engineering.
Mide si el contexto está mejorando las respuestas del agente.
"""
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from src.agents.prompt_dinamico import AgentePromptDinamico
from src.agents.memoria_usuario import MemoriaUsuario

load_dotenv()


class EvaluadorContexto:
    """
    Evalúa si el context engineering está funcionando correctamente.
    Mide uso del contexto, personalización y precisión.
    """

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.resultados = []

    def evaluar_respuesta(
        self,
        pregunta: str,
        respuesta: str,
        contexto_usado: str,
        categoria: str,
    ) -> dict:
        """
        Evalúa una respuesta en 3 dimensiones del context engineering.
        """
        prompt = f"""Evalúa esta respuesta de un agente de soporte técnico.

Pregunta del usuario: {pregunta}
Categoría detectada: {categoria}
Contexto disponible para el agente (resumen): {contexto_usado[:500]}
Respuesta del agente: {respuesta}

Evalúa en estas 3 dimensiones del 1 al 5:

1. uso_contexto: ¿el agente usó información del contexto/documentos en su respuesta?
   5=usó datos específicos del contexto, 1=ignoró el contexto completamente

2. personalizacion: ¿el agente personalizó la respuesta según el usuario específico?
   5=muy personalizada, 1=respuesta genérica que valdría para cualquier usuario

3. precision: ¿la respuesta es factualmente correcta y útil?
   5=completamente correcta y útil, 1=incorrecta o inútil

Responde SOLO con JSON:
{{"uso_contexto": N, "personalizacion": N, "precision": N, "feedback": "qué mejorar en el CLAUDE.md"}}"""

        respuesta_eval = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[
                {"role": "system", "content": "Eres un evaluador experto en context engineering. Responde SOLO con JSON válido."},
                {"role": "user", "content": prompt}
            ]
        )

        try:
            datos = json.loads(respuesta_eval.choices[0].message.content)
            media = (datos["uso_contexto"] + datos["personalizacion"] + datos["precision"]) / 3
            resultado = {
                "pregunta": pregunta,
                "categoria": categoria,
                "uso_contexto": datos["uso_contexto"],
                "personalizacion": datos["personalizacion"],
                "precision": datos["precision"],
                "media": round(media, 2),
                "feedback": datos.get("feedback", ""),
            }
            self.resultados.append(resultado)
            return resultado
        except Exception as e:
            return {"error": str(e)}

    def reporte_final(self) -> dict:
        """Genera el reporte final de evaluación."""
        if not self.resultados:
            return {"error": "No hay evaluaciones"}

        total = len(self.resultados)
        media_uso = sum(r["uso_contexto"] for r in self.resultados) / total
        media_personal = sum(r["personalizacion"] for r in self.resultados) / total
        media_precision = sum(r["precision"] for r in self.resultados) / total
        media_global = sum(r["media"] for r in self.resultados) / total

        feedbacks = [r["feedback"] for r in self.resultados if r.get("feedback")]

        return {
            "total_evaluaciones": total,
            "media_global": round(media_global, 2),
            "uso_contexto": round(media_uso, 2),
            "personalizacion": round(media_personal, 2),
            "precision": round(media_precision, 2),
            "feedbacks": feedbacks,
        }


if __name__ == "__main__":
    print("=== Evaluador de Context Engineering ===\n")

    agente = AgentePromptDinamico(usuario_id="alexander_123")
    evaluador = EvaluadorContexto()
    print()

    casos_prueba = [
        "No puedo instalar TechHelper en Mac, me sale error de seguridad",
        "Cuantos proyectos puedo tener en el plan Pro?",
        "Como configuro la integracion con Slack?",
        "Quiero cambiar del plan Free al Pro",
    ]

    for pregunta in casos_prueba:
        print(f"Pregunta: {pregunta}")
        resultado_agente = agente.chat(pregunta)

        evaluacion = evaluador.evaluar_respuesta(
            pregunta=pregunta,
            respuesta=resultado_agente["respuesta"],
            contexto_usado=f"CLAUDE.md + categoria:{resultado_agente['categoria']} + memoria usuario + RAG docs",
            categoria=resultado_agente["categoria"],
        )

        print(f"Categoria: {resultado_agente['categoria']}")
        print(f"Uso contexto: {evaluacion.get('uso_contexto')}/5")
        print(f"Personalizacion: {evaluacion.get('personalizacion')}/5")
        print(f"Precision: {evaluacion.get('precision')}/5")
        print(f"Media: {evaluacion.get('media')}/5")
        print(f"Feedback: {evaluacion.get('feedback')}")
        print("-" * 60)
        print()

    print("=== Reporte Final ===")
    reporte = evaluador.reporte_final()
    print(f"Total evaluaciones: {reporte['total_evaluaciones']}")
    print(f"Media global:       {reporte['media_global']}/5")
    print(f"Uso del contexto:   {reporte['uso_contexto']}/5")
    print(f"Personalización:    {reporte['personalizacion']}/5")
    print(f"Precisión:          {reporte['precision']}/5")
    print(f"\nFeedbacks para mejorar el CLAUDE.md:")
    for i, fb in enumerate(reporte['feedbacks'], 1):
        print(f"  {i}. {fb}")