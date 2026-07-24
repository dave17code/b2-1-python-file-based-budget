"""사용자에게 안전하게 보여 줄 애플리케이션 예외를 정의합니다.

CLI 프로그램에서 예상 가능한 오류까지 Python 스택트레이스로 출력하면 사용자가
문제를 이해하기 어렵습니다. 이 프로젝트는 예상 가능한 오류를 아래 예외로 바꾼 뒤
``[오류]``와 ``[힌트]`` 형식으로 출력합니다.
"""


class BudgetAppError(Exception):
    """가계부에서 예상하고 처리할 수 있는 모든 오류의 부모 클래스입니다."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class ValidationError(BudgetAppError):
    """날짜, 금액, 타입 등 사용자 입력값이 규칙에 맞지 않을 때 사용합니다."""


class NotFoundError(BudgetAppError):
    """요청한 거래, 카테고리 또는 파일이 존재하지 않을 때 사용합니다."""


class ConflictError(BudgetAppError):
    """중복 카테고리나 사용 중인 카테고리 삭제처럼 충돌이 있을 때 사용합니다."""


class StorageError(BudgetAppError):
    """JSONL/CSV 파일을 읽거나 저장할 수 없을 때 사용합니다."""
