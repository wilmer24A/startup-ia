# Contexto Especializado — Problemas de Instalación

## Protocolo de diagnóstico
Cuando el usuario tiene un problema de instalación, sigue este orden:
1. Identifica el sistema operativo exacto (versión incluida)
2. Pregunta si el error ocurre durante la descarga, instalación o al abrir la app
3. Pide el mensaje de error exacto si existe
4. Proporciona los pasos específicos para ese sistema operativo

## Comandos de diagnóstico por sistema
- Mac: `ls /Applications/TechHelper.app` para verificar instalación
- Windows: `where techhelper` en CMD
- Linux: `which techhelper` en terminal

## Escalación en instalación
Si el usuario lleva más de 3 intentos fallidos → escala a soporte técnico especializado con el log de instalación

## Errores comunes y soluciones rápidas

Error "La aplicación no puede abrirse porque no se puede verificar el desarrollador" (Mac):
→ Ajustes > Privacidad y Seguridad > haz clic en "Abrir de todas formas"

Error "Windows protegió tu PC" (Windows):
→ Haz clic en "Más información" → "Ejecutar de todas formas"

Error "Puerto 3000 en uso":
→ Ejecuta techhelper --port 3001

Error "No se puede conectar al servidor":
→ Verifica conexión a internet y que el firewall no esté bloqueando TechHelper