import time
import traceback
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager




# 아이디 비번 입력
def get_credentials():
    username = input("아이디를 입력하세요: ")
    password = input("비밀번호를 입력하세요: ")
    return username, password



# 로그인 및 드라이버 관리

BASE_URL = "https://dsat.dev.9rum.cc/#/user/login"


def dsat_login(username, password, headless, log):

    try:
        log.log("웹 드라이버 설정을 시작합니다.")
        options = Options()
        options.add_argument("--start-maximized")

        if headless:
            log.log("헤드리스 모드로 실행합니다.")
            options.add_argument("--headless")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")

        driver_path = ChromeDriverManager().install()
        driver = webdriver.Chrome(service=Service(driver_path), options=options)
        log.log("웹 드라이버가 성공적으로 생성되었습니다.")

        driver.get(BASE_URL)
        log.log(f"로그인 페이지로 이동: {BASE_URL}")

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "password"))).send_keys(
            password + Keys.RETURN)
        log.log("아이디와 비밀번호를 입력했습니다.")

        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#root > div > section > div.ant-layout > header"))
        )
        log.log("✅ DSAT 로그인에 성공했습니다.")
        return driver

    except Exception as e:
        log.log(f"❌ DSAT 로그인 실패: {str(e)}", level='ERROR')
        if 'driver' in locals() and driver:
            driver.quit()
        return None


def close_chrome(driver):
    if driver:
        driver.quit()



# DSAT 홈 정보 크롤링

HOME_URL = "https://dsat.dev.9rum.cc/#/home"


def progress_info(driver, log):
    #평가 진행률 정보
    try:
        log.log(f"홈 페이지로 이동: {HOME_URL}")
        driver.get(HOME_URL)

        progress_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ant-progress-text"))
        )
        progress_text_value = progress_element.text.strip()
        log.log(f"✅ '평가 진행율' 값 '{progress_text_value}' 가져오기 성공.")
        return progress_text_value

    except Exception as e:
        log.log(f"❌ 평가 진행률 정보 수집 중 오류: {str(e)}", level='ERROR')
        return "(정보 없음)"


def query_count_info(driver, log):
    #평가 현황(대기, 진행, 완료) 정보
    try:
        statistic_sections = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "ant-statistic"))
        )
        log.log(f"평가 현황 섹션 {len(statistic_sections)}개를 찾았습니다.")

        # ... (기존 query_count_info 로직) ...
        valuation_pending = None
        valuation_in_progress = None
        valuation_completed = None

        for section in statistic_sections:
            try:
                title_element = section.find_element(By.CLASS_NAME, "ant-statistic-title")
                title_text = title_element.text.strip()
                if title_text == "평가대기":
                    value_element = section.find_element(By.CLASS_NAME, "ant-statistic-content-value-int")
                    valuation_pending = value_element.text.strip()
                elif title_text == "평가진행":
                    value_element = section.find_element(By.CLASS_NAME, "ant-statistic-content-value-int")
                    valuation_in_progress = value_element.text.strip()
                elif title_text == "평가완료":
                    value_element = section.find_element(By.CLASS_NAME, "ant-statistic-content-value-int")
                    valuation_completed = value_element.text.strip()
            except NoSuchElementException:
                continue
        log.log("✅ 평가 현황 정보 수집 완료.")
        return valuation_pending, valuation_in_progress, valuation_completed

    except Exception as e:
        log.log(f"❌ 평가 현황 정보 수집 중 오류: {str(e)}", level='ERROR')
        return None, None, None


def result_info(driver, log):
    #햄/스팸 문서 개수 정보
    try:
        statistic_sections = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "ant-statistic"))
        )
        log.log(f"햄/스팸 섹션 {len(statistic_sections)}개를 찾았습니다.")

        # ... (기존 result_info 로직) ...
        ham_count = None
        spam_count = None

        for section in statistic_sections:
            try:
                title_element = section.find_element(By.CLASS_NAME, "ant-statistic-title")
                title_text = title_element.text.strip()
                if title_text == "햄":
                    value_element = section.find_element(By.CLASS_NAME, "ant-statistic-content-value-int")
                    ham_count = value_element.text.strip()
                elif title_text == "스팸":
                    value_element = section.find_element(By.CLASS_NAME, "ant-statistic-content-value-int")
                    spam_count = value_element.text.strip()
            except NoSuchElementException:
                continue
        log.log("✅ 햄/스팸 문서 개수 정보 수집 완료.")
        return ham_count, spam_count

    except Exception as e:
        log.log(f"❌ 햄/스팸 정보 수집 중 오류: {str(e)}", level='ERROR')
        return None, None


# 평가 리포트 페이지 정보 크롤링

