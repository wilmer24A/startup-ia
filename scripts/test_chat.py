import os
from dotenv import load_dotenv
load_dotenv()

from src.agents.optimizador_contexto import OptimizadorContexto
from pathlib import Path

claude_md = Path("CLAUDE.md").read_text(encoding="utf-8")
optimizador = OptimizadorContexto(claude_md)

pregunta = "cuanto cuesta el plan pro"
docs = ["Plan Pro: $29/mes, proyectos ilimitados, 50GB"]
hechos = ["plan: Pro", "sistema: macOS"]

contexto, complejidad, tokens = optimizador.construir_contexto_optimizado(pregunta, docs, hechos)

print(f"Complejidad: {complejidad}")
print(f"Tokens: {tokens}")
print(f"Contexto (primeros 200 chars):")
print(contexto[:200])
print()

# Llama al LLM con ese contexto
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
r = client.chat.completions.create(
    model="gpt-4o-mini",
    temperature=0.3,
    messages=[
        {"role": "system", "content": contexto},
        {"role": "user", "content": pregunta}
    ]
)
print(f"Respuesta: {r.choices[0].message.content[:200]}")