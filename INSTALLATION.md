# 📥 安裝與使用指南

完整的安裝教學，適合第一次使用的新手。

## ⚡ 快速開始（TL;DR）

```bash
# 1. 下載專案
git clone <專案網址>
cd test

# 2. 安裝套件
uv sync

# 3. 設定 API Key
copy .env.example .env
notepad .env  # 填入你的 Gemini API Key

# 4. 啟動程式
uv run streamlit run matcher_app.py
```

---

## 📋 系統需求

| 項目 | 需求 |
|------|------|
| **作業系統** | Windows 10/11, macOS, Linux |
| **Python** | 3.10 或以上 |
| **瀏覽器** | Google Chrome |
| **網路** | 穩定的網路連線 |
| **硬碟** | 至少 2GB 可用空間 |
| **RAM** | 建議 8GB 以上 |

---

## 🔧 詳細安裝步驟

### 步驟 1️⃣：安裝 Python

#### Windows 使用者

1. 前往 [Python 官網](https://www.python.org/downloads/)
2. 下載最新的 Python 3.10+ 版本
3. 執行安裝程式
4. **⚠️ 重要**：勾選「Add Python to PATH」選項
5. 點擊「Install Now」

驗證安裝：
```powershell
python --version
# 應該顯示：Python 3.10.x 或更高
```

#### macOS 使用者

使用 Homebrew：
```bash
# 如果還沒有 Homebrew，先安裝：
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安裝 Python
brew install python@3.10
```

#### Linux 使用者 (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.10 python3-pip python3-venv
```

---

### 步驟 2️⃣：安裝 Google Chrome

前往 [Chrome 官網](https://www.google.com/chrome/) 下載並安裝

> Chrome 用於網頁爬蟲功能，必須安裝。

---

### 步驟 3️⃣：安裝 uv（套件管理器）

uv 是比 pip 更快的 Python 套件管理器（可選但強烈推薦）。

#### Windows PowerShell

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

重新開啟終端機後驗證：
```bash
uv --version
```

> **如果不想安裝 uv**：可以使用傳統的 pip，將後續指令中的 `uv` 替換為 `pip` 即可。

---

### 步驟 4️⃣：下載專案

#### 方法 A：使用 Git（推薦）

```bash
# 如果還沒安裝 Git，先前往 https://git-scm.com/ 安裝

# 複製專案
git clone <你的專案 GitHub 網址>

# 進入專案資料夾
cd test
```

#### 方法 B：下載 ZIP 檔案

1. 在 GitHub 專案頁面點擊綠色的「Code」按鈕
2. 選擇「Download ZIP」
3. 解壓縮到你想要的資料夾
4. 開啟終端機並切換到該資料夾：
   ```bash
   cd "C:\Users\你的名字\Downloads\test"
   ```

---

### 步驟 5️⃣：安裝依賴套件

在專案資料夾中執行：

#### 使用 uv（推薦）

```bash
uv sync
```

#### 使用 pip

如果沒有 `requirements.txt`，先創建一個：
```bash
pip install streamlit selenium pandas torch sentence-transformers google-generativeai python-dotenv
```

或如果有 `requirements.txt`：
```bash
pip install -r requirements.txt
```

這個過程可能需要 5-10 分鐘，請耐心等待。

---

### 步驟 6️⃣：取得 Gemini API Key

#### 6.1 註冊並取得 API Key

1. 開啟 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 使用你的 Google 帳號登入
3. 點擊「**Create API Key**」按鈕
4. 選擇或創建一個 Google Cloud 專案
5. 複製產生的 API Key

API Key 格式範例：
```
AIzaSyDXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

> **💡 提示**：
> - API Key 是**完全免費**的
> - 有每日使用配額限制（對一般使用綽綽有餘）
> - 請妥善保管，不要分享給他人

#### 6.2 設定環境變數

**Windows：**
```powershell
# 複製範例檔案
copy .env.example .env

# 用記事本編輯
notepad .env
```

**macOS / Linux：**
```bash
# 複製範例檔案
cp .env.example .env

# 用文字編輯器開啟
nano .env
```

#### 6.3 填入 API Key

在 `.env` 檔案中，將內容修改為：

```env
GEMINI_API_KEY=AIzaSyDXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GEMINI_MODEL=gemini-2.5-flash
MODEL_PATH=models/models20-multilingual-e5-large_fold_1
```

⚠️ **注意**：
- 將 `AIzaSyDXXX...` 替換為你自己的 API Key
- 不要加引號
- 儲存後關閉編輯器

---

### 步驟 7️⃣：啟動應用程式

在專案資料夾執行：

```bash
uv run streamlit run matcher_app.py
```

或使用 Python：
```bash
streamlit run matcher_app.py
```

---

### 步驟 8️⃣：開始使用！

應用程式會自動在瀏覽器開啟。如果沒有，手動訪問：

- **本機網址**：http://localhost:8501
- **區域網路**：http://你的IP:8501

你會看到兩個選項：
1. 📁 **使用現有資料** - 如果已經有爬取的資料
2. 🕷️ **開始爬蟲** - 抓取新的商品資料

---

## 📚 使用教學

### 🕷️ 第一次使用：爬取商品

1. 選擇「**開始爬蟲**」
2. 填寫表單：
   - **搜尋關鍵字（中文）**：例如 `dyson 吸塵器`
   - **關鍵字（英文標記）**：例如 `dyson`
   - **抓取數量**：建議從 10 開始測試
   - **儲存模式**：選擇「覆蓋現有資料」
3. 點擊「🚀 開始爬取」
4. 等待爬蟲完成（約 2-5 分鐘）

### 🔍 比對商品

爬取完成後會自動跳轉，或手動選擇「使用現有資料」：

1. **側邊欄** - 選擇：
   - 商品類別（你剛才輸入的關鍵字）
   - 目標商品（MOMO 的某個商品）
2. 點擊「**🔍 啟動雙階段比對引擎**」
3. 查看比對結果：
   - ✅ **綠色卡片**：AI 判斷為相同商品
   - ❌ **紅色卡片**：AI 判斷為不同商品
   - 每個結果都有詳細的 AI 分析理由

---

## ❓ 常見問題與解決方法

### 問題 1：`python: command not found`

**原因**：Python 未安裝或未加入 PATH

**解決**：
1. 重新安裝 Python，勾選「Add Python to PATH」
2. 或手動將 Python 加入系統環境變數

---

### 問題 2：`streamlit: command not found`

**原因**：Streamlit 未安裝或虛擬環境未啟動

**解決**：
```bash
# 重新安裝
pip install streamlit

# 或使用 uv
uv add streamlit
```

---

### 問題 3：找不到模型路徑

**錯誤訊息**：
```
找不到模型路徑：models/models20-multilingual-e5-large_fold_1
```

**解決**：
- 程式會在首次執行時自動下載模型
- 需要穩定的網路連線
- 或手動下載模型並放到 `models/` 資料夾

---

### 問題 4：爬蟲失敗或抓不到商品

**可能原因**：
- Chrome 未安裝
- 網路連線不穩定
- 關鍵字太特殊

**解決**：
1. 確認 Chrome 已安裝
2. 檢查網路連線
3. 嘗試更換常見的關鍵字（如：iPhone, dyson）
4. 減少抓取數量

---

### 問題 5：API Key 錯誤

**錯誤訊息**：
```
請設定 Gemini API Key 才能使用 AI 驗證功能
```

**解決**：
1. 確認 `.env` 檔案在專案根目錄
2. 檢查 API Key 格式是否正確
3. 確認沒有多餘的空格或引號
4. 重新啟動應用程式

---

### 問題 6：無法從其他裝置訪問

**需求**：兩台裝置在同一個 WiFi 網路

**步驟**：
1. 找到你電腦的 IP 位址：
   ```powershell
   # Windows
   ipconfig
   
   # macOS/Linux
   ifconfig
   ```
2. 在其他裝置瀏覽器輸入：`http://你的IP:8501`
3. 如果還是無法連線，檢查防火牆設定

**Windows 開放防火牆**：
```powershell
New-NetFirewallRule -DisplayName "Streamlit" -Direction Inbound -LocalPort 8501 -Protocol TCP -Action Allow
```

---

## 🎓 更多資源

### 官方文件

- [Streamlit 文件](https://docs.streamlit.io/)
- [Google Gemini API 文件](https://ai.google.dev/docs)
- [Selenium 文件](https://selenium-python.readthedocs.io/)

### 教學影片（可選）

- YouTube 搜尋：「Streamlit 教學」
- Python 網頁爬蟲基礎

### 需要協助？

如果遇到問題：
1. 先檢查本文件的「常見問題」章節
2. 查看錯誤訊息並 Google 搜尋
3. 在 GitHub 專案頁面開啟 Issue
4. 附上錯誤訊息截圖和系統資訊

---

## 🚀 下次使用

完成安裝後，之後每次使用只需：

```bash
# 1. 切換到專案資料夾
cd 你的專案路徑

# 2. 啟動
uv run streamlit run matcher_app.py
```

就這麼簡單！

---

## 🛑 停止程式

在終端機按 `Ctrl + C`

---

## 📝 建議

### 給第一次使用的新手

1. 先用少量商品測試（10 筆）
2. 選擇常見的商品關鍵字（如：iPhone, dyson）
3. 確保網路連線穩定
4. 不要關閉終端機視窗

### 進階使用者

1. 可以修改 `matcher_app.py` 調整相似度門檻
2. 使用「追加模式」累積多個關鍵字的資料
3. 定期備份 CSV 檔案
4. 可以將程式部署到雲端服務（Streamlit Cloud, Heroku 等）

---

**祝你使用愉快！** 🎉
