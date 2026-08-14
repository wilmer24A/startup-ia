"""
Agente de soporte conectado a Supabase.
Guarda conversaciones y memoria del usuario en PostgreSQL.
"""
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from src.database.supabase_client import UsuariosDB, ConversacionesDB, MemoriaDB
from src.agents.rag_avanzado import RAGAvanzado
from src.agents.agente_multinivel import ClasificadorContexto, CONTEXTOS_ESPECIALIZADOS
from src.agents.prompt_dinamico import PromptDinamico

load_dotenv()


class AgenteConDB:
    """
    Agente de soporte con PostgreSQL como almacenamiento.
    Reemplaza archivos JSON con Supabase real.
    """

    def __init__(self, knowledge_dir: str = "data/knowledge"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.rag = RAGAvanzado(knowledge_dir)
        self.clasificador = ClasificadorContexto()
        self.prompt_dinamico = PromptDinamico()
        self.claude_md_base = Path("CLAUDE.md").read_text(encoding="utf-8")

        # Conexiones a Supabase
        self.usuarios_db = UsuariosDB()
        self.conv_db = ConversacionesDB()
        self.memoria_db = MemoriaDB()

        # Estado de la sesión
        self.usuario = None
        self.conversacion_id = None
        self.hechos_usuario = []
        self.historial = []

    def iniciar_sesion(self, email: str, plan: str = "free") -> dict:
        """
        Crea o recupera el usuario en PostgreSQL y abre una conversación.
        """
        # Obtiene o crea el usuario
        self.usuario = self.usuarios_db.obtener_o_crear(email, plan)
        print(f"Usuario: {self.usuario['email']} | Plan: {self.usuario['plan']}")

        # Carga hechos del usuario desde PostgreSQL
        self.hechos_usuario = self.memoria_db.cargar_hechos(self.usuario["id"])
        print(f"Hechos cargados desde PostgreSQL: {len(self.hechos_usuario)}")

        # Crea nueva conversación
        conversacion = self.conv_db.crear_conversacion(self.usuario["id"])
        self.conversacion_id = conversacion["id"]
        print(f"Conversación iniciada: {self.conversacion_id}\n")

        return self.usuario

    def _construir_contexto(self, mensaje: str) -> tuple[str, str]:
        """Construye el contexto optimizado con prompt dinámico."""
        categoria = self.clasificador.clasificar(mensaje)

        # CLAUDE.md base
        contexto = self.claude_md_base

        # Contexto especializado
        archivo_esp = CONTEXTOS_ESPECIALIZADOS.get(categoria)
        if archivo_esp and Path(archivo_esp).exists():
            contexto += f"\n\n{Path(archivo_esp).read_text(encoding='utf-8')}"

        # RAG avanzado
        docs = self.rag.buscar(mensaje, top_k=2)
        if docs:
            contexto += f"\n\n## Documentación técnica relevante\n" + "\n\n".join(docs)

        # Prompt dinámico con hechos del usuario
        instrucciones = self.prompt_dinamico.construir(
            mensaje, self.hechos_usuario, categoria
        )
        contexto += instrucciones

        return contexto, categoria

    def chat(self, mensaje: str) -> str:
        """
        Responde al usuario y guarda el mensaje en Supabase.
        """
        if not self.conversacion_id:
            raise ValueError("Debes llamar a iniciar_sesion() primero")

        # Guarda mensaje del usuario en PostgreSQL
        self.conv_db.guardar_mensaje(self.conversacion_id, "user", mensaje)

        # Construye contexto y genera respuesta
        contexto, categoria = self._construir_contexto(mensaje)
        self.historial.append({"role": "user", "content": mensaje})

        respuesta = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {"role": "system", "content": contexto},
                *self.historial
            ]
        )

        contenido = respuesta.choices[0].message.content
        self.historial.append({"role": "assistant", "content": contenido})

        # Guarda respuesta del agente en PostgreSQL
        self.conv_db.guardar_mensaje(self.conversacion_id, "assistant", contenido)

        print(f"[{categoria}] Mensaje guardado en Supabase")
        return contenido

    def finalizar_sesion(self) -> None:
        """
        Extrae hechos nuevos de la conversación y los guarda en PostgreSQL.
        """
        if not self.historial or not self.usuario:
            return

        from src.agents.memoria_usuario import MemoriaUsuario
        from openai import OpenAI
        import json

        conversacion = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in self.historial
        ])

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        respuesta = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": """Extrae hechos importantes sobre el usuario de esta conversación.
Solo hechos durables: sistema operativo, plan, integraciones, problemas frecuentes.
Responde SOLO con JSON: {"hechos": ["hecho1", "hecho2"]}
Si no hay hechos responde: {"hechos": []}"""
                },
                {"role": "user", "content": f"Conversación:\n{conversacion}"}
            ]
        )

        try:
            datos = json.loads(respuesta.choices[0].message.content)
            nuevos_hechos = datos.get("hechos", [])
            guardados = 0
            for hecho in nuevos_hechos:
                resultado = self.memoria_db.guardar_hecho(self.usuario["id"], hecho)
                if resultado:
                    guardados += 1
            print(f"\nHechos guardados en PostgreSQL: {guardados} nuevos")
        except Exception as e:
            print(f"Error extrayendo hechos: {e}")


if __name__ == "__main__":
    print("=== Agente con Supabase ===\n")

    agente = AgenteConDB()
    print()

    # Inicia sesión con el usuario de prueba
    agente.iniciar_sesion("alexander@techhelper.io", "pro")

    preguntas = [
        "No puedo instalar TechHelper en Mac, me sale error de seguridad",
        "Cuantos proyectos puedo tener en el plan Pro?",
        "Como configuro la integracion con Slack?",
    ]

    for pregunta in preguntas:
        print(f"Usuario: {pregunta}")
        respuesta = agente.chat(pregunta)
        print(f"Agente: {respuesta[:120]}...")
        print()

    agente.finalizar_sesion()
    print("\nConversación guardada en Supabase correctamente.")