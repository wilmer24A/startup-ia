content = open('CLAUDE.md', 'r', encoding='utf-8').read()

if 'Responde SOLO con una palabra' in content:
    inicio = content.find('"""Clasifica el mensaje')
    if inicio > 0:
        fin = content.find('"""', inicio + 3) + 3
        content = content[:inicio] + content[fin:]
        with open('CLAUDE.md', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Bloque clasificador eliminado del CLAUDE.md")
    else:
        print("Bloque no encontrado")
else:
    print("El bloque ya no está en CLAUDE.md")