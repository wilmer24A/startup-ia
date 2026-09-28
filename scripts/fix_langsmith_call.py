content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''    # Genera respuesta
    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": contexto},
            {"role": "user", "content": request.mensaje}
        ]
    )
    contenido = respuesta.choices[0].message.content'''

new = '''    # Genera respuesta con tracing de LangSmith
    contenido = procesar_chat_langsmith(
        mensaje=request.mensaje,
        usuario_email=usuario.email,
        hechos=hechos_usuario,
        categoria=categoria,
        contexto=contexto
    )'''

content = content.replace(old, new)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("LangSmith call conectado")