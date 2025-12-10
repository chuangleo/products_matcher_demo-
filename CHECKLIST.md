# ✅ 安裝檢查清單

使用此清單確保所有步驟都正確完成。

---

## 📋 安裝前檢查

- [ ] 電腦已連接網路
- [ ] 至少有 2GB 可用硬碟空間
- [ ] RAM 至少 4GB（建議 8GB）

---

## 🔧 軟體安裝檢查

### Python

- [ ] 已安裝 Python 3.10 或更高版本
- [ ] 驗證指令：`python --version`
- [ ] 顯示版本號（例如：Python 3.10.x）

### Google Chrome

- [ ] 已安裝 Google Chrome 瀏覽器
- [ ] 能正常開啟 Chrome

### uv 或 pip

- [ ] 已安裝 uv（推薦）或可以使用 pip
- [ ] 驗證指令：`uv --version` 或 `pip --version`

---

## 📥 專案下載檢查

- [ ] 已下載專案（Git clone 或 ZIP）
- [ ] 解壓縮到指定資料夾
- [ ] 能在終端機切換到專案資料夾
- [ ] 資料夾中包含以下檔案：
  - [ ] `matcher_app.py`
  - [ ] `product_scraper.py`
  - [ ] `.env.example`
  - [ ] `requirements.txt`

---

## 📦 依賴套件安裝檢查

- [ ] 已執行 `uv sync` 或 `pip install -r requirements.txt`
- [ ] 沒有出現錯誤訊息
- [ ] 安裝完成顯示成功訊息

測試指令：
```bash
python -c "import streamlit; import selenium; import pandas; print('✅ 所有套件安裝成功')"
```

- [ ] 顯示「✅ 所有套件安裝成功」

---

## 🔑 API Key 設定檢查

### 取得 API Key

- [ ] 已前往 https://makersuite.google.com/app/apikey
- [ ] 使用 Google 帳號登入
- [ ] 成功創建 API Key
- [ ] 已複製 API Key

### 設定 .env 檔案

- [ ] 已複製 `.env.example` 為 `.env`
- [ ] 已開啟 `.env` 檔案
- [ ] 已填入 API Key（格式：`GEMINI_API_KEY=AIzaSy...`）
- [ ] 已儲存檔案

驗證 .env 檔案：
```bash
# Windows
type .env

# macOS/Linux
cat .env
```

- [ ] 確認內容包含你的 API Key

---

## 🚀 啟動測試

### 啟動程式

- [ ] 已執行 `uv run streamlit run matcher_app.py` 或 `streamlit run matcher_app.py`
- [ ] 終端機顯示「You can now view your Streamlit app...」
- [ ] 顯示本機網址：http://localhost:8501
- [ ] 瀏覽器自動開啟或手動訪問網址

### 介面檢查

- [ ] 網頁正常載入
- [ ] 看到「AI 跨平台商品比對系統」標題
- [ ] 看到兩個選項：「使用現有資料」和「開始爬蟲」
- [ ] 沒有出現紅色錯誤訊息

---

## 🧪 功能測試

### 測試爬蟲功能

- [ ] 點擊「開始爬蟲」
- [ ] 填寫表單：
  - [ ] 搜尋關鍵字：`iPhone`
  - [ ] 英文標記：`iphone`
  - [ ] 抓取數量：`10`
- [ ] 點擊「開始爬取」
- [ ] 進度條正常顯示
- [ ] 顯示「成功抓取 X 筆商品」

### 測試比對功能

- [ ] 自動跳轉到比對頁面或點擊「使用現有資料」
- [ ] 側邊欄顯示商品類別
- [ ] 可以選擇商品
- [ ] 點擊「啟動雙階段比對引擎」
- [ ] 顯示比對進度
- [ ] 顯示比對結果（綠色或紅色卡片）
- [ ] 結果包含 AI 分析理由

---

## ✅ 完成！

如果以上所有項目都已勾選，恭喜你安裝成功！

### 🎯 下一步

- 嘗試不同的關鍵字
- 增加抓取數量
- 使用「追加模式」累積更多資料

---

## ❌ 如果有未勾選的項目

請參考以下文件：

- **安裝問題**：查看 [INSTALLATION.md](./INSTALLATION.md)
- **使用問題**：查看 [QUICKSTART.md](./QUICKSTART.md)
- **技術問題**：查看 [README.md](./README.md)

或在 GitHub 開啟 Issue 尋求協助。

---

**記得儲存這個清單，供日後參考！** 📌
