from machine import Pin, ADC
import time
import network
import urequests
import ujson
import gc

# =============================
# WIFI SETUP
# =============================
SSID = "Apa"
PASSWORD = "12345678"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

print("Menghubungkan WiFi...")
while not wlan.isconnected():
    time.sleep(1)

print("WiFi Terhubung:", wlan.ifconfig())

# =============================
# TELEGRAM CONFIG (GANTI INI)
# =============================
BOT_TOKEN = "8707486844:AAGel7P2I-VE3qFga6BZUgfpHZ_XquNKnJA"
CHAT_ID = "7789479206"

# =============================
# INISIALISASI PIN
# =============================
sensor_gas = ADC(Pin(34))
sensor_gas.atten(ADC.ATTN_11DB)

buzzer = Pin(26, Pin.OUT)
led = Pin(27, Pin.OUT)

# =============================
# BATAS KONDISI
# =============================
BATAS_WASPADA = 1500
BATAS_BAHAYA = 2500

# =============================
# FIREBASE URL
# =============================
URL_DATA = "https://firesafe-c6869-default-rtdb.asia-southeast1.firebasedatabase.app/data.json"
URL_LOGS = "https://firesafe-c6869-default-rtdb.asia-southeast1.firebasedatabase.app/logs.json"

# =============================
# VARIABEL
# =============================
blink_state = False
last_send = 0
interval_kirim = 3000

# 🔥 TELEGRAM CONTROL
last_telegram = 0
interval_telegram = 30000  # 30 detik

# =============================
# FUNGSI TELEGRAM
# =============================
def kirim_telegram(pesan):
    try:
        url = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}".format(
            BOT_TOKEN, CHAT_ID, pesan
        )
        urequests.get(url)
        print("📱 Telegram terkirim")
    except Exception as e:
        print("❌ Telegram error:", e)

# =============================
# LOOP UTAMA
# =============================
while True:
    nilai_gas = sensor_gas.read()
    sekarang = time.ticks_ms()

    print("Nilai Gas:", nilai_gas)

    # ======== LOGIKA ========
    if nilai_gas < BATAS_WASPADA:
        status = "AMAN"

        led.off()
        buzzer.off()
        blink_state = False

        delay = 0.8
        print("✅ Gas Aman")

    elif nilai_gas < BATAS_BAHAYA:
        status = "WASPADA"

        blink_state = not blink_state
        led.value(blink_state)
        buzzer.off()

        delay = 0.8
        print("⚠️ Gas Waspada")

    else:
        status = "BAHAYA"

        blink_state = not blink_state
        led.value(blink_state)
        buzzer.value(blink_state)

        delay = 0.4
        print("🔥 Gas Berbahaya!")

        # 🔥 TELEGRAM (TIAP 30 DETIK)
        if time.ticks_diff(sekarang, last_telegram) > interval_telegram:
            kirim_telegram("🔥🔥 BAHAYA!! GAS TINGGI TERDETEKSI DI DAPURR 🔥🔥!")
            last_telegram = sekarang

    # =============================
    # FIREBASE
    # =============================
    if time.ticks_diff(sekarang, last_send) > interval_kirim:
        gc.collect()

        data = {
            "gas": nilai_gas,
            "status": status,
            "timestamp": time.time()
        }

        headers = {"Content-Type": "application/json"}

        try:
            r = urequests.put(URL_DATA, data=ujson.dumps(data), headers=headers)
            r.close()
            print("📤 Realtime terkirim")
        except Exception as e:
            print("❌ Error realtime:", e)

        try:
            r = urequests.post(URL_LOGS, data=ujson.dumps(data), headers=headers)
            r.close()
            print("📊 Histori terkirim")
        except Exception as e:
            print("❌ Error histori:", e)

        last_send = sekarang

    time.sleep(delay)