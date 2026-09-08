content = open('src/tasks/celery_app.py', 'r', encoding='utf-8').read()

old = 'CELERY_BROKER_URL = _redis_url + "?ssl_cert_reqs=CERT_NONE" if "rediss://" in _redis_url else _redis_url'

new = '''if "rediss://" in _redis_url and "ssl_cert_reqs" not in _redis_url:
    CELERY_BROKER_URL = _redis_url + "?ssl_cert_reqs=CERT_NONE"
else:
    CELERY_BROKER_URL = _redis_url'''

content = content.replace(old, new)

with open('src/tasks/celery_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix aplicado correctamente")