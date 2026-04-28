import random 
from flask import Flask, render_template, request, redirect, send_from_directory, url_for, session , jsonify,flash, Response 
from config import get_db_connection
import sys
from datetime import date
import io
import csv
import random
import string
import re
from apscheduler.schedulers.background import BackgroundScheduler
import os
sys.path.append('C:/robotik')

from Desktop.modules import printer

ARCHIVE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__name__)), 'archives')
os.makedirs(ARCHIVE_FOLDER, exist_ok=True)

# 2. Baru lakukan import module-nya setelah path ditambahkan

# inisialisasi aplikasi Flask
app = Flask(__name__)
app.secret_key = 'kunci_rahasia_sekolah'


# [BARU] Fungsi Pintar Penyeragam Nama Kelas
def normalisasi_kelas(teks):
    if not teks: return ""
    
    # 1. Jadikan huruf besar semua dan hapus spasi berlebih di awal/akhir
    t = str(teks).upper().strip()
    
    # 2. Ganti angka jadi romawi (10 -> X, 11 -> XI, 12 -> XII)
    # \b digunakan agar angka 111 tidak ikut terganti
    t = re.sub(r'\b10\b', 'X', t)
    t = re.sub(r'\b11\b', 'XI', t)
    t = re.sub(r'\b12\b', 'XII', t)
    
    # 3. Hapus spasi ganda di tengah (misal "XI  RPL   1" jadi "XI RPL 1")
    t = " ".join(t.split())
    
    return t

# route untuk halaman login
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
                
                # [BARU] Ambil kelas pantau jika ada
                kelas_target = akun.get('kelas_pantau')
                session['kelas_pantau'] = kelas_target 
                
                if akun['role'] == 'admin':
                    return redirect(url_for('dashboard_admin'))
                elif akun['role'] == 'guru':
                    return redirect(url_for('dashboard_guru'))
                elif akun['role'] == 'pantau':
                    # [PENCEGAHAN ERROR] Cek apakah kelasnya ada isinya
                    if kelas_target:
                        return redirect(url_for('pantau_per_kelas', kelas=kelas_target))
                    else:
                        # Jika di database kosong, jangan di-redirect, tapi beri pesan error
                        session.pop('loggedin', None) # Batalkan login
                        msg = 'Akun Pantau ini belum diatur untuk kelas manapun! Lapor ke Admin.'
            else:
                msg = 'Username atau Password Salah!'
    
    return render_template('login.html', msg=msg)

