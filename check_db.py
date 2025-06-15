from django.db import connection
from django.conf import settings

print(f"Using database engine: {settings.DATABASES['default']['ENGINE']}")
with connection.cursor() as cursor:
    cursor.execute("SELECT version();")
    print("PostgreSQL version:", cursor.fetchone()[0])
    cursor.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public';")
    print("Tables in database:", [row[0] for row in cursor.fetchall()])