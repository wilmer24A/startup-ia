content = open('src/database/supabase_client.py', 'r', encoding='utf-8').read()

# Añade el método eliminar_hecho a MemoriaDB
old = '''    def cargar_hechos(self, usuario_id: str) -> list[str]:
        respuesta = self.client.table("memoria_usuario").select("hecho").eq(
            "usuario_id", usuario_id
        ).order("timestamp").execute()
        return [r["hecho"] for r in respuesta.data] if respuesta.data else []'''

new = '''    def cargar_hechos(self, usuario_id: str) -> list[str]:
        respuesta = self.client.table("memoria_usuario").select("hecho").eq(
            "usuario_id", usuario_id
        ).order("timestamp").execute()
        return [r["hecho"] for r in respuesta.data] if respuesta.data else []

    def eliminar_hecho(self, usuario_id: str, hecho: str) -> None:
        self.client.table("memoria_usuario").delete().eq(
            "usuario_id", usuario_id
        ).eq("hecho", hecho).execute()'''

content = content.replace(old, new)

with open('src/database/supabase_client.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Metodo eliminar_hecho añadido correctamente")