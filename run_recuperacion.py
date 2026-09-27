"""
Script para ejecutar el sistema de recuperación de usuarios.
Se ejecuta diariamente via cron job en EC2.
"""
import sys
import os
from datetime import datetime

# Añade el directorio del proyecto al path
sys.path.insert(0, '/home/ubuntu/startup-ia')

os.chdir('/home/ubuntu/startup-ia')

from dotenv import load_dotenv
load_dotenv()

from src.email.recuperacion import RecuperacionUsuarios

if __name__ == "__main__":
    print(f"[{datetime.now().isoformat()}] Iniciando recuperación de usuarios...")
    
    recuperacion = RecuperacionUsuarios(dias_inactividad=7)
    resultado = recuperacion.enviar_emails_recuperacion(dry_run=False)
    
    print(f"[{datetime.now().isoformat()}] Completado:")
    print(f"  Inactivos: {resultado['inactivos_detectados']}")
    print(f"  Enviados:  {resultado['emails_enviados']}")
    print(f"  Errores:   {resultado['errores']}")