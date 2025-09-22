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
        # .exe 환경과 .py 환경 모두에서 올바른 경로를 찾도록 수정
        if getattr(sys, 'frozen', False):
            # .exe로 실행된 경우, 실행 파일이 있는 디렉토리를 기준으로 경로 설정
            base_path = os.path.dirname(sys.executable)
        else:
            # .py 스크립트로 실행된 경우, 이 파일이 있는 디렉토리의 상위 폴더(프로젝트 루트)를 기준
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.log_dir = os.path.join(base_path, 'Log')
        os.makedirs(self.log_dir, exist_ok=True)

        self.log_file = os.path.join(self.log_dir, f'Log_{self._current_date_str()}.log')

        # 로그 메시지가 중복으로 출력되는 것을 방지하기 위해 기존 핸들러를 모두 제거
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # 새로운 로그 설정 적용
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='[%(levelname)s] %(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            encoding='utf-8'
        )

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

        # 1. 로그 파일에 기록
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

        # 2. 콘솔에 출력 (시간을 포함하여 즉시 확인 용이)
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        print(f"[{level}] {timestamp} - {msg}")

        # 3. GUI 로그 출력 (연결된 경우)
        if self.gui_logger:
            try:
                # GUI에는 레벨과 메시지를 함께 전달하여 더 자세한 정보 제공
                self.gui_logger(f"[{level}] {msg}")
            except Exception as e:
                # GUI가 닫혔을 때 오류가 발생할 수 있으므로 간단히 처리
                pass
