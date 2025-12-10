# 快速部署指南

## 🚀 立即部署到 Railway（推薦）

### 1. 上傳到 GitHub
```bash
# 初始化 Git（如果還沒有）
git init

# 添加所有檔案
git add .

# 提交變更
git commit -m "準備部署到雲端"

# 連接到您的 GitHub repository
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 推送到 GitHub
git push -u origin main
```

### 2. 部署到 Railway
1. 前往 https://railway.app/
2. 點擊 "Start a New Project"
3. 選擇 "Deploy from GitHub repo"
4. 選擇您的 repository
5. 設定環境變數：
   - `GEMINI_API_KEY` = 您的 Gemini API 金鑰
6. 等待部署完成（約 10-15 分鐘）

### 3. 完成！
Railway 會自動提供一個公開網址，例如：
`https://your-app-name.railway.app`

---

## ⚠️ 重要提醒

### 模型檔案處理 ✅ 已解決！
程式已修改為**自動從 Hugging Face 下載模型**，不需要上傳 `models/` 資料夾！

**首次啟動時：**
- 程式會自動從 Hugging Face 下載 `intfloat/multilingual-e5-large` 模型
- 下載時間約 2-5 分鐘（取決於網路速度）
- 下載後會快取，之後啟動不需要重新下載

**`.gitignore` 已設定忽略 `models/` 資料夾**，不會上傳到 GitHub。

---

## 💰 預估費用

### Railway.app
- **免費試用**: $5 credit（可用約 1 個月）
- **Developer 方案**: $5/月（建議，512MB RAM）
- **Hobby 方案**: $10/月（1GB RAM，更穩定）

**建議配置**：
- RAM: 至少 512MB（建議 1GB）
- CPU: 0.5 vCPU
- Storage: 1GB

---

## 🔧 疑難排解

### Chrome 啟動失敗
確認 Dockerfile 中已正確安裝 Chrome。

### 記憶體不足錯誤
1. 減少爬取商品數量（例如從 50 降到 20）
2. 升級到更高的方案
3. 修改程式碼，分批處理

### 部署時間過長
首次部署需要安裝 Chrome 和所有依賴，耐心等待約 15 分鐘。

### 找不到環境變數
確認在 Railway 的 Variables 設定中已添加 `GEMINI_API_KEY`。

---

## 📝 檢查清單

部署前確認：
- [ ] 已將 `.env` 加入 `.gitignore`（不上傳敏感資訊）✅
- [ ] 已在 Railway 設定環境變數 `GEMINI_API_KEY`
- [ ] 已啟用 Chrome 無頭模式（已完成）✅
- [ ] 已準備好 Dockerfile 和相關設定檔（已完成）✅
- [ ] **不需要上傳模型檔案**（程式會自動下載）✅

---

## 🎉 部署成功後

使用者可以：
1. 開啟您的應用網址
2. 點擊「🔍 搜尋新商品」
3. 輸入關鍵字並設定爬取數量
4. 等待爬蟲完成
5. 選擇商品進行比對

---

需要詳細的步驟說明，請參考 `DEPLOYMENT.md` 文件。
