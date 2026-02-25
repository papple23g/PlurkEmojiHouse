import os

worker_class = "gthread"

workers = os.environ.get("WEB_CONCURRENCY", 2)

threads = 4

timeout = 20

graceful_timeout = 20

keepalive = 95

max_requests = 5000
max_requests_jitter = 500

accesslog = "-"

preload_app = True

forwarded_allow_ips = "*"
