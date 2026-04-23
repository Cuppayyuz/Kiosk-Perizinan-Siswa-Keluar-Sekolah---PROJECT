from modules.rfid_handler import RFIDHandler
import time

rfid = RFIDHandler()
if rfid.connect():
    print("Silakan tempelkan kartu pelajar kamu...")
    try:
        while True:
            data = rfid.read_uid()
            if data:
                print(f"BERHASIL! ID KARTU ANDA: {data}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        rfid.disconnect()