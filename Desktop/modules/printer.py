from escpos.printer import Win32Raw
import traceback

# =================================================================
# Ganti dengan nama printer EPSON kamu di Control Panel Windows
NAMA_PRINTER_WINDOWS = "EPSON TM-T82 Receipt" 
# =================================================================

# 1. FUNGSI UNTUK GURU TATIB (Mencetak Barcode)
def cetak_barcode(token, jenis_izin):
    try:
        p = Win32Raw(NAMA_PRINTER_WINDOWS)
        p.set(align='center', bold=True, double_height=True, double_width=True)
        p.text("SMART EXIT\n")
        p.set(align='center', bold=False)
        p.text("================================\n\n")
        p.text(f"TIPE IZIN: {jenis_izin.upper()}\n\n")
        
        # Cetak Barcode
        p.barcode(token, 'CODE128', 64, 2, '', '')
        p.text("\n")
        p.text("Harap scan barcode ini\n")
        p.text("di layar Kiosk Pos Satpam.\n")
        p.text("================================\n\n\n")
        
        try: p.cut() 
        except: pass
        return True
    except Exception as e:
        print(f"Error Printer Barcode: {e}")
        return False

# 2. FUNGSI UNTUK KIOSK (Mencetak Bukti Keluar Final 2 RANGKAP)
def cetak_struk_final(nama_siswa, kelas, jenis_izin, waktu):
    try:
        p = Win32Raw(NAMA_PRINTER_WINDOWS)
        
        # Kita buat daftar untuk 2 rangkap (Satpam & Siswa)
        rangkap = [
            {"judul": "--- BUKTI UNTUK SATPAM ---", "pesan": "(Serahkan struk ini ke Satpam)"},
            {"judul": "--- BUKTI UNTUK SISWA ---", "pesan": "(Simpan sebagai bukti sah izin)"}
        ]

        # Looping untuk mencetak 2 kali berturut-turut
        for salinan in rangkap:
            # Penanda Rangkap
            p.set(align='center', bold=True)
            p.text(f"{salinan['judul']}\n\n")

            # Header Struk
            p.set(align='center', bold=True, double_height=True, double_width=True)
            p.text("E-PASS KELUAR\n")
            p.set(align='center', bold=False, double_height=False, double_width=False)
            p.text("SMART EXIT - BUKTI VALIDASI\n")
            p.text("================================\n\n")
            
            # Data Siswa (Rata Kiri)
            p.set(align='left', bold=False)
            p.text(f"NAMA  : {nama_siswa}\n")
            p.text(f"KELAS : {kelas}\n")
            p.text(f"IZIN  : {jenis_izin.upper()}\n")
            p.text(f"WAKTU : {waktu}\n\n")
            
            # Footer (Rata Tengah)
            p.set(align='center', bold=True)
            p.text("VALIDASI KIOSK: BERHASIL\n")
            p.set(align='center', bold=False)
            p.text(f"{salinan['pesan']}\n")
            p.text("================================\n\n\n\n")
            
            # Potong kertas otomatis untuk setiap rangkap
            try: p.cut() 
            except: pass
            
        return True
    except Exception as e:
        print(f"Error Printer Final: {e}")
        return False