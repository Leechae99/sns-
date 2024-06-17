from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
import time

def get_image_urls(keyword, num_images):
    driver = webdriver.Chrome()
    driver.get("https://pixabay.com/ko/")
    
    # 검색어 입력
    search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div[1]/div[1]/div[3]/div[1]/div/form/input')))
    search_box.click()
    time.sleep(1)
    search_box.send_keys(keyword)
    
    # 검색 버튼 클릭
    search_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div[1]/div[1]/div[3]/div[1]/div/form/button')))
    search_button.click()
    
    # 이미지 로드 대기 및 URL 수집
    image_urls = set()
    while len(image_urls) < num_images:
        try:
            thumbnails = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//img[@srcset]')))
            for thumbnail in thumbnails:
                if len(image_urls) >= num_images:
                    break
                srcset = thumbnail.get_attribute('srcset')
                src = srcset.split(', ')[-1].split(' ')[0]  # 가장 큰 해상도의 이미지를 선택
                if src and src.startswith('https'):
                    image_urls.add(src)
            
            print(f"현재 수집된 이미지 URL 개수: {len(image_urls)}")
            print(image_urls)  # 수집된 이미지 URL 출력
            
            if len(image_urls) < num_images:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # 추가 이미지 로드를 위한 대기 시간
        except Exception as e:
            print(f"이미지 URL 수집 중 오류 발생: {e}")
    
    driver.quit()
    return list(image_urls)

def download_images(image_urls, folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    for i, url in enumerate(image_urls):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                file_path = os.path.join(folder_path, f'{i+1}.jpg')
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f"이미지 {i+1} 다운로드 성공: {url}")
            else:
                print(f"이미지 {i+1} 다운로드 실패 (상태 코드: {response.status_code}): {url}")
        except Exception as e:
            print(f"이미지 {i+1} 다운로드 오류: {e}")

def main():
    keyword = input("크롤링할 이미지의 키워드는 무엇입니까?: ")
    num_images = int(input("크롤링 할 건수는 몇 건입니까?: "))
    folder_path = input("파일이 저장될 경로를 쓰세요(예: c:\\temp): ")
    
    image_urls = get_image_urls(keyword, num_images)
    download_images(image_urls, folder_path)
    print("이미지 다운로드가 완료되었습니다.")

if __name__ == "__main__":
    main()
