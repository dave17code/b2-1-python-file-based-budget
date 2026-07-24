"""로그와 실행 시간 측정을 담당하는 데코레이터입니다.

거래 추가, 수정, 삭제, 요약 같은 여러 메서드에 같은 로깅 코드를 반복하지 않고
``@log_execution`` 한 줄로 공통 관심사를 적용합니다. 이것이 미션에서 요구하는
데코레이터 분리의 실제 예입니다.
"""

from __future__ import annotations

import logging
from functools import wraps
from time import perf_counter
from typing import Any, Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")
LOGGER = logging.getLogger("budget_app")


def log_execution(func: Callable[P, R]) -> Callable[P, R]:
    """함수 성공/실패와 실행 시간을 ``data/app.log``에 기록합니다."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        started = perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            elapsed_ms = (perf_counter() - started) * 1000
            LOGGER.error(
                "action=%s status=failed elapsed_ms=%.3f error=%s",
                func.__qualname__,
                elapsed_ms,
                exc,
            )
            # 예외를 여기서 숨기지 않고 다시 발생시켜 CLI의 공통 오류 처리로 보냅니다.
            raise

        elapsed_ms = (perf_counter() - started) * 1000
        LOGGER.info(
            "action=%s status=success elapsed_ms=%.3f",
            func.__qualname__,
            elapsed_ms,
        )
        return result

    return wrapper
