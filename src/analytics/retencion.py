"""
Análisis de retención de usuarios para TechHelper AI.
Calcula cuántos usuarios vuelven a usar el producto cada semana.
"""
from datetime import datetime, timedelta
from src.database.supabase_client import get_client


class AnalizadorRetencion:
    """
    Analiza la retención de usuarios semana a semana.
    """

    def __init__(self):
        self.client = get_client()

    def usuarios_activos_por_semana(self, semanas: int = 4) -> dict:
        """
        Obtiene cuántos usuarios únicos estuvieron activos cada semana.
        """
        ahora = datetime.now()
        resultado = {}

        for i in range(semanas):
            inicio_semana = ahora - timedelta(weeks=i+1)
            fin_semana = ahora - timedelta(weeks=i)

            try:
                r = self.client.table("eventos").select("usuario_id").gte(
                    "timestamp", inicio_semana.isoformat()
                ).lte(
                    "timestamp", fin_semana.isoformat()
                ).execute()

                usuarios_unicos = {e["usuario_id"] for e in (r.data or [])}
                semana_label = f"Hace {i+1} semana{'s' if i > 0 else ''}"
                resultado[semana_label] = len(usuarios_unicos)

            except Exception as e:
                print(f"Error: {e}")
                resultado[f"Semana -{i+1}"] = 0

        return resultado

    def calcular_retencion_simple(self) -> dict:
        """
        Calcula la retención comparando usuarios activos esta semana
        vs la semana pasada.
        """
        ahora = datetime.now()

        # Usuarios activos esta semana
        inicio_esta_semana = ahora - timedelta(weeks=1)
        try:
            r_esta = self.client.table("eventos").select("usuario_id").gte(
                "timestamp", inicio_esta_semana.isoformat()
            ).execute()
            activos_esta_semana = {e["usuario_id"] for e in (r_esta.data or [])}
        except Exception:
            activos_esta_semana = set()

        # Usuarios activos la semana pasada
        inicio_semana_pasada = ahora - timedelta(weeks=2)
        fin_semana_pasada = ahora - timedelta(weeks=1)
        try:
            r_pasada = self.client.table("eventos").select("usuario_id").gte(
                "timestamp", inicio_semana_pasada.isoformat()
            ).lte(
                "timestamp", fin_semana_pasada.isoformat()
            ).execute()
            activos_semana_pasada = {e["usuario_id"] for e in (r_pasada.data or [])}
        except Exception:
            activos_semana_pasada = set()

        # Usuarios que volvieron
        volvieron = activos_esta_semana & activos_semana_pasada

        tasa = round(len(volvieron) / len(activos_semana_pasada) * 100, 1) if activos_semana_pasada else 0

        return {
            "activos_semana_pasada": len(activos_semana_pasada),
            "activos_esta_semana": len(activos_esta_semana),
            "volvieron": len(volvieron),
            "tasa_retencion": f"{tasa}%",
            "interpretacion": "Buena retención" if tasa >= 20 else "Retención baja — mejorar el producto"
        }

    def usuarios_nunca_regresaron(self) -> int:
        """Cuenta usuarios que solo usaron el producto una vez."""
        try:
            r = self.client.table("eventos").select("usuario_id").execute()
            conteo = {}
            for e in (r.data or []):
                uid = e["usuario_id"]
                conteo[uid] = conteo.get(uid, 0) + 1
            return sum(1 for c in conteo.values() if c == 1)
        except Exception:
            return 0


if __name__ == "__main__":
    print("=== Análisis de Retención — TechHelper AI ===\n")

    analizador = AnalizadorRetencion()

    print("ACTIVIDAD POR SEMANA:")
    print("-" * 50)
    por_semana = analizador.usuarios_activos_por_semana()
    for semana, usuarios in por_semana.items():
        barra = "█" * usuarios
        print(f"  {semana}: {usuarios} usuarios {barra}")

    print("\nRETENCIÓN SEMANA A SEMANA:")
    print("-" * 50)
    retencion = analizador.calcular_retencion_simple()
    print(f"  Activos semana pasada: {retencion['activos_semana_pasada']}")
    print(f"  Activos esta semana:   {retencion['activos_esta_semana']}")
    print(f"  Volvieron:             {retencion['volvieron']}")
    print(f"  Tasa de retención:     {retencion['tasa_retencion']}")
    print(f"  Interpretación:        {retencion['interpretacion']}")

    print(f"\nUsuarios que solo usaron el producto una vez: {analizador.usuarios_nunca_regresaron()}")
