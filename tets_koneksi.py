import mysql.connector

# SETTINGAN DATABASE (Cek lagi password/nama db kamu)
config = {
    'host': '127.0.0.1',    # KITA PAKAI ANGKA IP, JANGAN 'localhost'
    'user': 'root',
    'password': '',
    'database': 'kiosk_db'  # Pastikan nama ini BENAR
}

print("--- MULAI DIAGNOSA ---")

try:
    # 1. COBA KONEK
    conn = mysql.connector.connect(**config)
    print("✅ 1. Koneksi Database BERHASIL!")
    
    cursor = conn.cursor(dictionary=True)
    
    # 2. CEK APAKAH TABEL ADA?
    cursor.execute("SHOW TABLES LIKE 'transaksi_izin'")
    tabel = cursor.fetchone()
    if tabel:
        print("✅ 2. Tabel 'transaksi_izin' DITEMUKAN!")
    else:
        print("❌ 2. Tabel 'transaksi_izin' TIDAK ADA! (Salah Database?)")
        exit()

    # 3. TAMPILKAN SEMUA TOKEN YANG 'WAITING'
    print("\n--- ISI DATA TOKEN SAAT INI ---")
    cursor.execute("SELECT * FROM transaksi_izin WHERE status = 'WAITING'")
    data = cursor.fetchall()
    
    if not data:
        print("⚠️ TIDAK ADA TOKEN YANG 'WAITING'.")
        print("   (Artinya Web Guru belum berhasil menyimpan data, atau semua token sudah terpakai)")
    else:
        print(f"✅ Ditemukan {len(data)} Token Aktif:")
        for baris in data:
            print(f"   -> TOKEN: '{baris['kode_token']}' | JENIS: {baris['jenis_izin']}")

    conn.close()

except mysql.connector.Error as err:
    print(f"❌ KONEKSI GAGAL: {err}")

print("\n--- SELESAI ---")