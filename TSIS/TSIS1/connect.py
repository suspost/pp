# connect.py
import psycopg2
from psycopg2 import OperationalError
from config import DB_CONFIG

def get_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except OperationalError as e:
        print(f"Database connection error: {e}")
        raise