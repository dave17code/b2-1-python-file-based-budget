"""JSONL 파일 입출력과 저장소(Repository) 계층을 구현합니다.

Repository는 데이터를 어디에, 어떤 형식으로 저장하는지 책임집니다. 서비스는
``transactions.jsonl``의 세부 구조를 몰라도 ``add()``, ``update()`` 같은 메서드를
통해 데이터를 사용할 수 있습니다.

핵심 학습 포인트
----------------
1. ``iter_records()``는 한 줄씩 ``yield``하여 전체 파일을 메모리에 올리지 않습니다.
2. ``iter_records_reverse()``는 파일 끝에서 읽어 최신 거래부터 스트리밍합니다.
3. update/delete는 임시 파일을 완성한 뒤 ``os.replace()``로 원자 교체합니다.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Generator, Iterable
from pathlib import Path
from typing import Any

from .errors import StorageError
from .models import Budget, Transaction

DEFAULT_CATEGORIES = [
    "food",
    "transport",
    "rent",
    "utilities",
    "salary",
    "health",
    "education",
    "etc",
]


def _serialize_json_line(data: dict[str, Any]) -> str:
    """딕셔너리를 한 줄짜리 UTF-8 JSON 문자열로 변환합니다."""

    return json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"


class JsonlFile:
    """특정 JSONL 파일 한 개를 다루는 저수준 도우미 클래스입니다."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.was_created = not path.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def append(self, data: dict[str, Any]) -> None:
        """JSON 객체 한 건을 파일 끝에 추가하고 디스크까지 반영합니다."""

        try:
            with self.path.open("a", encoding="utf-8", newline="") as file:
                file.write(_serialize_json_line(data))
                file.flush()
                # flush는 Python 버퍼, fsync는 운영체제 버퍼를 디스크에 반영합니다.
                os.fsync(file.fileno())
        except OSError as exc:
            raise StorageError(
                f"파일에 데이터를 저장하지 못했습니다: {self.path}",
                "저장 폴더의 존재 여부와 쓰기 권한을 확인하세요.",
            ) from exc

    def iter_records(self) -> Generator[dict[str, Any], None, None]:
        """파일 앞에서부터 JSON 객체를 한 건씩 생성하는 제너레이터입니다."""

        try:
            with self.path.open("r", encoding="utf-8") as file:
                for line_number, line in enumerate(file, start=1):
                    if not line.strip():
                        continue
                    yield self._decode_line(line, location=f"{line_number}번째 줄")
        except OSError as exc:
            raise StorageError(
                f"파일을 읽지 못했습니다: {self.path}",
                "파일의 존재 여부와 읽기 권한을 확인하세요.",
            ) from exc

    def iter_records_reverse(self) -> Generator[dict[str, Any], None, None]:
        """파일 끝에서부터 JSON 객체를 한 건씩 생성합니다.

        거래는 추가될수록 파일 끝에 기록되므로, 역순 읽기를 사용하면 전체 목록을
        메모리에 적재하고 뒤집지 않아도 최신순으로 출력할 수 있습니다.
        """

        for reverse_index, line in enumerate(self._iter_lines_reverse(), start=1):
            yield self._decode_line(line, location=f"끝에서 {reverse_index}번째 줄")

    def rewrite(self, records: Iterable[dict[str, Any]]) -> None:
        """임시 파일을 완성한 뒤 기존 파일과 원자적으로 교체합니다.

        기존 파일을 바로 덮어쓰다가 프로그램이 중단되면 일부 데이터만 남을 수
        있습니다. 같은 폴더에 임시 파일을 만든 후 ``os.replace``를 호출하면 교체
        순간 전까지 기존 파일이 유지되어 update/delete가 더 안전해집니다.
        """

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                for record in records:
                    temporary_file.write(_serialize_json_line(record))
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, self.path)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise StorageError(
                f"파일을 안전하게 갱신하지 못했습니다: {self.path}",
                "저장 공간과 폴더 쓰기 권한을 확인하세요.",
            ) from exc

    def _decode_line(self, line: str, *, location: str) -> dict[str, Any]:
        """JSONL 한 줄을 딕셔너리로 변환하고 손상 여부를 검사합니다."""

        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise StorageError(
                f"JSONL 데이터가 손상되었습니다: {self.path.name} {location}",
                "손상된 줄을 수정하거나 정상 파일로 복구하세요.",
            ) from exc

        if not isinstance(data, dict):
            raise StorageError(
                f"JSONL 객체 형식이 올바르지 않습니다: {self.path.name} {location}",
                "각 줄이 JSON 객체인지 확인하세요.",
            )
        return data

    def _iter_lines_reverse(self, chunk_size: int = 8192) -> Generator[str, None, None]:
        """바이너리 파일을 일정 크기로 나눠 끝에서부터 줄 단위로 반환합니다."""

        try:
            with self.path.open("rb") as file:
                file.seek(0, os.SEEK_END)
                position = file.tell()
                buffer = b""

                while position > 0:
                    read_size = min(chunk_size, position)
                    position -= read_size
                    file.seek(position)
                    buffer = file.read(read_size) + buffer
                    lines = buffer.split(b"\n")
                    # 첫 조각은 줄 중간에서 잘렸을 수 있으므로 다음 반복까지 보관합니다.
                    buffer = lines[0]

                    for raw_line in reversed(lines[1:]):
                        if raw_line.strip():
                            yield raw_line.decode("utf-8")

                if buffer.strip():
                    yield buffer.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise StorageError(
                f"파일을 역순으로 읽지 못했습니다: {self.path}",
                "파일이 UTF-8 JSONL 형식인지 확인하세요.",
            ) from exc


