import asyncio
import datetime
import os
import pandas as pd
from quotexpy.new import Quotex
import requests

EMAIL_QUOTEX = os.getenv("EMAIL_QUOTEX", "Anggunyana1627@gmail.com")
PASSWORD_QUOTEX = os.getenv("PASSWORD_QUOTEX", "Uptownreko")
IS_DEMO = True

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8794567698:AAFGTt04VG4Aea5fFmavIHONxLBLfDYNXnM")
CHAT_ID = os.getenv("CHAT_ID", "-1004482046792")

PAIRS = ["EURUSD_otc", "GBPUSD_otc", "AUDUSD_otc"]
DURASI_TRADE_DETIK = 60

def send_telegram_signal(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=6)
    except Exception as e:
        print("Gagal kirim Telegram:", e)

async def analyze_sma_strategy(client, asset):
    try:
        candles = await client.get_candles(asset, 60, 50)
        if not candles or len(candles) < 30:
            return None, "Data belum cukup", 0
        
        df = pd.DataFrame(candles)
        df["close"] = df["close"].astype(float)
        
        df["sma_8"] = df["close"].rolling(window=8).mean()
        df["sma_13"] = df["close"].rolling(window=13).mean()
        
        last_close = df["close"].iloc[-2]
        sma8_now = df["sma_8"].iloc[-2]
        sma13_now = df["sma_13"].iloc[-2]
        
        sma8_prev = df["sma_8"].iloc[-3]
        sma13_prev = df["sma_13"].iloc[-3]
        
        crossover = (sma8_prev <= sma13_prev) and (sma8_now > sma13_now)
        crossunder = (sma8_prev >= sma13_prev) and (sma8_now < sma13_now)
        
        if last_close > sma8_now and last_close > sma13_now and crossover:
            return "BUY", "SMA 8 & 13 Crossover (Bullish)", last_close
        elif last_close < sma8_now and last_close < sma13_now and crossunder:
            return "SELL", "SMA 8 & 13 Crossunder (Bearish)", last_close
            
        return None, "None", last_close
    except Exception as e:
        print(f"Error analisa {asset}: {e}")
        return None, "Error", 0

async def main():
    print("Menghubungkan ke server WebSocket Quotex...")
    client = Quotex(
        email=EMAIL_QUOTEX,
        password=PASSWORD_QUOTEX,
        iss_demo=1 if IS_DEMO else 0,
        lang="en"
    )
    
    check_auth, reason = await client.connect()
    if not check_auth:
        print(f"❌ Gagal login ke Quotex: {reason}")
        send_telegram_signal(f"❌ *Bot Gagal Login Quotex:* {reason}")
        return
        
    print("✅ Berhasil terhubung ke server WebSocket Quotex!")
    send_telegram_signal("📈 *Bot Quotex WebSocket (Cloud GitHub Actions) Diaktifkan!*")
    
    start_time = datetime.datetime.now()
    
    while True:
        try:
            if (datetime.datetime.now() - start_time).total_seconds() > 18000:
                break

            while datetime.datetime.now().second != 30:
                await asyncio.sleep(0.2)
                
            for asset in PAIRS:
                signal, strategi_info, current_price = await analyze_sma_strategy(client, asset)
                if signal:
                    msg_signal = (
                        f"📈 *SINYAL TRADING QTX (WSS)*\n\n"
                        f"Aset: *{asset}*\n"
                        f"Metode: *{strategi_info}*\n"
                        f"Arah: *{signal}*\n"
                        f"Durasi: *1 Menit*\n\n"
                        f"💡 *Sinyal dari server Quotex (Cloud)*"
                    )
                    send_telegram_signal(msg_signal)
                    
                    while datetime.datetime.now().second != 0:
                        await asyncio.sleep(0.1)
                        
                    await asyncio.sleep(DURASI_TRADE_DETIK)
                    break
                    
                await asyncio.sleep(1)
            await asyncio.sleep(15)
        except Exception as e:
            print("Error:", e)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
