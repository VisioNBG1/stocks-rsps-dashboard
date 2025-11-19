# Gunicorn configuration file for production
import os

# Server socket - Render sets PORT automatically
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"

# Worker processes - Use 2 workers for Render free tier
workers = 2
worker_class = "sync"
timeout = 600  # 10 minutes - backtest can take 5+ minutes for 300+ stocks
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "stocks-rsps-dashboard"

