import random 
from flask import Flask, render_template, request, redirect, url_for, session , jsonify
from config import get_db_connection
import sys
from datetime import date

sys.path.append('C:/robotik/Desktop')

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
                else:
                    return redirect(url_for('dashboard_guru'))
            else:
                msg = 'Username atau Password Salah!'
    
    return render_template('login.html', msg=msg)

# jalur dashboard guru
@app.route('/dashboard_guru')
def dashboard_guru():
    if 'loggedin' not in session:
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
    if 'loggedin' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    
    nama = request.form['nama_lengkap']
    username = request.form['username']
    password = request.form['password'] # Ingat, ini masih plain-text untuk belajar
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO guru (nama_lengkap, username, password, role) VALUES (%s, %s, %s, 'guru')", (nama, username, password))
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

# token 
    angka_token = random.randint(100000, 999999)
    token_baru = f'{jenis}-{angka_token}'

# simpan ke database 
    id_guru = session['id']

    conn = get_db_connection()
    cursor = conn.cursor()

# query untuk memasukkan token baru ke database
    query = "INSERT INTO transaksi_izin (kode_token, id_guru, jenis_izin, status) VALUES (%s, %s, %s, 'WAITING')"
    cursor.execute(query, (token_baru, id_guru, jenis))

    conn.commit()
    conn.closer()

#  kebali ke dashboard guru
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