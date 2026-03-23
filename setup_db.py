import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from core.config import settings

def create_database():
    # Parse existing database URL to get connection details
    # expected format: postgresql://user:password@host:port/dbname
    url = settings.DATABASE_URL
    
    db_name = url.split('/')[-1]
    base_url = url.rsplit('/', 1)[0]
    
    # Connect to the default 'postgres' database to create the new one
    try:
        # We need to extract the credentials
        conn = psycopg2.connect(base_url + '/postgres')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE {db_name};')
            print(f"Database {db_name} created successfully.")
            
            # Now we need to create the tables
            from db.database import engine, Base
            import db.models
            print("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            print("Tables created successfully.")
            
        else:
            print(f"Database {db_name} already exists.")
            
    except Exception as e:
        print(f"Error checking/creating database: {e}")
        print("You may need to update the DATABASE_URL in the .env file with the correct postgres credentials.")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    create_database()
