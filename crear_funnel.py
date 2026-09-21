content = '''"""
Analizador de funnel de conversión para TechHelper AI.
Calcula cuántos usuarios completan cada paso del proceso de upgrade.
"""
from src.database.supabase_client import get_client


PASOS_FUNNEL = [
    ("chat_mensaje", "Usaron el chat"),
    ("perfil_visto", "Vieron el perfil"),
    ("upgrade_intentado", "Intentaron hacer upgrade"),
    ("upgrade_completado", "Completaron el upgrade"),
]


class AnalizadorFunnel:
    """
    Analiza el funnel de conversión desde los eventos de Supabase.
    """

    def __init__(self):
        self.client = get_client()

    def usuarios_por_evento(self, tipo_evento: str) -> set:
        """Obtiene el conjunto de usuario_ids que hicieron un evento."""
        try:
            r = self.client.table("eventos").select("usuario_id").eq(
                "tipo", tipo_evento
            ).execute()
            return {e["usuario_id"] for e in (r.data or [])}
        except Exception as e:
            print(f"Error: {e}")
            return set()

    def total_usuarios(self) -> int:
        """Total de usuarios registrados."""
        try:
            r = self.client.table("usuarios").select("id", count="exact").execute()
            return r.count or 0
        except Exception:
            return 0

    def calcular_funnel(self) -> list[dict]:
        """
        Calcula el funnel completo de conversión.
        Devuelve cada paso con usuarios únicos y tasa de conversión.
        """
        total = self.total_usuarios()
        pasos = []

        anterior = total
        for tipo_evento, descripcion in PASOS_FUNNEL:
            usuarios = self.usuarios_por_evento(tipo_evento)
            count = len(usuarios)
            tasa = round(count / total * 100, 1) if total > 0 else 0
            abandono = round((anterior - count) / anterior * 100, 1) if anterior > 0 else 0

            pasos.append({
                "paso": descripcion,
                "evento": tipo_evento,
                "usuarios": count,
                "tasa_total": tasa,
                "abandono_desde_anterior": abandono,
            })
            anterior = count if count > 0 else anterior

        return pasos

    def categorias_mas_usadas(self) -> dict:
        """Analiza qué categorías de preguntas son más frecuentes."""
        try:
            r = self.client.table("eventos").select("metadata").eq(
                "tipo", "chat_mensaje"
            ).execute()

            categorias = {}
            for evento in (r.data or []):
                categoria = evento.get("metadata", {}).get("categoria", "desconocida")
                categorias[categoria] = categorias.get(categoria, 0) + 1

            return dict(sorted(categorias.items(), key=lambda x: x[1], reverse=True))
        except Exception as e:
            print(f"Error: {e}")
            return {}


if __name__ == "__main__":
    print("=== Funnel de Conversión — TechHelper AI ===\\n")

    analizador = AnalizadorFunnel()
    total = analizador.total_usuarios()
    print(f"Total usuarios registrados: {total}\\n")

    print("FUNNEL DE CONVERSIÓN:")
    print("-" * 60)
    funnel = analizador.calcular_funnel()
    for paso in funnel:
        print(f"  {paso[\'paso\']}")
        print(f"    Usuarios: {paso[\'usuarios\']} ({paso[\'tasa_total\']}% del total)")
        print(f"    Abandono desde anterior: {paso[\'abandono_desde_anterior\']}%")
        print()

    print("\\nCATEGORÍAS MÁS USADAS EN CHAT:")
    print("-" * 60)
    categorias = analizador.categorias_mas_usadas()
    for categoria, count in categorias.items():
        print(f"  {categoria}: {count} mensajes")
'''

with open('src/analytics/funnel.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Funnel creado correctamente")