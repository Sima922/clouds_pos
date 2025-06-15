import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file")
    print("Please make sure:")
    print("1. You have a .env file in the same directory")
    print("2. It contains DATABASE_URL=your_connection_string")
    exit(1)

# Parse connection parameters
try:
    # Extract connection components from URL
    parts = DATABASE_URL.split("://")[1].split("@")
    credentials = parts[0].split(":")
    host_port = parts[1].split("/")[0]
    
    db_params = {
        "dbname": DATABASE_URL.split("/")[-1].split("?")[0],
        "user": credentials[0],
        "password": credentials[1],
        "host": host_port.split(":")[0],
        "port": host_port.split(":")[1] if ":" in host_port else "5432",
        "sslmode": "require"
    }
    
    # Test connection
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"✅ Connection successful! PostgreSQL version: {version}")
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
    print("\nTroubleshooting steps:")
    print("1. Verify .env file exists in same directory as this script")
    print("2. Check DATABASE_URL format: postgresql://user:password@host/dbname?sslmode=require")
    print("3. Ensure your IP is whitelisted in Neon Security settings")
    print("4. Try temporary password: " + DATABASE_URL.split(":")[2].split("@")[0])