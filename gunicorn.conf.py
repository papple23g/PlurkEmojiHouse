import os

worker_class = "gthread"

workers = int(os.environ.get("WEB_CONCURRENCY", "2"))

threads = 4

timeout = 20

graceful_timeout = 20

keepalive = 95

# 0 = 不在尖峰流量中強制重啟 worker（先前 max_requests 曾觸發重啟與 H12 雪崩）
max_requests = 0
max_requests_jitter = 0

accesslog = "-"

preload_app = True

forwarded_allow_ips = "*"
