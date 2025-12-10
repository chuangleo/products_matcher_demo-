import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
from urllib.parse import quote
import re
import warnings
import logging
import os

# 在文件開頭添加這些行來抑制所有警告和日誌
warnings.filterwarnings("ignore")
logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

# 抑制 Chrome 相關的錯誤訊息
os.environ['WDM_LOG_LEVEL'] = '0'
os.environ['WDM_PRINT_FIRST_LINE'] = 'False'

def fetch_products_for_momo(keyword, max_products=50, progress_callback=None):
    """
    使用 Selenium 從 momo 購物網抓取商品資訊
    
    Args:
        keyword (str): 搜尋關鍵字
        max_products (int): 最大抓取商品數量
        progress_callback (function): 進度回調函式，接收 (current, total, message) 參數
    
    Returns:
        list: 商品資訊列表，每個商品包含 id, title, price, image_url, url, platform, sku
    """
    
    products = []
    product_id = 1  # 順序編號
    driver = None
    page = 1  # 當前頁數
    seen_skus = set()  # 追蹤已經收集的 SKU，避免重複
    consecutive_empty_pages = 0  # 連續空白頁計數器
    
    try:
        # 設定 Chrome 選項
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 啟用無頭模式（雲端部署必需）
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 禁用圖片載入以提高速度
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 初始化 WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        print(f"正在搜尋 momo: {keyword}")
        
        # 📊 回報初始進度
        if progress_callback:
            progress_callback(0, max_products, f'🔍 正在搜尋 MOMO: {keyword}')
        
        # 等待頁面載入
        wait = WebDriverWait(driver, 15)
        
        # 多頁抓取循環
        while len(products) < max_products:
            # 建構搜尋 URL（包含頁數）
            encoded_keyword = quote(keyword)
            search_url = f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={encoded_keyword}&searchType=1&cateLevel=0&ent=k&sortType=1&curPage={page}"
            
            print(f"正在抓取第 {page} 頁...")
            
            # 📊 回報頁面載入進度
            if progress_callback:
                progress_callback(len(products), max_products, f'📄 MOMO 第 {page} 頁載入中... (已收集 {len(products)}/{max_products} 筆)')
            
            # 頁面載入重試
            attempt = 1
            max_attempts = 3
            product_elements = []
            while attempt <= max_attempts:
                try:
                    driver.get(search_url)
                    time.sleep(3)  # 等待頁面載入
                    
                    # 嘗試查找商品元素
                    selectors_to_try = [
                        "li.listAreaLi",
                        ".listAreaUl li.listAreaLi",
                        "li.goodsItemLi",
                        ".prdListArea .goodsItemLi",
                        ".searchPrdListArea li",
                        "li[data-gtm]",
                        ".goodsItemLi",
                        ".searchPrdList li"
                    ]
                    
                    for selector in selectors_to_try:
                        try:
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            product_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if product_elements:
                                #print(f"使用選擇器 '{selector}' 找到 {len(product_elements)} 個商品")
                                break
                        except TimeoutException:
                            continue
                    
                    # 如果找到有效商品元素或商品數量少於 20 個但大於 0，則退出重試
                    if product_elements:
                        break
                    # 如果未找到商品元素或商品數量少於 20 個，則重試
                    print(f"第 {page} 頁未找到足夠商品元素（找到 {len(product_elements)} 個），重試 {attempt}/{max_attempts}")
                    attempt += 1
                    time.sleep(random.uniform(3, 6))  # 重試間隔
                except TimeoutException:
                    print(f"第 {page} 頁載入超時，重試 {attempt}/{max_attempts}")
                    attempt += 1
                    time.sleep(random.uniform(3, 6))
            
            if not product_elements:
                print("無法找到商品元素，可能頁面結構已改變或已到達最後一頁")
                break
            
            print(f"開始解析 {len(product_elements)} 個商品")
            page_products_count = 0
            
            # 解析每個商品
            for i, element in enumerate(product_elements):
                try:
                    # 如果已經獲得足夠的商品，就停止
                    if len(products) >= max_products:
                        break
                    
                    # 提取商品標題
                    title = ""
                    title_selectors = [
                        "h3.prdName",
                        ".prdNameTitle h3.prdName",
                        ".prdName",
                        "h3",
                        "a[title]",
                        "img[alt]",
                        ".goodsName",
                        ".goodsInfo h3",
                        "a"
                    ]
                    
                    for selector in title_selectors:
                        try:
                            title_elem = element.find_element(By.CSS_SELECTOR, selector)
                            if selector == "img[alt]":
                                title = title_elem.get_attribute("alt").strip()
                            elif selector == "a[title]":
                                title = title_elem.get_attribute("title").strip()
                            else:
                                title = title_elem.text.strip()
                            
                            if title and len(title) > 5:  # 確保標題有足夠長度
                                break
                        except NoSuchElementException:
                            continue
                    
                    # 如果沒有找到標題，跳過這個商品
                    if not title:
                        continue
                    
                    # 提取價格（先用多種選擇器，若失敗則用整個元素的文字做回退）
                    price = 0
                    price_selectors = [
                        ".money .price b",
                        ".price b",
                        ".money b",
                        ".price",
                        ".money",
                        ".cost",
                        "b",
                        "strong",
                        ".goodsPrice",
                        ".priceInfo",
                        ".prodPrice",
                        ".prdPrice"
                    ]

                    for selector in price_selectors:
                        try:
                            price_elements = element.find_elements(By.CSS_SELECTOR, selector)
                            for price_elem in price_elements:
                                price_text = price_elem.text
                                if price_text and any(c.isdigit() for c in price_text):
                                    # 提取數字
                                    numbers = re.findall(r'\d+', price_text.replace(',', ''))
                                    if numbers:
                                        # 取最大的數字作為價格（避免取到折扣百分比等小數字）
                                        potential_prices = [int(num) for num in numbers if int(num) > 10]
                                        if potential_prices:
                                            price = max(potential_prices)
                                            break
                            if price > 0:
                                break
                        except NoSuchElementException:
                            continue

                    # 回退策略：用整個元素的文本抓取數字（如果先前沒抓到價格）
                    if price <= 0:
                        try:
                            full_text = element.text
                            numbers = re.findall(r'\d+', full_text.replace(',', ''))
                            if numbers:
                                potential_prices = [int(num) for num in numbers if int(num) > 10]
                                if potential_prices:
                                    price = max(potential_prices)
                        except Exception:
                            price = 0

                    # 如果還沒有找到價格，就跳過這個商品
                    if price <= 0:
                        continue
                    
                    # 提取商品連結
                    url = ""
                    try:
                        link_elem = element.find_element(By.CSS_SELECTOR, "a.goods-img-url")
                        url = link_elem.get_attribute("href")
                        if not url.startswith("http"):
                            url = "https://www.momoshop.com.tw" + url
                    except NoSuchElementException:
                        # 嘗試找其他可能的連結選擇器
                        try:
                            link_elem = element.find_element(By.CSS_SELECTOR, "a[href*='/goods/']")
                            url = link_elem.get_attribute("href")
                            if not url.startswith("http"):
                                url = "https://www.momoshop.com.tw" + url
                        except NoSuchElementException:
                            # 嘗試找任何連結
                            try:
                                link_elem = element.find_element(By.CSS_SELECTOR, "a[href]")
                                url = link_elem.get_attribute("href")
                                if url and not url.startswith("http"):
                                    url = "https://www.momoshop.com.tw" + url
                            except NoSuchElementException:
                                url = ""
                    
                    # 嘗試從隱藏 input 取得商品 id 作為 sku（momo 的 list 中常見）
                    sku = ""
                    try:
                        input_elem = element.find_element(By.CSS_SELECTOR, "input#viewProdId")
                        sku_val = input_elem.get_attribute("value")
                        if sku_val:
                            sku = sku_val
                    except NoSuchElementException:
                        sku = ""

                    # 若仍無 sku，嘗試從 url 提取 i_code 或最後一段
                    if not sku and url:
                        match = re.search(r'i_code=(\d+)', url)
                        if match:
                            sku = match.group(1)
                        else:
                            url_parts = url.rstrip('/').split('/')
                            if url_parts:
                                last_part = url_parts[-1]
                                if '?' in last_part:
                                    last_part = last_part.split('?')[0]
                                if '.' in last_part:
                                    last_part = last_part.split('.')[0]
                                sku = last_part
                    # 如果有 sku 但沒有 url，可以用 momo 的商品頁樣式組成 url
                    if not url and sku:
                        url = f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={sku}"
                    
                    # 提取商品圖片
                    image_url = ""
                    try:
                        # 優先尋找第一個商品圖片
                        img_elem = element.find_element(By.CSS_SELECTOR, "img.prdImg")
                        # 優先使用 src，然後是 data-original，最後是 data-src
                        image_url = (img_elem.get_attribute("src") or 
                                   img_elem.get_attribute("data-original") or 
                                   img_elem.get_attribute("data-src"))
                        
                        if image_url:
                            # 處理相對路徑和協議相對路徑
                            if image_url.startswith("//"):
                                image_url = "https:" + image_url
                            elif image_url.startswith("/"):
                                image_url = "https://www.momoshop.com.tw" + image_url
                            elif not image_url.startswith("http"):
                                # 如果是相對路徑但不以 / 開頭，假設是 momoshop 的圖片
                                if "momoshop" not in image_url:
                                    image_url = "https://cdn3.momoshop.com.tw/momoshop/upload/media/" + image_url
                                else:
                                    image_url = "https://" + image_url
                    except NoSuchElementException:
                        # 如果找不到 prdImg，嘗試其他圖片選擇器
                        try:
                            img_elem = element.find_element(By.CSS_SELECTOR, "img")
                            image_url = (img_elem.get_attribute("src") or 
                                       img_elem.get_attribute("data-original") or 
                                       img_elem.get_attribute("data-src"))
                            
                            if image_url:
                                # 處理相對路徑和協議相對路徑
                                if image_url.startswith("//"):
                                    image_url = "https:" + image_url
                                elif image_url.startswith("/"):
                                    image_url = "https://www.momoshop.com.tw" + image_url
                                elif not image_url.startswith("http"):
                                    if "momoshop" not in image_url:
                                        image_url = "https://cdn3.momoshop.com.tw/momoshop/upload/media/" + image_url
                                    else:
                                        image_url = "https://" + image_url
                        except NoSuchElementException:
                            image_url = ""
                    
                    # 確保所有必要欄位都有值才加入商品
                    if title and price > 0 and url:
                        # 檢查 SKU 是否重複
                        if sku and sku in seen_skus:
                            #print(f"跳過重複 SKU: {sku}")
                            continue
                        
                        product = {
                            "id": product_id,
                            "title": title,
                            "price": price,
                            "image_url": image_url if image_url else "",
                            "url": url,
                            "platform": "momo",
                            "sku": sku
                        }
                        products.append(product)
                        if sku:
                            seen_skus.add(sku)
                        product_id += 1
                        page_products_count += 1
                        
                        # 📊 回報即時進度（每抓到一個商品就更新）
                        if progress_callback:
                            progress_callback(
                                len(products), 
                                max_products, 
                                f'📦 MOMO: 已收集 {len(products)}/{max_products} 筆商品'
                            )
                        
                        #print(f"成功解析商品 {len(products)}: {title[:50]}... (NT$ {price:,})")
                    
                    # 避免過於頻繁的操作
                    time.sleep(random.uniform(0.05, 0.1))
                    
                except Exception as e:
                    print(f"解析第 {i+1} 個商品時發生錯誤: {e}")
                    continue
            
            print(f"第 {page} 頁找到 {len(product_elements)} 個商品元素，成功解析 {page_products_count} 個有效商品，目前總計 {len(products)} 個商品")
            
            # 🔧 改進：只有在「已達到目標數量」或「連續多頁都沒有商品」時才停止
            # 移除「商品數量少於 20 就停止」的限制，因為有些關鍵字本來商品就少
            
            # 如果這一頁沒有找到任何有效商品，檢查是否要繼續
            if page_products_count == 0:
                consecutive_empty_pages += 1
                print(f"⚠️ 第 {page} 頁沒有找到有效商品（連續 {consecutive_empty_pages} 頁為空）")
                
                # 🆕 只有在頁面商品元素也很少時才停止（真的沒商品了）
                if len(product_elements) < 5:
                    print("商品元素也很少，判定為真正的最後一頁，停止抓取")
                    break
                # 如果連續3頁都沒有有效商品，也停止（避免無限循環）
                elif consecutive_empty_pages >= 3:
                    print(f"連續 {consecutive_empty_pages} 頁都沒有有效商品，停止抓取")
                    break
                else:
                    print(f"但頁面還有商品元素，可能只是被過濾掉（例如重複SKU），繼續嘗試下一頁")
                    # 附加偵錯輸出：印出前 3 個商品元素的 outerHTML，幫助分析為何無法解析
                    try:
                        print("--- MOMO sample product_elements outerHTML (first 3) ---")
                        for idx, pe in enumerate(product_elements[:3]):
                            try:
                                outer = pe.get_attribute('outerHTML')
                            except Exception:
                                outer = '<unable to get outerHTML>'
                            print(f"--- element #{idx+1} ---")
                            # 印較多字數以便找到價格資訊
                            print(outer[:4000])
                            try:
                                text_snip = pe.text
                            except Exception:
                                text_snip = '<unable to get text>'
                            print("element.text:\n", text_snip[:1000])
                        print("--- end sample ---")
                    except Exception as e:
                        print(f"列印 sample outerHTML 時發生錯誤: {e}")
            else:
                # 重置連續空白頁計數器
                consecutive_empty_pages = 0
                    # 繼續到下一頁嘗試
                
            # 如果還需要更多商品，則跳到下一頁
            if len(products) < max_products:
                page += 1
                print(f"📄 準備抓取第 {page} 頁...")
                time.sleep(random.uniform(2, 3))  # 頁面間隔
            else:
                print(f"✅ 已達到目標數量 {max_products} 筆，停止抓取")
                break
        
        print(f"成功從 momo 獲取 {len(products)} 個唯一商品（已自動過濾重複 SKU）")
        
        # 📊 回報完成進度
        if progress_callback:
            progress_callback(len(products), max_products, f'✅ MOMO 完成！共收集 {len(products)} 筆商品')
        
        return products
        
    except Exception as e:
        print(f"momo Selenium 爬蟲發生錯誤: {e}")
        return []
    
    finally:
        # 確保關閉瀏覽器
        if driver:
            try:
                driver.quit()
            except:
                pass


