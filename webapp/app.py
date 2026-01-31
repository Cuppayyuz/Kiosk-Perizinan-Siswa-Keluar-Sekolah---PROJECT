import random 
from flask import Flask, render_template, request, redirect, url_for, session
from config import get_db_connection

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