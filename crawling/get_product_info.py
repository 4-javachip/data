import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

BASE_ITEM_URL = "https://www.ssg.com/item/itemView.ssg?itemId={itemId}"

def get_product_info(itemId):
    product_url = BASE_ITEM_URL.format(itemId=itemId)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(product_url)

    wait = WebDriverWait(driver, 5)  # 요소 최대 대기 시간 (5초)

    product = {
        "카테고리": [],
        "상품상세URL": product_url,
        "썸네일이미지": [],
        "옵션명": [],
        "제품명": "",
        "정가": 0,
        "할인가": 0,
        "상세정보HTML": "",
        "총리뷰수": 0,
        "평균별점": 0.0,
        "리뷰목록": [],
        "상품필수정보": []
    }

    # 썸네일 이미지
    try:
        thumbnail_elements = driver.find_elements(By.CSS_SELECTOR, "ul.cdtl_pager_lst li img")
        for img in thumbnail_elements:
            product["썸네일이미지"].append({
                "url": img.get_attribute("src"),
                "alt": img.get_attribute("alt")
            })
    except:
        pass

    # 옵션명
    try:
        dt_elements = driver.find_elements(By.CSS_SELECTOR, "div#_ordOpt_area dt")
        product["옵션명"] = [dt.text.strip() for dt in dt_elements if dt.text.strip()]
    except:
        pass

    # 제품명
    try:
        name_elem = driver.find_element(By.CSS_SELECTOR, "span.cdtl_info_tit_txt")
        product["제품명"] = name_elem.text.strip()
    except:
        pass

    # 정가 / 할인가
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.cdtl_optprice_wrap")))
        price_scope = driver.find_element(By.CSS_SELECTOR, "div.cdtl_optprice_wrap")
        price_elems = price_scope.find_elements(By.CSS_SELECTOR, "em.ssg_price")
        prices = [
            int(elem.text.replace(",", "").replace("원", ""))
            for elem in price_elems
            if elem.text.strip() and elem.text.replace(",", "").replace("원", "").isdigit()
        ]
        if len(prices) >= 2:
            product["할인가"] = min(prices)
            product["정가"] = max(prices)
        elif len(prices) == 1:
            product["할인가"] = product["정가"] = prices[0]
    except:
        pass

    # 리뷰 수집
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.rvw_expansion_panel.v2")))
        reviews = []
        current_page = 1
        while len(reviews) < 100:
            time.sleep(0.5)  # 페이지 전환 후 로딩 시간 확보
            review_elements = driver.find_elements(By.CSS_SELECTOR, "li.rvw_expansion_panel.v2")
            for elem in review_elements:
                if len(reviews) >= 100:
                    break
                try:
                    별점 = float(elem.find_element(By.CSS_SELECTOR, "div.cdtl_star_area span.blind em").text.strip())
                except:
                    별점 = 0.0
                try:
                    리뷰내용 = elem.find_element(By.CSS_SELECTOR, "div.rvw_panel_expand_hide_group p.rvw_item_text").text.strip()
                except:
                    리뷰내용 = ""
                try:
                    이미지 = [img.get_attribute("src") for img in elem.find_elements(By.CSS_SELECTOR, "div.rvw_item_thumb_group img") if img.get_attribute("src")]
                except:
                    이미지 = []
                try:
                    작성자 = elem.find_element(By.CSS_SELECTOR, "div.rvw_item_label.rvw_item_user_id").text.strip()
                except:
                    작성자 = ""
                try:
                    작성일_raw = elem.find_element(By.CSS_SELECTOR, "div.rvw_item_label.rvw_item_date").text.strip()
                    작성일 = datetime.strptime(작성일_raw.replace(".", "-"), "%Y-%m-%d").strftime("%Y-%m-%d")
                except:
                    작성일 = 작성일_raw

                # ⛔ 리뷰 내용 없는 것 거르기
                if 리뷰내용 or 별점 > 0:
                    reviews.append({
                        "별점": 별점,
                        "리뷰내용": 리뷰내용,
                        "리뷰이미지url": 이미지,
                        "작성자": 작성자,
                        "작성일": 작성일
                    })

            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, f"a[onclick=\"fn_GoCommentPage('{current_page + 1}')\"]")
                next_btn.click()
                current_page += 1
            except:
                break

        product["리뷰목록"] = reviews
        product["총리뷰수"] = len(reviews)
        if reviews:
            product["평균별점"] = round(sum(r["별점"] for r in reviews) / len(reviews), 2)
    except:
        pass

    # 상품필수정보
    try:
        info_section = driver.find_element(By.ID, "item_size")
        rows = info_section.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in rows:
            try:
                th = row.find_element(By.CSS_SELECTOR, "th div.in").text.strip()
                td = row.find_element(By.CSS_SELECTOR, "td div.in").text.strip()
                if th and td:
                    product["상품필수정보"].append({
                        "유형": th,
                        "값": td
                    })
            except:
                continue
    except:
        pass

    # 상세정보 HTML
    try:
        detail_div = driver.find_element(By.CSS_SELECTOR, "div.cdtl_tabcont.cdtl_tabcont_detail")
        product["상세정보HTML"] = detail_div.get_attribute("outerHTML")
    except Exception as e:
        product["상세정보HTML"] = f"상세정보 HTML 추출 실패: {str(e)}"

    driver.quit()
    return product