# jalur dashboard guru
# jalur dashboard guru
@app.route('/dashboard_guru')
def dashboard_guru():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    # KUNCI PINTU KHUSUS GURU
    if session.get('role') != 'guru':
        if session.get('role') == 'admin':
            return redirect(url_for('dashboard_admin'))
        elif session.get('role') == 'pantau':
            # [PENCEGAHAN ERROR] Bawa variabel kelas saat menendang balik
            kelas_target = session.get('kelas_pantau')
            if kelas_target:
                return redirect(url_for('pantau_per_kelas', kelas=kelas_target))
            else:
                return redirect(url_for('login'))
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
    kelas = normalisasi_kelas(request.form['kelas'])

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Masukkan ke database
    query = "INSERT INTO siswa (rfid_uid, nama_siswa, kelas) VALUES (%s, %s, %s)"
    cursor.execute(query, (rfid, nama, kelas))
    
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard_admin'))
@app.route('/admin/edit_siswa', methods=['POST'])
def edit_siswa():
    if 'loggedin' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    id_siswa = request.form['id_siswa']
    rfid = request.form['rfid_uid']
    nama = request.form['nama']
    # Gunakan fungsi normalisasi di sini
    kelas = normalisasi_kelas(request.form['kelas'])

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "UPDATE siswa SET rfid_uid=%s, nama_siswa=%s, kelas=%s WHERE id_siswa=%s"
        cursor.execute(query, (rfid, nama, kelas, id_siswa))
        conn.commit()
        flash(f"Data {nama} berhasil diperbarui.", "success")
    except Exception as e:
        flash(f"Gagal memperbarui data: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for('dashboard_admin'))

@app.route('/admin/promosi_kelas', methods=['POST'])
def promosi_kelas():
    if 'loggedin' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    kelas_lama = request.form['kelas_lama']
    # Jangan lupa gunakan normalisasi agar inputan seperti "12 rpl 1" tetap rapi
    kelas_baru = normalisasi_kelas(request.form['kelas_baru']) 

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Pindahkan SEMUA siswa di kelas lama ke kelas baru
        query = "UPDATE siswa SET kelas = %s WHERE kelas = %s"
        cursor.execute(query, (kelas_baru, kelas_lama))
        conn.commit()
        
        # Mengecek berapa jumlah data siswa yang berhasil dipindah
        jumlah_siswa = cursor.rowcount
        
        if jumlah_siswa > 0:
            flash(f"Promosi sukses! {jumlah_siswa} siswa dari kelas {kelas_lama} telah dipindahkan ke {kelas_baru}.", "success")
        else:
            flash(f"Tidak ada siswa yang ditemukan di kelas {kelas_lama}.", "warning")
            
    except Exception as e:
        flash(f"Gagal mempromosikan kelas: {e}", "danger")
    finally:
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
                if row_idx == 0 and not rfid_raw.isdigit():
                    continue 

                nama = str(row[1]).strip() if len(row) > 1 else ""
                
                # =======================================================
                # [DI SINI PERUBAHANNYA] 
                # Menggunakan fungsi normalisasi_kelas agar format kelas selalu rapi
                # =======================================================
                kelas = normalisasi_kelas(row[2]) if len(row) > 2 else ""

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
    
    # 1. Tangkap request tanggal dari kalender HTML
    tanggal_filter = request.args.get('tanggal')
    
    # 2. Jika admin tidak memilih tanggal (atau baru buka web), gunakan tanggal hari ini
    if not tanggal_filter:
        tanggal_filter = date.today().strftime('%Y-%m-%d')
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 3. Query disesuaikan untuk mencari HANYA pada tanggal yang difilter
    query = """
        SELECT t.kode_token, t.jenis_izin, t.status, t.waktu_dibuat, g.nama_lengkap as nama_guru 
        FROM transaksi_izin t
        LEFT JOIN guru g ON t.id_guru = g.id_guru
        WHERE DATE(t.waktu_dibuat) = %s
        ORDER BY t.id DESC LIMIT 50
    """
    cursor.execute(query, (tanggal_filter,))
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
    role = request.form['role']
    # [BARU] Tangkap input kelas pantau (jika tidak ada, set jadi None/NULL)
    # Ubah baris penangkap kelas pantau menjadi:
    kelas_pantau_raw = request.form.get('kelas_pantau')
    kelas_pantau = normalisasi_kelas(kelas_pantau_raw) if role == 'pantau' else None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # [BARU] Masukkan kelas_pantau ke database
    query = "INSERT INTO guru (nama_lengkap, username, password, role, kelas_pantau) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, (nama, username, password, role, kelas_pantau))
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

@app.route('/guru/konfirmasi_kembali/<token>')
def konfirmasi_kembali(token):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Update status menjadi KEMBALI dan catat waktunya
        query = "UPDATE transaksi_izin SET status = 'KEMBALI', waktu_kembali = NOW() WHERE kode_token = %s"
        cursor.execute(query, (token,))
        conn.commit()
        flash(f"Siswa dengan token {token} telah ditandai kembali secara manual.", "success")
    except Exception as e:
        flash(f"Gagal memproses data: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for('dashboard_guru'))

@app.route('/buat_token/<jenis>')
def buat_token(jenis):  
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    angka_token = random.randint(100000, 999999)
    token_baru = f'{jenis}-{angka_token}'
    id_guru = session['id']
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        # [REVISI]: Ganti 'WAITING' menjadi 'MENUNGGU'
        query = "INSERT INTO transaksi_izin (kode_token, id_guru, jenis_izin, status) VALUES (%s, %s, %s, 'MENUNGGU')"
        cursor.execute(query, (token_baru, id_guru, jenis))
        conn.commit()
    except Exception as e:
        flash(f"Terjadi kesalahan pada database: {e}")
        conn.close()
        return redirect(url_for('dashboard_guru'))
        
    conn.close()

    try:
        printer.cetak_barcode(token_baru, jenis)
        flash(f"Izin {jenis} berhasil diterbitkan! Struk barcode {token_baru} sedang dicetak.", "success")
    except Exception as e:
        print(f"[WARNING PRINTER]: {e}")
        flash(f"Izin {jenis} TERSIMPAN, tapi STRUK GAGAL DICETAK! Periksa sambungan printer thermal.", "warning")

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
# SISTEM ARSIP & AUTO-EXPORT (ROBOT)
# =========================================================

def auto_export_harian():
    """Fungsi ini akan dijalankan otomatis oleh mesin jam 18.00"""
    print("[SISTEM] Memulai Auto-Export Laporan Harian...")
    
    hari_ini = date.today().strftime('%Y-%m-%d')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Cek apakah hari ini ada izin?
    query = """
        SELECT t.waktu_dibuat, t.kode_token, t.jenis_izin, t.status, 
               s.nama_siswa, s.kelas, g.nama_lengkap as nama_guru
        FROM transaksi_izin t
        LEFT JOIN siswa s ON t.rfid_siswa = s.rfid_uid
        LEFT JOIN guru g ON t.id_guru = g.id_guru
        WHERE DATE(t.waktu_dibuat) = %s
        ORDER BY t.waktu_dibuat ASC
    """
    cursor.execute(query, (hari_ini,))
    data_hari_ini = cursor.fetchall()
    conn.close()

    # Jika tidak ada izin sama sekali, batalkan ekspor
    if len(data_hari_ini) == 0:
        print(f"[SISTEM] Auto-Export dibatalkan: Tidak ada izin pada {hari_ini}.")
        return

    # Jika ada, buat file CSV di folder archives/
    nama_file = f"Laporan_{hari_ini}.csv"
    path_file = os.path.join(ARCHIVE_FOLDER, nama_file)
    
    with open(path_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['WAKTU_IZIN', 'KODE_TOKEN', 'JENIS_IZIN', 'STATUS', 'NAMA_SISWA', 'KELAS_SISWA', 'GURU_PIKET'])
        for row in data_hari_ini:
            nama = row['nama_siswa'] if row['nama_siswa'] else "Belum Scan"
            kelas = row['kelas'] if row['kelas'] else "-"
            writer.writerow([
                row['waktu_dibuat'], row['kode_token'], row['jenis_izin'], 
                row['status'], nama, kelas, row['nama_guru']
            ])
            
    print(f"[SISTEM] Auto-Export Berhasil! File disimpan: {nama_file}")

# API untuk menampilkan daftar CSV di Modal HTML
@app.route('/api/admin/list_arsip')
def api_list_arsip():
    if 'loggedin' not in session or session.get('role') != 'admin': return jsonify([])
    
    file_arsip = []
    # Baca semua file di folder archives yang berakhiran .csv
    for f in os.listdir(ARCHIVE_FOLDER):
        if f.endswith('.csv'):
            file_arsip.append(f)
            
    # Urutkan dari yang terbaru (Z-A)
    file_arsip.sort(reverse=True)
    return jsonify(file_arsip)

# Rute untuk mendownload file arsip
@app.route('/admin/download_arsip/<nama_file>')
def download_arsip(nama_file):
    if 'loggedin' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return send_from_directory(ARCHIVE_FOLDER, nama_file, as_attachment=True)
# =========================================================
# ROUTE LAYAR PANTAU (UNTUK SEKRETARIS & GURU MAPEL)
# =========================================================
# --- ROUTE UNTUK HALAMAN PANTAU PER KELAS ---
@app.route('/pantau/<kelas>')
def pantau_per_kelas(kelas):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    # [BARU] SECURITY CHECK: Cegah perangkat kelas mengintip kelas lain!
    user_role = session.get('role')
    kelas_milik_user = session.get('kelas_pantau')
    
    # Jika dia role pantau, TAPI kelas di URL tidak sama dengan kelas aslinya -> BLOKIR!
    if user_role == 'pantau' and kelas_milik_user != kelas:
        return "<h1>AKSES DITOLAK!</h1><p>Anda hanya memiliki otorisasi untuk memantau kelas Anda sendiri.</p>", 403

    return render_template('pantau_per_kelas.html', nama=session['nama'], kelas_target=kelas)

# --- API LIVE UNTUK DATA PER KELAS ---
# Cari fungsi ini di app.py dan ganti bagian query-nya
@app.route('/api/pantau_live/<kelas>')
def api_pantau_live_filtered(kelas):
    if 'loggedin' not in session: 
        return jsonify([])
        
    # 1. Tangkap parameter tanggal dari URL (jika tidak ada, pakai hari ini)
    tanggal_filter = request.args.get('tanggal')
    if not tanggal_filter:
        tanggal_filter = date.today().strftime('%Y-%m-%d')
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 2. Query filter tanggal menggunakan DATE(t.waktu_dibuat)
    query = """
        SELECT t.waktu_dibuat, t.waktu_keluar, t.waktu_kembali, t.jenis_izin, t.status, 
               s.nama_siswa, s.kelas
        FROM transaksi_izin t
        INNER JOIN siswa s ON t.rfid_siswa = s.rfid_uid
        WHERE DATE(t.waktu_dibuat) = %s 
          AND s.kelas = %s 
          AND t.status IN ('SEDANG_KELUAR', 'KEMBALI', 'SELESAI')
        ORDER BY t.waktu_keluar DESC
    """
    cursor.execute(query, (tanggal_filter, kelas))
    data = cursor.fetchall()
    conn.close()
    
    # 3. Format Jam (Ubah None/NULL menjadi tanda strip '-')
    for row in data:
        row['jam_keluar'] = row['waktu_keluar'].strftime('%H:%M') if row['waktu_keluar'] else '-'
        row['jam_kembali'] = row['waktu_kembali'].strftime('%H:%M') if row['waktu_kembali'] else '-'
        
    return jsonify(data)
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
    # 1. Nyalakan Robot Penjadwal
    scheduler = BackgroundScheduler()
    # Atur agar berjalan setiap hari jam 18:00 (Pastikan jam laptopmu benar)
    scheduler.add_job(func=auto_export_harian, trigger="cron", hour=20, minute=30)
    scheduler.start()
    
    # 2. Nyalakan Server Web (use_reloader=False agar robot tidak jalan dobel)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)