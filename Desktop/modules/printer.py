from escpos.printer import Win32Raw
import traceback

NAMA_PRINTER_WINDOWS = "EPSON TM-T82 Receipt" 

def cetak_barcode(token, jenis_izin):
    # (Fungsi ini tetap sama seperti milikmu)
    try:
        p = Win32Raw(NAMA_PRINTER_WINDOWS)
        p.set(align='center', bold=True, double_height=True, double_width=True)
        p.text("SMART EXIT\n")
        p.set(align='center', bold=False)
        p.text("================================\n\n")
        p.text(f"TIPE IZIN: {jenis_izin.upper()}\n\n")
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

# [UPDATE] Menambahkan parameter 'token'
def cetak_struk_final(nama_siswa, kelas, jenis_izin, waktu, token):
    try:
        p = Win32Raw(NAMA_PRINTER_WINDOWS)
        
        rangkap = [
            {"judul": "--- BUKTI UNTUK SATPAM ---", "pesan": "(Serahkan struk ini ke Satpam)"},
            {"judul": "--- BUKTI UNTUK SISWA ---", "pesan": "(Simpan sebagai bukti sah)"}
        ]

        for salinan in rangkap:
            p.set(align='center', bold=True)
            p.text(f"{salinan['judul']}\n\n")

            p.set(align='center', bold=True, double_height=True, double_width=True)
            p.text("E-PASS KELUAR\n")
            p.set(align='center', bold=False, double_height=False, double_width=False)
            p.text("SMART EXIT - BUKTI VALIDASI\n")
            p.text("================================\n\n")
            
            p.set(align='left', bold=False)
            p.text(f"NAMA  : {nama_siswa}\n")
            p.text(f"KELAS : {kelas}\n")
            p.text(f"IZIN  : {jenis_izin.upper()}\n")
            p.text(f"WAKTU : {waktu}\n\n")
            
            # [LOGIKA BARU] Jika IZIN KELUAR dan untuk RANGKAP SISWA, cetak barcode kembali
            if jenis_izin.upper() == "KELUAR" and "SISWA" in salinan['judul']:
                p.set(align='center')
                p.text("SCAN INI SAAT ANDA KEMBALI:\n")
                p.barcode(token, 'CODE128', 64, 2, '', '')
                p.text("\n")
                p.text("Jangan sampai barcode ini hilang/rusak!\n\n")

            p.set(align='center', bold=True)
            p.text("VALIDASI KIOSK: BERHASIL\n")
            p.set(align='center', bold=False)
            p.text(f"{salinan['pesan']}\n")
            p.text("================================\n\n\n\n")
            
            try: p.cut() 
            except: pass
            
        return True
    except Exception as e:
        print(f"Error Printer Final: {e}")
        return False