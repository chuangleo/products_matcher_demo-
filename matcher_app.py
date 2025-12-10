import streamlit as st
import pandas as pd
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
import json
import time
import sys
from product_scraper import fetch_products_for_momo, fetch_products_for_pchome, save_to_csv
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# ============= 頁面配置 =============
st.set_page_config(
    page_title="購物比價小幫手",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============= 全域樣式設計 (CSS) =============
st.markdown("""
    <style>
    /* 引入 Google Fonts: Noto Sans TC */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
        color: #333;
    }

    /* 背景優化 */
    .stApp {
        background-color: #f4f7f6;
    }

    /* 標題樣式 */
    h1, h2, h3 {
        font-weight: 700 !important;
        color: #2c3e50;
    }

    /* 側邊欄美化 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02);
    }

    /* 按鈕優化 */
    .stButton>button {
        border-radius: 50px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 7px 14px rgba(50, 50, 93, 0.1), 0 3px 6px rgba(0, 0, 0, 0.08);
    }
    
    /* 主要按鈕 (Primary) */
    button[kind="primary"] {
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        border: none;
    }

    /* 自定義商品卡片容器 */
    .product-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        margin-bottom: 24px;
        border: 1px solid #edf2f7;
        transition: transform 0.2s ease;
    }
    .product-card:hover {
        border-color: #cbd5e0;
    }

    /* 平台標籤 */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 12px;
    }
    .badge-momo {
        background-color: #fff0f5;
        color: #d61f69;
        border: 1px solid #fecdd3;
    }
    .badge-pchome {
        background-color: #eef2ff;
        color: #3730a3;
        border: 1px solid #c7d2fe;
    }

    /* 價格顯示 */
    .price-tag {
        font-family: 'Roboto', sans-serif;
        font-size: 1.5rem;
        font-weight: 800;
        color: #e53e3e;
        margin: 8px 0;
    }
    .price-symbol {
        font-size: 0.9rem;
        color: #718096;
        font-weight: normal;
    }

    /* 結果比對卡片 */
    .match-result-container {
        background: linear-gradient(to right, #ffffff, #fafffd);
        border-left: 6px solid #48bb78;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        padding: 20px;
        margin-top: 20px;
    }
    
    .ai-reasoning-box {
        background-color: #f7fafc;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 12px;
        border-left: 4px solid #4299e1;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #2d3748;
    }

    /* 進度條樣式微調 */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
    }
    
    /* 圖片容器 */
    .img-container {
        width: 100%;
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        background-color: #fff;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .img-container img {
        max-height: 100%;
        max-width: 100%;
        object-fit: contain;
    }
    </style>
""", unsafe_allow_html=True)

# ============= 安全配置：從環境變數或 Streamlit secrets 載入 =============
def get_api_key():
    """
    安全地獲取 API Key
    優先順序：Streamlit Secrets > 環境變數 > 側邊欄輸入
    """
    # 1. 嘗試從 Streamlit Secrets 讀取（部署到 Streamlit Cloud 時使用）
    try:
        if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
            return st.secrets['GEMINI_API_KEY']
    except:
        pass
    
    # 2. 嘗試從環境變數讀取（本地開發時使用）
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        return api_key
    
    # 3. 如果都沒有，返回 None（稍後會要求用戶輸入）
    return None

GEMINI_API_KEY = get_api_key()
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

# 模型路徑：優先使用本地模型，如果不存在則從 Hugging Face 下載
MODEL_PATH = os.getenv('MODEL_PATH', os.path.join("models", "models20-multilingual-e5-large_fold_1"))
# 您的 Hugging Face 模型
HUGGINGFACE_MODEL_NAME = os.getenv('HUGGINGFACE_MODEL_NAME', 'leochuang/multilingual-e5-large-custom')
# 如果模型在 Google Drive，提供分享連結（選用）
GDRIVE_MODEL_URL = os.getenv('GDRIVE_MODEL_URL', None)

# 如果沒有 API Key，顯示警告並要求輸入
if not GEMINI_API_KEY:
    st.sidebar.warning("⚠️ 未設定 Gemini API Key")
    GEMINI_API_KEY = st.sidebar.text_input(
        "請輸入 Gemini API Key", 
        type="password",
        help="API Key 不會被保存，僅在當前會話中使用"
    )
    if not GEMINI_API_KEY:
        st.error("請設定 Gemini API Key 才能使用 AI 驗證功能")
        st.info("""
        **設定方式：**
        1. 在專案目錄創建 `.env` 檔案
        2. 添加：`GEMINI_API_KEY=你的API金鑰`
        3. 重新啟動應用程式
        """)
        st.stop()

genai.configure(api_key=GEMINI_API_KEY)

@st.cache_resource
def load_model(local_path=None, hf_model_name=None, gdrive_url=None):
    """
    載入 Sentence Transformer 模型
    優先使用本地模型，如果不存在則從其他來源下載
    
    Args:
        local_path: 本地模型路徑
        hf_model_name: Hugging Face 模型名稱
        gdrive_url: Google Drive 分享連結（選用）
    """
    # 先嘗試載入本地模型
    if local_path and os.path.exists(local_path):
        try:
            st.info(f"📦 載入本地模型: {local_path}")
            return SentenceTransformer(local_path)
        except Exception as e:
            st.warning(f"⚠️ 本地模型載入失敗: {e}")
    
    # 如果有 Google Drive 連結，先嘗試從 Google Drive 下載
    if gdrive_url:
        try:
            import gdown
            import zipfile
            import shutil
            
            st.info(f"🌐 從 Google Drive 下載模型...")
            
            # 下載到暫存資料夾
            download_path = "temp_model.zip"
            extract_path = "temp_model"
            
            gdown.download(gdrive_url, download_path, quiet=False, fuzzy=True)
            
            # 解壓縮
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # 載入模型
            model = SentenceTransformer(extract_path)
            
            # 清理暫存檔案
            os.remove(download_path)
            shutil.rmtree(extract_path)
            
            st.success("✅ 從 Google Drive 下載並載入成功！")
            return model
        except Exception as e:
            st.warning(f"⚠️ 從 Google Drive 下載失敗: {e}")
    
    # 如果本地模型不存在或載入失敗，從 Hugging Face 下載
    if hf_model_name:
        try:
            st.info(f"🌐 從 Hugging Face 下載模型: {hf_model_name}（首次下載需要幾分鐘）")
            model = SentenceTransformer(hf_model_name)
            st.success("✅ 模型下載並載入成功！")
            return model
        except Exception as e:
            st.error(f"❌ 模型下載失敗: {e}")
            return None
    
    st.error("❌ 無法載入模型：本地模型不存在且未指定其他來源")
    return None

@st.cache_data
def load_local_data():
    """載入本地預設資料"""
    # 先嘗試從根目錄讀取
    momo_path = "momo.csv"
    pchome_path = "pchome.csv"
    
    # 如果根目錄沒有，再試 dataset/test/
    if not os.path.exists(momo_path):
        momo_path = os.path.join("dataset", "test", "momo.csv")
        pchome_path = os.path.join("dataset", "test", "pchome.csv")
    
    try:
        # 檢查檔案是否為空
        momo_empty = os.path.getsize(momo_path) == 0 if os.path.exists(momo_path) else True
        pchome_empty = os.path.getsize(pchome_path) == 0 if os.path.exists(pchome_path) else True
        
        if momo_empty or pchome_empty:
            # 如果檔案為空，返回空的 DataFrame
            return pd.DataFrame(), pd.DataFrame()
        
        # 定義 CSV 欄位名稱
        column_names = [
            'id', 'sku', 'title', 'image', 'url', 'platform', 
            'connect', 'price', 'uncertainty_problem', 'query', 
            'annotator', 'created_at', 'updated_at'
        ]
        
        # 讀取 CSV，檢查第一行是否為 header
        # 策略：讀取第一行，看第一個欄位是否為 'id'（header）或數字（資料）
        with open(momo_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            momo_has_header = first_line.startswith('id,') or first_line.startswith('"id"')
        
        with open(pchome_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            pchome_has_header = first_line.startswith('id,') or first_line.startswith('"id"')
        
        # 根據是否有 header 來讀取
        if momo_has_header:
            momo_df = pd.read_csv(momo_path, sep=',')
        else:
            momo_df = pd.read_csv(momo_path, sep=',', names=column_names, header=None)
        
        if pchome_has_header:
            pchome_df = pd.read_csv(pchome_path, sep=',')
        else:
            pchome_df = pd.read_csv(pchome_path, sep=',', names=column_names, header=None)
        
        # 移除 dtype=str，讓 pandas 自動推斷類型
        # 確保價格欄位是數值型
        if 'price' in momo_df.columns:
            momo_df['price'] = pd.to_numeric(momo_df['price'], errors='coerce')
        if 'price' in pchome_df.columns:
            pchome_df['price'] = pd.to_numeric(pchome_df['price'], errors='coerce')
            
        return momo_df, pchome_df
    except Exception as e:
        st.error(f"資料載入失敗: {e}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame(), pd.DataFrame()

def prepare_text(title, platform):
    return ("query: " if platform == 'momo' else "passage: ") + str(title)

def get_single_embedding(model, text):
    return model.encode([text], convert_to_tensor=True).cpu()

def get_batch_embeddings(model, texts):
    return model.encode(texts, convert_to_tensor=True).cpu()

def gemini_verify_match(momo_title, pchome_title, similarity_score):
    prompt = f"""你是一個電商產品匹配專家。請判斷以下兩個商品是否為同一個產品。

商品 A (Momo)：{momo_title}
商品 B (PChome)：{pchome_title}
第一階段相似度：{similarity_score:.4f}

請嚴格依照以下規則判斷：

**核心匹配規則**：
1. **品牌與型號**：必須完全一致（注意：不同語言的品牌名稱，如 "Logitech" 和 "羅技" 是同一品牌）。
2. **規格變體**：主要規格（如容量 128G vs 256G）不同視為「不同商品」。
3. **顏色差異**：**相同產品的不同顏色，一律視為「相同商品」**（例如：黑色 iPhone 和白色 iPhone 視為同一商品，請忽略顏色差異）。

**嚴格排除規則（以下情況視為不同商品，絕對不可匹配）**：
1. **組合包 vs 單品**：
   - 單品 ≠ 組合包/套組/多入組
   - 關鍵字識別：「組合」「套組」「×2」「×3」「多入」「+」「贈」「送」
2. **原廠 vs 副廠/相容配件**：
   - 原廠商品 ≠ 副廠/相容/通用商品
   - 關鍵字識別：「副廠」「相容」「適用」「通用」「compatible」
3. **限量/特殊版本 vs 一般版本**：
   - 一般商品 ≠ 限量/福利品/特殊版本
   - 即使兩邊都是福利品，也建議視為不同商品（狀況可能不同）

請回傳純 JSON 格式：
{{
    "is_match": true 或 false,
    "confidence": "high" 或 "medium" 或 "low",
    "reasoning": "請用繁體中文簡述判斷理由 (30字以內)"
}}
"""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        text = response.text.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        return json.loads(text)
    except Exception as e:
        return {"is_match": False, "confidence": "low", "reasoning": f"API 錯誤: {str(e)}"}

# ============= 初始化 Session State =============
if 'momo_df' not in st.session_state:
    st.session_state.momo_df, st.session_state.pchome_df = load_local_data()
if 'scraping_done' not in st.session_state:
    st.session_state.scraping_done = False

# ============= 搜尋商品 Dialog 函數 =============
@st.dialog("🔍 搜尋商品", width="large")
def search_products_dialog():
    st.markdown("輸入您想找的商品關鍵字，系統會自動在 MOMO 和 PChome 搜尋")
    
    with st.form("scraping_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            keyword = st.text_input("🔍 商品類別（中文）", placeholder="例如：dyson 吸塵器")
        
        with col2:
            english_keyword = st.text_input("🏷️ 商品英文名稱", placeholder="例如：dyson", help="方便系統分類儲存，可與中文一樣或簡寫")
        
        max_products = st.slider("🛍️ 每個網站搜尋數量", min_value=10, max_value=100, value=50, step=10, help="建議 50 件，數量越多搜尋時間越長")
        
        # 搜尋模式：加入到現有資料
        append_mode = True
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit_scraping = st.form_submit_button("🚀 開始搜尋商品", use_container_width=True, type="primary")
        with col_btn2:
            cancel_btn = st.form_submit_button("取消", use_container_width=True)
    
    if cancel_btn:
        st.rerun()
    
    # 處理搜尋
    if submit_scraping:
        if not keyword or not english_keyword:
            st.error("請填寫商品類別和英文名稱！")
        else:
            st.markdown("---")
            
            # MOMO 爬蟲
            st.markdown("#### 📦 正在 MOMO 購物網搜尋商品...")
            momo_progress_bar = st.progress(0)
            momo_status = st.empty()
            
            def momo_callback(current, total, message):
                progress = min(current / total, 1.0)
                momo_progress_bar.progress(progress)
                momo_status.info(message)
            
            with st.spinner("在 MOMO 搜尋中，請稍候..."):
                momo_products = fetch_products_for_momo(keyword, max_products, momo_callback)
                save_to_csv(momo_products, "momo.csv", english_keyword, append_mode=append_mode)
            
            if momo_products:
                st.success(f"✅ MOMO: 找到 {len(momo_products)} 件商品")
            else:
                st.warning("⚠️ MOMO: 沒有找到相關商品")
            
            st.markdown("---")
            
            # PChome 爬蟲
            st.markdown("#### 📦 正在 PChome 購物網搜尋商品...")
            pchome_progress_bar = st.progress(0)
            pchome_status = st.empty()
            
            def pchome_callback(current, total, message):
                progress = min(current / total, 1.0)
                pchome_progress_bar.progress(progress)
                pchome_status.info(message)
            
            with st.spinner("在 PChome 搜尋中，請稍候..."):
                pchome_products = fetch_products_for_pchome(keyword, max_products, pchome_callback)
                save_to_csv(pchome_products, "pchome.csv", english_keyword, append_mode=append_mode)
            
            if pchome_products:
                st.success(f"✅ PChome: 找到 {len(pchome_products)} 件商品")
            else:
                st.warning("⚠️ PChome: 沒有找到相關商品")
            
            st.markdown("---")
            
            # 重新載入資料
            st.cache_data.clear()
            st.session_state.momo_df, st.session_state.pchome_df = load_local_data()
            
            if not st.session_state.momo_df.empty or not st.session_state.pchome_df.empty:
                st.success("✅ 搜尋完成！正在重新載入頁面...")
                st.rerun()
            else:
                st.error("整理商品清單時發生錯誤，請重試")

# ============= UI 介面 =============

# 頁首區塊
col_header_1, col_header_2 = st.columns([3, 1])
with col_header_1:
    st.markdown("# 🛒 購物比價小幫手")
    st.markdown("### 幫您在 MOMO 和 PChome 找到相同商品")
with col_header_2:
    st.markdown("""
    <div style="text-align: right; color: #718096;">
        <small>系統狀態</small><br>
        <span style="color: #48bb78; font-weight: bold;">● 運作中</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============= 比對模式（唯一頁面）=============
# 載入資料
momo_df = st.session_state.momo_df
pchome_df = st.session_state.pchome_df

# 如果沒有資料，顯示歡迎頁面
if momo_df.empty:
    st.markdown("### 🔍 歡迎使用購物比價小幫手")
    st.markdown("請先搜尋商品，系統會自動在 MOMO 和 PChome 尋找相同的商品讓您比價。")
    st.markdown("---")
    
    if st.button("🔍 開始搜尋商品", use_container_width=True, type="primary"):
        search_products_dialog()
    
    st.stop()

# 載入資源
with st.spinner("系統準備中，請稍候..."):
    model = load_model(
        local_path=MODEL_PATH, 
        hf_model_name=HUGGINGFACE_MODEL_NAME,
        gdrive_url=GDRIVE_MODEL_URL
    )

if model is None:
    st.error("❌ 無法載入模型，請檢查設定或網路連線")
    st.stop()

# ============= 側邊欄設計 =============
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331966.png", width=60)
    st.markdown("### 🎯 開始比對商品")
    
    # 搜尋按鈕
    if st.button("🔍 搜尋新商品", use_container_width=True):
        search_products_dialog()
    
    st.markdown("---")
    
    # 檢查 DataFrame 是否為空或沒有 'query' 欄位
    if momo_df.empty or 'query' not in momo_df.columns:
        st.warning("⚠️ 目前沒有商品資料，請點擊上方「🔍 搜尋新商品」按鈕開始搜尋商品。")
        st.stop()
    
    # 顯示商品類別統計
    unique_queries = sorted(momo_df['query'].unique().tolist())
    momo_count = len(momo_df)
    pchome_count = len(pchome_df)
    st.success(f"📊 已載入 {len(unique_queries)} 個商品類別\nMOMO: {momo_count} 件 | PChome: {pchome_count} 件")
    
    st.markdown("---")
    st.markdown("#### 步驟 1：選擇商品類別")
    selected_query = st.selectbox(
        "選擇要比對的商品類別",
        unique_queries,
        help="選擇您想要比對的商品類別"
    )
    
    # 篩選該類別的 Momo 商品
    momo_products_in_query = momo_df[momo_df['query'] == selected_query].reset_index(drop=True)
    pchome_candidates_pool = pchome_df[pchome_df['query'] == selected_query].reset_index(drop=True)
    
    if momo_products_in_query.empty:
        st.warning("這個類別沒有商品")
        st.stop()

    st.markdown("---")
    st.markdown("#### ℹ️ 系統設定")
    # 固定相似度門檻為 0.739465
    threshold = 0.739465
    st.info(f"🎯 比對精準度：{threshold:.2%}")

# ============= 主內容區 =============

col_main_left, col_main_right = st.columns([1, 2], gap="large")

# --- 左側：選擇 MOMO 商品（可捲動選單）---
with col_main_left:
    st.markdown("### 🎯 選擇 MOMO 商品")
    
    # 使用 selectbox 顯示完整商品資訊
    momo_display_options = ["-- 請選擇要比對的商品 --"]  # 添加預設選項
    for i, row in momo_products_in_query.iterrows():
        price_str = f"NT$ {row.get('price', 'N/A')}"
        # 顯示編號、完整標題和價格
        display_text = f"[{i+1}] {row['title']} - {price_str}"
        momo_display_options.append(display_text)
    
    selected_display = st.selectbox(
        "請選擇商品：",
        momo_display_options,
        label_visibility="collapsed",
        key="momo_product_selector"
    )
    
    # 檢查是否選擇了預設選項
    if selected_display == "-- 請選擇要比對的商品 --":
        st.info("👆 請從下拉選單中選擇一個商品開始比對")
        st.stop()  # 停止執行後續代碼
    
    # 找出選中的商品索引（減1因為有預設選項）
    selected_momo_idx = momo_display_options.index(selected_display) - 1
    selected_momo_row = momo_products_in_query.iloc[selected_momo_idx]
    
    # 顯示選中商品的詳細卡片
    st.markdown("---")
    
    # 使用 HTML 構建精美卡片
    st.markdown(f"""
    <div class="product-card">
        <div class="badge badge-momo">MOMO 購物網</div>
        <div class="img-container">
            <img src="{selected_momo_row.get('image', '')}" onerror="this.src='https://via.placeholder.com/200x200?text=No+Image'">
        </div>
        <h4 style="margin-top:15px; line-height:1.4;">{selected_momo_row['title']}</h4>
        <div class="price-tag"><span class="price-symbol">NT$</span> {selected_momo_row.get('price', 'N/A')}</div>
        <div style="color:#718096; font-size:0.9rem; margin-top:10px;">
            <strong>ID:</strong> {selected_momo_row.get('id', 'N/A')}<br>
            <strong>SKU:</strong> {selected_momo_row.get('sku', 'N/A')}
        </div>
        <a href="{selected_momo_row.get('url', '#')}" target="_blank" 
           style="display:block; text-align:center; margin-top:20px; background:#f7f9fc; color:#4a5568; padding:8px; border-radius:8px; text-decoration:none; font-weight:bold; font-size:0.9rem;">
           開啟商品頁面 ↗
        </a>
    </div>
    """, unsafe_allow_html=True)

# --- 右側：Action & Results ---
with col_main_right:
    st.markdown("### ⚡ 在 PChome 尋找相同商品")
    
    # 初始化 session state 來追蹤上次比對的商品
    if 'last_matched_product' not in st.session_state:
        st.session_state.last_matched_product = None
    
    # 建立當前商品的唯一識別
    current_product_id = f"{selected_query}_{selected_momo_idx}"
    
    # 檢查是否為新選擇的商品（不同於上次比對的商品）
    should_auto_match = (st.session_state.last_matched_product != current_product_id)
    
    if should_auto_match:
        # 自動開始比對
        st.session_state.last_matched_product = current_product_id
        
        # 準備資料
        pchome_candidates = pchome_candidates_pool.copy()
        if len(pchome_candidates) > 100:
            pchome_candidates = pchome_candidates.head(100)

        # 進度容器
        with st.container():
            # Stage 1
            progress_text = "第一階段：快速篩選相似商品..."
            my_bar = st.progress(0, text=progress_text)
            
            # 計算 Embedding
            momo_text = prepare_text(selected_momo_row['title'], 'momo')
            pchome_texts = [prepare_text(row['title'], 'pchome') for _, row in pchome_candidates.iterrows()]
            
            # 模擬進度條動畫效果
            my_bar.progress(20, text="正在分析商品特徵...")
            momo_emb = get_single_embedding(model, momo_text)
            pchome_embs = get_batch_embeddings(model, pchome_texts)
            
            my_bar.progress(60, text="正在比對商品相似度...")
            momo_emb = torch.nn.functional.normalize(momo_emb, p=2, dim=1)
            pchome_embs = torch.nn.functional.normalize(pchome_embs, p=2, dim=1)
            similarities = torch.mm(momo_emb, pchome_embs.T).numpy().flatten()
            
            pchome_candidates['similarity'] = similarities
            stage1_matches = pchome_candidates[pchome_candidates['similarity'] >= threshold].sort_values(by='similarity', ascending=False)
            
            my_bar.progress(100, text="第一階段完成！")
            time.sleep(0.5)
            my_bar.empty()

        # 顯示結果區
        if stage1_matches.empty:
            st.warning("⚠️ 第一階段沒有找到相似的商品。")
        else:
            candidates_to_verify = stage1_matches
            
            st.markdown(f"""
            <div style="background:#e6fffa; color:#2c7a7b; padding:10px 15px; border-radius:8px; margin-bottom:20px; border:1px solid #b2f5ea;">
                <strong>✅ 第一階段完成</strong>：找到 <b>{len(stage1_matches)}</b> 件可能相同的商品，正在進行詳細比對...
            </div>
            """, unsafe_allow_html=True)

            # Stage 2 Loop
            verified_count = 0
            overall_progress = st.progress(0, text="第二階段：仔細比對每件商品...")
            
            for i, (_, row) in enumerate(candidates_to_verify.iterrows()):
                overall_progress.progress((i + 1) / len(candidates_to_verify), text=f"🤖 正在詳細比對商品 ({i+1}/{len(candidates_to_verify)})...")
                
                result = gemini_verify_match(selected_momo_row['title'], row['title'], row['similarity'])

                # 根據結果顯示不同樣式
                if result.get('is_match'):
                    verified_count += 1
                    card_style = "border-left: 6px solid #48bb78; background: #f0fff4;" # Green match
                    icon = "✅ 配對成功 (MATCH)"
                    text_color = "#2f855a"
                else:
                    card_style = "border-left: 6px solid #f56565; background: #fff5f5;" # Red mismatch
                    icon = "❌ 未配對 (Mismatch)"
                    text_color = "#c53030"

                # 結果卡片渲染
                st.markdown(f"""
                <div class="product-card" style="{card_style} padding: 20px; display: flex; align-items: start; gap: 20px; margin-bottom: 15px;">
                    <div style="width: 120px; flex-shrink: 0; text-align: center;">
                        <div class="badge badge-pchome" style="margin-bottom: 5px;">PChome</div>
                        <img src="{row.get('image', '')}" style="width: 100%; border-radius: 4px; object-fit: contain;" onerror="this.src='https://via.placeholder.com/100'">
                    </div>
                    <div style="flex-grow: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <h4 style="margin: 0; font-size: 1.1rem; color: #2d3748;">{row['title']}</h4>
                            <span style="font-weight: bold; color: {text_color}; white-space: nowrap; margin-left: 10px;">{icon}</span>
                        </div>
                        <div style="margin-top: 8px; display: flex; gap: 15px; font-size: 0.9rem; color: #4a5568;">
                            <span>💰 <strong>NT$ {row.get('price', 'N/A')}</strong></span>
                            <span>📊 相似度: {row['similarity']:.4f}</span>
                        </div>
                        <div class="ai-reasoning-box">
                            <strong>💡 判斷理由：</strong>{result.get('reasoning', '無詳細理由')}
                        </div>
                        <div style="margin-top: 8px; text-align: right;">
                            <a href="{row.get('url', '#')}" target="_blank" style="color: #3182ce; text-decoration: none; font-size: 0.85rem;">查看商品詳情 &rarr;</a>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            overall_progress.empty()

        if verified_count == 0:
            st.info("👀 已檢查所有商品，但沒有找到完全相同的商品。")
        else:
            st.success(f"🎉 比對完成！在 PChome 找到 {verified_count} 件相同商品。")
    else:
        # 顯示上次比對的結果提示
        st.info("💡 已顯示比對結果。若要重新比對，請選擇其他商品。")