REPORT_URL = "https://dsat.dev.9rum.cc/#/valuation/result/report"


def click_report(driver, log):
    #'대기중' 상태 리포트 클릭
    try:
        log.log(f"평가리포트 페이지로 이동: {REPORT_URL}")
        driver.get(REPORT_URL)

        wait = WebDriverWait(driver, 25)

        log.log("리포트 카드 목록이 나타나기를 기다립니다...")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.ant-list-item")))

        all_cards = driver.find_elements(By.CSS_SELECTOR, "div.ant-list-item")
        log.log(f"✅ 총 {len(all_cards)}개의 리포트 카드를 찾았습니다.")

        # ... (기존 click_report 로직) ...
        target_card = None
        for card in all_cards:
            if '대기중' in card.text:
                target_card = card
                log.log("'대기중' 상태의 리포트를 찾았습니다.")
                break

        if target_card is None:
            raise ValueError("'대기중' 상태의 리포트가 없습니다.")

        link_element = target_card.find_element(By.CSS_SELECTOR, "div.ant-card-meta-title a")
        link_txt = link_element.text
        link_href = link_element.get_attribute('href')
        log.log(f"클릭할 리포트: {link_txt}")

        wait.until(EC.element_to_be_clickable(link_element)).click()

        log.log("상세 페이지가 로드되기를 기다립니다...")
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, "//*[text()='스팸율 - 문서 기준']"))
        )
        log.log(f"✅ 상세 페이지 로드 완료.")
        return link_txt, link_href

    except Exception as e:
        log.log(f"❌ '대기중' 리포트 처리 중 오류: {e}", level='ERROR')
        # ... (디버깅용 스크린샷/소스 저장 로직) ...
        return None, None


def get_spam_percentage(driver, log):
    #상세 페이지 스팸률 정보
    try:
        spam_rate_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//td[text()='스팸']/following-sibling::td[2]"))
        )
        spam_percentage = spam_rate_element.text
        log.log(f"✅ 스팸률 '{spam_percentage}' 가져오기 성공.")
        return spam_percentage
    except Exception as e:
        log.log(f"⚠️ 스팸률 정보 수집 실패: {e}", level='WARNING')
        return "(정보 없음)"


# 스팸 문서 목록을 크롤링하여 DataFrame으로 반환

def get_spam_doc(driver, log):
    #'스팸문서 예시' 테이블 데이터 DataFrame 반환
    try:
        log.log("스팸 문서 크롤링을 시작합니다.")

        # ... (기존 get_spam_doc 로직) ...
        spam_list_section_xpath = "//section[@id='spam-list']"
        spam_list_section = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, spam_list_section_xpath)))
        log.log("'스팸문서 예시' 섹션을 찾았습니다.")

        # 페이지당 100개 보기로 변경
        pagination_success = False
        for attempt in range(3):
            try:
                page_size_selector = 'li.ant-pagination-options div.ant-select-selector'
                page_size_dropdown = WebDriverWait(spam_list_section, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, page_size_selector))
                )
                if "100" not in page_size_dropdown.text:
                    page_size_dropdown.click()
                    option_xpath = "//div[contains(@class, 'ant-select-item-option-content') and contains(text(), '100')]"
                    option_100 = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, option_xpath))
                    )
                    option_100.click()
                    time.sleep(2)  # 데이터 로딩 대기
                    log.log("✅ 페이지당 100개 보기로 변경했습니다.")
                else:
                    log.log("페이지당 100개 보기가 이미 설정되어 있습니다.")
                pagination_success = True
                break
            except Exception as e:
                if attempt < 2:
                    driver.refresh()
                    spam_list_section = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, spam_list_section_xpath)))
                else:
                    raise e

        if not pagination_success: return None

        # 테이블 데이터 추출
        table = spam_list_section.find_element(By.CSS_SELECTOR, "div.ant-table-wrapper")
        headers = [h.text.strip() for h in table.find_elements(By.CSS_SELECTOR, "thead th") if h.text.strip()]
        desired_headers = ['검색어', '판정사유', 'Url']
        if 'Url' not in headers: headers.append('Url')

        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr.ant-table-row")
        final_data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            row_data = {}
            for i, cell in enumerate(cells):
                header = headers[i]
                if header in desired_headers:
                    if header == 'Url':
                        row_data[header] = cell.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    else:
                        row_data[header] = cell.text
            final_data.append(row_data)

        df = pd.DataFrame(final_data, columns=desired_headers)
        log.log(f"✅ {len(df)}개의 스팸 문서를 성공적으로 수집했습니다.")
        return df

    except Exception as e:
        log.log(f"❌ 스팸 문서 수집 중 오류: {str(e)}", level='ERROR')
        return None
