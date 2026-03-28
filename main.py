import sqlite3
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from flask_cors import CORS # 務必確認已執行 pip install flask-cors

app = Flask(__name__)
CORS(app) # 允許 Vue 前端存取 API

DB_NAME = "travel_data.db"

# --- [Issue #01 & #02 的邏輯保留] ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price TEXT)')
    conn.commit()
    conn.close()

def scrape_to_db():
    url = "https://www.tenlong.com.tw/zh_tw/recent"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 使用你剛才測試成功的 .list-wrapper ul li 結構
    books_data = soup.select(".list-wrapper ul li")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books")
    
    count = 0
    for book in books_data:
        title_el = book.select_one("a.title") or book.select_one(".title")
        price_el = book.select_one(".pricing") or book.select_one(".price")
        if title_el:
            cursor.execute("INSERT INTO books (title, price) VALUES (?, ?)", 
                           (title_el.text.strip(), price_el.text.strip() if price_el else "N/A"))
            count += 1
    conn.commit()
    conn.close()
    print(f"🚩 [Issue #02] 數據已就緒，共 {count} 筆。")

# --- [Issue #03 新增：API 路由] ---
@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "OK", "endpoints": ["/api/books"]})

@app.route('/api/books', methods=['GET'])
def get_books():
    """這是前端會呼叫的 API 端點"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT title, price FROM books")
    rows = cursor.fetchall()
    conn.close()
    
    # 將資料庫的 tuple 格式轉換為前端好處理的 list of dicts
    data = [{"title": r[0], "price": r[1]} for r in rows]
    return jsonify(data)

if __name__ == "__main__":
    init_db()       # 初始化資料庫
    scrape_to_db()  # 先爬一次資料
    print("🚀 [Issue #03] API 伺服器啟動於 http://localhost:5000/api/books")
    app.run(port=5000, debug=True)