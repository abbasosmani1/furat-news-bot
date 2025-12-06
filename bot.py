import time
import requests
import feedparser
from deep_translator import GoogleTranslator
from html import unescape
import re
import os

# ---------------------------------
# تنظیمات
# ---------------------------------
BOT_TOKEN = "8435178994:AAGY-qQ10TgmG98N1sWiSGqJJh7qBYDokHo"   # مثل: 1234567890:ABC-DEF...
CHANNEL_USERNAME = "@furatbtc"      # کانالی که ربات در آن ادمین است

RSS_URL = "https://cointelegraph.com/rss"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# مترجم به عربی
translator = GoogleTranslator(source="auto", target="ar")

# فایل برای ذخیره آخرین لینک ارسال‌شده (برای جلوگیری از تکرار)
LAST_LINK_FILE = "last_link.txt"


# ---------------------------------
# توابع کمکی
# ---------------------------------
def load_last_published_link():
    if os.path.exists(LAST_LINK_FILE):
        try:
            with open(LAST_LINK_FILE, "r", encoding="utf-8") as f:
                link = f.read().strip()
                return link if link else None
        except Exception as e:
            print("خطا در خواندن فایل آخرین لینک:", e)
    return None


def save_last_published_link(link: str):
    try:
        with open(LAST_LINK_FILE, "w", encoding="utf-8") as f:
            f.write(link or "")
    except Exception as e:
        print("خطا در ذخیره آخرین لینک:", e)


def clean_html(html_text: str) -> str:
    """حذف تگ‌های HTML و تبدیل به متن ساده."""
    if not html_text:
        return ""
    # حذف تگ‌های HTML
    text = re.sub(r"<[^>]+>", "", html_text)
    # دیکد کردن HTML entities
    text = unescape(text)
    # تمیز کردن فاصله‌های اضافی
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_latest_news():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return None
    return feed.entries[0]


def translate_to_ar(text: str) -> str:
    if not text:
        return ""
    try:
        return translator.translate(text)
    except Exception as e:
        print("خطا در ترجمه:", e)
        return text  # اگر ترجمه شکست خورد، متن اصلی را می‌فرستیم


def send_message(text: str):
    data = {
        "chat_id": CHANNEL_USERNAME,
        "text": text
    }
    r = requests.post(BASE_URL + "/sendMessage", data=data)
    if not r.ok:
        print("sendMessage error:", r.text)


def send_photo_with_caption(photo_url: str, caption: str):
    data = {
        "chat_id": CHANNEL_USERNAME,
        "photo": photo_url,
        "caption": caption
    }
    r = requests.post(BASE_URL + "/sendPhoto", data=data)
    if not r.ok:
        print("sendPhoto error:", r.text)


# ---------------------------------
# حلقهٔ اصلی
# ---------------------------------
def main_loop():
    last_published_link = load_last_published_link()
    print("آخرین لینک قبلی:", last_published_link)

    while True:
        try:
            item = get_latest_news()
            if not item:
                print("هیچ خبری در RSS پیدا نشد.")
                time.sleep(60)
                continue

            link = getattr(item, "link", None)
            if not link:
                print("این خبر لینک ندارد، رد شد.")
                time.sleep(60)
                continue

            # جلوگیری از ارسال دوباره همان خبر
            if link == last_published_link:
                # خبری جدید نیست
                time.sleep(60)
                continue

            # عنوان و خلاصه خام
            original_title = getattr(item, "title", "")
            original_summary_html = getattr(item, "summary", "")

            # پاک کردن HTML از خلاصه
            clean_summary = clean_html(original_summary_html)

            # ترجمه به عربی
            title_ar = translate_to_ar(original_title)
            summary_ar = translate_to_ar(clean_summary)

            # متن نهایی
            caption = f"{title_ar}\n\n{summary_ar}\n\n@Furatbtc"

            # استخراج تصویر (اگر موجود باشد)
            image_url = None
            if hasattr(item, "media_content"):
                try:
                    if item.media_content:
                        image_url = item.media_content[0].get("url")
                except Exception as e:
                    print("خطا در خواندن media_content:", e)

            if image_url:
                print("ارسال خبر جدید با تصویر...")
                send_photo_with_caption(image_url, caption)
            else:
                print("ارسال خبر جدید بدون تصویر...")
                send_message(caption)

            # ذخیره آخرین لینک برای جلوگیری از تکرار
            last_published_link = link
            save_last_published_link(link)

            # فاصله بین چک‌کردن‌ها (ثانیه)
            time.sleep(60)

        except Exception as e:
            print("Error in main_loop:", e)
            time.sleep(10)


if __name__ == "__main__":
    print("ربات شروع به کار کرد...")
    main_loop()
