import random 
from flask import Flask, render_template, request, redirect, url_for, session , jsonify,flash, Response 
from config import get_db_connection
import sys
from datetime import date
import io
import csv

sys.path.append('C:/robotik')

from Desktop.modules import printer



# 2. Baru lakukan import module-nya setelah path ditambahkan

# inisialisasi aplikasi Flask
app = Flask(__name__)
app.secret_key = 'kunci_rahasia_sekolah'



# route untuk halaman login
@app.route('/' , methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()

        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM guru WHERE username = %s AND password = %s", (username, password))
            akun = cursor.fetchone()
            conn.close()
            
            if akun:
                session['loggedin'] = True
                session['id'] = akun['id_guru'] 
                session['nama'] = akun['nama_lengkap']
                session['role'] = akun['role']
                
                if akun['role'] == 'admin':
                    return redirect(url_for('dashboard_admin'))
                elif akun['role'] == 'guru':
                    return redirect(url_for('dashboard_guru'))
                elif akun['role'] == 'pantau':
                    return redirect(url_for('pantau_kelas'))
            else:
                msg = 'Username atau Password Salah!'
    
    return render_template('login.html', msg=msg)

# jalur dashboard guru
@app.route('/dashboard_guru')
def dashboard_guru():
    # 1. Cek apakah sudah login
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    # 2. [BARU] KUNCI PINTU KHUSUS GURU
    if session.get('role') != 'guru':
        # Jika dia Admin, usir kembali ke halaman Admin
        if session.get('role') == 'admin':
            return redirect(url_for('dashboard_admin'))
        # Jika dia Pemantau, usir ke halaman Pemantau
        elif session.get('role') == 'pantau':
            return redirect(url_for('pantau_kelas'))
        # Jika tidak jelas, kembalikan ke login
        else:
            return redirect(url_for('login'))

    return render_template('guru/dashboard.html', nama=session['nama'])

# 1. Update Route Dashboard Admin untuk mengirim data ke HTML (READ)
@app.route('/dashboard_admin')
def dashboard_admin():
    # Pastikan sudah login
    if 'loggedin' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    # WAJIB pakai dictionary=True agar bisa dipanggil g.nama_lengkap di HTML
    cursor = conn.cursor(dictionary=True) 
    
    # 1. Tarik Data Siswa
    cursor.execute("SELECT * FROM siswa ORDER BY id_siswa DESC")
    list_siswa = cursor.fetchall()

    # 2. Tarik Data Guru & Admin
    # Mengambil semua data di tabel guru (karena admin juga disimpan di sini)
    cursor.execute("SELECT * FROM guru ORDER BY id_guru DESC")
    list_guru = cursor.fetchall()
    
    conn.close()

    # 3. LEMPAR DATA KE HTML (Ini yang paling penting!)
    return render_template('admin/dashboard.html', 
                           nama=session['nama'], 
                           data_siswa=list_siswa, 
                           data_guru=list_guru)


# 2. Route untuk Menambah Siswa (CREATE)
@app.route('/admin/tambah_siswa', methods=['POST'])
def tambah_siswa():
    if 'loggedin' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    # Tangkap data dari form (atribut 'name' di HTML)
    rfid = request.form['rfid_uid']
    nama = request.form['nama']
    kelas = request.form['kelas']

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Masukkan ke database
    query = "INSERT INTO siswa (rfid_uid, nama_siswa, kelas) VALUES (%s, %s, %s)"
    cursor.execute(query, (rfid, nama, kelas))
    
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard_admin'))

# =========================================================
# ROUTE IMPORT DATA SISWA (DENGAN VALIDASI KETAT)
# =========================================================
@app.route('/admin/import_siswa', methods=['POST'])
def import_siswa():
    if 'loggedin' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    # Cek apakah ada file yang diupload
    if 'file_csv' not in request.files:
        flash("Tidak ada file yang diunggah!", "danger")
        return redirect(url_for('dashboard_admin'))
        
    file = request.files['file_csv']
    if file.filename == '':
        flash("File belum dipilih!", "danger")
        return redirect(url_for('dashboard_admin'))

    if file and file.filename.endswith('.csv'):
        try:
            # Deteksi pemisah (Koma atau Titik Koma)
            sample = file.stream.read(1024).decode('utf-8')
            delimiter = ';' if ';' in sample else ','
            file.stream.seek(0) # Kembalikan kursor ke awal file

            stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
            csv_input = csv.reader(stream, delimiter=delimiter)

            conn = get_db_connection()
            cursor = conn.cursor()
            
            sukses = 0
            gagal = 0
            pesan_error = []

            for row_idx, row in enumerate(csv_input):
                # Abaikan baris yang benar-benar kosong di akhir file
                if not row or "".join(row).strip() == "":
                    continue

                # Ambil data kolom pertama dulu untuk dicek
                rfid_raw = str(row[0]).strip() if len(row) > 0 else ""

                # --- AUTO-DETEKSI JUDUL (HEADER) ---
                # Jika ini baris pertama (index 0) DAN isinya BUKAN angka murni (mengandung huruf)
                # Maka bisa dipastikan itu adalah Judul Kolom. Kita lewati!
                if row_idx == 0 and not rfid_raw.isdigit():
                    continue 

                nama = str(row[1]).strip() if len(row) > 1 else ""
                kelas = str(row[2]).strip().upper() if len(row) > 2 else ""

                # --- SISTEM VALIDASI & KEAMANAN ---
                # 1. Cek Data Kosong
                if not rfid_raw or not nama or not kelas:
                    gagal += 1
                    pesan_error.append(f"Baris {row_idx+1}: Ada kolom yang kosong.")
                    continue
                
                # 2. Sanitasi RFID (Ambil angkanya saja jika ada salah ketik)
                rfid = ''.join(filter(str.isdigit, rfid_raw))
                if not rfid:
                    gagal += 1
                    pesan_error.append(f"Baris {row_idx+1}: RFID '{rfid_raw}' tidak valid (bukan angka).")
                    continue

                # Jika lolos semua validasi, masukkan ke database
                try:
                    cursor.execute("INSERT INTO siswa (rfid_uid, nama_siswa, kelas) VALUES (%s, %s, %s)", (rfid, nama, kelas))
                    sukses += 1
                except Exception as db_err:
                    gagal += 1
                    pesan_error.append(f"Baris {row_idx+1}: RFID {rfid} sudah ada di database.")

            conn.commit()
            conn.close()

            # Susun Laporan Hasil Import
            if gagal > 0:
                laporan = f"Import selesai! {sukses} Berhasil, {gagal} Gagal dilewati.<br><strong>Detail Error:</strong><br>" + "<br>".join(pesan_error[:5])
                if gagal > 5: laporan += "<br>...(dan lainnya)"
                flash(laporan, "warning")
            else:
                flash(f"Import Sempurna! {sukses} data siswa berhasil ditambahkan.", "success")

        except Exception as e:
            flash(f"Terjadi kesalahan saat membaca file: {e}", "danger")
    else:
        flash("Format file harus .csv!", "danger")

    return redirect(url_for('dashboard_admin'))

# 3. Route untuk Menghapus Siswa (DELETE)
@app.route('/admin/hapus_siswa/<int:id>')
def hapus_siswa(id):
    if 'loggedin' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM siswa WHERE id_siswa = %s", (id,))
    
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard_admin'))

@app.route('/api/admin/dashboard_stats')
def api_dashboard_stats():
    if 'loggedin' not in session or session.get('role') != 'admin': return jsonify({})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) as total FROM siswa")
    total_siswa = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM guru")
    total_guru = cursor.fetchone()['total']
    
    hari_ini = date.today().strftime('%Y-%m-%d')
    # PERUBAHAN DI SINI: Gunakan waktu_dibuat
    cursor.execute("SELECT COUNT(*) as total FROM transaksi_izin WHERE DATE(waktu_dibuat) = %s", (hari_ini,))
    izin_hari_ini = cursor.fetchone()['total']
    
    conn.close()
    return jsonify({
        'total_siswa': total_siswa,
        'total_guru': total_guru,
        'izin_hari_ini': izin_hari_ini
    })

