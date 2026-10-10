import os, re, asyncio, threading
from datetime import datetime
from flask import Flask
import numpy as np
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = None

app_web = Flask(__name__)
@app_web.route('/')
def home(): return "THEX v4 alive", 200
def run_web():
    app_web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

def _fetch_live_sync():
    try:
        url = "https://www.gosloto.co.za/uk-49s-results/"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        text = BeautifulSoup(r.text, 'html.parser').get_text(" ")
        lun = re.search(r'Lunchtime.*?(\d+)[^\d]+(\d+)[^\d]+(\d+)[^\d]+(\d+)[^\d]+(\d+)[^\d]+(\d+).*?Booster[^\d]+(\d+)', text, re.I|re.S)
        tea = re.search(r'Teatime.*?(\d+)[^\d]+(\d+)[^\d]+(\d+)[^\d]+(\d+)[^\d]+(\d+)[^\d]+(\d+).*?Booster[^\d]+(\d+)', text, re.I|re.S)
        return {"lunchtime": lun.groups() if lun else None, "teatime": tea.groups() if tea else None, "source": url, "time": datetime.now().strftime("%d %b %H:%M SAST")}
    except Exception as e:
        return {"error": str(e)}
async def fetch_live_results(): return await asyncio.to_thread(_fetch_live_sync)
def get_prediction(pool_max, count):
    hot_pool=[7,14,18,23,27,32,41]; cold_pool=[1,9,13,24,36,44]
    hot_pick=list(np.random.choice(hot_pool, min(3,count-3), replace=False))
    cold_pick=list(np.random.choice(cold_pool, min(2,count-len(hot_pick)), replace=False))
    remaining=[n for n in range(1, pool_max+1) if n not in hot_pick+cold_pick]
    random_pick=list(np.random.choice(remaining, count-len(hot_pick)-len(cold_pick), replace=False))
    return sorted(hot_pick+cold_pick+random_pick), hot_pick, cold_pick
async def start(update, context): await update.message.reply_text("🎯 @Thex_uk_aon_bot v4 FIXED\n\n/49 - UK49s\n/aon - AON\n/greece - Greece\n/results - LIVE\n/hot - Hot/Cold\n/check\n/payouts\n/help")
async def help_cmd(update, context): await start(update, context)
async def uk49(update, context):
    nums, hot, cold = get_prediction(49, 6); live = await fetch_live_results()
    await update.message.reply_text(f"🟢 UK 49s v4\n{nums}\nHOT:{hot} COLD:{cold}\nT1:{nums[:3]}=R650\nT2:{nums[3:]}=R650\nFetch:{live.get('time')}")
async def aon(update, context):
    nums, h, c = get_prediction(24, 12); await update.message.reply_text(f"🔵 AON\n{nums}\nA:{nums[:6]}\nB:{nums[6:]}")
async def greece(update, context):
    nums, _, _ = get_prediction(45, 5); pb=int(np.random.choice([4,9,17])); await update.message.reply_text(f"🔴 GREECE\n{nums}+Joker {pb}")
async def results_cmd(update, context):
    await update.message.reply_text("⏳ Fetching..."); live = await fetch_live_results()
    if live.get("lunchtime") or live.get("teatime"):
        msg="📊 LIVE\n";
        if live.get("lunchtime"): msg+=f"LUNCH:{live['lunchtime'][:6]}+B{live['lunchtime'][6]}\n"
        if live.get("teatime"): msg+=f"TEA:{live['teatime'][:6]}+B{live['teatime'][6]}\n"
        await update.message.reply_text(msg+live['source'])
    else: await update.message.reply_text(f"Fail {live.get('error')}")
async def hot_cmd(update, context): await update.message.reply_text("🔥 HOT:7,14,18,23,27,32,41 COLD:1,9,13,24,36,44")
async def check_cmd(update, context): await update.message.reply_text("Use: /check 7,14,23")
async def payouts_cmd(update, context): await update.message.reply_text("💰 R1: 3B=R650 4B=R6.5k")
def main():
    app = Application.builder().token(TOKEN).build()
    for cmd, fn in [("start",start),("help",help_cmd),("49",uk49),("aon",aon),("allornothing",aon),("greece",greece),("results",results_cmd),("hot",hot_cmd),("check",check_cmd),("payouts",payouts_cmd)]: app.add_handler(CommandHandler(cmd, fn))
    print("THEX v4 LIVE..."); app.run_polling(drop_pending_updates=True)
if __name__=="__main__": main()
