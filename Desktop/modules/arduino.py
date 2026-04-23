import serial
import time

class ArduinoHandler:
    def __init__(self, port_name="COM3", baudrate=9600):
        # PENTING: Ganti COM3 dengan port Arduino-mu nanti (bisa dilihat di Arduino IDE)
        self.port = port_name 
        self.baudrate = baudrate
        self.ser = None

    def connect(self):
        """ Membuka jalur komunikasi ke Arduino """
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Jeda 2 detik wajib! Arduino selalu me-restart diri saat port serial dibuka
            print(f"[OK] Terhubung ke Arduino di {self.port}")
            return True
        except Exception as e:
            print(f"[!] Gagal terhubung ke Arduino: {e}")
            return False

    def kirim_sinyal_buka(self):
        """ Mengirim kata sandi 'BUKA' ke Arduino """
        if self.ser and self.ser.is_open:
            try:
                # Mengubah teks "BUKA\n" menjadi format byte (b'') agar bisa lewat kabel
                self.ser.write(b"BUKA\n") 
                print("[#] Sinyal 'BUKA' sukses ditembakkan ke Arduino!")
                return True
            except Exception as e:
                print(f"[!] Gagal menembakkan sinyal: {e}")
                return False
        return False

    def disconnect(self):
        if self.ser:
            self.ser.close()
            print("[#] Koneksi Arduino ditutup.")