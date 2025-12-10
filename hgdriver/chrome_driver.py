import os
import zipfile
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import subprocess
import psutil


def kill_chromedriver():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and "chromedriver.exe" in proc.info['name'].lower():
                print(f"기존 크롬드라이버 종료: PID={proc.info['pid']}")
                proc.terminate()   # 프로세스 종료 요청
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass



class HGChromeDriverManager:
    """
    크롬 및 크롬드라이버 버전 관리, 다운로드, 실행을 담당하는 매니저 클래스 (Windows 전용)
    """
    def __init__(self, program_dir=None, driver_path=None, chrome_binary=None, print_fn=None):
        # 기본 경로: 현재 실행 위치\HGDriver\chromedriver-win64\chromedriver.exe
        default_program_dir = os.path.join(os.getcwd(), "HGDriver")
        self.program_dir = program_dir or default_program_dir
        self.driver_path = driver_path or os.path.join(self.program_dir, "chromedriver-win64", "chromedriver.exe")
        self.chrome_binary = chrome_binary or r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.print_fn = print_fn if print_fn is not None else print
        self.driver = None

    def set_paths(self, program_dir=None, driver_path=None, chrome_binary=None):
        """
        드라이버/프로그램/크롬 바이너리 경로를 동적으로 변경
        """
        if program_dir:
            self.program_dir = program_dir
            if not driver_path:
                self.driver_path = os.path.join(self.program_dir, "chromedriver-win64", "chromedriver.exe")
        if driver_path:
            self.driver_path = driver_path
        if chrome_binary:
            self.chrome_binary = chrome_binary

    def set_drive_file_path(self, base_dir):
        """
        사용자가 원하는 디렉터리를 기준으로 드라이버 설치 경로를 설정
        예) manager.set_drive_file_path(os.getcwd())
        """
        self.set_paths(program_dir=base_dir)

    def get_MainChrome_version(self):
        """
        현재 PC에 설치된 메인 크롬 브라우저(MainChrome) 버전 반환
        """
        try:
            output = subprocess.check_output(
                r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
                shell=True
            ).decode("utf-8")
            version = output.strip().split()[-1]
            return version
        except Exception as e:
            self.print_fn(f"[오류] 크롬 버전 확인 실패: {e}")
            raise RuntimeError("크롬을 찾을 수 없습니다. Chrome 설치를 확인하세요.")

    def get_LocalDriver_version(self):
        """
        로컬 드라이버(LocalDriver) 버전 반환.
        보안 도구 트리거를 피하기 위해 바이너리 실행 대신 버전 파일을 읽음.
        """
        version_file = os.path.join(os.path.dirname(self.driver_path), "LocalDriver.version")
        if os.path.exists(version_file):
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                self.print_fn(f"[오류] LocalDriver.version 읽기 실패: {e}")
                return None
        # 버전 파일이 없으면 조용히 None 반환
        return None

    def download_driver(self, version):
        """
        지정 버전의 chromedriver를 다운로드하고 zip 파일 경로 반환
        """
        url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip"
        zip_file_path = f"chromedriver_{version}.zip"
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(zip_file_path, "wb") as file:
                file.write(response.content)
            self.print_fn(f"Chromedriver {version} 다운로드 성공")
            return zip_file_path
        except Exception as e:
            self.print_fn(f"[오류] Chromedriver {version} 다운로드 실패: {e}")
            return None

    def extract_zip(self, zip_file, extract_to="."):
        """
        zip 파일 압축 해제
        """
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(extract_to)

    def update_driver(self, version):
        """
        chromedriver를 다운로드 및 압축 해제하여 driver_path 위치에 배치
        """
        zip_path = self.download_driver(version)
        if not zip_path:
            raise RuntimeError("Chromedriver 다운로드 실패")
        os.makedirs(self.program_dir, exist_ok=True)
        self.extract_zip(zip_path, self.program_dir)
        os.remove(zip_path)
        # 보안 프로그램 트리거를 피하기 위해 버전 정보를 별도 파일에 저장
        try:
            version_file = os.path.join(os.path.dirname(self.driver_path), "LocalDriver.version")
            with open(version_file, "w", encoding="utf-8") as f:
                f.write(str(version))
        except Exception as e:
            self.print_fn(f"[경고] LocalDriver.version 파일 저장 실패: {e}")

    def create_chrome_profile_path(self):
        """
        Selenium용 크롬 사용자 프로필 경로 생성 및 반환
        """
        user_profile = os.environ.get("USERPROFILE", "")
        profile_path = os.path.join(
            user_profile, "AppData", "Local", "Google", "Chrome", "User Data", "Selenium_Profile"
        )
        os.makedirs(profile_path, exist_ok=True)
        return profile_path

    def get_webdriver(self, options=None):
        """
        selenium.webdriver.Chrome 인스턴스 반환
        """
        chrome_options = Options()
        chrome_profile_path = self.create_chrome_profile_path()
        chrome_options.add_argument(f"user-data-dir={chrome_profile_path}")

        if options:
            for opt in options:
                chrome_options.add_argument(opt)

        if os.path.exists(self.chrome_binary):
            chrome_options.binary_location = self.chrome_binary

        service = Service(self.driver_path)
        return webdriver.Chrome(service=service, options=chrome_options)

    def get_driver(self, options=None):
        """
        메인 크롬(MainChrome)과 로컬 드라이버(LocalDriver) 버전이 다르면
        자동으로 드라이버를 맞추고 webdriver 인스턴스 반환
        """
        MainChrome_version = self.get_MainChrome_version()
        LocalDriver_version = self.get_LocalDriver_version()

        if not MainChrome_version:
            raise RuntimeError("크롬 브라우저를 찾을 수 없습니다.")
        if MainChrome_version != LocalDriver_version:
            self.print_fn(
                f"LocalDriver 버전({LocalDriver_version})과 MainChrome 버전({MainChrome_version})이 달라 드라이버를 업데이트합니다."
            )
            self.update_driver(MainChrome_version)

        self.driver = self.get_webdriver(options)
        return self.driver


# 사용 편의를 위한 짧은 이름
HGManager = HGChromeDriverManager

if __name__ == "__main__":
    manager = HGChromeDriverManager()
    print("MainChrome 버전: ", manager.get_MainChrome_version())
    print("LocalDriver 버전: ", manager.get_LocalDriver_version())
    print("드라이버 버전 확인 완료")
    manager.get_driver()

