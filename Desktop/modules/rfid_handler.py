import serial
import serial.tools.list_ports
import time

class RFIDHandler:
    def __init__(self, baudrate=9600, timeout=1):
        self.port = None
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

    def find_rfid_port(self):
        """ Mencari secara otomatis di mana alat RFID dicolokkan """
        ports = serial.tools.list_ports.comports()
        for p in ports:
            # Biasanya alat RFID USB terbaca sebagai 'USB-Serial' atau 'CH340'
            if "USB" in p.description or "Serial" in p.description:
                print(f"[*] Menemukan calon alat RFID di: {p.device}")
                return p.device
        return None

    def connect(self, port_name=None):
        """ Membuka koneksi ke alat RFID """
        target_port = port_name if port_name else self.find_rfid_port()
        
        if not target_port:
            print("[!] Gagal menemukan port RFID. Pastikan kabel sudah dicolok!")
            return False

        try:
            self.ser = serial.Serial(target_port, self.baudrate, timeout=self.timeout)
            # Bersihkan sisa data lama di kabel
            self.ser.flushInput()
            print(f"[OK] Terhubung ke RFID di {target_port}")
            return True
        except Exception as e:
            print(f"[!] Error Koneksi RFID: {e}")
            return False

    def read_uid(self):
        """ Membaca ID kartu saat ditempelkan """
        if not self.ser or not self.ser.is_open:
            return None

        try:
            # Cek apakah ada data masuk di kabel serial
            if self.ser.in_waiting > 0:
                # Baca satu baris data
                raw_data = self.ser.readline()
                # Ubah dari byte ke string dan bersihkan spasi/enter
                uid = raw_data.decode('utf-8').strip()
                
                if uid:
                    print(f"[DEBUG] Kartu Terdeteksi: {uid}")
                    return uid
            return None
        except Exception as e:
            print(f"[!] Error saat membaca kartu: {e}")
            return None

    def disconnect(self):
        """ Menutup koneksi """
        if self.ser:
            self.ser.close()
            print("[#] Koneksi RFID ditutup.")