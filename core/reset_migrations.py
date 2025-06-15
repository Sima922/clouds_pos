import os
import shutil
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def reset_migrations():
    # Delete migration files
    apps_path = settings.BASE_DIR / 'apps'
    for app_dir in apps_path.iterdir():
        if app_dir.is_dir():
            migrations_dir = app_dir / 'migrations'
            if migrations_dir.exists():
                for file in migrations_dir.iterdir():
                    if file.name != '__init__.py':
                        file.unlink()
                print(f"Cleared migrations in {app_dir.name}")
    
    # Reset database
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("DROP SCHEMA public CASCADE;")
        cursor.execute("CREATE SCHEMA public;")
        cursor.execute("GRANT ALL ON SCHEMA public TO postgres;")
        cursor.execute("GRANT ALL ON SCHEMA public TO public;")
    print("Database schema reset")

if __name__ == '__main__':
    reset_migrations()