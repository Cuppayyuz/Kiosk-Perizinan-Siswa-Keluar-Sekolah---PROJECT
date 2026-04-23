import cv2
import time
import os
from datetime import datetime

class CameraHandler:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        # Muat Model AI Bawaan OpenCV untuk Deteksi Wajah (Ringan)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Folder untuk menyimpan foto jepretan
        self.save_folder = "hasil_foto"
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)

    def open_camera(self):
        """ Membuka koneksi ke webcam """
        self.cap = cv2.VideoCapture(self.camera_index)
        # Atur resolusi kamera agar tidak terlalu berat (misal 640x480)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not self.cap.isOpened():
            print("[!] Gagal membuka webcam.")
            return False
        print("[OK] Webcam berhasil dibuka.")
        return True

    def get_frame(self):
        """ Mengambil satu frame, mendeteksi wajah, dan mengembalikannya untuk Tkinter """
        if not self.cap or not self.cap.isOpened():
            return None, False

        ret, frame = self.cap.read()
        if not ret:
            return None, False

        # Balik gambar (mirror effect) agar siswa tidak bingung
        frame = cv2.flip(frame, 1)
        
        # Deteksi Wajah
        # 1. Ubah ke Grayscale (hitam putih) untuk mempercepat AI
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 2. AI mencari wajah
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(100, 100))
        
        wajah_terdeteksi = False
        # 3. Jika ketemu, gambar kotak hijau di wajah
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            # Penanda bahwa wajah sudah pas
            wajah_terdeteksi = True
            break # Kita hanya butuh 1 wajah terdepan

        # Ubah format warna dari BGR (OpenCV) ke RGB (Tkinter/PIL)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame_rgb, wajah_terdeteksi

    def take_snapshot(self, filename_prefix="izin"):
        """ Menjepret frame saat ini dan menyimpannya sebagai file """
        if not self.cap or not self.cap.isOpened():
            return None

        ret, frame = self.cap.read()
        if ret:
            # Balik gambar
            frame = cv2.flip(frame, 1)
            
            # Buat nama file unik berdasarkan waktu
            waktu_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{waktu_str}.jpg"
            filepath = os.path.join(self.save_folder, filename)
            
            # Simpan file gambar kualitas tinggi
            cv2.imwrite(filepath, frame)
            print(f"[OK] Foto berhasil dijepret & disimpan di: {filepath}")
            return filepath
        return None

    def close_camera(self):
        """ Menutup webcam """
        if self.cap:
            self.cap.release()
            print("[#] Webcam ditutup.")

