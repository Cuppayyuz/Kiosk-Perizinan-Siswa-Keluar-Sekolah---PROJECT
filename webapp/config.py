import mysql.connector

DB_CONFIG = {
    'host': 'localhost',      
    'user': 'root',           
    'password': '',           
    'database': 'kiosk_db'  # Pastikan nama database ini BENAR ada di phpMyAdmin
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print("database tersambung")
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

if __name__ == "__main__":
    get_db_connection()