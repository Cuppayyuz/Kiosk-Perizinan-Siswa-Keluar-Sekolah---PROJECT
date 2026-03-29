import mysql.connector

DB_CONFIG = {
    'host': '127.0.0.1',      
    'user': 'root',           
    'password': '',           
    'database': 'kiosk_db'  #buat seperti nama database yang dibuat
}

class DatabaseClient:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(dictionary=True)
            return True
        except mysql.connector.Error as err:
            print(f"error connection : {err}")
            return False

    def disconnect(self):
        if self.cursor: self.cursor.close()
        if self.conn: self.conn.close()

    def cek_token(self, kode):
        kode_bersih = kode.strip() 
        
        print(f"DEBUG: Mencari token '{kode_bersih}'...")

        if self.connect():
            query = "SELECT * FROM transaksi_izin WHERE kode_token = %s AND status = 'WAITING'"
            
            # Kita cari persis sesuai inputan user dulu
            self.cursor.execute(query, (kode_bersih,))
            hasil = self.cursor.fetchone()
            
            # Jika tidak ketemu, coba cari versi Huruf Besarnya (Backup Plan)
            if not hasil:
                self.cursor.execute(query, (kode_bersih.upper(),))
                hasil = self.cursor.fetchone()

            self.disconnect()
            
            if hasil:
                print(f"✅ DITEMUKAN: {hasil['kode_token']}")
                return hasil
            else:
                print("❌ TIDAK DITEMUKAN di Database.")
                return None
        
        return None
    def cek_rfid_siswa(self, uid_kartu):
        uid_bersih = uid_kartu.strip()
        if self.connect():
            # Asumsi nama tabelnya 'siswa' dan kolomnya 'rfid_uid'
            query = "SELECT * FROM siswa WHERE rfid_uid = %s"
            self.cursor.execute(query, (uid_bersih,))
            hasil = self.cursor.fetchone()
            self.disconnect()
            return hasil
        return None

    # [BARU] Fungsi Finalisasi (Kunci Token & Catat Waktu)
    def update_izin_sukses(self, kode_token, rfid_siswa):
        if self.connect():
            try:
                # 1. Update status jadi SUCCESS
                # 2. Masukkan rfid siswa yang melakukan tap
                # 3. Isi waktu_scan dengan waktu sekarang (NOW())
                query = """
                    UPDATE transaksi_izin 
                    SET status = 'SUCCESS', 
                        rfid_siswa = %s, 
                        waktu_scan = NOW() 
                    WHERE kode_token = %s
                """
                self.cursor.execute(query, (rfid_siswa, kode_token))
                self.conn.commit() # Wajib commit biar tersimpan permanen
                self.disconnect()
                return True
            except Exception as e:
                print(f"Error Update: {e}")
                self.disconnect()
                return False
        return False