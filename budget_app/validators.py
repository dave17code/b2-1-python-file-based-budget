"""CLI와 서비스에서 공통으로 사용하는 입력 검증 함수입니다.

검증을 한 파일에 모으면 add, update, search, import가 모두 같은 규칙을 사용합니다.
잘못된 값은 ``ValidationError``로 바꾸어 CLI가 스택트레이스 없이 안내합니다.
"""

from __future__ import annotations

from datetime import datetime
import re

from .errors import ValidationError

ALLOWED_TYPES = {"income", "expense"}


def validate_date(value: str) -> str:
    """문자열이 실제로 존재하는 ``YYYY-MM-DD`` 날짜인지 검증합니다."""

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        raise ValidationError(
            "날짜 형식이 올바르지 않습니다.",
            "YYYY-MM-DD 형식으로 입력하세요. 예: 2026-07-22",
        )

    try:
        # 정규식은 모양만 확인하므로 2026-13-40 같은 값은 strptime으로 다시 검사합니다.
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError(
            "존재하지 않는 날짜입니다.",
            "실제 달력에 있는 날짜를 입력하세요. 예: 2026-07-22",
        ) from exc

    return value


def validate_month(value: str) -> str:
    """문자열이 ``YYYY-MM`` 형식의 실제 월인지 검증합니다."""

    if re.fullmatch(r"\d{4}-\d{2}", value) is None:
        raise ValidationError(
            "월 형식이 올바르지 않습니다.",
            "YYYY-MM 형식으로 입력하세요. 예: 2026-07",
        )

    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError as exc:
        raise ValidationError(
            "존재하지 않는 월입니다.",
            "01부터 12 사이의 월을 입력하세요. 예: 2026-07",
        ) from exc

    return value


def validate_amount(value: int | str) -> int:
    """금액을 양수 정수로 변환하여 반환합니다."""

    try:
        amount = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "금액은 정수여야 합니다.",
            "0보다 큰 정수를 입력하세요. 예: 15000",
        ) from exc

    if amount <= 0:
        raise ValidationError(
            "금액은 0보다 커야 합니다.",
            "양수 정수를 입력하세요. 예: 15000",
        )

    return amount


def validate_transaction_type(value: str) -> str:
    """거래 타입을 소문자로 정규화하고 income/expense인지 확인합니다."""

    normalized = value.strip().lower()
    if normalized not in ALLOWED_TYPES:
        raise ValidationError(
            "거래 타입이 올바르지 않습니다.",
            "income 또는 expense 중 하나를 입력하세요.",
        )
    return normalized


def validate_category_name(value: str) -> str:
    """카테고리 이름을 소문자로 정규화하고 공백 사용을 막습니다."""

    normalized = value.strip().lower()
    if not normalized:
        raise ValidationError(
            "카테고리 이름은 비어 있을 수 없습니다.",
            "예: food, transport, salary",
        )
    if any(character.isspace() for character in normalized):
        raise ValidationError(
            "카테고리 이름에는 공백을 사용할 수 없습니다.",
            "공백 대신 하이픈(-) 또는 밑줄(_)을 사용하세요.",
        )
    return normalized


def parse_tags(value: str | list[str] | None) -> list[str]:
    """쉼표 문자열 또는 문자열 리스트를 중복 없는 태그 리스트로 변환합니다."""

    if value is None:
        return []

    raw_tags = value if isinstance(value, list) else value.split(",")
    result: list[str] = []
    seen: set[str] = set()

    for raw_tag in raw_tags:
        tag = str(raw_tag).strip().lower()
        if tag and tag not in seen:
            result.append(tag)
            seen.add(tag)

    return result


def validate_date_range(from_date: str | None, to_date: str | None) -> None:
    """선택 날짜 범위를 검증하고 시작일이 종료일보다 늦지 않게 합니다."""

    if from_date is not None:
        validate_date(from_date)
    if to_date is not None:
        validate_date(to_date)
    if from_date and to_date and from_date > to_date:
        raise ValidationError(
            "검색 시작일이 종료일보다 늦습니다.",
            "--from 날짜가 --to 날짜보다 빠르거나 같아야 합니다.",
        )