def fetch_products_for_pchome(keyword, max_products=50, progress_callback=None):
    """
    使用 Selenium 從 PChome 購物網抓取商品資訊，適應 2025年10月 的新版網頁結構。
    
    Args:
        keyword (str): 搜尋關鍵字
        max_products (int): 最大抓取商品數量
        progress_callback (function): 進度回調函式，接收 (current, total, message) 參數
    
    Returns:
        list: 商品資訊列表
    """
    products = []
    product_id = 1
    driver = None
    page = 1
    seen_skus = set()
    consecutive_empty_pages = 0  # 連續空白頁計數器

    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 啟用無頭模式（雲端部署必需）
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        prefs = {"profile.default_content_setting_values.notifications": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(40)
        wait = WebDriverWait(driver, 20)
        print(f"正在搜尋 PChome: {keyword}")
        
        # 📊 回報初始進度
        if progress_callback:
            progress_callback(0, max_products, f'🔍 正在搜尋 PChome: {keyword}')

        encoded_keyword = quote(keyword)
        search_url = f"https://24h.pchome.com.tw/search/?q={encoded_keyword}"
        driver.get(search_url)
        time.sleep(2)

        while len(products) < max_products:
            print(f"正在抓取 PChome 第 {page} 頁...")
            
            # 📊 回報頁面載入進度
            if progress_callback:
                progress_callback(len(products), max_products, f'📄 PChome 第 {page} 頁載入中... (已收集 {len(products)}/{max_products} 筆)')
            
            try:
                # 等待新結構的商品項目出現
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.c-listInfoGrid__item--gridCardGray5")))
                
                # 滾動頁面以確保所有商品都載入
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 根據新結構獲取所有商品元素
                product_elements = driver.find_elements(By.CSS_SELECTOR, "li.c-listInfoGrid__item--gridCardGray5")
            except TimeoutException:
                print("頁面加載超時或找不到新結構的商品容器 (li.c-listInfoGrid__item--gridCardGray5)。")
                try:
                    driver.save_screenshot("pchome_error_screenshot.png")
                    print("已儲存錯誤截圖: pchome_error_screenshot.png")
                except Exception as e:
                    print(f"儲存截圖失敗: {e}")
                break

            print(f"第 {page} 頁找到 {len(product_elements)} 個商品元素")
            
            # 記錄這一頁成功解析的商品數
            page_products_count = 0

            for element in product_elements:
                if len(products) >= max_products:
                    break

                try:
                    # 提取連結和 SKU
                    link_element = element.find_element(By.CSS_SELECTOR, "a.c-prodInfoV2__link")
                    url = link_element.get_attribute("href")
                    if not url.startswith("https://"):
                        url = "https://24h.pchome.com.tw" + url
                    
                    sku_match = re.search(r'/prod/(.*?)(?:\?|$)', url)
                    sku = sku_match.group(1) if sku_match else ""

                    # 提取標題
                    title_elem = element.find_element(By.CSS_SELECTOR, "div.c-prodInfoV2__title")
                    title = title_elem.text.strip()

                    # 提取價格：優先抓取促銷價格，如果沒有則抓取網路價
                    price = 0
                    price_found_by = None  # 用於調試
                    
                    # 新策略：抓取整個商品卡片的 HTML，然後分析所有價格
                    try:
                        # 獲取整個價格區域的所有文字
                        price_container = element.find_element(By.CSS_SELECTOR, "div.c-prodInfoV2__body")
                        full_html = price_container.get_attribute('innerHTML')
                        
                        # 使用正則表達式找出所有價格數字
                        # 尋找格式如 $7,999 或 $10,900 的價格
                        price_matches = re.findall(r'\$\s*([\d,]+)', full_html)
                        
                        if price_matches:
                            # 轉換所有找到的價格為整數
                            all_prices = []
                            for match in price_matches:
                                try:
                                    price_val = int(match.replace(',', ''))
                                    if price_val > 10:  # 過濾掉不合理的小數字
                                        all_prices.append(price_val)
                                except:
                                    continue
                            
                            if all_prices:
                                # 取最小的價格（通常優惠價會比原價小）
                                price = min(all_prices)
                                price_found_by = f"從 HTML 找到 {len(all_prices)} 個價格，選擇最低: {all_prices}"
                    except:
                        pass
                    
                    # 備用策略：如果上面的方法失敗，使用傳統選擇器
                    if price == 0:
                        price_selectors = [
                            "div[class*='o-prodPrice__price']",
                            "div.o-prodPrice__originalPrice",
                            "div.c-prodInfoV2__salePrice"
                        ]
                        
                        for selector in price_selectors:
                            try:
                                price_elem = element.find_element(By.CSS_SELECTOR, selector)
                                price_text = price_elem.text.strip()
                                if price_text and any(c.isdigit() for c in price_text):
                                    extracted_price = int(re.sub(r'[^\d]', '', price_text))
                                    if extracted_price > 0:
                                        price = extracted_price
                                        price_found_by = f"備用選擇器: {selector}"
                                        break
                            except NoSuchElementException:
                                continue
                    
                    # 調試輸出
                    if price_found_by and page == 1 and len(products) < 5:
                        print(f"  [{len(products)+1}] {title[:40]}... -> NT$ {price:,}")
                        print(f"      來源: {price_found_by}")

                    # 提取圖片
                    image_url = ""
                    try:
                        img_elem = element.find_element(By.CSS_SELECTOR, "div.c-prodInfoV2__head img")
                        image_url = img_elem.get_attribute("src")
                    except NoSuchElementException:
                        image_url = "" # 找不到圖片就算了

                    if title and price > 0 and url and sku:
                        if sku in seen_skus:
                            continue
                        
                        seen_skus.add(sku)
                        product = {
                            "id": product_id,
                            "title": title,
                            "price": price,
                            "image_url": image_url,
                            "url": url,
                            "platform": "pchome",
                            "sku": sku
                        }
                        products.append(product)
                        product_id += 1
                        page_products_count += 1  # 記錄這一頁成功解析的商品數
                        
                        # 📊 回報即時進度（每抓到一個商品就更新）
                        if progress_callback:
                            progress_callback(
                                len(products), 
                                max_products, 
                                f'📦 PChome: 已收集 {len(products)}/{max_products} 筆商品'
                            )

                except (NoSuchElementException, ValueError) as e:
                    continue
            
            print(f"第 {page} 頁找到 {len(product_elements)} 個商品元素，成功解析 {page_products_count} 個有效商品，目前總計 {len(products)} 個商品")
            
            # 🔧 改進：智慧停止判斷
            if page_products_count == 0:
                consecutive_empty_pages += 1
                print(f"⚠️ 第 {page} 頁沒有找到有效商品（連續 {consecutive_empty_pages} 頁為空）")
                
                # 只有在頁面商品元素也很少時才停止（真的沒商品了）
                if len(product_elements) < 5:
                    print("商品元素也很少，判定為真正的最後一頁，停止抓取")
                    break
                # 如果連續3頁都沒有有效商品，也停止（避免無限循環）
                elif consecutive_empty_pages >= 3:
                    print(f"連續 {consecutive_empty_pages} 頁都沒有有效商品，停止抓取")
                    break
                else:
                    print(f"但頁面還有商品元素，可能只是被過濾掉（例如重複SKU），繼續嘗試下一頁")
            else:
                # 重置連續空白頁計數器
                consecutive_empty_pages = 0
            
            # 如果已達到目標數量就停止
            if len(products) >= max_products:
                print(f"✅ 已達到目標數量 {max_products} 筆，停止抓取")
                break

            # 點擊下一頁按鈕
            try:
                # 先滾動到頁面底部，確保下一頁按鈕可見
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # 使用新的選擇器來找到下一頁按鈕
                # 根據 HTML 結構，尋找包含向右箭頭圖示的元素
                next_icon = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "i.o-iconFonts--arrowSolidRight")))
                # 點擊圖示的父元素（應該是可點擊的按鈕）
                next_page_button = next_icon.find_element(By.XPATH, "..")
                driver.execute_script("arguments[0].click();", next_page_button)
                page += 1
                time.sleep(random.uniform(3, 5))
            except (TimeoutException, NoSuchElementException):
                print("找不到下一頁按鈕，抓取結束。")
                break
        
        print(f"成功從 PChome 獲取 {len(products)} 個唯一商品。")
        
        # 📊 回報完成進度
        if progress_callback:
            progress_callback(len(products), max_products, f'✅ PChome 完成！共收集 {len(products)} 筆商品')
        
        return products

    except Exception as e:
        print(f"PChome Selenium 爬蟲發生錯誤: {e}")
        return []

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def save_to_csv(products, filename, query_keyword, append_mode=True):
    """
    將商品資訊儲存為CSV格式
    
    Args:
        products (list): 商品資訊列表
        filename (str): CSV檔案名稱
        query_keyword (str): 查詢關鍵字
        append_mode (bool): True=追加模式，False=覆蓋模式
    """
    if not products:
        print(f"沒有商品資料可以儲存到 {filename}")
        return
    
    # CSV欄位定義（與你的CSV格式一致）
    fieldnames = [
        'id', 'sku', 'title', 'image', 'url', 'platform', 
        'connect', 'price', 'uncertainty_problem', 'query', 
        'annotator', 'created_at', 'updated_at'
    ]
    
    # 當前時間
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    
    # 檢查檔案是否存在，以及是否需要追加
    file_exists = os.path.exists(filename)
    
    # 如果是追加模式且檔案存在，需要先讀取現有的最大 id
    start_id = 1
    if append_mode and file_exists:
        try:
            import pandas as pd
            existing_df = pd.read_csv(filename)
            if not existing_df.empty and 'id' in existing_df.columns:
                start_id = existing_df['id'].max() + 1
        except Exception as e:
            print(f"讀取現有檔案失敗，將從 id=1 開始: {e}")
            start_id = 1
    
    # 決定開啟模式：追加或覆蓋
    mode = 'a' if (append_mode and file_exists) else 'w'
    
    with open(filename, mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # 只有在新建檔案或覆蓋模式時才寫入表頭
        if mode == 'w':
            writer.writeheader()
        
        for i, product in enumerate(products):
            # 構建CSV行資料（匹配你的格式）
            row = {
                'id': start_id + i,  # 使用連續的 id
                'sku': product['sku'],
                'title': product['title'],
                'image': product['image_url'],
                'url': product['url'],
                'platform': product['platform'],
                'connect': '',  # 空值，如果需要可以後續填入
                'price': f"{product['price']:.2f}",
                'uncertainty_problem': '0',
                'query': query_keyword,
                'annotator': 'model_prediction',
                'created_at': current_time,
                'updated_at': current_time
            }
            writer.writerow(row)
    
    print(f"✅ 成功儲存 {len(products)} 筆商品至 {filename}")


if __name__ == "__main__":
    # 測試爬蟲
    keyword = input("輸入關鍵字: ")
    english_keyword = input("輸入關鍵字的英文名稱: ")
    num = int(input("輸入數量: "))
    
    # 抓取 MOMO 商品
    print("\n=== 開始抓取 MOMO 商品 ===")
    momo_products = fetch_products_for_momo(keyword, num)
    
    # 儲存 MOMO 商品至 CSV 檔案
    save_to_csv(momo_products, "momo.csv", english_keyword)

    if momo_products:
        print(f"\n找到 {len(momo_products)} 個 MOMO 商品：")
        for product in momo_products[:5]:  # 只顯示前5個
            print(f"ID: {product['id']}")
            print(f"標題: {product['title']}")
            print(f"價格: NT$ {product['price']:,}")
            print(f"圖片: {product['image_url']}")
            print(f"連結: {product['url']}")
            print(f"平台: {product['platform']}")
            print("-" * 50)
        if len(momo_products) > 5:
            print(f"... 以及其他 {len(momo_products) - 5} 個商品")
    else:
        print("沒有找到 MOMO 商品")

    # 抓取 PChome 商品
    print("\n=== 開始抓取 PChome 商品 ===")
    pchome_products = fetch_products_for_pchome(keyword, num)
    
    # 儲存 PChome 商品至 CSV 檔案
    save_to_csv(pchome_products, "pchome.csv", english_keyword)

    if pchome_products:
        print(f"\n找到 {len(pchome_products)} 個 PChome 商品：")
        for product in pchome_products[:5]:  # 只顯示前5個
            print(f"ID: {product['id']}")
            print(f"標題: {product['title']}")
            print(f"價格: NT$ {product['price']:,}")
            print(f"圖片: {product['image_url']}")
            print(f"連結: {product['url']}")
            print(f"平台: {product['platform']}")
            print("-" * 50)
        if len(pchome_products) > 5:
            print(f"... 以及其他 {len(pchome_products) - 5} 個商品")
    else:
        print("沒有找到 PChome 商品")
    
    print(f"\n=== 完成！===")
    print(f"MOMO 商品已儲存至: momo.csv")
    print(f"PChome 商品已儲存至: pchome.csv")