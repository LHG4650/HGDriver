# HGDriver (Windows-only)

크롬 버전과 Chromedriver를 자동으로 맞춰주는 간단한 매니저입니다. 기본적으로 실행 위치 아래 `HGDriver/`에 드라이버를 설치하며, Selenium에서 사용할 크롬 프로필도 별도로 생성합니다.

## 설치
로컬 editable 설치:
```
pip install -e .
```

Git 리포지토리에서 직접 설치:
```
pip install "git+https://github.com/LHG4650/HGDriver.git"
```

## 사용 예시
```python
from hgdriver import HGManager
import os

manager = HGManager()
# 원하는 경로로 드라이버 설치/사용 위치 지정 (선택)
manager.set_drive_file_path(os.getcwd())

driver = manager.get_driver(["--headless=new"])
driver.get("https://www.google.com")
print(driver.title)
driver.quit()
```

## 주요 기능
- MainChrome(설치된 크롬) 버전과 LocalDriver(다운로드한 chromedriver) 버전을 비교해 자동 다운로드/교체
- 보안 프로그램 트리거 방지: chromedriver 실행 대신 `LocalDriver.version` 파일로 버전 관리
- 별도 Selenium 프로필(`Selenium_Profile`) 생성으로 메인 크롬 프로필과 분리

## 공개 API
- `HGManager` (`HGChromeDriverManager` 별칭)
  - `set_drive_file_path(path)`: 드라이버 설치/사용 경로 지정
  - `get_MainChrome_version()`: 설치된 크롬 버전 조회 (없으면 예외)
  - `get_LocalDriver_version()`: 로컬 드라이버 버전 조회 (`LocalDriver.version` 파일)
  - `get_driver(options=None)`: 크롬/드라이버 버전 자동 맞춤 후 `selenium.webdriver.Chrome` 반환
- `kill_chromedriver()`: 실행 중인 `chromedriver.exe` 프로세스 종료

## 동작 환경
- Windows 전용 (레지스트리 조회 및 경로 기준)
- Python 3.9+

## 빌드/배포
```
python -m build
python -m twine upload dist/*
```
