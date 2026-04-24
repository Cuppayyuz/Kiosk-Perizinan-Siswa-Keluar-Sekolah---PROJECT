import customtkinter as ctk
from PIL import Image
import os
import datetime
import time 

# --- IMPORT SEMUA MODUL HARDWARE & DATABASE ---
from modules.database_client import DatabaseClient
from modules.camera import CameraHandler
from modules.arduino import ArduinoHandler
from modules.printer import cetak_struk_final

# Setup Tampilan
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class SmartExitKiosk(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SMART EXIT KIOSK - SMKN 1")
        self.geometry("1024x600") 
        
        self.tahapan = "IDLE" 
        self.token_sementara = ""
        self.jenis_izin_sementara = ""
        self.nama_siswa_sementara = ""
        self.kelas_siswa_sementara = ""
        self.waktu_deteksi_wajah = None 
        self.is_locked = False 
        
        self.db = DatabaseClient()
        self.kamera = CameraHandler(camera_index=0)
        self.arduino = ArduinoHandler(port_name="COM3")
        self.arduino.connect()
        
        self.gambar_iklan = []
        self.indeks_iklan = 0
        self.timer_slideshow = None
        self.muat_gambar_assets()

        self.buat_halaman_idle()
        self.buat_halaman_rfid()
        self.buat_halaman_kamera()
        self.buat_halaman_sukses()

        self.entry_global = ctk.CTkEntry(
            self, width=400, height=40, font=("Arial", 18), justify="center",
            placeholder_text="[MODE TEST] Ketik Token / RFID lalu tekan Enter"
        )
        self.entry_global.place(relx=0.5, rely=0.95, anchor="center") 
        self.entry_global.bind("<Return>", self.proses_scan)
        self.bind("<Button-1>", lambda e: self.entry_global.focus())
        
        self.reset_ke_awal()

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
        ctk.CTkLabel(self.frame_idle, text="SELAMAT DATANG DI SMART-EXIT", font=("Arial", 36, "bold"), text_color="#1f538d").pack(pady=(40, 20))
        self.lbl_gambar = ctk.CTkLabel(self.frame_idle, text="") 
        self.lbl_gambar.pack(pady=10)
        self.lbl_teks_iklan = ctk.CTkLabel(self.frame_idle, text="Siapkan Kartu Pelajar Anda", font=("Georgia", 24, "italic"), text_color="#555555")
        if len(self.gambar_iklan) == 0:
            self.lbl_teks_iklan.pack(pady=30)
        ctk.CTkLabel(self.frame_idle, text="👇 Arahkan Barcode Izin Anda ke Scanner 👇", font=("Arial", 20, "bold"), text_color="#28a745").pack(pady=(30, 0))

    def putar_slideshow(self):
        if len(self.gambar_iklan) > 0:
            self.lbl_gambar.configure(image=self.gambar_iklan[self.indeks_iklan])
            self.indeks_iklan = (self.indeks_iklan + 1) % len(self.gambar_iklan)
            self.timer_slideshow = self.after(3000, self.putar_slideshow)

    def hentikan_slideshow(self):
        if self.timer_slideshow is not None:
            self.after_cancel(self.timer_slideshow)
            self.timer_slideshow = None

    def buat_halaman_rfid(self):
        self.frame_rfid = ctk.CTkFrame(self, fg_color="#f0f4f8", corner_radius=0)
        info_box = ctk.CTkFrame(self.frame_rfid, fg_color="#ffffff", corner_radius=15)
        info_box.pack(pady=100, padx=100, fill="both", expand=True)
        
        self.lbl_info_jenis_rfid = ctk.CTkLabel(info_box, text="IZIN: -", font=("Arial", 28, "bold"), text_color="#1f538d")
        self.lbl_info_jenis_rfid.pack(pady=(40, 20))
        ctk.CTkLabel(info_box, text="💳", font=("Arial", 80)).pack(pady=10)
        self.lbl_instruksi_rfid = ctk.CTkLabel(info_box, text="SILAKAN TEMPEL\nKARTU PELAJAR ANDA", font=("Arial", 30, "bold"), text_color="#d9534f")
        self.lbl_instruksi_rfid.pack(pady=20)

    def buat_halaman_kamera(self):
        self.frame_kamera = ctk.CTkFrame(self, fg_color="#f0f4f8", corner_radius=0)
        self.lbl_sapaan_siswa = ctk.CTkLabel(self.frame_kamera, text="Halo Siswa, silakan foto terlebih dahulu", font=("Arial", 28, "bold"), text_color="#1f538d")
        self.lbl_sapaan_siswa.pack(pady=(20, 10))

        self.kamera_box = ctk.CTkFrame(self.frame_kamera, fg_color="#000000", width=640, height=480, corner_radius=15)
        self.kamera_box.pack_propagate(False) 
        self.kamera_box.pack(pady=10)
        
        self.lbl_kamera_live = ctk.CTkLabel(self.kamera_box, text="MEMBUKA KAMERA...", font=("Arial", 18), text_color="white")
        self.lbl_kamera_live.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_status_kamera = ctk.CTkLabel(self.frame_kamera, text="Mencari wajah...", font=("Arial", 20), text_color="#555555")
        self.lbl_status_kamera.pack(pady=10)

    def buat_halaman_sukses(self):
        self.frame_sukses = ctk.CTkFrame(self, fg_color="#d4edda", corner_radius=0)
        self.lbl_sukses_icon = ctk.CTkLabel(self.frame_sukses, text="✅", font=("Arial", 80))
        self.lbl_sukses_icon.pack(pady=(100, 20))
        
        self.lbl_sukses_teks = ctk.CTkLabel(self.frame_sukses, text="VALIDASI BERHASIL!", font=("Arial", 36, "bold"), text_color="#155724")
        self.lbl_sukses_teks.pack(pady=10)
        
        self.lbl_sukses_nama = ctk.CTkLabel(self.frame_sukses, text="Hati-hati di jalan", font=("Arial", 24), text_color="#155724")
        self.lbl_sukses_nama.pack(pady=10)
        
        self.lbl_tunggu = ctk.CTkLabel(self.frame_sukses, text="Gerbang Dibuka! Silakan ambil struk Anda.", font=("Arial", 16, "italic"), text_color="#6c757d")
        self.lbl_tunggu.pack(pady=40)

    def sembunyikan_semua_halaman(self):
        self.frame_idle.pack_forget()
        self.frame_rfid.pack_forget()
        self.frame_kamera.pack_forget()
        self.frame_sukses.pack_forget()

    def reset_ke_awal(self):
        self.sembunyikan_semua_halaman()
        self.frame_idle.pack(fill="both", expand=True)
        self.tahapan = "IDLE"
        self.token_sementara = ""
        self.jenis_izin_sementara = ""
        self.nama_siswa_sementara = ""
        self.kelas_siswa_sementara = ""
        self.waktu_deteksi_wajah = None
        self.is_locked = False 
        
        self.kamera.close_camera()
        self.lbl_kamera_live.configure(image="", text="MEMBUKA KAMERA...")
        self.lbl_instruksi_rfid.configure(text="SILAKAN TEMPEL\nKARTU PELAJAR ANDA", text_color="#d9534f")
        
        self.putar_slideshow() 
        self.entry_global.focus()

    def proses_scan(self, event):
        if self.is_locked:
            self.entry_global.delete(0, "end")
            return

        input_data = self.entry_global.get().strip().upper()
        self.entry_global.delete(0, "end") 

        # --- TAHAP 1: SCAN BARCODE (CEK STATUS IZIN) ---
        if self.tahapan == "IDLE":
            data_token = self.db.cek_token(input_data)
            
            if data_token:
                self.hentikan_slideshow()
                self.token_sementara = data_token['kode_token']
                self.jenis_izin_sementara = data_token['jenis_izin']
                status_izin = data_token['status']

                # [LOGIKA BARU] PERCABANGAN BERDASARKAN STATUS
                if status_izin == 'MENUNGGU':
                    # ALUR KELUAR -> Lanjut Scan RFID
                    self.lbl_info_jenis_rfid.configure(text=f"IZIN: {self.jenis_izin_sementara.upper()}")
                    self.sembunyikan_semua_halaman()
                    self.frame_rfid.pack(fill="both", expand=True)
                    self.tahapan = "TAP_KARTU"

                elif status_izin == 'SEDANG_KELUAR':
                    # ALUR KEMBALI -> Langsung Eksekusi Sukses Kembali
                    self.eksekusi_kembali()

        # --- TAHAP 2: TAP RFID (Hanya untuk Alur Keluar) ---
        elif self.tahapan == "TAP_KARTU":
            siswa = self.db.cek_rfid_siswa(input_data)
            if siswa:
                self.nama_siswa_sementara = siswa['nama_siswa']
                self.kelas_siswa_sementara = siswa['kelas']
                self.rfid_sementara = input_data
                
                self.lbl_sapaan_siswa.configure(text=f"Halo {self.nama_siswa_sementara}!\nSilakan hadap kamera.")
                self.sembunyikan_semua_halaman()
                self.frame_kamera.pack(fill="both", expand=True)
                self.tahapan = "AMBIL_FOTO" 
                
                if self.kamera.open_camera():
                    self.update_kamera() 
            else:
                self.lbl_instruksi_rfid.configure(text="KARTU TIDAK DIKENAL!\nCOBA LAGI", text_color="red")

    def update_kamera(self):
        if self.tahapan == "AMBIL_FOTO":
            frame_rgb, wajah_terdeteksi = self.kamera.get_frame()
            if frame_rgb is not None:
                img_pil = Image.fromarray(frame_rgb)
                img_ctk = ctk.CTkImage(light_image=img_pil, size=(640, 480)) 
                self.lbl_kamera_live.configure(image=img_ctk, text="") 

            if wajah_terdeteksi:
                if self.waktu_deteksi_wajah is None:
                    self.waktu_deteksi_wajah = time.time()
                    self.lbl_status_kamera.configure(text="Wajah ditemukan! Memotret dalam 1 detik...", text_color="#d9534f")
                else:
                    waktu_berjalan = time.time() - self.waktu_deteksi_wajah
                    if waktu_berjalan >= 1.5:
                        self.eksekusi_keluar() 
                        return 
            else:
                self.waktu_deteksi_wajah = None
                self.lbl_status_kamera.configure(text="Mencari wajah... (Pastikan tidak tertutup masker)", text_color="#555555")

            self.after(30, self.update_kamera)

    # [BARU] Eksekusi Khusus Alur Keluar
    def eksekusi_keluar(self):
        self.is_locked = True 
        
        # 1. Jepret & Simpan Foto (Dapatkan nama filenya saja)
        path_foto = self.kamera.take_snapshot(f"izin_{self.nama_siswa_sementara.replace(' ', '_')}")
        nama_file_db = os.path.basename(path_foto) if path_foto else None
        self.kamera.close_camera() 
        
        # 2. Update Database (Kirim nama file foto)
        self.db.update_izin_sukses(self.token_sementara, self.rfid_sementara, nama_file_db)
        
        # 3. Cetak Struk
        waktu_sekarang = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        cetak_struk_final(self.nama_siswa_sementara, self.kelas_siswa_sementara, self.jenis_izin_sementara, waktu_sekarang, self.token_sementara)
        
        # 4. Buka Gerbang
        self.arduino.kirim_sinyal_buka()
        
        # 5. Tampilkan Halaman Sukses
        self.lbl_sukses_teks.configure(text="VALIDASI BERHASIL!")
        self.lbl_sukses_nama.configure(text=f"Hati-hati di jalan,\n{self.nama_siswa_sementara}")
        self.lbl_tunggu.configure(text="Gerbang Dibuka! Silakan ambil struk Anda.")
        
        self.sembunyikan_semua_halaman()
        self.frame_sukses.pack(fill="both", expand=True)
        self.after(5000, self.reset_ke_awal) 

    # [BARU] Eksekusi Khusus Alur Kembali
    def eksekusi_kembali(self):
        self.is_locked = True
        
        # 1. Update Database (Ubah status jadi KEMBALI)
        sukses = self.db.update_izin_kembali(self.token_sementara)
        
        if sukses:
            # 2. Buka Gerbang
            self.arduino.kirim_sinyal_buka()
            
            # 3. Tampilkan Halaman Sukses Kembali
            self.lbl_sukses_teks.configure(text="SELAMAT DATANG KEMBALI!")
            self.lbl_sukses_nama.configure(text="Jangan lupa ambil HP Anda di ruang Tatib.")
            self.lbl_tunggu.configure(text="Gerbang Dibuka!")
            
            self.sembunyikan_semua_halaman()
            self.frame_sukses.pack(fill="both", expand=True)
        else:
            print("[!] Gagal mengupdate data kembali ke database")

        self.after(5000, self.reset_ke_awal)

if __name__ == "__main__":
    app = SmartExitKiosk()
    app.mainloop()