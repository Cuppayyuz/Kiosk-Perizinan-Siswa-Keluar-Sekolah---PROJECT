import customtkinter as ctk
from PIL import Image
import os
from modules.database_client import DatabaseClient
from modules.coba_suara import bicara

# Setup Tampilan
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SmartExitKiosk(ctk.CTk):
    def __init__(self):
        super().__init__()

        bicara("Sistem Perizinan Digital Siap Digunakan.")
        # 1. KONFIGURASI LAYAR
        self.title("SMART EXIT KIOSK - SMKN 1")
        self.geometry("1024x600") 
        # self.attributes('-fullscreen', True) # Aktifkan nanti kalau sudah final
        
        # Grid Layout 2 Kolom (Kiri: Info, Kanan: Instruksi)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- FRAME KIRI (LOGO & STATUS) ---
        self.frame_kiri = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.frame_kiri.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        self.lbl_judul = ctk.CTkLabel(self.frame_kiri, text="SISTEM PERIZINAN\nDIGITAL", font=("Arial", 30, "bold"))
        self.lbl_judul.pack(pady=40)
        
        self.lbl_status = ctk.CTkLabel(self.frame_kiri, text="MENUNGGU TOKEN...", font=("Arial", 24), text_color="yellow")
        self.lbl_status.pack(pady=20)

        # --- FRAME KANAN (INPUT & INSTRUKSI) ---
        self.frame_kanan = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.frame_kanan.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.lbl_instruksi = ctk.CTkLabel(self.frame_kanan, text="SCAN QR / KETIK TOKEN", font=("Arial", 20))
        self.lbl_instruksi.pack(pady=40)

        # Input Box (Untuk Barcode Scanner)
        # Barcode scanner itu sebenarnya cuma keyboard yang ngetik cepat + Enter
        self.entry_token = ctk.CTkEntry(self.frame_kanan, width=300, height=50, font=("Arial", 24), placeholder_text="Arahkan Barcode...")
        self.entry_token.pack(pady=10)
        self.entry_token.bind("<Return>", self.proses_scan) # Kalau di-Enter, jalanin fungsi
        self.entry_token.focus() # Otomatis kursor aktif disini

        # Variabel Penyimpan Data
        # ... kode layout lainnya ...
        
        self.db = DatabaseClient()
        
        # [BARU] Variabel untuk mengingat sedang di tahap mana
        self.tahapan = "SCAN_TOKEN" # Pilihan: "SCAN_TOKEN" atau "TAP_KARTU"
        self.token_sementara = ""   # Untuk menyimpan token yang valid

        
        self.db = DatabaseClient()
    def proses_scan(self, event): # Pastikan nama fungsinya sama dengan yang di .bind
        input_data = self.entry_token.get().strip().upper()
        self.entry_token.delete(0, "end") # Bersihkan input box langsung

        # --- LOGIKA TAHAP 1: CEK TOKEN ---
        if self.tahapan == "SCAN_TOKEN":
            self.lbl_status.configure(text="MEMERIKSA TOKEN...", text_color="white")
            self.update()

            data_token = self.db.cek_token(input_data)

            if data_token:
                bicara("Token tervalid. Silakan tempel kartu RFID Anda.")
                # Token Valid! Lanjut ke Tahap 2
                self.token_sementara = data_token['kode_token']
                jenis = data_token['jenis_izin']
                
                self.lbl_status.configure(text=f"✅ TOKEN OK: {jenis}\nSILAKAN TAP KARTU ANDA!", text_color="#00ff00")
                self.lbl_instruksi.configure(text=">>> TEMPEL KARTU SEKARANG <<<", font=("Arial", 24, "bold"), text_color="cyan")
                
                # UBAH MODE JADI MENUNGGU KARTU
                self.tahapan = "TAP_KARTU"
                
            else:
                bicara("Token tidak dikenal. Silakan coba lagi.")
                self.lbl_status.configure(text="❌ TOKEN TIDAK DIKENAL!", text_color="red")
                self.after(2000, self.reset_tampilan)

        # --- LOGIKA TAHAP 2: CEK KARTU RFID ---
        elif self.tahapan == "TAP_KARTU":
            self.lbl_status.configure(text="MEMBACA KARTU...", text_color="yellow")
            self.update()

            # 1. Cek apakah kartu terdaftar di database siswa?
            siswa = self.db.cek_rfid_siswa(input_data)

            if siswa:
                bicara("Kartu terdeteksi. Memproses izin Anda.")
                nama = siswa['nama_siswa']
                kelas = siswa['kelas']
                
                # 2. Simpan Transaksi (Update Database)
                sukses = self.db.update_izin_sukses(self.token_sementara, input_data)
                
                if sukses:
                    self.lbl_status.configure(text=f"✅ IZIN BERHASIL!\nHATI-HATI DI JALAN, {nama}", text_color="#00ff00")
                    self.lbl_instruksi.configure(text="MENCETAK STRUK...", font=("Arial", 20))
                    self.update() # Paksa UI update tulisan
                    
                    # --- EKSEKUSI PRINTER ---
                    # Kita ambil jenis izin dari data_token sebelumnya
                    bicara("Izin berhasil. Silakan ambil struk Anda.")
                    
                    
                    self.after(4000, self.reset_tampilan) # Reset ke awal setelah 4 detik
                else:
                    self.lbl_status.configure(text="❌ GAGAL MENYIMPAN DATA", text_color="red")
                    self.after(2000, self.reset_tampilan)
            else:
                bicara("Kartu tidak terdaftar. Silakan coba lagi.")
                self.lbl_status.configure(text="❌ KARTU TIDAK TERDAFTAR!", text_color="red")
                # Jangan reset tampilan dulu, kasih kesempatan tap ulang
                self.lbl_instruksi.configure(text="Coba Tap Kartu Lain", text_color="yellow")

    def reset_tampilan(self):
        bicara("Sistem siap menerima token baru.")
        self.tahapan = "SCAN_TOKEN" # Kembali ke mode awal
        self.token_sementara = ""
        self.lbl_status.configure(text="MENUNGGU TOKEN...", text_color="yellow")
        self.lbl_instruksi.configure(text="SCAN QR / KETIK TOKEN", text_color="white", font=("Arial", 20))
        self.entry_token.focus()


if __name__ == "__main__":
    app = SmartExitKiosk()
    app.mainloop()