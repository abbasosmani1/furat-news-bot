import requests
import time
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = "@furatbtc"
API_URL = os.environ["SCRAPER_URL"]  # مثلاً https://yourapp.onrender.com/breaking

seen_links = set()  # حافظهٔ خبرهای منتشرشده


def send_photo(image_url, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    data = {
        "chat_id": CHAT_ID,
        "caption": caption
    }
    files = {
        "photo": requests.get(image_url, stream=True).raw
    }
    r = requests.post(url, data=data, files=files)
    print("Telegram:", r.text)


def run_loop():
    global seen_links

    while True:
        try:
            data = requests.get(API_URL, timeout=10).json()

            for item in data["items"]:
                link = item["link"]
                title_ar = item["title_ar"]
                img = item["image"]

                if link in seen_links:
                    continue

                caption = f"{title_ar}\n\n🔗 منبع: {link}"

                if img:
                    send_photo(img, caption)
                else:
                    # پیام بدون عکس
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        data={"chat_id": CHAT_ID, "text": caption}
                    )

                seen_links.add(link)
                time.sleep(1)

        except Exception as e:
            print("Error:", e)

        time.sleep(120)  # هر ۲ دقیقه چک کن


if __name__ == "__main__":
    run_loop()
