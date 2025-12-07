import os
import time
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# ----- تنظیمات اصلی -----
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # اینو تو Render ست می‌کنیم
CHAT_ID = "@furatbtc"                    # کانال مقصد
URL = "https://arzdigital.com/breaking/" # صفحه اخبار فوری
# ------------------------

translator = GoogleTranslator(source="auto", target="ar")
seen_links = set()  # لینک خبرهایی که قبلا ارسال کرده‌ایم


def get_breaking_news():
    """
    از صفحه breaking خبرها را می‌گیرد.
    خروجی: لیست دیکشنری:
    { title_fa, title_ar, link, image }
    """
    resp = requests.get(URL, timeout=15)
    resp.raise_for_status()

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    items = []

    # همه لینک‌هایی که به /news/... اشاره می‌کنند (خبرها)
    links = soup.select('a[href*="/news/"]')

    seen_local = set()

    for a in links:
        title = (a.get_text() or "").strip()
        href = a.get("href")

        if not title or not href:
            continue

        # لینک کامل
        if href.startswith("/"):
            href = "https://arzdigital.com" + href

        key = (title, href)
        if key in seen_local:
            continue
        seen_local.add(key)

        # سعی می‌کنیم تصویر نزدیک به این لینک را پیدا کنیم
        img_url = None
        parent = a.parent
        for _ in range(4):  # چند سطح بالا/پایین را می‌گردیم
            if parent is None:
                break
            img = parent.find("img")
            if img and img.get("src"):
                img_url = img.get("src")
                if img_url.startswith("/"):
                    img_url = "https://arzdigital.com" + img_url
                break
            parent = parent.parent

        try:
            title_ar = translator.translate(title)
        except Exception as e:
            print("خطا در ترجمه:", e)
            title_ar = title  # اگر ترجمه خراب شد، همان فارسی را می‌گذاریم

        items.append(
            {
                "title_fa": title,
                "title_ar": title_ar,
                "link": href,
                "image": img_url,
            }
        )

    return items


def send_to_telegram(item):
    """
    یک خبر را به کانال تلگرام می‌فرستد (ترجیحاً به صورت photo + caption).
    """
    caption = f"{item['title_ar']}\n\n🔗 منبع: {item['link']}"

    if item["image"]:
        # ارسال عکس با URL (خود تلگرام دانلود می‌کند)
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        data = {
            "chat_id": CHAT_ID,
            "photo": item["image"],
            "caption": caption,
        }
    else:
        # اگر عکس نداریم، پیام متنی
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": caption,
        }

    r = requests.post(url, data=data)
    print("ارسال به تلگرام:", r.status_code, r.text)


def main_loop():
    global seen_links

    # مرحله‌ی warm-up:
    # بار اول همه لینک‌های فعلی را فقط علامت می‌زنیم که تکراری محسوب شوند،
    # تا یک‌دفعه ده‌ها خبر قدیمی را پست نکنیم.
    print("راه‌اندازی اولیه، خواندن خبرهای فعلی بدون ارسال...")
    try:
        current = get_breaking_news()
        for item in current:
            seen_links.add(item["link"])
        print(f"{len(seen_links)} خبر به‌عنوان دیده‌شده علامت خورد.")
    except Exception as e:
        print("خطا در warm-up:", e)

    print("شروع مانیتورینگ اخبار جدید...")
    while True:
        try:
            news = get_breaking_news()
            # از اول لیست می‌آید؛ فرض می‌گیریم بالایی‌ها جدیدترند
            for item in news:
                link = item["link"]
                if link in seen_links:
                    continue

                print("خبر جدید پیدا شد:", item["title_fa"])
                send_to_telegram(item)
                seen_links.add(link)
                time.sleep(2)  # بین پیام‌ها کمی فاصله

        except Exception as e:
            print("خطا در حلقه اصلی:", e)

        # هر ۶۰ ثانیه صفحه را چک می‌کنیم
        time.sleep(60)


if __name__ == "__main__":
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN تنظیم نشده! در Render باید متغیر محیطی BOT_TOKEN را ست کنی.")
    main_loop()
