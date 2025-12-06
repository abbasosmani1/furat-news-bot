import time
import os
import re
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from html import unescape

# ---------------------------------
# تنظیمات
# ---------------------------------
BOT_TOKEN = "8435178994:AAGY-qQ10TgmG98N1sWiSGqJJh7qBYDokHo"   # مثل: 1234567890:ABC-DEF...
CHANNEL_USERNAME = "@furatbtc"      # کانالی که ربات در آن ادمین است

BREAKING_URL = "https://arzdigital.com/breaking/"
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


def clean_text(text: str) -> str:
    """تمیز کردن فاصله‌ها و تبدیل HTML entities."""
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_breaking_page():
    resp = requests.get(BREAKING_URL, timeout=10)
    resp.raise_for_status()
    return resp.text


def parse_latest_breaking(html: str):
    """
    تلاش می‌کنیم از صفحه‌ی breaking:
    - اولین خبر
    - لینک
    - عنوان
    - تصویر (در صورت موجود)
    را استخراج کنیم.
    """
    soup = BeautifulSoup(html, "html.parser")

    # همه‌ی لینک‌هایی که به یک خبر می‌روند (معمولاً /news/ در URL دارند)
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # بعضی لینک‌ها نسبی هستند، بعضی مطلق
        if href.startswith("/"):
            full = "https://arzdigital.com" + href
        else:
            full = href

        # فقط لینک‌های خبر (حدسی: /news/)
        if "arzdigital.com" in full and "/news/" in full:
            title = clean_text(a.get_text())
            if len(title) > 10:  # یه حداقل طول برای حذف لینک‌های ضعیف
                links.append((full, title, a))
    
    if not links:
        return None

    # اولین خبر در صفحه را می‌گیریم
    link, title, a_tag = links[0]

    # سعی می‌کنیم عکس مرتبط را پیدا کنیم (نزدیک همان لینک)
    image_url = None

    # 1) اگر داخل تگ <figure> یا والد باشد
    parent = a_tag.parent
    for _ in range(3):  # حداکثر 3 سطح بالا می‌رویم
        if parent is None:
            break
        img = parent.find("img")
        if img and img.get("src"):
            src = img["src"]
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = "https://arzdigital.com" + src
            image_url = src
            break
        parent = parent.parent

    # اگر هنوز عکس نداریم، به صورت کلی‌تر یک img نزدیک همان بخش را می‌گیریم
    if not image_url:
        img = a_tag.find_previous("img")
        if img and img.get("src"):
            src = img["src"]
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = "https://arzdigital.com" + src
            image_url = src

    # متن خلاصه‌ی کوتاه (در صفحه‌ی breaking معمولاً زیر یا کنار عنوان هست، ولی ساختارشان ثابت نیست)
    # برای سادگی فعلاً فقط عنوان را استفاده می‌کنیم.
    summary = ""

    return {
        "link": link,
        "title": title,
        "summary": summary,
        "image_url": image_url,
    }


def translate_to_ar(text: str) -> str:
    if not text:
        return ""
    try:
        return translator.translate(text)
    except Exception as e:
        print("خطا در ترجمه:", e)
        return text  # اگر ترجمه شکست خورد، همان متن اصلی را می‌فرستیم


def send_message(text: str):
    data = {
        "chat_id": CHANNEL_USERNAME,
        "text": text
    }
    r = requests.post(BASE_URL + "/sendMessage", data=data)
    if not r.ok:
        print("sendMessage error:", r.status_code, r.text)


def send_photo_with_caption(photo_url: str, caption: str):
    data = {
        "chat_id": CHANNEL_USERNAME,
        "photo": photo_url,
        "caption": caption
    }
    r = requests.post(BASE_URL + "/sendPhoto", data=data)
    if not r.ok:
        print("sendPhoto error:", r.status_code, r.text)


# ---------------------------------
# حلقه‌ی اصلی
# ---------------------------------
def main_loop():
    last_link = load_last_published_link()
    print("آخرین لینک قبلی:", last_link)

    while True:
        try:
            html = fetch_breaking_page()
            item = parse_latest_breaking(html)

            if not item:
                print("هیچ خبر معتبری در صفحه‌ی breaking پیدا نشد.")
                time.sleep(60)
                continue

            link = item["link"]
            title = item["title"]
            summary = item["summary"]
            image_url = item["image_url"]

            # جلوگیری از ارسال خبر تکراری
            if link == last_link:
                time.sleep(60)
                continue

            # ترجمه به عربی
            title_ar = translate_to_ar(title)
            summary_ar = translate_to_ar(summary) if summary else ""

            # کپشن نهایی
            if summary_ar:
                caption = f"{title_ar}\n\n{summary_ar}\n\n{link}\n\n@Furatbtc"
            else:
                caption = f"{title_ar}\n\n{link}\n\n@Furatbtc"

            # ارسال
            if image_url:
                print("ارسال خبر جدید با تصویر...")
                send_photo_with_caption(image_url, caption)
            else:
                print("ارسال خبر جدید بدون تصویر...")
                send_message(caption)

            # ذخیره لینک برای جلوگیری از تکرار
            last_link = link
            save_last_published_link(link)

            time.sleep(60)

        except Exception as e:
            print("Error in main_loop:", e)
            time.sleep(15)


if __name__ == "__main__":
    print("ربات شروع به کار کرد...")
    main_loop()
