"""프로그램에서 주고받는 데이터 구조를 ``dataclass``로 정의합니다.

모델은 데이터를 표현하는 책임만 가집니다. 파일을 읽는 방법이나 거래를 추가하는
규칙은 각각 ``repositories.py``와 ``services.py``가 담당합니다. 이렇게 책임을
나누면 저장 형식이나 CLI가 바뀌어도 모델 코드를 크게 수정하지 않아도 됩니다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Transaction:
    """수입 또는 지출 거래 한 건을 표현합니다.

    ``slots=True``는 정의하지 않은 속성이 실수로 추가되는 것을 막고, 일반적인
    dataclass보다 메모리를 조금 절약합니다.
    """

    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """JSONL에 기록할 수 있도록 dataclass를 딕셔너리로 변환합니다."""

        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        """JSONL 한 줄을 읽어 만든 딕셔너리를 Transaction으로 복원합니다."""

        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            date=str(data["date"]),
            amount=int(data["amount"]),
            category=str(data["category"]),
            memo=str(data.get("memo", "")),
            tags=[str(tag) for tag in data.get("tags", [])],
        )


@dataclass(slots=True)
class Budget:
    """특정 월의 지출 예산을 표현합니다."""

    month: str
    amount: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Budget":
        return cls(month=str(data["month"]), amount=int(data["amount"]))


@dataclass(slots=True)
class SearchCriteria:
    """search 명령에 전달되는 선택 검색 조건을 한 객체로 묶습니다."""

    from_date: str | None = None
    to_date: str | None = None
    category: str | None = None
    transaction_type: str | None = None
    query: str | None = None
    tag: str | None = None


@dataclass(slots=True)
class MonthlySummary:
    """summary 명령이 화면에 출력할 월별 집계 결과입니다."""

    month: str
    total_income: int
    total_expense: int
    balance: int
    expense_by_category: list[tuple[str, int]]
    transaction_count: int
    budget: int | None = None

    @property
    def budget_usage_percent(self) -> float | None:
        """예산이 있을 때 지출액의 예산 사용률을 계산합니다."""

        if self.budget is None:
            return None
        return (self.total_expense / self.budget) * 100

    @property
    def is_budget_exceeded(self) -> bool:
        """총지출이 설정된 예산보다 큰지 알려 줍니다."""

        return self.budget is not None and self.total_expense > self.budget
