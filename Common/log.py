import logging
import datetime
import os
import sys


class Log:
    """
    로그 기록 및 관리 클래스.
    - 로그를 파일과 콘솔에 출력하며, PyQt GUI 연동 시 GUI에 실시간 출력 가능.
    - 로그 파일은 'Log_YYYYMMDD.log' 형식으로 저장됨.
    - PyInstaller 실행 파일(.exe)과 일반 스크립트(.py) 환경 모두를 지원.
    """

    def __init__(self, gui_logger=None):
        """
        로그 클래스 초기화.
        :param gui_logger: PyQt 등의 GUI에 출력할 콜백 함수 (예: self.progress_signal.emit)
        """
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)   # exe 환경
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # py 환경

        self.log_dir = os.path.join(base_path, 'Log')
        os.makedirs(self.log_dir, exist_ok=True)

        self.log_file = os.path.join(self.log_dir, f'Log_{self._current_date_str()}.log')

        # 기존 핸들러 제거
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # 파일 핸들러 (UTF-8 강제 지정)
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '[%(levelname)s] %(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

        # 콘솔 핸들러 (UTF-8 강제 지정)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '[%(levelname)s] %(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

        logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

        self.gui_logger = gui_logger

    def _current_date_str(self):
        """현재 날짜를 'YYYYMMDD' 문자열로 반환 (로그 파일명에 사용)"""
        return datetime.datetime.now().strftime("%Y%m%d")

    def log(self, msg, level='INFO'):
        """
        메시지를 지정된 로그 레벨로 기록하고 콘솔 및 GUI에 출력합니다.
        :param msg: 출력할 메시지
        :param level: 로그 레벨 ('INFO', 'ERROR', 'DEBUG', 'WARNING')
        """
        level = level.upper()

        if level == "ERROR":
            logging.error(msg)
        elif level == "INFO":
            logging.info(msg)
        elif level == "WARNING":
            logging.warning(msg)
        elif level == "DEBUG":
            logging.debug(msg)
        else:
            print(f"알 수 없는 로그 레벨: {level}")
            return

        # GUI 로그 출력 (연결된 경우)
        if self.gui_logger:
            try:
                self.gui_logger(f"[{level}] {msg}")
            except Exception:
                pass
