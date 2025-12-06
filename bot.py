import time
import requests
import feedparser
from deep_translator import GoogleTranslator

# -----------------------------
# تنظیمات ربات
# -----------------------------
BOT_TOKEN = "8435178994:AAGY-qQ10TgmG98N1sWiSGqJJh7qBYDokHo"   # مثل: 1234567890:ABC....
CHANNEL_USERNAME = "@furatbtc"      # کانالی که ربات توش ادمینه

RSS_URL = "https://cointelegraph.com/rss"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

translator = GoogleTranslator(source="auto", target="fa")
LAST_PUBLISHED_LINK = None  # برای جلوگیری از ارسال تکراری


# -----------------------------
# گرفتن آخرین خبر از RSS
# -----------------------------
def get_latest_news():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return None
    return feed.entries[0]


# -----------------------------
# ترجمه متن به فارسی
# -----------------------------
def translate_to_fa(text: str) -> str:
    if not text:
        return ""
    return translator.translate(text)


# -----------------------------
# ارسال پیام متنی به کانال
# -----------------------------
def send_message(text: str):
    data = {
        "chat_id": CHANNEL_USERNAME,
        "text": text
    }
    r = requests.post(BASE_URL + "/sendMessage", data=data)
    if not r.ok:
        print("sendMessage error:", r.text)


# -----------------------------
# ارسال عکس به همراه کپشن
# -----------------------------
def send_photo_with_caption(photo_url: str, caption: str):
    data = {
        "chat_id": CHANNEL_USERNAME,
        "photo": photo_url,
        "caption": caption
    }
    r = requests.post(BASE_URL + "/sendPhoto", data=data)
    if not r.ok:
        print("sendPhoto error:", r.text)


# -----------------------------
# حلقهٔ اصلی ربات
# -----------------------------
def main_loop():
    global LAST_PUBLISHED_LINK

    while True:
        try:
            item = get_latest_news()
            if not item:
                print("هیچ خبری در RSS پیدا نشد.")
                time.sleep(60)
                continue

            link = item.link

            # جلوگیری از ارسال خبر تکراری
            if link == LAST_PUBLISHED_LINK:
                # خبری جدید نیست
                time.sleep(60)
                continue

            # عنوان و خلاصه را ترجمه می‌کنیم
            original_title = getattr(item, "title", "")
            original_summary = getattr(item, "summary", "")

            title_fa = translate_to_fa(original_title)
            summary_fa = translate_to_fa(original_summary)

            # متن نهایی برای ارسال
            caption = f"{title_fa}\n\n{summary_fa}\n\n@Furatbtc"

            # پیدا کردن عکس اگر وجود داشته باشد
            image_url = None
            if hasattr(item, "media_content"):
                try:
                    if item.media_content:
                        image_url = item.media_content[0].get("url")
                except Exception as e:
                    print("خطا در خواندن media_content:", e)

            if image_url:
                print("ارسال خبر به همراه عکس...")
                send_photo_with_caption(image_url, caption)
            else:
                print("ارسال خبر بدون عکس...")
                send_message(caption)

            LAST_PUBLISHED_LINK = link

            # کمی صبر می‌کنیم تا دوباره چک کنیم (مثلاً هر ۶۰ ثانیه)
            time.sleep(60)

        except Exception as e:
            print("Error in main_loop:", e)
            time.sleep(10)


if __name__ == "__main__":
    print("ربات شروع به کار کرد...")
    main_loop()
