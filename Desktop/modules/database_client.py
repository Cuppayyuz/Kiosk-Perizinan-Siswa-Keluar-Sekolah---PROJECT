import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'kiosk_db'
}

class database_client:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(dictionary=True)
            print("Database connected successfully.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False
        
    def disconnect(self):
        if self.conn: self.conn.close()
        if self.cursor: self.cursor.close()

    def chechk_token(self,code):
        if self.connect():
            query = "SELECT * FROM transaksi_izin WHERE kode_token = %s AND status = 'WAITING'"
            self.cursor.execute(query,(code, ))
            hasil = self.cursor.fetchone()
            self.disconnect()
            return hasil 
        return None
    

