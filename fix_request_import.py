content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = 'from fastapi import FastAPI, HTTPException, Depends'
new = 'from fastapi import FastAPI, HTTPException, Depends, Request'

content = content.replace(old, new)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Request importado correctamente")