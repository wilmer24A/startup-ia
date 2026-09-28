content = '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY data/ ./data/
COPY CLAUDE.md .
COPY CLAUDE_instalacion.md .
COPY CLAUDE_facturacion.md .
COPY CLAUDE_integraciones.md .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.api_final_s4:app", "--host", "0.0.0.0", "--port", "8000"]
'''

with open('Dockerfile', 'w') as f:
    f.write(content)
print("Dockerfile actualizado")