import cv2
from modules.camera import CameraHandler

def jalankan_tes():
    print("Mulai inisialisasi Kamera...")
    cam = CameraHandler(camera_index=0) # 0 biasanya untuk webcam bawaan laptop
    
    if not cam.open_camera():
        print("[!] Gagal membuka kamera. Pastikan webcam tidak sedang dipakai aplikasi lain (seperti Zoom/Meet).")
        return

    print("\n" + "="*40)
    print("MATA KIOSK DIAKTIFKAN!")
    print("- Munculkan wajahmu ke depan kamera.")
    print("- Tekan tombol 's' di keyboard untuk menjepret foto.")
    print("- Tekan tombol 'q' di keyboard untuk mematikan kamera.")
    print("="*40 + "\n")

    while True:
        # Panggil fungsi yang ada di modul camera.py
        frame_rgb, wajah_terdeteksi = cam.get_frame()

        if frame_rgb is not None:
            # Kembalikan ke BGR khusus untuk preview cv2.imshow() di tes ini
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            # Beri indikator teks di pojok kiri atas layar
            if wajah_terdeteksi:
                cv2.putText(frame_bgr, "WAJAH PAS - SIAP JEPRET!", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                cv2.putText(frame_bgr, "Mencari wajah...", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # Tampilkan jendela kamera
            cv2.imshow("TEST KAMERA SMART-EXIT", frame_bgr)

        # Tangkap input keyboard
        key = cv2.waitKey(1) & 0xFF
        
        # Jika tekan 'q', keluar dari perulangan
        if key == ord('q'):
            print("Mematikan tes kamera...")
            break
            
        # Jika tekan 's', simpan foto
        elif key == ord('s'):
            if wajah_terdeteksi:
                print("CEKREK! Menyimpan foto...")
                filepath = cam.take_snapshot("tes_wajah")
                print(f"Buka folder 'hasil_foto' untuk melihat hasilnya: {filepath}")
            else:
                print("[!] Gagal menjepret: Tolong hadapkan wajah ke kamera terlebih dahulu!")

    # Matikan kamera dengan aman
    cam.close_camera()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    jalankan_tes()