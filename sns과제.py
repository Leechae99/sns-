from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import os

def get_search_results(keyword, start_date, end_date):
    driver = webdriver.Chrome()
    driver.get("https://www.g2b.go.kr/index.jsp")
    
    # 팝업 닫기 시도
    try:
        popup_close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@class="btn_md" and @href="javascript:window.close();"]'))
        )
        popup_close_button.click()
        print("팝업 닫기 성공")
    except TimeoutException:
        print("팝업이 없습니다.")
    
    # 공고명 입력
    search_box = driver.find_element(By.ID, "bidNm")
    search_box.send_keys(keyword)
    
    # 조회 시작일 입력
    from_date = driver.find_element(By.ID, "fromBidDt")
    from_date.clear()
    from_date.send_keys(start_date)
    
    # 조회 종료일 입력
    to_date = driver.find_element(By.ID, "toBidDt")
    to_date.clear()
    to_date.send_keys(end_date)
    
    # 검색 버튼 클릭
    search_button = driver.find_element(By.XPATH, "//a[contains(@href, 'javascript:search1()')]")
    search_button.click()
    
    # 페이지 로드 대기
    time.sleep(10)  # 10초 대기
    
    # 첫 번째 프레임 전환
    try:
        driver.switch_to.frame("sub")
        print("첫 번째 프레임 전환 성공")
    except Exception as e:
        print(f"첫 번째 프레임 전환 실패: {e}")
    
    # 두 번째 프레임 전환
    try:
        driver.switch_to.frame("main")
        print("두 번째 프레임 전환 성공")
    except Exception as e:
        print(f"두 번째 프레임 전환 실패: {e}")
    
    # 검색 결과 페이지 로드 대기
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="resultForm"]/div[2]/table/tbody')))

    results = []
    page = 1
    while True:
        try:
            rows = driver.find_elements(By.XPATH, '//*[@id="resultForm"]/div[2]/table/tbody/tr')
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if cols:
                    result = {
                        "업무": cols[0].text.strip(),
                        "공고번호-차수": cols[1].text.strip(),
                        "분류": cols[2].text.strip(),
                        "공고명": cols[3].text.strip(),
                        "공고URL": "https://www.g2b.go.kr" + cols[3].find_element(By.TAG_NAME, "a").get_attribute("href") if cols[3].find_element(By.TAG_NAME, "a") else '',
                        "공고기관": cols[4].text.strip(),
                        "수요기관": cols[5].text.strip(),
                        "계약방법": cols[6].text.strip(),
                        "입력일시": cols[7].text.strip(),
                        "공동수급": cols[8].text.strip(),
                        "투찰": cols[9].text.strip(),
                    }
                    results.append(result)
            
            # 현재 페이지 번호 확인
            current_page_elem = driver.find_element(By.XPATH, '//*[@id="pagination"]/strong/span')
            current_page = int(current_page_elem.text.strip())
            
            # '더보기' 링크 클릭
            try:
                more_button = driver.find_element(By.XPATH, "//a[@href='javascript:to_more(1)']")
                driver.execute_script("arguments[0].click();", more_button)
                print(f"'더보기' 클릭 - 페이지 {current_page + 1}로 이동 중")
                
                # 현재 페이지가 업데이트될 때까지 대기
                wait.until(EC.staleness_of(current_page_elem))
                wait.until(EC.text_to_be_present_in_element((By.XPATH, '//*[@id="pagination"]/strong/span'), str(current_page + 1)))
                
                print(f"페이지 {current_page + 1}로 이동 성공")
                page += 1
                
                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="resultForm"]/div[2]/table/tbody')))
            except NoSuchElementException:
                print(f"다음 페이지가 존재하지 않습니다. 스크래핑 종료.")
                break
        
        except TimeoutException:
            print(f"페이지 {page}에서 TimeoutException 발생. 다음 페이지로 이동을 시도합니다.")
            try:
                more_button = driver.find_element(By.XPATH, "//a[@href='javascript:to_more(1)']")
                driver.execute_script("arguments[0].click();", more_button)
                print(f"'더보기' 클릭 - 페이지 {current_page + 1}로 이동 중")
                
                # 현재 페이지가 업데이트될 때까지 대기
                wait.until(EC.staleness_of(current_page_elem))
                wait.until(EC.text_to_be_present_in_element((By.XPATH, '//*[@id="pagination"]/strong/span'), str(current_page + 1)))
                
                print(f"페이지 {current_page + 1}로 이동 성공")
                page += 1
                
                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="resultForm"]/div[2]/table/tbody')))
            except NoSuchElementException:
                print(f"다음 페이지가 존재하지 않습니다. 스크래핑 종료.")
                break

    driver.quit()
    return results

def save_results(results, folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # TXT 형식으로 저장
    txt_file = os.path.join(folder_path, "results.txt")
    with open(txt_file, "w", encoding='utf-8') as f:
        for result in results:
            f.write(str(result) + "\n")
    
    # XLS 형식으로 저장
    df = pd.DataFrame(results)
    xls_file = os.path.join(folder_path, "results.xlsx")
    df.to_excel(xls_file, index=False)

# 메인 함수
def main():
    keyword = input("공고명으로 검색할 키워드는 무엇입니까?: ")
    start_date = input("조회 시작일자 입력(예:2019/01/01): ")
    end_date = input("조회 종료일자 입력(예:2019/03/31): ")
    folder_path = input("파일로 저장할 폴더 이름을 쓰세요(예:c:\\data): ")

    results = get_search_results(keyword, start_date, end_date)
    save_results(results, folder_path)
    print("결과가 성공적으로 저장되었습니다")

if __name__ == "__main__":
    main()

