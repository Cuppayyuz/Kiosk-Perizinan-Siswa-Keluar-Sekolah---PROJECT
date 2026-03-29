import pyttsx3

def bicara(teks):
    print(f"[AI]: {teks}")
    try:
        engine = pyttsx3.init('sapi5')
        
        # --- BAGIAN PENTING: MENCARI SUARA INDONESIA ---
        voices = engine.getProperty('voices')
        found_id = None

        # Cari yang namanya mengandung "Andika" atau "Gadis" (Suara Indo Windows)
        for voice in voices:
            if "Andika" in voice.name or "Gadis" in voice.name:
                found_id = voice.id
                break
        
        # Jika ketemu Andika/Gadis, pakai ID-nya
        if found_id:
            engine.setProperty('voice', found_id)
        else:
            # JAGA-JAGA: Jika tidak ketemu nama spesifik, cari kode "ID"
            for voice in voices:
                if "Indonesia" in voice.name or "id_ID" in voice.id:
                    engine.setProperty('voice', voice.id)
                    break
        
        engine.setProperty('rate', 150) 
        engine.say(teks)
        engine.runAndWait()
        engine.stop()
        
    except Exception as e:
        print(f"Error Suara: {e}")