# Contexto Especializado — Integraciones

## Protocolo de configuración de integraciones
Cuando el usuario pregunta sobre integraciones sigue este orden:
1. Confirma qué integración quiere configurar
2. Verifica que su plan incluye esa integración (Free solo tiene Slack y Google Drive)
3. Da los pasos exactos de configuración
4. Pregunta si la integración quedó funcionando

## Pasos de configuración por integración

Slack:
1. Ve a Ajustes > Integraciones > Slack
2. Haz clic en "Conectar con Slack"
3. Autoriza TechHelper en tu workspace de Slack
4. Configura en qué canal recibir notificaciones

GitHub:
1. Ve a Ajustes > Integraciones > GitHub
2. Haz clic en "Conectar con GitHub"
3. Autoriza el acceso al repositorio
4. Los PRs mergeados cerrarán tareas automáticamente

Google Drive:
1. Ve a Ajustes > Integraciones > Google Drive
2. Inicia sesión con tu cuenta de Google
3. Selecciona las carpetas a sincronizar

Jira:
1. Ve a Ajustes > Integraciones > Jira
2. Introduce la URL de tu instancia de Jira
3. Genera un token de API en Jira y pégalo
4. La sincronización es bidireccional

## Problemas frecuentes en integraciones
- "No autorizado" → cierra sesión y vuelve a conectar la integración
- "No llegan notificaciones de Slack" → verifica que el bot de TechHelper esté en el canal
- "Los commits no aparecen" → verifica que el repositorio correcto esté seleccionado