@app.route('/api/admin/laporan_live')
def api_laporan_live():
    if 'loggedin' not in session or session.get('role') != 'admin': return jsonify([])
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # PERUBAHAN DI SINI: Ambil waktu_dibuat, bukan waktu_keluar
    query = """
        SELECT t.kode_token, t.jenis_izin, t.status, t.waktu_dibuat, g.nama_lengkap as nama_guru 
        FROM transaksi_izin t
        LEFT JOIN guru g ON t.id_guru = g.id_guru
        ORDER BY t.id DESC LIMIT 20
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    
    return jsonify(data)

# =========================================================
# 2. CRUD GURU
# =========================================================

@app.route('/admin/tambah_guru', methods=['POST'])
def tambah_guru():
    if 'loggedin' not in session or session.get('role') != 'admin': 
        return redirect(url_for('login'))
    
    nama = request.form['nama_lengkap']
    username = request.form['username']
    password = request.form['password'] 
    role = request.form['role'] # <-- [BARU] Menangkap pilihan dari dropdown HTML
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # <-- [BARU] Memasukkan variabel 'role', bukan ditulis mati 'guru'
    cursor.execute("INSERT INTO guru (nama_lengkap, username, password, role) VALUES (%s, %s, %s, %s)", (nama, username, password, role))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard_admin'))

@app.route('/admin/hapus_guru/<int:id>')
def hapus_guru(id):
    if 'loggedin' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guru WHERE id_guru = %s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_admin'))

# =========================================================
# 2. CRUD ADMIN
# =========================================================
@app.route('/admin/tambah_admin', methods=['POST'])
def tambah_admin():
    if 'loggedin' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    
    nama = request.form['nama_lengkap']
    username = request.form['username']
    password = request.form['password'] # Ingat, ini masih plain-text untuk belajar
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO guru (nama_lengkap, username, password, role) VALUES (%s, %s, %s, 'admin')", (nama, username, password))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_admin'))

@app.route('/admin/hapus_admin/<int:id>')
def hapus_admin(id):
    if 'loggedin' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guru WHERE id_guru = %s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_admin'))

@app.route('/guru/riwayat')
def riwayat_guru():
    # UBAH BAGIAN INI: Samakan dengan pengecekan di dashboard_guru
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Ambil SEMUA data token yang dibuat oleh guru ini, urutkan dari yang terbaru
    query = """
        SELECT kode_token, jenis_izin, status, waktu_dibuat 
        FROM transaksi_izin 
        WHERE id_guru = %s 
        ORDER BY id DESC
    """
    cursor.execute(query, (session['id'],))
    data_riwayat = cursor.fetchall()
    conn.close()

    # Lempar datanya ke riwayat.html
    return render_template('guru/riwayat.html', nama=session['nama'], riwayat=data_riwayat)

@app.route('/buat_token/<jenis>')
def buat_token(jenis):  

    if 'loggedin' not in session:
        return redirect(url_for('login'))

    # 1. Generate Token Unik
    angka_token = random.randint(100000, 999999)
    token_baru = f'{jenis}-{angka_token}'

    # 2. Simpan ke Database
    id_guru = session['id']
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        query = "INSERT INTO transaksi_izin (kode_token, id_guru, jenis_izin, status) VALUES (%s, %s, %s, 'WAITING')"
        cursor.execute(query, (token_baru, id_guru, jenis))
        conn.commit()
    except Exception as e:
        flash(f"Terjadi kesalahan pada database: {e}")
        conn.close()
        return redirect(url_for('dashboard_guru'))
        
    conn.close() # Typo diperbaiki (sebelumnya conn.closer())

    # 3. EKSEKUSI PRINTER THERMAL (Pengaman Anti-Crash)
    try:
        # KODE INI SEKARANG AKTIF!
        printer.cetak_barcode(token_baru, jenis)
        
        # Pesan Sukses jika printer aman dan berhasil mencetak
        flash(f"Izin {jenis} berhasil diterbitkan! Struk barcode {token_baru} sedang dicetak.", "success")
        
    except Exception as e:
        # Jika printer mati/error, aplikasi web tetap aman!
        print(f"[WARNING PRINTER]: {e}")
        flash(f"Izin {jenis} TERSIMPAN, tapi STRUK GAGAL DICETAK! Periksa sambungan printer thermal.", "warning")

    # 4. Kembali ke dashboard guru
    return redirect(url_for('dashboard_guru'))

@app.route('/api/riwayat_terbaru')
def api_riwayat_terbaru():
    if 'loggedin' not in session: return jsonify([]) # Kembalikan list kosong jika belum login

    conn = get_db_connection()
    data = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        # Ambil 5 data terakhir milik guru ini
        query = "SELECT * FROM transaksi_izin WHERE id_guru = %s ORDER BY id DESC LIMIT 5"
        cursor.execute(query, (session['id'],))
        data = cursor.fetchall()
        conn.close()
    
    # Kirim data ke Javascript dalam bentuk JSON
    return jsonify(data)

# =========================================================
# ROUTE EXPORT LAPORAN TRANSAKSI (LENGKAP)
# =========================================================
@app.route('/admin/export_laporan')
def export_laporan():
    if 'loggedin' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Query Kompleks: Menggabungkan tabel transaksi, siswa, dan guru
    # (Asumsi di tabel transaksi_izin ada kolom rfid_siswa yang diisi saat tap di kiosk)
    query = """
        SELECT t.waktu_dibuat, t.kode_token, t.jenis_izin, t.status, 
               s.nama_siswa, s.kelas, g.nama_lengkap as nama_guru
        FROM transaksi_izin t
        LEFT JOIN siswa s ON t.rfid_siswa = s.rfid_uid
        LEFT JOIN guru g ON t.id_guru = g.id_guru
        ORDER BY t.waktu_dibuat DESC
    """
    try:
        cursor.execute(query)
        data_laporan = cursor.fetchall()
    except Exception as e:
        conn.close()
        flash(f"Gagal menarik laporan: {e}", "danger")
        return redirect(url_for('dashboard_admin'))
        
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Tulis Judul Kolom di Excel
    writer.writerow(['WAKTU_IZIN', 'KODE_TOKEN', 'JENIS_IZIN', 'STATUS', 'NAMA_SISWA', 'KELAS_SISWA', 'GURU_PIKET'])
    
    # Tulis Data
    for row in data_laporan:
        # Jika siswa belum tap (nama_siswa = None), berikan nilai default
        nama = row['nama_siswa'] if row['nama_siswa'] else "Belum Scan"
        kelas = row['kelas'] if row['kelas'] else "-"
        
        writer.writerow([
            row['waktu_dibuat'], 
            row['kode_token'], 
            row['jenis_izin'], 
            row['status'], 
            nama, 
            kelas, 
            row['nama_guru']
        ])

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=Laporan_Transaksi_SmartExit.csv"
    return response

# =========================================================
# ROUTE LAYAR PANTAU (UNTUK SEKRETARIS & GURU MAPEL)
# =========================================================
@app.route('/pantau_kelas')
def pantau_kelas():
    # Keamanan Tinggi: Hanya yang sudah login yang bisa masuk
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    return render_template('pantau_kelas.html', nama=session['nama'])

@app.route('/api/pantau_live')
def api_pantau_live():
    # Keamanan Tinggi: Cegat jika tidak ada session
    if 'loggedin' not in session: 
        return jsonify([])
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Ambil data izin HARI INI saja, urutkan dari yang terbaru
    hari_ini = date.today().strftime('%Y-%m-%d')
    query = """
        SELECT t.waktu_dibuat, t.kode_token, t.jenis_izin, t.status, 
               s.nama_siswa, s.kelas
        FROM transaksi_izin t
        LEFT JOIN siswa s ON t.rfid_siswa = s.rfid_uid
        WHERE DATE(t.waktu_dibuat) = %s AND t.status IN ('WAITING', 'KELUAR', 'SUCCESS')
        ORDER BY t.waktu_dibuat DESC
    """
    cursor.execute(query, (hari_ini,))
    data = cursor.fetchall()
    conn.close()
    
    return jsonify(data)

import random
import string

# =========================================================
# API UNTUK APLIKASI ANDROID GURU (KIVYMD) - VERSI LOGIN
# =========================================================

# 1. API VERIFIKASI LOGIN DARI HP
@app.route('/api/mobile/login', methods=['POST'])
def api_mobile_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM guru WHERE username = %s", (username,))
    akun = cursor.fetchone()
    conn.close()

    if not akun:
        return jsonify({"status": "error", "type": "USER_NOT_FOUND", "pesan": "Username tidak terdaftar!"}), 404
    
    if akun['password'] != password:
        return jsonify({"status": "error", "type": "WRONG_PASSWORD", "pesan": "Password salah, silakan cek kembali!"}), 401

    return jsonify({
        "status": "sukses", 
        "id_guru": akun['id_guru'], 
        "nama": akun['nama_lengkap'],
        "role": akun['role']
    }), 200

# 2. API MEMBUAT TOKEN BARU (Format Disamakan dengan Web)
@app.route('/api/mobile/buat_token', methods=['POST'])
def api_mobile_buat_token_post():
    data = request.get_json()
    jenis = data.get('jenis')
    id_guru = data.get('id_guru') # Sekarang menerima ID dari HP

    conn = get_db_connection()
    cursor = conn.cursor()

    # Logika Token sama persis dengan web (Contoh: SAKIT-837492)
    angka_token = random.randint(100000, 999999)
    token = f'{jenis}-{angka_token}'

    try:
        cursor.execute(
            "INSERT INTO transaksi_izin (kode_token, id_guru, jenis_izin, status) VALUES (%s, %s, %s, %s)",
            (token, id_guru, jenis.upper(), 'WAITING')
        )
        conn.commit()
        sukses = True
    except:
        sukses = False
    finally:
        conn.close()

    return jsonify({"status": "sukses" if sukses else "gagal", "token": token, "jenis": jenis})

# 3. API AMBIL 5 RIWAYAT TERAKHIR (Dengan Tanggal)
@app.route('/api/mobile/riwayat_terbaru/<int:id_guru>', methods=['GET'])
def api_mobile_riwayat_guru(id_guru):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Ambil 5 data beserta waktu_dibuat
    cursor.execute("SELECT kode_token, jenis_izin, status, waktu_dibuat FROM transaksi_izin WHERE id_guru = %s ORDER BY waktu_dibuat DESC LIMIT 5", (id_guru,))
    data = cursor.fetchall()
    conn.close()

    # Ubah format waktu agar bisa dibaca oleh JSON dan HP
    for baris in data:
        if baris['waktu_dibuat']:
            baris['waktu_dibuat'] = baris['waktu_dibuat'].strftime('%d-%m-%Y %H:%M')

    return jsonify(data)

# 4. API AMBIL SEMUA RIWAYAT (Khusus Halaman "Lihat Semua")
@app.route('/api/mobile/riwayat_semua/<int:id_guru>', methods=['GET'])
def api_mobile_riwayat_semua(id_guru):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Ambil SEMUA data tanpa LIMIT
    cursor.execute("SELECT kode_token, jenis_izin, status, waktu_dibuat FROM transaksi_izin WHERE id_guru = %s ORDER BY waktu_dibuat DESC", (id_guru,))
    data = cursor.fetchall()
    conn.close()

    for baris in data:
        if baris['waktu_dibuat']:
            baris['waktu_dibuat'] = baris['waktu_dibuat'].strftime('%d-%m-%Y %H:%M')

    return jsonify(data)


# jalur logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('nama', None)
    return redirect(url_for('login'))

# --- 4. MENJALANKAN APLIKASI (PALING BAWAH) ---
if __name__ == '__main__':
    app.run(debug=True)