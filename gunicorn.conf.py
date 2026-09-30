import os
import multiprocessing

# La cantidad inicial documentada es (2 x núcleos) + 1
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
threads = int(os.environ.get("GUNICORN_THREADS", 1))

timeout = int(os.environ.get("GUNICORN_TIMEOUT", 30))
graceful_timeout = 30
keepalive = 5

# Recicla los workers después de mil peticiones para evitar fugas de memoria
max_requests = 1000
max_requests_jitter = 100

# Escribe los logs directamente en la consola para que Docker los capture
accesslog = "-"
errorlog = "-"

# Confía en las cabeceras proxy (necesario si luego pones Nginx delante)
forwarded_allow_ips = "*"