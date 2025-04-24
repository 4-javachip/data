import os
import json

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def wait_for_document_ready(driver, timeout=10):
    """문서의 readyState가 'complete'가 될 때까지 대기"""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    
def process_detail_html(driver, url):
    """
    주어진 URL을 headless 브라우저에서 로드한 후,
    상세정보 컨테이너 내부의 iframe 태그들을 찾아서,
    각 iframe 태그 내의 body 내부의 모든 <div> 태그들의 outerHTML을 추출해
    치환한 최종 HTML(상세정보HTML)을 반환합니다.
    """
    wait = WebDriverWait(driver, 10)
    
    # URL 접속 및 페이지 로딩 대기
    driver.get(url)
    wait_for_document_ready(driver, timeout=10)
    print('url:', url)
    
    # 상세정보 컨테이너
    detail_div = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "div.cdtl_tabcont.cdtl_tabcont_detail")
    ))
    
    # iframe이 남아 있는 동안 반복
    while True:
        iframe_list = driver.find_elements(By.TAG_NAME, "iframe")
        if not iframe_list:
            break

        # 첫 번째 iframe 처리
        iframe = iframe_list[0]
        driver.execute_script("arguments[0].scrollIntoView();", iframe)

        try:
            # iframe 복사 (reference stale 방지용)
            iframe_to_replace = iframe

            # 프레임 전환
            driver.switch_to.frame(iframe_to_replace)

            # body 로드 대기
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(0.5)

            # <div> 태그 수집
            divs = driver.find_elements(By.CSS_SELECTOR, "body > div")
            inner_html = "".join([div.get_attribute("outerHTML") for div in divs])

            # <div>가 없으면 body 전체
            if not inner_html.strip():
                inner_html = driver.execute_script("return document.body.innerHTML;")

            # 프레임 해제
            driver.switch_to.default_content()

            # iframe 치환
            driver.execute_script("arguments[0].outerHTML = arguments[1];", iframe_to_replace, inner_html)

            # 치환된 요소가 사라질 때까지 대기
            wait.until(EC.staleness_of(iframe_to_replace))

        except Exception as e:
            print(f"  [WARNING] iframe 처리 중 오류 발생: {e}")
            driver.switch_to.default_content()
            break  # 무한 루프 방지용 탈출

    # 최종 HTML 반환
    detail_div = driver.find_element(By.CSS_SELECTOR, "div.cdtl_tabcont.cdtl_tabcont_detail")
    updated_html = detail_div.get_attribute("innerHTML")
    return updated_html

def main():
    # 1. Headless 모드로 크롬 실행 (실제 브라우저 창이 뜨지 않음)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    data_folder = "output"
    output_folder = "data_html_fix"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # data 폴더 내의 모든 JSON 파일 순회
    json_files = [f for f in os.listdir(data_folder) if f.endswith(".json")]
    for file_name in json_files:
        file_path = os.path.join(data_folder, file_name)
        print(f"Processing file: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        processed_items = []
        skipped_items = []

        # 각 아이템 처리: "상품상세URL"에 접속하여 상세정보HTML 갱신
        for idx, item in enumerate(data):
            if "상품상세URL" in item and item["상품상세URL"].strip():
                url = item["상품상세URL"]
                try:
                    updated_html = process_detail_html(driver, url)
                    # 성공하면 수정된 HTML을 저장
                    item["상세정보HTML"] = updated_html
                    processed_items.append(item)
                except Exception as e:
                    print(f"  [WARNING] Item index {idx} 처리 중 에러 발생: {e}")
                    skipped_items.append(item)
            else:
                processed_items.append(item)

        # 정상 처리된 아이템 저장 (원본 파일명 그대로)
        output_file_path = os.path.join(output_folder, file_name)
        with open(output_file_path, "w", encoding="utf-8") as out_f:
            json.dump(processed_items, out_f, ensure_ascii=False, indent=2)
        print(f"  => Processed data saved: {output_file_path}")

        # 스킵된 아이템이 있으면 별도의 파일로 저장 (파일명 앞에 'skipped_' 추가)
        if skipped_items:
            skipped_file_path = os.path.join(output_folder, f"skipped_{file_name}")
            with open(skipped_file_path, "w", encoding="utf-8") as skip_f:
                json.dump(skipped_items, skip_f, ensure_ascii=False, indent=2)
            print(f"  => Skipped data saved: {skipped_file_path}")

    driver.quit()

if __name__ == "__main__":
    main()