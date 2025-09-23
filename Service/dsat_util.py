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
from knw_Chromedriver_manager import Chromedriver_manager


class DSATUtil:
    """
    DSAT 웹사이트 크롤링 및 스팸 문서 수집을 위한 클래스
    모든 함수를 하나의 클래스로 묶음
    """

    # 전역변수
    BASE_URL = "https://dsat.dev.9rum.cc/#/user/login"
    HOME_URL = "https://dsat.dev.9rum.cc/#/home"
    REPORT_URL = "https://dsat.dev.9rum.cc/#/valuation/result/report"

    def __init__(self, log, headless=False):
        self.log = log
        self.headless = headless
        self.driver = None


    # 크롬 드라이버 및 로그인 - 헤드리스 모드 선택 가능
    def login(self, username, password):
        try:
            self.log.log("웹 드라이버 설정을 시작합니다.")
            options = Options()
            options.add_argument("--start-maximized")

            if self.headless:
                self.log.log("헤드리스 모드로 실행합니다.")
                options.add_argument("--headless")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--disable-gpu")

            driver_path = Chromedriver_manager.install()
            self.driver = webdriver.Chrome(service=Service(driver_path), options=options)
            self.log.log("웹 드라이버가 성공적으로 생성되었습니다.")

            self.driver.get(self.BASE_URL)
            self.log.log(f"로그인 페이지로 이동: {self.BASE_URL}")

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(username)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "password"))
            ).send_keys(password + Keys.RETURN)
            self.log.log("아이디와 비밀번호를 입력했습니다.")

            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#root > div > section > div.ant-layout > header"))
            )
            self.log.log("✅ DSAT 로그인에 성공했습니다.")
            return True

        except Exception as e:
            self.log.log(f"❌ DSAT 로그인 실패: {str(e)}", level='ERROR')
            self.close()
            return False


    # 브라우저 종료
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None


    # DSAT 홈 정보 크롤링 - 평가 진행률
    def get_progress_info(self):
        try:
            self.log.log(f"홈 페이지로 이동: {self.HOME_URL}")
            self.driver.get(self.HOME_URL)
            progress_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ant-progress-text"))
            )
            progress_text_value = progress_element.text.strip()
            self.log.log(f"✅ '평가 진행율' 값 '{progress_text_value}' 가져오기 성공.")
            return progress_text_value
        except Exception as e:
            self.log.log(f"❌ 평가 진행률 정보 수집 중 오류: {str(e)}", level='ERROR')
            return "(정보 없음)"

    # 평가 현황 정보 크롤링
    def get_query_count_info(self):
        try:
            statistic_sections = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "ant-statistic"))
            )
            valuation_pending = None
            valuation_in_progress = None
            valuation_completed = None

            for section in statistic_sections:
                try:
                    title_element = section.find_element(By.CLASS_NAME, "ant-statistic-title")
                    title_text = title_element.text.strip()
                    value_element = section.find_element(By.CLASS_NAME, "ant-statistic-content-value-int")
                    value_text = value_element.text.strip()
                    if title_text == "평가대기":
                        valuation_pending = value_text
                    elif title_text == "평가진행":
                        valuation_in_progress = value_text
                    elif title_text == "평가완료":
                        valuation_completed = value_text
                except NoSuchElementException:
                    continue
            self.log.log("✅ 평가 현황 정보 수집 완료.")
            return valuation_pending, valuation_in_progress, valuation_completed

        except Exception as e:
            self.log.log(f"❌ 평가 현황 정보 수집 중 오류: {str(e)}", level='ERROR')
            return None, None, None


    # 햄/스팸 발생 문서 수 정보 크롤링
    def get_result_info(self):
        try:
            statistic_sections = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "ant-statistic"))
            )
            ham_count = None
            spam_count = None

            for section in statistic_sections:
                try:
                    title_element = section.find_element(By.CLASS_NAME, "ant-statistic-title")
                    title_text = title_element.text.strip()
                    value_element = section.find_element(By.CLASS_NAME, "ant-statistic-content-value-int")
                    value_text = value_element.text.strip()
                    if title_text == "햄":
                        ham_count = value_text
                    elif title_text == "스팸":
                        spam_count = value_text
                except NoSuchElementException:
                    continue
            self.log.log("✅ 햄/스팸 문서 개수 정보 수집 완료.")
            return ham_count, spam_count
        except Exception as e:
            self.log.log(f"❌ 햄/스팸 정보 수집 중 오류: {str(e)}", level='ERROR')
            return None, None


    # 현재 평가 진행 중인 리포트 페이지만 골라서 클릭
    def click_report(self):
        try:
            self.log.log(f"평가리포트 페이지로 이동: {self.REPORT_URL}")
            self.driver.get(self.REPORT_URL)
            wait = WebDriverWait(self.driver, 25)
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.ant-list-item")))

            all_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.ant-list-item")
            target_card = None
            for card in all_cards:
                if '대기중' in card.text:
                    target_card = card
                    break
            if not target_card:
                raise ValueError("'대기중' 상태의 리포트가 없습니다.")

            link_element = target_card.find_element(By.CSS_SELECTOR, "div.ant-card-meta-title a")
            link_txt = link_element.text
            link_href = link_element.get_attribute('href')
            wait.until(EC.element_to_be_clickable(link_element)).click()
            WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.XPATH, "//*[text()='스팸율 - 문서 기준']"))
            )
            self.log.log("✅ 리포트 상세 페이지 로드 완료.")
            return link_txt, link_href
        except Exception as e:
            self.log.log(f"❌ '대기중' 리포트 처리 중 오류: {str(e)}", level='ERROR')
            return None, None


    # 평가 진행 중인 차수의 스팸률만 가져오기
    def get_spam_percentage(self):
        try:
            spam_rate_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//td[text()='스팸']/following-sibling::td[2]"))
            )
            return spam_rate_element.text
        except Exception as e:
            self.log.log(f"⚠️ 스팸률 정보 수집 실패: {str(e)}", level='WARNING')
            return "(정보 없음)"


    # 스팸 문서 목록 데이터 크롤링 - 페이지 노출 문서 수 100개로 변경
    def get_spam_doc(self):
        try:
            self.log.log("스팸 문서 크롤링 시작")
            spam_list_section_xpath = "//section[@id='spam-list']"
            spam_list_section = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, spam_list_section_xpath))
            )
            self.log.log("'스팸문서 예시' 섹션을 찾았습니다.")

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
                        option_100 = WebDriverWait(self.driver, 15).until(
                            EC.element_to_be_clickable((By.XPATH, option_xpath))
                        )
                        option_100.click()
                        time.sleep(2)
                        self.log.log("✅ 페이지당 100개 보기로 변경했습니다.")
                    else:
                        self.log.log("페이지당 100개 보기가 이미 설정되어 있습니다.")
                    pagination_success = True
                    break
                except Exception as e:
                    if attempt < 2:
                        self.driver.refresh()
                        spam_list_section = WebDriverWait(self.driver, 20).until(
                            EC.presence_of_element_located((By.XPATH, spam_list_section_xpath))
                        )
                    else:
                        raise e

            if not pagination_success:
                return None

            # 테이블 데이터 추출
            table = spam_list_section.find_element(By.CSS_SELECTOR, "div.ant-table-wrapper")
            headers = [h.text.strip() for h in table.find_elements(By.CSS_SELECTOR, "thead th") if h.text.strip()]
            desired_headers = ['검색어', '판정사유', 'Url']
            if 'Url' not in headers:
                headers.append('Url')

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

            import pandas as pd
            df = pd.DataFrame(final_data, columns=desired_headers)
            self.log.log(f"✅ {len(df)}개의 스팸 문서를 성공적으로 수집했습니다.")
            return df

        except Exception as e:
            self.log.log(f"❌ 스팸 문서 수집 중 오류: {str(e)}", level='ERROR')
            return None

