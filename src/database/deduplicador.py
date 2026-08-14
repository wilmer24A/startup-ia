"""
Deduplicador de memoria de usuario en PostgreSQL.
Limpia hechos duplicados y resuelve contradicciones.
"""
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from src.database.supabase_client import get_client, MemoriaDB

load_dotenv()


class DeduplicadorMemoria:
    """
    Detecta y elimina hechos duplicados o contradictorios
    en la memoria del usuario en PostgreSQL.
    """

    def __init__(self):
        self.client = get_client()
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.memoria_db = MemoriaDB()

    def detectar_duplicados(self, hechos: list[str]) -> list[tuple[str, str]]:
        """
        Usa el LLM para detectar pares de hechos que son duplicados
        o se refieren a lo mismo con diferente wording.
        """
        if len(hechos) < 2:
            return []

        hechos_texto = "\n".join(f"{i+1}. {h}" for i, h in enumerate(hechos))

        respuesta = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en deduplicación de datos. Responde SOLO con JSON válido."
                },
                {
                    "role": "user",
                    "content": f"""Analiza estos hechos sobre un usuario y detecta duplicados o contradicciones.

Hechos:
{hechos_texto}

Identifica pares que:
- Son el mismo hecho expresado de forma diferente (ej: "mac" y "macOS Ventura")
- Se contradicen (ej: "plan: Free" y "plan: Pro")

Para cada par indica cuál mantener (el más específico o más reciente).

Responde SOLO con JSON:
{{"duplicados": [
    {{"mantener": "hecho a conservar", "eliminar": "hecho a eliminar", "razon": "por que"}},
]}}
Si no hay duplicados: {{"duplicados": []}}"""
                }
            ]
        )

        try:
            datos = json.loads(respuesta.choices[0].message.content)
            pares = []
            for d in datos.get("duplicados", []):
                pares.append((d["mantener"], d["eliminar"]))
            return pares
        except Exception as e:
            print(f"Error detectando duplicados: {e}")
            return []

    def limpiar_usuario(self, usuario_id: str) -> dict:
        """
        Limpia la memoria del usuario eliminando duplicados y contradicciones.
        """
        # Carga todos los hechos del usuario
        hechos = self.memoria_db.cargar_hechos(usuario_id)
        print(f"Hechos antes de limpiar: {len(hechos)}")

        if len(hechos) < 2:
            return {"hechos_antes": len(hechos), "eliminados": 0, "hechos_despues": len(hechos)}

        # Detecta duplicados con el LLM
        pares_duplicados = self.detectar_duplicados(hechos)

        eliminados = 0
        for mantener, eliminar in pares_duplicados:
            print(f"  Eliminando: '{eliminar}' (manteniendo: '{mantener}')")
            self.memoria_db.eliminar_hecho(usuario_id, eliminar)
            eliminados += 1

        hechos_limpios = self.memoria_db.cargar_hechos(usuario_id)
        print(f"Hechos después de limpiar: {len(hechos_limpios)}")

        return {
            "hechos_antes": len(hechos),
            "eliminados": eliminados,
            "hechos_despues": len(hechos_limpios),
            "hechos_finales": hechos_limpios,
        }


if __name__ == "__main__":
    print("=== Deduplicador de Memoria ===\n")

    from src.database.supabase_client import UsuariosDB

    # Busca el usuario de prueba
    usuarios_db = UsuariosDB()
    usuario = usuarios_db.buscar_por_email("alexander@techhelper.io")

    if not usuario:
        print("Usuario no encontrado")
        exit()

    print(f"Usuario: {usuario['email']}")

    # Muestra hechos antes de limpiar
    memoria_db = MemoriaDB()
    hechos_antes = memoria_db.cargar_hechos(usuario["id"])
    print(f"\nHechos en PostgreSQL ({len(hechos_antes)}):")
    for h in hechos_antes:
        print(f"  - {h}")

    # Limpia duplicados
    print("\nDetectando y eliminando duplicados...")
    dedup = DeduplicadorMemoria()
    resultado = dedup.limpiar_usuario(usuario["id"])

    print(f"\nResultado:")
    print(f"  Antes:     {resultado['hechos_antes']} hechos")
    print(f"  Eliminados: {resultado['eliminados']}")
    print(f"  Después:   {resultado['hechos_despues']} hechos")

    print(f"\nHechos limpios:")
    for h in resultado["hechos_finales"]:
        print(f"  - {h}")