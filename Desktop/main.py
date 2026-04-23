import customtkinter as ctk
from PIL import Image
import os
import datetime

# --- IMPORT SEMUA MODUL HARDWARE & DATABASE ---
from modules.database_client import DatabaseClient
from modules.coba_suara import bicara
from modules.camera import CameraHandler
from modules.arduino import ArduinoHandler
from modules.printer import cetak_struk_final

# Setup Tampilan (MODE CERAH)
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class SmartExitKiosk(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. KONFIGURASI LAYAR UTAMA
        self.title("SMART EXIT KIOSK - SMKN 1")
        self.geometry("1024x600") 
        # self.attributes('-fullscreen', True) # HAPUS TANDA '#' SAAT HARI-H DEPLOYMENT
        
        # Variabel Status Sistem
        self.tahapan = "IDLE" 
        self.token_sementara = ""
        self.jenis_izin_sementara = ""
        self.is_locked = False 
        
        # --- INISIALISASI HARDWARE ---
        self.db = DatabaseClient()
        self.kamera = CameraHandler(camera_index=0)
        self.arduino = ArduinoHandler(port_name="COM3") # PASTIKAN COM3 SESUAI DENGAN ARDUINO-MU NANTI
        self.arduino.connect() # Sambungkan ke Arduino sejak awal
        
        # --- PERSIAPAN SLIDESHOW IKLAN ---
        self.gambar_iklan = []
        self.indeks_iklan = 0
        self.timer_slideshow = None
        self.muat_gambar_assets()

        # --- BUAT 3 HALAMAN (FRAMES) ---
        self.buat_halaman_idle()
        self.buat_halaman_proses()
        self.buat_halaman_sukses()

        # Input Box Ghaib
       # --- INPUT BOX TEST (SEMENTARA) ---
        # Diperbesar dan diberi teks panduan agar mudah diketik manual
        self.entry_global = ctk.CTkEntry(
            self, 
            width=400, 
            height=40,
            font=("Arial", 18), 
            justify="center",
            placeholder_text="[MODE TEST] Ketik Token / RFID lalu tekan Enter"
        )
        # Kita letakkan di tengah paling bawah layar agar terlihat
        self.entry_global.place(relx=0.5, rely=0.95, anchor="center") 
        self.entry_global.bind("<Return>", self.proses_scan)
        
        # Biarkan fokus tetap otomatis ke kotak ini saat layar diklik
        self.bind("<Button-1>", lambda e: self.entry_global.focus())
        # Mulai Aplikasi
        self.reset_ke_awal()
        bicara("Sistem Perizinan Digital Siap Digunakan.")

    def muat_gambar_assets(self):
        folder_assets = "assets"
        if not os.path.exists(folder_assets):
            os.makedirs(folder_assets)

        for file in os.listdir(folder_assets):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                path_gambar = os.path.join(folder_assets, file)
                img = ctk.CTkImage(light_image=Image.open(path_gambar), size=(800, 300))
                self.gambar_iklan.append(img)

    def buat_halaman_idle(self):
        self.frame_idle = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=0)
        lbl_welcome = ctk.CTkLabel(self.frame_idle, text="SELAMAT DATANG DI SMART-EXIT", font=("Arial", 36, "bold"), text_color="#1f538d")
        lbl_welcome.pack(pady=(40, 20))
        
        self.lbl_gambar = ctk.CTkLabel(self.frame_idle, text="") 
        self.lbl_gambar.pack(pady=10)

        self.lbl_teks_iklan = ctk.CTkLabel(self.frame_idle, text="Siapkan Kartu Pelajar Anda", font=("Georgia", 24, "italic"), text_color="#555555")
        if len(self.gambar_iklan) == 0:
            self.lbl_teks_iklan.pack(pady=30)
        
        lbl_instruksi_idle = ctk.CTkLabel(self.frame_idle, text="👇 Arahkan Barcode Izin Anda ke Scanner 👇", font=("Arial", 20, "bold"), text_color="#28a745")
        lbl_instruksi_idle.pack(pady=(30, 0))

    def putar_slideshow(self):
        if len(self.gambar_iklan) > 0:
            self.lbl_gambar.configure(image=self.gambar_iklan[self.indeks_iklan])
            self.indeks_iklan = (self.indeks_iklan + 1) % len(self.gambar_iklan)
            self.timer_slideshow = self.after(3000, self.putar_slideshow)

    def hentikan_slideshow(self):
        if self.timer_slideshow is not None:
            self.after_cancel(self.timer_slideshow)
            self.timer_slideshow = None

    def buat_halaman_proses(self):
        self.frame_proses = ctk.CTkFrame(self, fg_color="#f0f4f8", corner_radius=0)
        self.frame_proses.grid_columnconfigure(0, weight=1)
        self.frame_proses.grid_columnconfigure(1, weight=1)
        self.frame_proses.grid_rowconfigure(0, weight=1)

        # KOTAK KAMERA
        self.kamera_box = ctk.CTkFrame(self.frame_proses, fg_color="#000000", width=400, height=300, corner_radius=15)
        self.kamera_box.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")
        self.lbl_kamera_live = ctk.CTkLabel(self.kamera_box, text="MEMBUKA KAMERA...", font=("Arial", 18), text_color="white")
        self.lbl_kamera_live.place(relx=0.5, rely=0.5, anchor="center")

        info_box = ctk.CTkFrame(self.frame_proses, fg_color="#ffffff", corner_radius=15)
        info_box.grid(row=0, column=1, padx=40, pady=40, sticky="nsew")
        
        self.lbl_info_jenis = ctk.CTkLabel(info_box, text="IZIN: -", font=("Arial", 28, "bold"), text_color="#1f538d")
        self.lbl_info_jenis.pack(pady=(40, 20))
        
        lbl_animasi_tap = ctk.CTkLabel(info_box, text="💳", font=("Arial", 60))
        lbl_animasi_tap.pack(pady=10)
        
        self.lbl_instruksi_rfid = ctk.CTkLabel(info_box, text="SILAKAN TEMPEL\nKARTU PELAJAR ANDA", font=("Arial", 24, "bold"), text_color="#d9534f")
        self.lbl_instruksi_rfid.pack(pady=20)

    # --- FUNGSI UPDATE KAMERA LIVE ---
    def update_kamera(self):
        if self.tahapan == "TAP_KARTU":
            frame_rgb, wajah_terdeteksi = self.kamera.get_frame()
            if frame_rgb is not None:
                # Ubah gambar OpenCV ke format Tkinter
                img_pil = Image.fromarray(frame_rgb)
                img_ctk = ctk.CTkImage(light_image=img_pil, size=(400, 300))
                self.lbl_kamera_live.configure(image=img_ctk, text="") # Hilangkan teks, tampilkan gambar
            
            # Ulangi fungsi ini setiap 30 milidetik (sekitar 30 FPS)
            self.after(30, self.update_kamera)

    def buat_halaman_sukses(self):
        self.frame_sukses = ctk.CTkFrame(self, fg_color="#d4edda", corner_radius=0)
        self.lbl_sukses_icon = ctk.CTkLabel(self.frame_sukses, text="✅", font=("Arial", 80))
        self.lbl_sukses_icon.pack(pady=(100, 20))
        
        self.lbl_sukses_teks = ctk.CTkLabel(self.frame_sukses, text="VALIDASI BERHASIL!", font=("Arial", 36, "bold"), text_color="#155724")
        self.lbl_sukses_teks.pack(pady=10)
        
        self.lbl_sukses_nama = ctk.CTkLabel(self.frame_sukses, text="Hati-hati di jalan, Nama Siswa", font=("Arial", 24), text_color="#155724")
        self.lbl_sukses_nama.pack(pady=10)
        
        lbl_tunggu = ctk.CTkLabel(self.frame_sukses, text="Gerbang Dibuka! Silakan ambil struk Anda.", font=("Arial", 16, "italic"), text_color="#6c757d")
        lbl_tunggu.pack(pady=40)

    def sembunyikan_semua_halaman(self):
        self.frame_idle.pack_forget()
        self.frame_proses.pack_forget()
        self.frame_sukses.pack_forget()

    def reset_ke_awal(self):
        self.sembunyikan_semua_halaman()
        self.frame_idle.pack(fill="both", expand=True)
        self.tahapan = "IDLE"
        self.token_sementara = ""
        self.jenis_izin_sementara = ""
        self.is_locked = False 
        
        # Matikan kamera jika sedang menyala
        self.kamera.close_camera()
        self.lbl_kamera_live.configure(image="", text="MEMBUKA KAMERA...")
        
        self.putar_slideshow() 
        self.entry_global.focus()

    def proses_scan(self, event):
        if self.is_locked:
            self.entry_global.delete(0, "end")
            return

        input_data = self.entry_global.get().strip().upper()
        self.entry_global.delete(0, "end") 

        # --- TAHAP 1: SCAN BARCODE ---
        if self.tahapan == "IDLE":
            data_token = self.db.cek_token(input_data)

            if data_token:
                self.hentikan_slideshow()
                self.token_sementara = data_token['kode_token']
                self.jenis_izin_sementara = data_token['jenis_izin']
                
                self.lbl_info_jenis.configure(text=f"IZIN: {self.jenis_izin_sementara.upper()}")
                
                self.sembunyikan_semua_halaman()
                self.frame_proses.pack(fill="both", expand=True)
                
                self.tahapan = "TAP_KARTU"
                
                # NYALAKAN KAMERA
                if self.kamera.open_camera():
                    self.update_kamera() # Mulai loop live video
                
                bicara("Token valid. Silakan tempel kartu pelajar Anda menghadap kamera.")
            else:
                bicara("Token tidak valid.")

        # --- TAHAP 2: TAP RFID ---
        elif self.tahapan == "TAP_KARTU":
            siswa = self.db.cek_rfid_siswa(input_data)

            if siswa:
                nama = siswa['nama_siswa']
                kelas = siswa['kelas']
                sukses = self.db.update_izin_sukses(self.token_sementara, input_data)
                
                if sukses:
                    self.is_locked = True 
                    
                    # 1. JEPRET FOTO KAMERA
                    self.kamera.take_snapshot(f"izin_{nama.replace(' ', '_')}")
                    
                    # 2. CETAK STRUK PRINTER
                    waktu_sekarang = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    cetak_struk_final(nama, kelas, self.jenis_izin_sementara, waktu_sekarang)
                    
                    # 3. KIRIM SINYAL ARDUINO BUKA GERBANG
                    self.arduino.kirim_sinyal_buka()
                    
                    self.lbl_sukses_nama.configure(text=f"Hati-hati di jalan,\n{nama}")
                    self.sembunyikan_semua_halaman()
                    self.frame_sukses.pack(fill="both", expand=True)
                    
                    bicara(f"Izin berhasil. Gerbang dibuka. Hati-hati di jalan, {nama}.")
                    
                    # Tahan 5 detik lalu reset
                    self.after(5000, self.reset_ke_awal) 
                else:
                    bicara("Gagal menyimpan ke database.")
            else:
                self.lbl_instruksi_rfid.configure(text="KARTU TIDAK DIKENAL!\nCOBA LAGI", text_color="red")
                bicara("Kartu tidak terdaftar.")

if __name__ == "__main__":
    app = SmartExitKiosk()
    app.mainloop()