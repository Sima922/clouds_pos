import os
import django
from django.conf import settings
from pathlib import Path
from django.apps import apps as django_apps
from importlib import import_module

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def reset_migrations():
    # Delete migration files
    for app_config in django_apps.get_app_configs():
        try:
            app_module = import_module(app_config.name)
            app_path = Path(app_module.__file__).parent
            migrations_dir = app_path / 'migrations'
            if migrations_dir.exists():
                for file in migrations_dir.iterdir():
                    if file.name != '__init__.py' and file.name.endswith('.py'):
                        file.unlink()
                print(f"Cleared migrations in {app_config.name}")
        except Exception as e:
            print(f"Skipped {app_config.name}: {e}")

    # Reset database schema
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("DROP SCHEMA public CASCADE;")
        cursor.execute("CREATE SCHEMA public;")
        cursor.execute("GRANT ALL ON SCHEMA public TO neondb_owner;")

        cursor.execute("GRANT ALL ON SCHEMA public TO public;")
    print("Database schema reset")

if __name__ == '__main__':
    reset_migrations()
