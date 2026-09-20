"""
Optimizador de contexto para reducir tokens sin perder calidad.
Adapta el contexto según la complejidad de la pregunta.
"""
from pathlib import Path


# Palabras clave por categoría de complejidad
PREGUNTAS_SIMPLES = ["hola", "gracias", "bye", "adiós", "ok", "si", "no", "bien"]
PALABRAS_TECNICAS = ["instalar", "configurar", "error", "integración", "slack", "github",
                     "plan", "precio", "costo", "api", "webhook", "token", "ssl"]


class OptimizadorContexto:
    """
    Optimiza el contexto enviado al LLM según la complejidad de la pregunta.
    Reduce hasta un 60% los tokens en preguntas simples.
    """

    def __init__(self, claude_md_base: str = ""):
        self.claude_md_base = claude_md_base or self._cargar_claude_md()
        self.resumen_claude_md = self._resumir_claude_md()

    def _cargar_claude_md(self) -> str:
        try:
            return Path("CLAUDE.md").read_text(encoding="utf-8")
        except Exception:
            return "Eres un asistente de soporte técnico para TechHelper."

    def _resumir_claude_md(self) -> str:
        """Versión resumida del CLAUDE.md para preguntas de complejidad media."""
        lineas = self.claude_md_base.split("\n")
        # Toma solo las primeras 20 líneas — el resumen del producto
        resumen = "\n".join(lineas[:20])
        return resumen

    def clasificar_complejidad(self, pregunta: str) -> str:
        """
        Clasifica la complejidad de la pregunta.
        Devuelve: simple, media, compleja
        """
        pregunta_lower = pregunta.lower().strip()

        # Preguntas simples — saludos y respuestas cortas
        if any(simple in pregunta_lower for simple in PREGUNTAS_SIMPLES):
            return "simple"

        # Preguntas técnicas — necesitan contexto completo
        if any(tecnica in pregunta_lower for tecnica in PALABRAS_TECNICAS):
            return "compleja"

        # Resto — complejidad media
        return "media"

    def construir_contexto_optimizado(
        self,
        pregunta: str,
        docs_rag: list[str],
        hechos_usuario: list[str],
        contexto_especializado: str = ""
    ) -> tuple[str, str, int]:
        """
        Construye el contexto mínimo necesario según la complejidad.
        Devuelve: (contexto, complejidad, tokens_estimados)
        """
        complejidad = self.clasificar_complejidad(pregunta)

        if complejidad == "simple":
            # Solo instrucciones básicas
            contexto = "Eres un asistente de soporte técnico para TechHelper. Responde de forma breve y amable."
            if hechos_usuario:
                contexto += f"\n\nDatos del usuario: {hechos_usuario[:2]}"

        elif complejidad == "media":
            # CLAUDE.md resumido + hechos del usuario
            contexto = self.resumen_claude_md
            if hechos_usuario:
                contexto += f"\n\nDatos del usuario: {hechos_usuario}"

        else:  # compleja
            # Contexto completo
            contexto = self.claude_md_base
            if contexto_especializado:
                contexto += f"\n\n{contexto_especializado}"
            if docs_rag:
                contexto += f"\n\n## Documentación relevante\n" + "\n\n".join(docs_rag)
            if hechos_usuario:
                contexto += f"\n\nDatos del usuario: {hechos_usuario}"

        tokens_estimados = len(contexto.split()) * 1.3  # estimación aproximada
        return contexto, complejidad, int(tokens_estimados)

    def estimar_ahorro(self, pregunta: str, docs_rag: list[str]) -> dict:
        """Calcula el ahorro de tokens respecto al contexto completo."""
        _, _, tokens_optimizado = self.construir_contexto_optimizado(pregunta, docs_rag, [])

        # Contexto completo sin optimizar
        contexto_completo = self.claude_md_base + "\n\n".join(docs_rag)
        tokens_completo = int(len(contexto_completo.split()) * 1.3)

        ahorro = tokens_completo - tokens_optimizado
        porcentaje = round((ahorro / tokens_completo) * 100) if tokens_completo > 0 else 0

        return {
            "tokens_sin_optimizar": tokens_completo,
            "tokens_optimizado": tokens_optimizado,
            "tokens_ahorrados": ahorro,
            "porcentaje_ahorro": porcentaje,
        }


if __name__ == "__main__":
    print("=== Demo Optimizador de Contexto ===\n")

    optimizador = OptimizadorContexto()
    docs_rag = ["Documentación de instalación...", "Precios del plan Pro..."]

    preguntas = [
        ("hola", "Saludo simple"),
        ("quiero saber mas sobre techhelper", "Pregunta general"),
        ("como instalo techhelper en mac con error de seguridad", "Pregunta técnica"),
        ("cuanto cuesta el plan pro y que incluye", "Pregunta de precios"),
    ]

    for pregunta, descripcion in preguntas:
        _, complejidad, tokens = optimizador.construir_contexto_optimizado(
            pregunta, docs_rag, ["sistema: macOS", "plan: Pro"]
        )
        ahorro = optimizador.estimar_ahorro(pregunta, docs_rag)
        print(f"Pregunta: {descripcion}")
        print(f"  Complejidad: {complejidad}")
        print(f"  Tokens: {tokens} (ahorro: {ahorro['porcentaje_ahorro']}%)")
        print()
