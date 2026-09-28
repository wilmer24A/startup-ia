from src.database.supabase_client import UsuariosDB, get_client

usuarios_db = UsuariosDB()
usuario = usuarios_db.buscar_por_email("alexander@techhelper.io")

client = get_client()

# Elimina el hecho duplicado directamente
client.table("memoria_usuario").delete().eq(
    "usuario_id", usuario["id"]
).eq("hecho", "plan: Pro").execute()

# Verifica resultado
respuesta = client.table("memoria_usuario").select("hecho").eq(
    "usuario_id", usuario["id"]
).execute()

hechos = [r["hecho"] for r in respuesta.data]
print(f"Hechos limpios ({len(hechos)}):")
for h in hechos:
    print(f"  - {h}")