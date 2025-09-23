import sys
import os
import traceback
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QLineEdit
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.uic import loadUi
from PyQt5.QtGui import QIcon
from Common.log import Log
from Service.dsat_util import DSATUtil
from Service import agit_webhook
from tabulate import tabulate
import setup.knw_license


# PyInstaller 실행 파일(.exe)을 위한 리소스 경로 변환 함수
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# 백그라운드 작업 영역
class ScrapingWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, username, password, headless_mode):
        super().__init__()
        self.username = username
        self.password = password
        self.headless_mode = headless_mode

    def run(self):
        log = Log(gui_logger=self.progress.emit)
        try:
            log.log("★ 스팸률 수집 작업을 시작합니다. ★")
            dsat = DSATUtil(log=log, headless=self.headless_mode)

            # 로그인
            if not dsat.login(self.username, self.password):
                raise ConnectionError("비밀번호 오류 또는 로그인 실패")

            # 홈 정보 수집
            progress_text_value = dsat.get_progress_info()
            dsat.get_query_count_info()
            dsat.get_result_info()

            # 리포트 클릭
            link_txt, link_href = dsat.click_report()
            if link_txt is None or link_href is None:
                raise ValueError("'대기중' 상태인 평가 리포트 클릭 실패")

            # 스팸률 및 문서 수집
            spam_percentage = dsat.get_spam_percentage()
            spam_documents_df = dsat.get_spam_doc()

            # 아지트 글 작성 영역
            agit_txt = ""
            spam_doc_count = 0
            if spam_documents_df is not None and not spam_documents_df.empty:
                spam_doc_count = len(spam_documents_df)
                log.log(f"✅ 스팸 문서 {spam_doc_count}건 수집 완료.")

                spam_text = tabulate(
                    spam_documents_df.values.tolist(),
                    headers=spam_documents_df.columns.tolist(),
                    tablefmt="plain", stralign="left", numalign="left"
                )
                agit_txt = (
                    f'<인덱스평가 *{link_txt}* 스팸 발생 현황 알림>\n'
                    f'# 스팸률은 현재 {spam_percentage}입니다.\n'
                    f'# 평가 진행률은 현재 {progress_text_value}입니다.\n\n'
                    '────────────────────────────────\n'
                    '*[스팸 문서 목록]*\n'
                    f'{spam_text}\n'
                    '────────────────────────────────\n'
                    f'[리포트 페이지 : {link_href}]\n\n\n'
                    '@namoo.kim\n'
                    '@@index\n'
                )
            else:
                log.log("수집된 스팸 문서가 없습니다.")

            result_data = {
                'link_txt': link_txt,
                'spam_percentage': spam_percentage,
                'progress_text_value': progress_text_value,
                'spam_doc_count': spam_doc_count,
                'agit_txt': agit_txt
            }
            self.finished.emit(result_data)

        except Exception as e:
            error_msg = f"작업 중 오류 발생: {str(e)}"
            log.log(error_msg, level='ERROR')
            log.log(traceback.format_exc(), level='ERROR')
            self.error.emit(str(e))
        finally:
            dsat.close()
            log.gui_logger = None
            log.log("★ 크롬 브라우저 종료 완료 ★")



# 아지트 공유 버튼 작동 영역
class AgitShareWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, text_to_share):
        super().__init__()
        self.agit_txt = text_to_share

    def run(self):
        try:
            agit_webhook.AgitPost(self.agit_txt)
            self.finished.emit(True, "아지트에 성공적으로 공유되었습니다.")
        except Exception as e:
            self.finished.emit(False, f"아지트 공유에 실패했습니다:\n{str(e)}")



