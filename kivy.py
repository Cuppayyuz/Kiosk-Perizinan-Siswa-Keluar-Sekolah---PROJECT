from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatIconButton, MDRaisedButton, MDFlatButton, MDIconButton, MDTextButton
from kivymd.uix.list import MDList, TwoLineListItem, ThreeLineListItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.relativelayout import MDRelativeLayout
from kivy.storage.jsonstore import JsonStore
from datetime import datetime, timedelta
from kivy.metrics import dp
# from kivy.core.window import Window
import requests

# =======================================================
# MASUKKAN LINK NGROK KAMU DI SINI
URL_BASE = "https://unconverged-paragraphistical-gemma.ngrok-free.dev"
# =======================================================

# Window.size = (360, 640)
store = JsonStore('user_session.json')

# ==================================================
# 1. LAYAR LOGIN
# ==================================================
class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "login"
        
        # 1. KOTAK PEMBUNGKUS UTAMA (Dengan Mantra adaptive_height)
        kotak_tengah = MDBoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(20),
            size_hint_x=0.85,          # Lebar 85% layar
            size_hint_y=None,          # Matikan tinggi otomatis bawaan Kivy
            adaptive_height=True,      # NYALAKAN TINGGI CERDAS KIVYMD!
            pos_hint={"center_x": 0.5, "center_y": 0.5} # Kunci di tengah
        )

        # 2. ISI KOTAK (Kita beri ukuran pasti agar tidak tumpang tindih)
        judul = MDLabel(text="SMART EXIT", font_style="H4", halign="center", theme_text_color="Primary", size_hint_y=None, height=dp(50), bold=True)
        subjudul = MDLabel(text="Login Portal", font_style="Subtitle1", halign="center", theme_text_color="Secondary", size_hint_y=None, height=dp(30))
        
        # Input Text juga kita beri tinggi yang pasti
        self.inp_username = MDTextField(hint_text="Username", icon_right="account", size_hint_y=None, height=dp(60))
        
        pwd_layout = MDRelativeLayout(size_hint_y=None, height=dp(60))
        self.inp_password = MDTextField(hint_text="Password", password=True)
        self.btn_eye = MDIconButton(icon="eye-off", pos_hint={"center_y": .5, "right": 1}, theme_text_color="Hint", on_release=self.toggle_password)
        pwd_layout.add_widget(self.inp_password)
        pwd_layout.add_widget(self.btn_eye)

        # Tombol juga kita beri tinggi
        btn_login = MDRaisedButton(text="MASUK", size_hint_x=1, size_hint_y=None, height=dp(50), on_release=self.proses_login)
        self.lbl_error = MDLabel(text="", theme_text_color="Error", halign="center", size_hint_y=None, height=dp(30))

        # 3. MASUKKAN SEMUANYA KE KOTAK TENGAH
        kotak_tengah.add_widget(judul)
        kotak_tengah.add_widget(subjudul)
        kotak_tengah.add_widget(self.inp_username)
        kotak_tengah.add_widget(pwd_layout) 
        kotak_tengah.add_widget(self.lbl_error)
        kotak_tengah.add_widget(btn_login)
        
        # 4. TAMPILKAN DI LAYAR HP
        self.add_widget(kotak_tengah)

    def toggle_password(self, instance):
        if self.inp_password.password:
            self.inp_password.password = False
            self.btn_eye.icon = "eye"
            self.btn_eye.theme_text_color = "Primary" 
        else:
            self.inp_password.password = True
            self.btn_eye.icon = "eye-off"
            self.btn_eye.theme_text_color = "Hint" 

    def proses_login(self, instance):
        usr = self.inp_username.text
        pwd = self.inp_password.text
        if not usr or not pwd:
            self.lbl_error.text = "Username dan Password wajib diisi!"
            return
            
        self.lbl_error.text = "Mencoba login..."
        
        try:
            url = f"{URL_BASE}/api/mobile/login"
            # [BARU] Tambah verify=False dan timeout=10
            respon = requests.post(url, headers={'ngrok-skip-browser-warning': 'true'}, json={"username": usr, "password": pwd}, timeout=10, verify=False).json()
            if respon.get('status') == 'sukses':
                if respon['role'] == 'admin':
                    self.lbl_error.text = "Akses Ditolak! Admin wajib via Web."
                    return 
                    
                app = MDApp.get_running_app()
                app.id_guru_aktif = respon['id_guru']
                app.nama_guru_aktif = respon['nama']
                app.role_aktif = respon['role'] 
                
                store.put('user_data', id_guru=respon['id_guru'], nama=respon['nama'], role=respon['role'], login_at=datetime.now().strftime('%Y-%m-%d'))
                
                self.manager.current = "dashboard"
                self.inp_username.text = ""
                self.inp_password.text = ""
                self.inp_password.password = True
                self.btn_eye.icon = "eye-off"
                self.btn_eye.theme_text_color = "Hint"
                self.lbl_error.text = ""
                self.manager.get_screen("dashboard").setup_ui_by_role()
            else:
                self.lbl_error.text = respon.get('pesan', 'Gagal login')
        except Exception as e:
            # [BARU] Menampilkan error asli dari sistem
            print(f"Error Login: {e}")
            self.lbl_error.text = f"Error: {str(e)[:30]}..."    
