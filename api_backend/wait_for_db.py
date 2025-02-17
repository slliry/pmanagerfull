import os
import time
import psycopg2

def wait_for_db():
    db_host = os.environ.get('POSTGRES_HOST', 'db')
    db_name = os.environ.get('POSTGRES_DB', 'postgres')
    db_user = os.environ.get('POSTGRES_USER', 'postgres')
    db_password = os.environ.get('POSTGRES_PASSWORD', 'postgres')

    while True:
        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host
            )
            conn.close()
            print("Database is ready!")
            break
        except psycopg2.OperationalError as e:
            print("Waiting for database...")
            time.sleep(1)

if __name__ == "__main__":
    wait_for_db() 