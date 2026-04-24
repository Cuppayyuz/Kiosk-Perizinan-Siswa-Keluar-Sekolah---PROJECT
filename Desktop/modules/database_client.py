import mysql.connector

DB_CONFIG = {
    'host': '127.0.0.1',      
    'user': 'root',           
    'password': '',           
    'database': 'kiosk_db'  
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
            print(f"Error connection: {err}")
            return False

    def disconnect(self):
        if self.cursor: self.cursor.close()
        if self.conn: self.conn.close()

    def cek_token(self, kode):
        kode_bersih = kode.strip().upper() 
        print(f"DEBUG: Mencari token '{kode_bersih}'...")

        if self.connect():
            # [REVISI] Kita cari token yang statusnya MENUNGGU (mau keluar) 
            # ATAU SEDANG_KELUAR (mau kembali)
            query = "SELECT * FROM transaksi_izin WHERE kode_token = %s AND status IN ('MENUNGGU', 'SEDANG_KELUAR')"
            
            self.cursor.execute(query, (kode_bersih,))
            hasil = self.cursor.fetchone()
            self.disconnect()
            
            if hasil:
                print(f"✅ DITEMUKAN: {hasil['kode_token']} | Status: {hasil['status']}")
                return hasil
            else:
                print("❌ TIDAK DITEMUKAN atau Token Expired/Selesai.")
                return None
        
        return None

    def cek_rfid_siswa(self, uid_kartu):
        uid_bersih = uid_kartu.strip()
        if self.connect():
            query = "SELECT * FROM siswa WHERE rfid_uid = %s"
            self.cursor.execute(query, (uid_bersih,))
            hasil = self.cursor.fetchone()
            self.disconnect()
            return hasil
        return None

    # [REVISI] Fungsi Finalisasi Keluar (Kunci Token, Waktu Keluar & Simpan Foto)
    def update_izin_sukses(self, kode_token, rfid_siswa, nama_file_foto):
        if self.connect():
            try:
                # [REVISI] Update sesuai nama kolom di database baru
                query = """
                    UPDATE transaksi_izin 
                    SET status = 'SEDANG_KELUAR', 
                        rfid_siswa = %s, 
                        waktu_keluar = NOW(),
                        foto_bukti = %s
                    WHERE kode_token = %s
                """
                self.cursor.execute(query, (rfid_siswa, nama_file_foto, kode_token))
                self.conn.commit() 
                self.disconnect()
                return True
            except Exception as e:
                print(f"Error Update Izin Keluar: {e}")
                self.disconnect()
                return False
        return False

    # [BARU] Fungsi Khusus untuk Mencatat Siswa Kembali
    # [REVISI] Fungsi Finalisasi Keluar dengan Logika Pemisahan Status
    def update_izin_sukses(self, kode_token, rfid_siswa, nama_file_foto):
        if self.connect():
            try:
                # Menggunakan logika IF bawaan MySQL:
                # Jika jenis_izin adalah KELUAR, status jadi 'SEDANG_KELUAR'
                # Jika jenis_izin BUKAN KELUAR (Sakit/Dispen), status otomatis 'SELESAI'
                query = """
                    UPDATE transaksi_izin 
                    SET status = IF(jenis_izin = 'KELUAR', 'SEDANG_KELUAR', 'SELESAI'), 
                        rfid_siswa = %s, 
                        waktu_keluar = NOW(),
                        foto_bukti = %s
                    WHERE kode_token = %s
                """
                self.cursor.execute(query, (rfid_siswa, nama_file_foto, kode_token))
                self.conn.commit() 
                self.disconnect()
                return True
            except Exception as e:
                print(f"Error Update Izin Keluar: {e}")
                self.disconnect()
                return False
        return False