# ==================================================
# 2. LAYAR DASHBOARD GURU
# ==================================================
class DashboardScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "dashboard"
        self.dialog_info = None
        self.dialog_tanya = None
        
        layout = MDBoxLayout(orientation="vertical")

        self.toolbar = MDTopAppBar(title="Memuat...", elevation=4)
        self.toolbar.right_action_items = [
            ["refresh", lambda x: self.load_history()],
            ["logout", lambda x: self.konfirmasi_logout()] 
        ]
        layout.add_widget(self.toolbar)

        self.menu_layout = MDBoxLayout(orientation="horizontal", spacing=dp(10), padding=dp(15), size_hint_y=None, height=dp(80))

        btn_sakit = MDFillRoundFlatIconButton(text="SAKIT", icon="ambulance", md_bg_color=(0.86, 0.21, 0.27, 1), on_release=lambda x: self.konfirmasi_izin("SAKIT"))
        btn_izin = MDFillRoundFlatIconButton(text="IZIN", icon="message-text", md_bg_color=(1, 0.75, 0.02, 1), text_color=(0,0,0,1), icon_color=(0,0,0,1), on_release=lambda x: self.konfirmasi_izin("IZIN"))
        btn_dispen = MDFillRoundFlatIconButton(text="DISPEN", icon="account-group", md_bg_color=(0.05, 0.43, 0.99, 1), on_release=lambda x: self.konfirmasi_izin("DISPEN"))

        self.menu_layout.add_widget(btn_sakit)
        self.menu_layout.add_widget(btn_izin)
        self.menu_layout.add_widget(btn_dispen)
        layout.add_widget(self.menu_layout)

        # Header Riwayat Terakhir
        header_list = MDBoxLayout(orientation="horizontal", padding=dp(15), size_hint_y=None, height=dp(40))
        lbl_riwayat = MDLabel(text="5 Token Terakhir", theme_text_color="Secondary", font_style="Subtitle2")
        btn_semua = MDTextButton(text="Lihat Semua Riwayat ➔", theme_text_color="Custom", text_color=(0.1, 0.4, 0.9, 1), on_release=lambda x: self.ke_halaman_riwayat())
        header_list.add_widget(lbl_riwayat)
        header_list.add_widget(btn_semua)
        layout.add_widget(header_list)

        scroll = MDScrollView()
        self.list_view = MDList()
        scroll.add_widget(self.list_view)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def ke_halaman_riwayat(self):
        self.manager.current = "riwayat"
        self.manager.get_screen("riwayat").load_semua_riwayat()

    def setup_ui_by_role(self):
        app = MDApp.get_running_app()
        self.load_history()
        
        if app.role_aktif == 'pantau':
            self.toolbar.title = f"Pemantau: {app.nama_guru_aktif}"
            self.menu_layout.opacity = 0
            self.menu_layout.disabled = True
        else:
            self.toolbar.title = f"Guru: {app.nama_guru_aktif}"
            self.menu_layout.opacity = 1
            self.menu_layout.disabled = False

    def konfirmasi_logout(self):
        self.dialog_tanya = MDDialog(
            title="Keluar Aplikasi?", text="Apakah Anda yakin ingin logout dari akun ini?",
            buttons=[
                MDFlatButton(text="BATAL", on_release=lambda x: self.dialog_tanya.dismiss()),
                MDFlatButton(text="YA, KELUAR", text_color=(1,0,0,1), on_release=lambda x: self.eksekusi_logout())
            ]
        )
        self.dialog_tanya.open()

    def eksekusi_logout(self):
        self.dialog_tanya.dismiss()
        store.delete('user_data') # HAPUS DATA INGAT SAYA!
        app = MDApp.get_running_app()
        app.id_guru_aktif = None
        app.nama_guru_aktif = ""
        app.role_aktif = ""
        self.manager.current = "login"

    def konfirmasi_izin(self, jenis):
        self.dialog_tanya = MDDialog(
            title=f"Izin {jenis}", text=f"Terbitkan token {jenis} sekarang?",
            buttons=[
                MDFlatButton(text="BATAL", on_release=lambda x: self.dialog_tanya.dismiss()),
                MDFlatButton(text="TERBITKAN", text_color=self.theme_cls.primary_color, on_release=lambda x: self.eksekusi_buat_token(jenis))
            ]
        )
        self.dialog_tanya.open()

    def eksekusi_buat_token(self, jenis):
        self.dialog_tanya.dismiss()
        app = MDApp.get_running_app()
        try:
            headers = {'ngrok-skip-browser-warning': 'true'}
            url = f"{URL_BASE}/api/mobile/buat_token"
            # [BARU] Tambah verify=False dan timeout=10
            respon = requests.post(url, headers=headers, json={"jenis": jenis, "id_guru": app.id_guru_aktif}, timeout=10, verify=False).json()
            if respon['status'] == 'sukses':
                self.tampilkan_info("Berhasil!", f"Kode Token {jenis}:\n\n{respon['token']}\n\nBerikan kode ini ke siswa.")
                self.load_history() 
            else:
                self.tampilkan_info("Gagal", "Database menolak penyimpanan data.")
        except Exception as e:
            self.tampilkan_info("Error Koneksi", f"Detail: {str(e)[:50]}")
    def tampilkan_info(self, judul, teks):
        if not self.dialog_info:
            self.dialog_info = MDDialog(title=judul, text=teks, buttons=[MDFlatButton(text="TUTUP", on_release=lambda x: self.dialog_info.dismiss())])
        else:
            self.dialog_info.title = judul
            self.dialog_info.text = teks
        self.dialog_info.open()

    def load_history(self):
        self.list_view.clear_widgets()
        app = MDApp.get_running_app()
        
        try:
            headers = {'ngrok-skip-browser-warning': 'true'}
            url = f"{URL_BASE}/api/mobile/riwayat_terbaru/{app.id_guru_aktif}"
            # [BARU] Tambah verify=False dan timeout=10
            respon = requests.get(url, headers=headers, timeout=10, verify=False).json()

            if len(respon) == 0:
                self.list_view.add_widget(TwoLineListItem(text="Belum ada token", secondary_text="Belum ada riwayat tercatat."))
                return

            for baris in respon:
                tkn = baris['kode_token']
                jns = baris['jenis_izin']
                sts = baris['status']
                wkt = baris['waktu_dibuat']
                ikon = "✅" if sts == "KELUAR" else "⏳"
                
                # Menggunakan 3 Baris agar Tanggal Terlihat
                item = ThreeLineListItem(
                    text=f"{tkn} ({jns})", 
                    secondary_text=f"Status: {ikon} {sts}",
                    tertiary_text=f"Dibuat: {wkt}"
                )
                self.list_view.add_widget(item)

        except Exception as e:
            self.list_view.add_widget(TwoLineListItem(text="GAGAL KONEK", secondary_text=str(e)[:40]))


