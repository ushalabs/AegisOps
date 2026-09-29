import psycopg

from app.core.config import settings


def get_connection():
    return psycopg.connect(
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        connect_timeout=2,
    )

def check_database_connection() -> bool:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()

        return result == (1,)

    except psycopg.Error:
        return False