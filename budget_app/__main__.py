"""``python -m budget_app`` 명령의 시작점입니다.

패키지를 모듈로 실행하면 Python이 이 파일을 찾아 실행합니다. 프로그램의
구체적인 명령 처리 코드는 ``cli.py``에 두고, 이 파일은 시작 역할만 담당합니다.
"""

from .cli import main


if __name__ == "__main__":
    # main()이 돌려주는 종료 코드를 운영체제에 전달합니다.
    # 정상은 0, 사용자 입력/파일 오류는 1, Ctrl+C는 130입니다.
    raise SystemExit(main())