# ==================================================
# 3. LAYAR SEMUA RIWAYAT
# ==================================================
class RiwayatScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "riwayat"
        
        layout = MDBoxLayout(orientation="vertical")

        self.toolbar = MDTopAppBar(title="Semua Riwayat Izin", elevation=4)
        self.toolbar.left_action_items = [["arrow-left", lambda x: self.kembali()]]
        self.toolbar.right_action_items = [["refresh", lambda x: self.load_semua_riwayat()]]
        layout.add_widget(self.toolbar)

        scroll = MDScrollView()
        self.list_view = MDList()
        scroll.add_widget(self.list_view)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def kembali(self):
        self.manager.current = "dashboard"

    def load_semua_riwayat(self):
        self.list_view.clear_widgets()
        app = MDApp.get_running_app()
        try:
            headers = {'ngrok-skip-browser-warning': 'true'}
            url = f"{URL_BASE}/api/mobile/riwayat_semua/{app.id_guru_aktif}"
            # [BARU] Tambah verify=False dan timeout=10
            respon = requests.get(url, headers=headers, timeout=10, verify=False).json()
            if len(respon) == 0:
                self.list_view.add_widget(TwoLineListItem(text="Kosong", secondary_text="Anda belum pernah membuat token."))
                return

            for baris in respon:
                tkn = baris['kode_token']
                jns = baris['jenis_izin']
                sts = baris['status']
                wkt = baris['waktu_dibuat']
                
                ikon = "✅" if sts == "KELUAR" else "⏳"
                
                item = ThreeLineListItem(
                    text=f"{tkn} ({jns})", 
                    secondary_text=f"Status: {ikon} {sts}",
                    tertiary_text=f"Dibuat: {wkt}"
                )
                self.list_view.add_widget(item)
        except Exception as e:
            self.list_view.add_widget(TwoLineListItem(text="GAGAL KONEK", secondary_text=str(e)[:40]))

# ==================================================
# APP MAIN
# ==================================================
class SmartExitMobile(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.id_guru_aktif = None
        self.nama_guru_aktif = ""
        self.role_aktif = ""

        self.sm = MDScreenManager()
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(DashboardScreen(name="dashboard"))
        self.sm.add_widget(RiwayatScreen(name="riwayat")) # SUDAH DIDAFTARKAN!
        return self.sm

    def on_start(self):
        # SISTEM INGAT SAYA (PERSISTEN)
        if store.exists('user_data'):
            data = store.get('user_data')
            tgl_login = datetime.strptime(data['login_at'], '%Y-%m-%d')
            
            if datetime.now() > tgl_login + timedelta(days=7):
                store.delete('user_data') 
            else:
                self.id_guru_aktif = data['id_guru']
                self.nama_guru_aktif = data['nama']
                self.role_aktif = data['role']
                
                self.sm.current = "dashboard"
                self.sm.get_screen("dashboard").setup_ui_by_role()

if __name__ == "__main__":
    SmartExitMobile().run()