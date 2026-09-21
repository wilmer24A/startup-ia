"""
Sistema de planes y features para TechHelper AI.
Define qué puede hacer cada plan y centraliza la lógica de monetización.
"""
from dataclasses import dataclass, field


@dataclass
class PlanConfig:
    """Configuración de un plan de TechHelper."""
    nombre: str
    precio_mensual: float
    peticiones_por_minuto: int
    modelo_llm: str
    top_k_rag: int
    memoria_persistente: bool
    historial_conversaciones: int
    acceso_estadisticas: bool
    acceso_sistema_estado: bool


# Configuración de planes
PLANES = {
    "free": PlanConfig(
        nombre="Free",
        precio_mensual=0,
        peticiones_por_minuto=5,
        modelo_llm="gpt-4o-mini",
        top_k_rag=2,
        memoria_persistente=False,
        historial_conversaciones=5,
        acceso_estadisticas=False,
        acceso_sistema_estado=False,
    ),
    "pro": PlanConfig(
        nombre="Pro",
        precio_mensual=29,
        peticiones_por_minuto=20,
        modelo_llm="gpt-4o-mini",
        top_k_rag=5,
        memoria_persistente=True,
        historial_conversaciones=100,
        acceso_estadisticas=True,
        acceso_sistema_estado=True,
    ),
    "enterprise": PlanConfig(
        nombre="Enterprise",
        precio_mensual=99,
        peticiones_por_minuto=100,
        modelo_llm="gpt-4o-mini",
        top_k_rag=10,
        memoria_persistente=True,
        historial_conversaciones=1000,
        acceso_estadisticas=True,
        acceso_sistema_estado=True,
    ),
}


def obtener_plan(plan: str) -> PlanConfig:
    """Obtiene la configuración de un plan."""
    return PLANES.get(plan, PLANES["free"])


def obtener_modelo_llm(plan: str) -> str:
    """Devuelve el modelo de OpenAI según el plan."""
    return obtener_plan(plan).modelo_llm


def obtener_top_k_rag(plan: str) -> int:
    """Devuelve cuántos documentos del RAG usar según el plan."""
    return obtener_plan(plan).top_k_rag


def verificar_feature(plan: str, feature: str) -> bool:
    """Verifica si un plan tiene acceso a una feature específica."""
    config = obtener_plan(plan)
    return getattr(config, feature, False)


def comparar_planes() -> list[dict]:
    """Devuelve una comparación de todos los planes."""
    comparacion = []
    for plan_id, config in PLANES.items():
        comparacion.append({
            "plan": config.nombre,
            "precio": f"${config.precio_mensual}/mes",
            "peticiones_min": config.peticiones_por_minuto,
            "modelo": config.modelo_llm,
            "rag_docs": config.top_k_rag,
            "memoria": "Sí" if config.memoria_persistente else "No",
            "historial": config.historial_conversaciones,
        })
    return comparacion


if __name__ == "__main__":
    print("=== Sistema de Planes TechHelper AI ===\n")

    print("Comparación de planes:")
    print("-" * 70)
    for plan in comparar_planes():
        print(f"Plan: {plan['plan']} ({plan['precio']})")
        print(f"  Peticiones/min: {plan['peticiones_min']}")
        print(f"  Modelo LLM:     {plan['modelo']}")
        print(f"  Docs RAG:       {plan['rag_docs']}")
        print(f"  Memoria:        {plan['memoria']}")
        print(f"  Historial:      {plan['historial']} conversaciones")
        print()

    print("Verificación de features:")
    for plan_id in ["free", "pro", "enterprise"]:
        print(f"\n{plan_id.upper()}:")
        print(f"  Estadísticas:    {verificar_feature(plan_id, 'acceso_estadisticas')}")
        print(f"  Sistema estado:  {verificar_feature(plan_id, 'acceso_sistema_estado')}")
        print(f"  Memoria:         {verificar_feature(plan_id, 'memoria_persistente')}")
