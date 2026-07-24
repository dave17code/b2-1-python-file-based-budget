"""가계부의 업무 규칙을 담당하는 서비스 계층입니다.

CLI는 사용자의 입력과 출력만 담당하고, 서비스는 다음과 같은 규칙을 결정합니다.

- 등록된 카테고리만 거래에 사용할 수 있다.
- 금액은 양수여야 한다.
- 검색 조건은 모두 만족해야 한다.
- 사용 중인 카테고리는 삭제할 수 없다.
- CSV 가져오기에서 잘못된 행은 건너뛴다.

서비스가 파일을 직접 열지 않고 Repository를 사용하는 점을 확인해 보세요.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Generator
from dataclasses import replace
from itertools import islice
from pathlib import Path

from .decorators import log_execution
from .errors import ConflictError, NotFoundError, StorageError, ValidationError
from .models import Budget, MonthlySummary, SearchCriteria, Transaction
from .repositories import BudgetRepository, CategoryRepository, TransactionRepository
from .validators import (
    parse_tags,
    validate_amount,
    validate_category_name,
    validate_date,
    validate_date_range,
    validate_month,
    validate_transaction_type,
)

CSV_COLUMNS = ["date", "type", "category", "amount", "memo", "tags"]
CSV_REQUIRED_COLUMNS = {"date", "type", "category", "amount"}


class BudgetService:
    """CLI가 호출하는 가계부 기능의 단일 진입점입니다."""

    def __init__(self, data_dir: Path) -> None:
        # 저장소를 한 번만 만들어 각 명령이 같은 data 폴더를 사용하게 합니다.
        self.transactions = TransactionRepository(data_dir)
        self.categories = CategoryRepository(data_dir)
        self.budgets = BudgetRepository(data_dir)

    @log_execution
    def add_transaction(
        self,
        *,
        date: str,
        transaction_type: str,
        category: str,
        amount: int | str,
        memo: str = "",
        tags: str | list[str] | None = None,
    ) -> Transaction:
        """입력값을 검증하고 새 id를 만든 뒤 거래를 영구 저장합니다."""

        valid_category = validate_category_name(category)
        if not self.categories.exists(valid_category):
            raise ValidationError(
                f"등록되지 않은 카테고리입니다: {valid_category}",
                "category list로 확인하거나 category add로 먼저 등록하세요.",
            )

        transaction = Transaction(
            id=self.transactions.next_id(),
            type=validate_transaction_type(transaction_type),
            date=validate_date(date),
            amount=validate_amount(amount),
            category=valid_category,
            memo=memo.strip(),
            tags=parse_tags(tags),
        )
        self.transactions.add(transaction)
        return transaction

    def list_transactions(self, limit: int = 20) -> Generator[Transaction, None, None]:
        """최신 거래부터 최대 ``limit``건을 스트리밍합니다."""

        if limit <= 0:
            raise ValidationError(
                "--limit은 0보다 커야 합니다.",
                "예: --limit 10",
            )

        # islice는 제너레이터에서 필요한 개수만 꺼내므로 전체 거래를 읽지 않습니다.
        yield from islice(self.transactions.iter_all(latest_first=True), limit)

    def search_transactions(
        self,
        criteria: SearchCriteria,
    ) -> Generator[Transaction, None, None]:
        """모든 검색 조건을 만족하는 거래를 최신순으로 스트리밍합니다."""

        validate_date_range(criteria.from_date, criteria.to_date)
        category = (
            validate_category_name(criteria.category)
            if criteria.category is not None
            else None
        )
        transaction_type = (
            validate_transaction_type(criteria.transaction_type)
            if criteria.transaction_type is not None
            else None
        )
        query = criteria.query.strip().lower() if criteria.query else None
        tag = criteria.tag.strip().lower() if criteria.tag else None

        for transaction in self.transactions.iter_all(latest_first=True):
            if criteria.from_date and transaction.date < criteria.from_date:
                continue
            if criteria.to_date and transaction.date > criteria.to_date:
                continue
            if category and transaction.category != category:
                continue
            if transaction_type and transaction.type != transaction_type:
                continue
            if query and query not in transaction.memo.lower():
                continue
            if tag and tag not in transaction.tags:
                continue
            yield transaction

    @log_execution
    def update_transaction(
        self,
        *,
        transaction_id: str,
        date: str | None = None,
        transaction_type: str | None = None,
        category: str | None = None,
        amount: int | None = None,
        memo: str | None = None,
        tags: str | None = None,
    ) -> Transaction:
        """옵션으로 전달된 필드만 변경하고 파일을 안전하게 재작성합니다."""

        current = self.transactions.get_by_id(transaction_id)
        if current is None:
            raise NotFoundError(
                f"거래를 찾을 수 없습니다: {transaction_id}",
                "list 또는 search 명령으로 거래 id를 확인하세요.",
            )

        if all(
            value is None
            for value in (date, transaction_type, category, amount, memo, tags)
        ):
            raise ValidationError(
                "수정할 필드가 없습니다.",
                "--date, --type, --category, --amount, --memo, --tags 중 하나 이상 입력하세요.",
            )

        new_category = (
            validate_category_name(category)
            if category is not None
            else current.category
        )
        if not self.categories.exists(new_category):
            raise ValidationError(
                f"등록되지 않은 카테고리입니다: {new_category}",
                "category list로 확인하거나 category add로 먼저 등록하세요.",
            )

        # dataclasses.replace는 기존 객체에서 지정한 필드만 바꾼 새 객체를 만듭니다.
        replacement = replace(
            current,
            date=validate_date(date) if date is not None else current.date,
            type=(
                validate_transaction_type(transaction_type)
                if transaction_type is not None
                else current.type
            ),
            category=new_category,
            amount=validate_amount(amount) if amount is not None else current.amount,
            memo=memo.strip() if memo is not None else current.memo,
            tags=parse_tags(tags) if tags is not None else current.tags,
        )

        if not self.transactions.update(replacement):
            raise NotFoundError(
                f"거래를 찾을 수 없습니다: {transaction_id}",
                "다른 프로세스가 데이터를 변경했는지 확인하세요.",
            )
        return replacement

    @log_execution
    def delete_transaction(self, transaction_id: str) -> None:
        """id가 일치하는 거래를 삭제합니다."""

        if not self.transactions.delete(transaction_id):
            raise NotFoundError(
                f"거래를 찾을 수 없습니다: {transaction_id}",
                "list 또는 search 명령으로 거래 id를 확인하세요.",
            )

    @log_execution
    def summarize(self, month: str, top: int = 3) -> MonthlySummary:
        """한 달의 수입·지출·잔액과 지출 카테고리 TOP N을 계산합니다."""

        valid_month = validate_month(month)
        if top <= 0:
            raise ValidationError(
                "--top은 0보다 커야 합니다.",
                "예: --top 3",
            )

        total_income = 0
        total_expense = 0
        transaction_count = 0
        expense_by_category: dict[str, int] = defaultdict(int)

        # summary도 거래를 한 건씩 읽으며 누적하므로 전체 거래 리스트가 필요 없습니다.
        for transaction in self.transactions.iter_all():
            if not transaction.date.startswith(valid_month):
                continue
            transaction_count += 1
            if transaction.type == "income":
                total_income += transaction.amount
            else:
                total_expense += transaction.amount
                expense_by_category[transaction.category] += transaction.amount

        top_expenses = sorted(
            expense_by_category.items(),
            key=lambda item: (-item[1], item[0]),
        )[:top]
        saved_budget = self.budgets.get(valid_month)

        return MonthlySummary(
            month=valid_month,
            total_income=total_income,
            total_expense=total_expense,
            balance=total_income - total_expense,
            expense_by_category=top_expenses,
            transaction_count=transaction_count,
            budget=saved_budget.amount if saved_budget else None,
        )

    @log_execution
    def set_budget(self, month: str, amount: int | str) -> Budget:
        """월 예산을 새로 저장하거나 기존 값을 교체합니다."""

        budget = Budget(month=validate_month(month), amount=validate_amount(amount))
        self.budgets.set(budget)
        return budget

    def get_budget(self, month: str) -> Budget | None:
        return self.budgets.get(validate_month(month))

    def list_categories(self) -> list[str]:
        return sorted(self.categories.list_all())

    @log_execution
    def add_category(self, name: str) -> str:
        """중복되지 않은 새 카테고리를 저장합니다."""

        valid_name = validate_category_name(name)
        if self.categories.exists(valid_name):
            raise ConflictError(
                f"이미 존재하는 카테고리입니다: {valid_name}",
                "category list로 현재 목록을 확인하세요.",
            )
        self.categories.add(valid_name)
        return valid_name

    @log_execution
    def remove_category(self, name: str) -> str:
        """거래에서 사용하지 않는 카테고리만 삭제합니다."""

        valid_name = validate_category_name(name)
        if not self.categories.exists(valid_name):
            raise NotFoundError(
                f"카테고리를 찾을 수 없습니다: {valid_name}",
                "category list로 현재 목록을 확인하세요.",
            )
        if self.transactions.category_in_use(valid_name):
            raise ConflictError(
                f"사용 중인 카테고리는 삭제할 수 없습니다: {valid_name}",
                "해당 거래의 카테고리를 update로 변경한 뒤 다시 삭제하세요.",
            )
        self.categories.remove(valid_name)
        return valid_name

    @log_execution
    def import_csv(self, source: Path) -> tuple[int, int]:
        """CSV 행을 검증해 거래로 저장하고 성공/건너뜀 건수를 반환합니다."""

        if not source.exists() or not source.is_file():
            raise NotFoundError(
                f"가져올 CSV 파일을 찾을 수 없습니다: {source}",
                "--from 경로와 파일명을 확인하세요.",
            )

        imported = 0
        skipped = 0
        available_categories = set(self.categories.list_all())
        next_number = int(self.transactions.next_id()[3:])

        try:
            # utf-8-sig는 일반 UTF-8과 Excel이 자주 만드는 UTF-8 BOM을 모두 읽습니다.
            with source.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                headers = set(reader.fieldnames or [])
                missing = CSV_REQUIRED_COLUMNS - headers
                if missing:
                    raise ValidationError(
                        f"CSV 필수 헤더가 누락되었습니다: {', '.join(sorted(missing))}",
                        f"지원 헤더: {', '.join(CSV_COLUMNS)}",
                    )

                for row in reader:
                    try:
                        category = validate_category_name(
                            (row.get("category") or "").strip()
                        )
                        if category not in available_categories:
                            raise ValidationError(
                                f"등록되지 않은 카테고리입니다: {category}"
                            )

                        transaction = Transaction(
                            id=f"TX-{next_number:06d}",
                            date=validate_date((row.get("date") or "").strip()),
                            type=validate_transaction_type(
                                (row.get("type") or "").strip()
                            ),
                            category=category,
                            amount=validate_amount((row.get("amount") or "").strip()),
                            memo=(row.get("memo") or "").strip(),
                            tags=parse_tags(row.get("tags") or ""),
                        )
                        self.transactions.add(transaction)
                        next_number += 1
                        imported += 1
                    except (ValidationError, TypeError, ValueError):
                        # 한 행의 오류 때문에 정상인 다른 행까지 중단하지 않습니다.
                        skipped += 1
        except UnicodeError as exc:
            raise ValidationError(
                "CSV 파일 인코딩을 읽을 수 없습니다.",
                "UTF-8 또는 UTF-8 BOM 형식으로 저장하세요.",
            ) from exc
        except OSError as exc:
            raise StorageError(
                f"CSV 파일을 읽지 못했습니다: {source}",
                "파일 읽기 권한을 확인하세요.",
            ) from exc

        return imported, skipped

    @log_execution
    def export_csv(
        self,
        *,
        output: Path,
        month: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> int:
        """월 또는 날짜 조건에 맞는 거래를 CSV로 내보냅니다."""

        if month is None and from_date is None and to_date is None:
            raise ValidationError(
                "export에는 조회 조건이 필요합니다.",
                "--month, --from, --to 중 하나 이상 입력하세요.",
            )
        if month is not None and (from_date is not None or to_date is not None):
            raise ValidationError(
                "--month와 날짜 범위를 동시에 사용할 수 없습니다.",
                "--month 또는 --from/--to 중 한 방식을 선택하세요.",
            )

        if month is not None:
            valid_month = validate_month(month)
        else:
            valid_month = None
            validate_date_range(from_date, to_date)

        output.parent.mkdir(parents=True, exist_ok=True)
        exported = 0

        try:
            # utf-8-sig로 내보내면 Excel에서도 한글을 비교적 안정적으로 엽니다.
            with output.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
                writer.writeheader()

                for transaction in self.transactions.iter_all():
                    if valid_month and not transaction.date.startswith(valid_month):
                        continue
                    if from_date and transaction.date < from_date:
                        continue
                    if to_date and transaction.date > to_date:
                        continue

                    writer.writerow(
                        {
                            "date": transaction.date,
                            "type": transaction.type,
                            "category": transaction.category,
                            "amount": transaction.amount,
                            "memo": transaction.memo,
                            "tags": ",".join(transaction.tags),
                        }
                    )
                    exported += 1
        except OSError as exc:
            raise StorageError(
                f"CSV 파일을 저장하지 못했습니다: {output}",
                "출력 경로와 폴더 쓰기 권한을 확인하세요.",
            ) from exc

        return exported
