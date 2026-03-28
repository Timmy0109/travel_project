import requests
from bs4 import BeautifulSoup

url = "https://www.tenlong.com.tw/zh_tw/recent"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}
response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.text, "html.parser")

books = soup.select(".list-wrapper")

for book in books:
    title_el = book.select_one(".title a")
    price_el = book.select_one(".pricing del")

    title = title_el.text.strip() if title_el else "（無書名）"
    price = price_el.text.strip() if price_el else "（無價格）"

    print(f"書名：{title}")
    print(f"價格：{price}")
    print("-" * 30)