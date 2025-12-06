import feedparser
import time
import requests
from googletrans import Translator
from telegram import Bot

BOT_TOKEN = "8435178994:AAGY-qQ10TgmG98N1sWiSGqJJh7qBYDokHo"
CHANNEL = "@furatbtc"

translator = Translator()
bot = Bot(token=BOT_TOKEN)

LAST_PUBLISHED = None

RSS_URL = "https://cointelegraph.com/rss"

def get_latest_news():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return None
    return feed.entries[0]

def translate(text):
    return translator.translate(text, dest="fa").text

while True:
    try:
        item = get_latest_news()
        if item and item.link != LAST_PUBLISHED:
            title = translate(item.title)
            summary = translate(item.summary)

            caption = f"{title}\n\n{summary}\n\n@Furatbtc"

            image_url = None
            if "media_content" in item:
                image_url = item.media_content[0]["url"]

            if image_url:
                bot.send_photo(chat_id=CHANNEL, photo=image_url, caption=caption)
            else:
                bot.send_message(chat_id=CHANNEL, text=caption)

            LAST_PUBLISHED = item.link

        time.sleep(60)

    except Exception as e:
        print("Error:", e)
        time.sleep(10)
