import sqlite3
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from flask_cors import CORS # 務必確認已執行 pip install flask-cors

app = Flask(__name__)
CORS(app) # 允許 Vue 前端存取 API

app.config['JSON_AS_ASCII'] = False

DB_NAME = "travel_data.db"

# --- [Issue #01 & #02 的邏輯保留] ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price TEXT)')
    conn.commit()
    conn.close()

import time # 導入時間模組，避免爬太快被鎖 IP

def scrape_to_db():
    base_url = "https://www.tenlong.com.tw"
    current_path = "/zh_tw/recent" # 起始路徑
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books") # 清空舊資料
    
    count = 0
    page_count = 1

    while current_path:
        print(f"📄 正在爬取第 {page_count} 頁: {base_url + current_path}")
        
        headers = {"User-Agent": "Mozilla/5.0 ..."}
        response = requests.get(base_url + current_path, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. 抓取當前頁面的書籍
        books_data = soup.select(".list-wrapper ul li")
        for book in books_data:
            title_el = book.select_one("a.title") or book.select_one(".title")
            price_el = book.select_one(".pricing") or book.select_one(".price")
            if title_el:
                cursor.execute("INSERT INTO books (title, price) VALUES (?, ?)", 
                               (title_el.text.strip(), price_el.text.strip() if price_el else "N/A"))
                count += 1
        
        # 2. 【核心】尋找「下一頁」的連結
        # 根據你的結構：div .pagination 裡面的 a 標籤
        # 通常「下一頁」會是一個標示為 ">" 或 "Next" 的 a 標籤，或是目前頁碼的下一個
        pagination_links = soup.select(".pagination a")
        next_page_link = None
        
        for link in pagination_links:
            # 判斷邏輯：尋找文字包含 "下一頁" 或 ">" 的連結
            if ">" in link.text or "下一頁" in link.text:
                next_page_link = link.get("href")
                break
        
        # 3. 更新路徑或結束迴圈
        if next_page_link and page_count < 5: # 為了安全和測試，我們先限制抓 5 頁就好
            current_path = next_page_link
            page_count += 1
            time.sleep(1) # 工程師禮儀：每頁間隔 1 秒
        else:
            current_path = None # 沒有下一頁了，停止迴圈

    conn.commit()
    conn.close()
    print(f"🚩 [Issue #02.2] 多頁爬取完成！總共抓取 {count} 筆書籍存入資料庫。")

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