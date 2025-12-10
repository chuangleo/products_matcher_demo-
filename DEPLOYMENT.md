# 雲端部署說明文件

## 部署到 Railway.app（推薦）

### 步驟 1: 準備 GitHub Repository
1. 在 GitHub 建立新的 repository
2. 將專案檔案上傳到 GitHub：
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 步驟 2: 部署到 Railway
1. 前往 https://railway.app/
2. 註冊/登入帳號（可用 GitHub 登入）
3. 點擊 "New Project"
4. 選擇 "Deploy from GitHub repo"
5. 選擇您的 repository
6. Railway 會自動偵測到 Dockerfile 並開始部署

### 步驟 3: 設定環境變數
在 Railway 專案設定中添加環境變數：
- `GEMINI_API_KEY`: 您的 Google Gemini API 金鑰
- `PORT`: 8501（Railway 會自動設定）

### 步驟 4: 等待部署完成
- 首次部署約需 10-15 分鐘（需要安裝 Chrome）
- 部署完成後，Railway 會提供一個公開網址

---

## 部署到 Render（替代方案）

### 步驟 1: 準備 GitHub Repository（同上）

### 步驟 2: 部署到 Render
1. 前往 https://render.com/
2. 註冊/登入帳號
3. 點擊 "New +" → "Web Service"
4. 連接 GitHub repository
5. 設定如下：
   - **Name**: 自訂名稱
   - **Environment**: Docker
   - **Region**: Singapore（最接近台灣）
   - **Instance Type**: Free（或付費方案以獲得更好效能）

### 步驟 3: 設定環境變數
在 Render 的 Environment 設定中添加：
- `GEMINI_API_KEY`: 您的 Google Gemini API 金鑰

### 步驟 4: 部署
- 點擊 "Create Web Service"
- 等待部署完成（約 15-20 分鐘）

---

## 重要注意事項

### 1. Chrome 和 ChromeDriver
- Dockerfile 已自動安裝 Chrome
- 不需要手動下載 ChromeDriver

### 2. 記憶體限制
- 免費方案記憶體有限（約 512MB-1GB）
- Selenium + 模型可能會超過限制
- 建議使用付費方案以確保穩定運行

### 3. 執行時間限制
- 爬蟲可能需要較長時間
- 免費方案可能有執行時間限制
- 建議一次爬取的商品數量不要太多（例如限制在 20-30 個）

### 4. 模型檔案
- `models/` 資料夾需要完整上傳到 GitHub
- 檔案較大可能需要使用 Git LFS
- 或考慮在部署時從雲端下載模型

### 5. API 金鑰安全
- 絕對不要將 `.env` 檔案上傳到 GitHub
- 使用平台的環境變數設定功能
- 在 `.gitignore` 中加入 `.env`

---

## 檔案檢查清單

部署前確認以下檔案已準備好：
- ✅ `Dockerfile` - Docker 容器設定
- ✅ `requirements.txt` - Python 依賴
- ✅ `Procfile` - 啟動指令（Render 使用）
- ✅ `.streamlit/config.toml` - Streamlit 設定
- ✅ `matcher_app.py` - 主程式
- ✅ `product_scraper.py` - 爬蟲程式
- ✅ `.gitignore` - 忽略不需要的檔案

---

## 預估成本

### Railway.app
- 免費方案：$5 credit（約可用 1-2 個月）
- Hobby 方案：$5/月（建議）
- Pro 方案：$20/月

### Render
- 免費方案：有限制但可使用
- Starter 方案：$7/月（建議）
- Standard 方案：$25/月

---

## 疑難排解

### 問題 1: Chrome 啟動失敗
確保 Dockerfile 中的 Chrome 安裝指令正確執行。

### 問題 2: 記憶體不足
- 減少一次爬取的商品數量
- 升級到付費方案
- 優化模型載入（使用較小的模型）

### 問題 3: 部署很慢
首次部署需要安裝 Chrome 和所有依賴，需要耐心等待。

### 問題 4: 找不到 ChromeDriver
確認 `product_scraper.py` 中的 Chrome 設定使用系統安裝的 Chrome。

---

## 聯絡資訊

如有部署問題，請檢查：
1. Railway/Render 的部署日誌
2. Streamlit 應用的終端輸出
3. 環境變數是否正確設定