# 메인 윈도우
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        ui_file_path = resource_path(os.path.join("Resource", "main_window.ui"))
        icon_path = resource_path(os.path.join("Resource", "favicon_64x64.ico"))
        loadUi(ui_file_path, self)
        self.setWindowIcon(QIcon(icon_path))

        self.worker = None
        self.agit_worker = None
        self.agit_txt = ""

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.trigger_scraping)

        self.button_start.clicked.connect(self.start_auto_refresh)
        self.button_stop.clicked.connect(self.stop_auto_refresh)
        self.button_share_agit.clicked.connect(self.share_to_agit)
        self.button_stop.setEnabled(False)
        self.button_share_agit.setEnabled(False)
        self.lineEdit_password.setEchoMode(QLineEdit.Password)

    # 자동 새로고침 영역_로그인
    def start_auto_refresh(self):
        self.username = self.lineEdit_username.text()
        self.password = self.lineEdit_password.text()
        if not self.username or not self.password:
            QMessageBox.warning(self, "입력 오류", "아이디와 비밀번호를 모두 입력해주세요.")
            return

        interval_minutes = self.spinBox_interval.value()
        self.timer.start(interval_minutes * 60 * 1000)
        self.set_controls_enabled(False)
        self.label_status.setText(f"상태: {interval_minutes}분 간격으로 새로고침 시작.")
        self.trigger_scraping()

    # 자동 새로고침 영역_정지
    def stop_auto_refresh(self):
        self.timer.stop()
        self.set_controls_enabled(True)
        self.label_status.setText("상태: 자동 새로고침 중지됨.")

    # 자동 새로고침 영역_정보 표시
    def trigger_scraping(self):
        self.button_share_agit.setEnabled(False)
        self.label_status.setText("상태: 정보 수집 중...")
        headless_mode = self.checkBox_headless.isChecked()
        self.worker = ScrapingWorker(self.username, self.password, headless_mode)
        self.worker.finished.connect(self.update_ui_data)
        self.worker.error.connect(self.handle_error)
        self.worker.progress.connect(self.update_status_label)
        self.worker.start()

    # 자동 새로고침 영역_수집된 정보 ui 표시
    def update_ui_data(self, data):
        self.label_link_txt.setText(f"차수: {data.get('link_txt', 'N/A')}")
        self.label_spam_percentage.setText(f"스팸률: {data.get('spam_percentage', 'N/A')}")
        self.label_progress.setText(f"평가진행률: {data.get('progress_text_value', 'N/A')}")
        self.label_spam_doc_count.setText(f"스팸 문서 개수: {data.get('spam_doc_count', 0)}개")

        self.agit_txt = data.get('agit_txt', '')
        self.button_share_agit.setEnabled(bool(self.agit_txt))
        self.button_share_agit.setText("아지트 공유하기" if self.agit_txt else "공유할 스팸 없음")

        current_time = datetime.now().strftime("%H:%M:%S")
        if self.timer.isActive():
            interval = self.spinBox_interval.value()
            self.label_status.setText(f"상태: 마지막 업데이트 {current_time}. {interval}분 후 다음 실행.")
        else:
            self.label_status.setText(f"상태: 업데이트 완료 ({current_time})")

    # 자동 새로고침 영역_오류 알림
    def handle_error(self, error_msg):
        QMessageBox.critical(self, "오류", f"크롤링 중 오류가 발생했습니다:\n{error_msg}")
        self.label_status.setText("상태: 오류 발생으로 중지됨.")
        if self.timer.isActive():
            self.stop_auto_refresh()

    # ui 하단 진행 상태 표시
    def update_status_label(self, text):
        self.label_status.setText(f"상태: {text}")

    # 아지트 공유 처리 영역
    def share_to_agit(self):
        if not self.agit_txt:
            QMessageBox.warning(self, "알림", "공유할 내용이 없습니다.")
            return
        self.button_share_agit.setEnabled(False)
        self.button_share_agit.setText("공유 중...")
        self.agit_worker = AgitShareWorker(self.agit_txt)
        self.agit_worker.finished.connect(self.on_agit_share_finished)
        self.agit_worker.start()

    # 아지트 공유 완료/오류시 작동
    def on_agit_share_finished(self, success, message):
        if success:
            QMessageBox.information(self, "성공", message)
            self.button_share_agit.setText("공유 완료")
        else:
            QMessageBox.critical(self, "오류", message)
            self.button_share_agit.setEnabled(True)
            self.button_share_agit.setText("아지트 공유하기")

    # ui 세팅
    def set_controls_enabled(self, is_enabled):
        self.button_start.setEnabled(is_enabled)
        self.button_stop.setEnabled(not is_enabled)
        self.spinBox_interval.setEnabled(is_enabled)
        self.lineEdit_username.setEnabled(is_enabled)
        self.lineEdit_password.setEnabled(is_enabled)
        self.checkBox_headless.setEnabled(is_enabled)

    # 작업 종료
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        event.accept()



# 실행
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