class TransactionRepository:
    """거래 데이터 전용 저장소입니다."""

    def __init__(self, data_dir: Path) -> None:
        self.store = JsonlFile(data_dir / "transactions.jsonl")

    def add(self, transaction: Transaction) -> None:
        self.store.append(transaction.to_dict())

    def iter_all(self, *, latest_first: bool = False) -> Generator[Transaction, None, None]:
        """거래를 요청한 순서로 한 건씩 반환합니다."""

        records = (
            self.store.iter_records_reverse()
            if latest_first
            else self.store.iter_records()
        )
        for record in records:
            try:
                yield Transaction.from_dict(record)
            except (KeyError, TypeError, ValueError) as exc:
                raise StorageError(
                    "거래 데이터 필드가 손상되었습니다.",
                    "transactions.jsonl의 id/type/date/amount/category 필드를 확인하세요.",
                ) from exc

    def get_by_id(self, transaction_id: str) -> Transaction | None:
        for transaction in self.iter_all():
            if transaction.id == transaction_id:
                return transaction
        return None

    def next_id(self) -> str:
        """현재 가장 큰 TX 번호 다음 값을 생성합니다."""

        largest_number = 0
        for transaction in self.iter_all():
            if not transaction.id.startswith("TX-"):
                continue
            try:
                largest_number = max(largest_number, int(transaction.id[3:]))
            except ValueError:
                # 형식이 다른 id는 건너뛰고 정상 TX 번호만 기준으로 삼습니다.
                continue
        return f"TX-{largest_number + 1:06d}"

    def update(self, replacement: Transaction) -> bool:
        found = False

        def updated_records() -> Generator[dict[str, Any], None, None]:
            nonlocal found
            for transaction in self.iter_all():
                if transaction.id == replacement.id:
                    found = True
                    yield replacement.to_dict()
                else:
                    yield transaction.to_dict()

        self.store.rewrite(updated_records())
        return found

    def delete(self, transaction_id: str) -> bool:
        found = False

        def remaining_records() -> Generator[dict[str, Any], None, None]:
            nonlocal found
            for transaction in self.iter_all():
                if transaction.id == transaction_id:
                    found = True
                    continue
                yield transaction.to_dict()

        self.store.rewrite(remaining_records())
        return found

    def category_in_use(self, category: str) -> bool:
        return any(transaction.category == category for transaction in self.iter_all())


class CategoryRepository:
    """카테고리 데이터 전용 저장소입니다."""

    def __init__(self, data_dir: Path) -> None:
        self.store = JsonlFile(data_dir / "categories.jsonl")

        # 미션의 초기 실행 정책 중 '기본 카테고리 자동 생성' 방식을 선택했습니다.
        # 기존 파일을 사용자가 비운 경우에는 의도한 상태로 보고 자동 복원하지 않습니다.
        if self.store.was_created:
            self.store.rewrite({"name": name} for name in DEFAULT_CATEGORIES)

    def iter_all(self) -> Generator[str, None, None]:
        for record in self.store.iter_records():
            name = record.get("name")
            if not isinstance(name, str):
                raise StorageError(
                    "카테고리 데이터가 손상되었습니다.",
                    "categories.jsonl의 name 필드를 확인하세요.",
                )
            yield name

    def list_all(self) -> list[str]:
        # 카테고리 수는 작고 화면에 전체 목록을 보여야 하므로 리스트로 반환합니다.
        return list(self.iter_all())

    def exists(self, name: str) -> bool:
        return any(category == name for category in self.iter_all())

    def add(self, name: str) -> None:
        self.store.append({"name": name})

    def remove(self, name: str) -> bool:
        found = False

        def remaining_records() -> Generator[dict[str, Any], None, None]:
            nonlocal found
            for category in self.iter_all():
                if category == name:
                    found = True
                    continue
                yield {"name": category}

        self.store.rewrite(remaining_records())
        return found


class BudgetRepository:
    """월별 예산 데이터 전용 저장소입니다."""

    def __init__(self, data_dir: Path) -> None:
        self.store = JsonlFile(data_dir / "budgets.jsonl")

    def iter_all(self) -> Generator[Budget, None, None]:
        for record in self.store.iter_records():
            try:
                yield Budget.from_dict(record)
            except (KeyError, TypeError, ValueError) as exc:
                raise StorageError(
                    "예산 데이터가 손상되었습니다.",
                    "budgets.jsonl의 month와 amount 필드를 확인하세요.",
                ) from exc

    def get(self, month: str) -> Budget | None:
        for budget in self.iter_all():
            if budget.month == month:
                return budget
        return None

    def set(self, budget: Budget) -> None:
        """같은 월은 교체하고, 처음 설정하는 월은 마지막에 추가합니다."""

        replaced = False

        def updated_records() -> Generator[dict[str, Any], None, None]:
            nonlocal replaced
            for current in self.iter_all():
                if current.month == budget.month:
                    replaced = True
                    yield budget.to_dict()
                else:
                    yield current.to_dict()
            if not replaced:
                yield budget.to_dict()

        self.store.rewrite(updated_records())
