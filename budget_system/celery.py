import os
from celery import Celery

# 1) Tell Celery which Django settings module to use.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budget_system.settings")

# 2) Create a Celery application instance with a readable name.
app = Celery("budget_system")

# 3) Load any CELERY_* configs from Django settings (so we keep one place for config).
app.config_from_object("django.conf:settings", namespace="CELERY")

# 4) Auto-discover tasks.py in all installed apps (e.g., expenses/tasks.py).
app.autodiscover_tasks()
