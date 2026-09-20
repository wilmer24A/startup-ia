content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '@traceable(name="chat-endpoint", project_name="startup-ia")\ndef procesar_chat_langsmith'
new = 'def procesar_chat_langsmith'

content = content.replace(old, new)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Traceable eliminado temporalmente")