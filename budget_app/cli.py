"""터미널 명령, 대화형 입력, 화면 출력을 담당하는 CLI 계층입니다.

전체 흐름은 다음과 같습니다.

    터미널 명령 → argparse 파싱 → handle_* 함수 → BudgetService → Repository → JSONL

CLI는 파일을 직접 읽거나 업무 규칙을 계산하지 않습니다. 사용자의 입력을 서비스에
전달하고 결과를 보기 좋게 출력하는 역할에 집중합니다.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .errors import BudgetAppError, ValidationError
from .models import MonthlySummary, SearchCriteria, Transaction
from .services import BudgetService
from .validators import (
    validate_amount,
    validate_category_name,
    validate_date,
    validate_transaction_type,
)

# 각 명령 처리 함수가 받는 인자와 반환형을 타입 별칭으로 표현합니다.
Handler = Callable[[argparse.Namespace, BudgetService], None]


def build_parser() -> argparse.ArgumentParser:
    """모든 명령과 ``--`` 옵션을 정의한 argparse 파서를 만듭니다."""

    parser = argparse.ArgumentParser(
        prog="python -m budget_app",
        description="JSONL 파일 기반 가계부 콘솔 프로그램",
    )
    parser.add_argument(
        "--data-dir",
        default="./data",
        help="데이터 저장 폴더 (기본값: ./data, 명령 앞에 작성)",
    )

    commands = parser.add_subparsers(dest="command", required=True)

    add_parser = commands.add_parser("add", help="거래를 대화형으로 추가합니다.")
    add_parser.set_defaults(handler=handle_add)

    list_parser = commands.add_parser("list", help="최신순 거래 목록을 출력합니다.")
    list_parser.add_argument("--limit", type=int, default=20, help="출력할 최대 거래 수")
    list_parser.set_defaults(handler=handle_list)

    search_parser = commands.add_parser("search", help="조건에 맞는 거래를 검색합니다.")
    search_parser.add_argument("--from", dest="from_date", help="시작일 YYYY-MM-DD")
    search_parser.add_argument("--to", dest="to_date", help="종료일 YYYY-MM-DD")
    search_parser.add_argument("--category", help="카테고리")
    search_parser.add_argument("--type", dest="transaction_type", help="income 또는 expense")
    search_parser.add_argument("--q", dest="query", help="메모 검색어")
    search_parser.add_argument("--tag", help="태그")
    search_parser.set_defaults(handler=handle_search)

    summary_parser = commands.add_parser("summary", help="월별 요약을 출력합니다.")
    summary_parser.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    summary_parser.add_argument("--top", type=int, default=3, help="지출 카테고리 TOP N")
    summary_parser.set_defaults(handler=handle_summary)

    budget_parser = commands.add_parser("budget", help="월 예산을 설정하거나 조회합니다.")
    budget_commands = budget_parser.add_subparsers(dest="budget_command", required=True)

    budget_set = budget_commands.add_parser("set", help="월 예산을 설정합니다.")
    budget_set.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    budget_set.add_argument("--amount", required=True, type=int, help="예산 금액")
    budget_set.set_defaults(handler=handle_budget_set)

    budget_show = budget_commands.add_parser("show", help="월 예산을 조회합니다.")
    budget_show.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    budget_show.set_defaults(handler=handle_budget_show)

    category_parser = commands.add_parser("category", help="카테고리를 관리합니다.")
    category_commands = category_parser.add_subparsers(
        dest="category_command", required=True
    )

    category_add = category_commands.add_parser("add", help="카테고리를 추가합니다.")
    category_add.set_defaults(handler=handle_category_add)

    category_list = category_commands.add_parser("list", help="카테고리를 조회합니다.")
    category_list.set_defaults(handler=handle_category_list)

    category_remove = category_commands.add_parser("remove", help="카테고리를 삭제합니다.")
    category_remove.add_argument("--name", required=True, help="삭제할 카테고리 이름")
    category_remove.set_defaults(handler=handle_category_remove)

    update_parser = commands.add_parser("update", help="옵션 방식으로 거래를 수정합니다.")
    update_parser.add_argument("--id", required=True, dest="transaction_id", help="거래 id")
    update_parser.add_argument("--date", help="날짜 YYYY-MM-DD")
    update_parser.add_argument("--type", dest="transaction_type", help="income 또는 expense")
    update_parser.add_argument("--category", help="카테고리")
    update_parser.add_argument("--amount", type=int, help="금액")
    update_parser.add_argument("--memo", help="메모. 빈 문자열을 주면 삭제")
    update_parser.add_argument("--tags", help="쉼표 태그. 빈 문자열을 주면 삭제")
    update_parser.set_defaults(handler=handle_update)

    delete_parser = commands.add_parser("delete", help="id로 거래를 삭제합니다.")
    delete_parser.add_argument("--id", required=True, dest="transaction_id", help="거래 id")
    delete_parser.set_defaults(handler=handle_delete)

    import_parser = commands.add_parser("import", help="CSV 거래를 일괄 등록합니다.")
    import_parser.add_argument("--from", required=True, dest="source", help="가져올 CSV 파일")
    import_parser.set_defaults(handler=handle_import)

    export_parser = commands.add_parser("export", help="조건에 맞는 거래를 CSV로 내보냅니다.")
    export_parser.add_argument("--out", required=True, help="출력 CSV 파일")
    export_parser.add_argument("--month", help="대상 월 YYYY-MM")
    export_parser.add_argument("--from", dest="from_date", help="시작일 YYYY-MM-DD")
    export_parser.add_argument("--to", dest="to_date", help="종료일 YYYY-MM-DD")
    export_parser.set_defaults(handler=handle_export)

    return parser


def _print_error(error: BudgetAppError) -> None:
    """예상 가능한 오류를 스택트레이스 없이 사용자 친화적으로 출력합니다."""

    print(f"[오류] {error.message}", file=sys.stderr)
    if error.hint:
        print(f"[힌트] {error.hint}", file=sys.stderr)


def _prompt_until_valid(prompt: str, validator: Callable[[str], Any]) -> Any:
    """대화형 입력이 유효할 때까지 재입력받습니다."""

    while True:
        value = input(prompt).strip()
        try:
            return validator(value)
        except ValidationError as error:
            _print_error(error)


def _prompt_category(service: BudgetService) -> str:
    """등록된 카테고리 중 하나를 입력할 때까지 반복합니다."""

    while True:
        categories = service.list_categories()
        print("등록된 카테고리:", ", ".join(categories) or "(없음)")
        value = input("카테고리: ").strip()
        try:
            category = validate_category_name(value)
            if category not in categories:
                raise ValidationError(
                    f"등록되지 않은 카테고리입니다: {category}",
                    "category add로 먼저 등록하거나 위 목록에서 선택하세요.",
                )
            return category
        except ValidationError as error:
            _print_error(error)


def _format_money(amount: int) -> str:
    return f"{amount:,}원"


def _print_transaction(transaction: Transaction) -> None:
    """거래 한 건을 고정된 한 줄 형식으로 출력합니다."""

    tags = ",".join(transaction.tags) if transaction.tags else "-"
    memo = transaction.memo or "-"
    print(
        f"{transaction.id} | {transaction.date} | {transaction.type:<7} | "
        f"{transaction.category:<12} | {transaction.amount:>10,} | {memo} | tags={tags}"
    )


def _print_summary(summary: MonthlySummary) -> None:
    """월별 요약과 예산 사용률, 카테고리 TOP 결과를 출력합니다."""

    if summary.transaction_count == 0:
        print(f"[데이터 없음] {summary.month}에 등록된 거래가 없습니다.")
        return

    print(f"총 수입: {_format_money(summary.total_income)}")
    print(f"총 지출: {_format_money(summary.total_expense)}")
    print(f"잔액: {_format_money(summary.balance)}")

    if summary.budget is None:
        print("예산: 설정되지 않음")
    else:
        usage = summary.budget_usage_percent or 0.0
        print(f"예산: {_format_money(summary.budget)} (사용률 {usage:.1f}%)")
        if summary.is_budget_exceeded:
            exceeded = summary.total_expense - summary.budget
            print(f"[예산 초과 경고] 예산을 {_format_money(exceeded)} 초과했습니다.")

    print("\n지출 카테고리 TOP")
    if not summary.expense_by_category:
        print("- 지출 데이터 없음")
    else:
        for rank, (category, amount) in enumerate(summary.expense_by_category, start=1):
            print(f"{rank}) {category} {_format_money(amount)}")


def handle_add(_: argparse.Namespace, service: BudgetService) -> None:
    """add: 필드를 대화형으로 입력받아 거래를 저장합니다."""

    date = _prompt_until_valid("날짜(YYYY-MM-DD): ", validate_date)
    transaction_type = _prompt_until_valid(
        "타입(income/expense): ", validate_transaction_type
    )
    category = _prompt_category(service)
    amount = _prompt_until_valid("금액(양수 정수): ", validate_amount)
    memo = input("메모(선택): ").strip()
    tags = input("태그(쉼표로 구분, 없으면 엔터): ").strip()

    transaction = service.add_transaction(
        date=date,
        transaction_type=transaction_type,
        category=category,
        amount=amount,
        memo=memo,
        tags=tags,
    )
    print(f"[저장 완료] id={transaction.id}")


def handle_list(args: argparse.Namespace, service: BudgetService) -> None:
    """list: 최신순 거래를 제한 개수만 출력합니다."""

    count = 0
    for transaction in service.list_transactions(args.limit):
        _print_transaction(transaction)
        count += 1
    if count == 0:
        print("[데이터 없음] 등록된 거래가 없습니다.")


def handle_search(args: argparse.Namespace, service: BudgetService) -> None:
    """search: 옵션들을 SearchCriteria로 묶어 서비스에 전달합니다."""

    criteria = SearchCriteria(
        from_date=args.from_date,
        to_date=args.to_date,
        category=args.category,
        transaction_type=args.transaction_type,
        query=args.query,
        tag=args.tag,
    )
    count = 0
    for transaction in service.search_transactions(criteria):
        _print_transaction(transaction)
        count += 1
    if count == 0:
        print("[검색 결과 없음] 조건에 맞는 거래가 없습니다.")


def handle_summary(args: argparse.Namespace, service: BudgetService) -> None:
    _print_summary(service.summarize(args.month, args.top))


def handle_budget_set(args: argparse.Namespace, service: BudgetService) -> None:
    budget = service.set_budget(args.month, args.amount)
    print(f"[저장 완료] {budget.month} 예산 {_format_money(budget.amount)}")


def handle_budget_show(args: argparse.Namespace, service: BudgetService) -> None:
    budget = service.get_budget(args.month)
    if budget is None:
        print(f"[데이터 없음] {args.month} 예산이 설정되지 않았습니다.")
    else:
        print(f"{budget.month} 예산: {_format_money(budget.amount)}")


def handle_category_add(_: argparse.Namespace, service: BudgetService) -> None:
    name = input("카테고리명: ").strip()
    category = service.add_category(name)
    print(f"[저장 완료] category={category}")


def handle_category_list(_: argparse.Namespace, service: BudgetService) -> None:
    categories = service.list_categories()
    if not categories:
        print("[데이터 없음] 등록된 카테고리가 없습니다.")
        return
    for category in categories:
        print(f"- {category}")


def handle_category_remove(args: argparse.Namespace, service: BudgetService) -> None:
    category = service.remove_category(args.name)
    print(f"[삭제 완료] category={category}")


def handle_update(args: argparse.Namespace, service: BudgetService) -> None:
    transaction = service.update_transaction(
        transaction_id=args.transaction_id,
        date=args.date,
        transaction_type=args.transaction_type,
        category=args.category,
        amount=args.amount,
        memo=args.memo,
        tags=args.tags,
    )
    print(f"[수정 완료] id={transaction.id}")
    _print_transaction(transaction)


def handle_delete(args: argparse.Namespace, service: BudgetService) -> None:
    service.delete_transaction(args.transaction_id)
    print(f"[삭제 완료] id={args.transaction_id}")


def handle_import(args: argparse.Namespace, service: BudgetService) -> None:
    imported, skipped = service.import_csv(Path(args.source))
    print(f"[완료] imported={imported}, skipped={skipped}")


def handle_export(args: argparse.Namespace, service: BudgetService) -> None:
    output = Path(args.out)
    count = service.export_csv(
        output=output,
        month=args.month,
        from_date=args.from_date,
        to_date=args.to_date,
    )
    print(f"[완료] {output} ({count} records)")


def _configure_logging(data_dir: Path) -> None:
    """데코레이터와 예상 밖 오류가 기록될 로그 파일을 설정합니다."""

    data_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=data_dir / "app.log",
        level=logging.INFO,
        format="%(asctime)s level=%(levelname)s %(message)s",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    """CLI 전체 실행을 관리하고 운영체제 종료 코드를 반환합니다."""

    parser = build_parser()
    args = parser.parse_args(argv)
    data_dir = Path(args.data_dir).expanduser().resolve()
    _configure_logging(data_dir)

    try:
        service = BudgetService(data_dir)
        handler: Handler = args.handler
        handler(args, service)
        return 0
    except BudgetAppError as error:
        _print_error(error)
        return 1
    except KeyboardInterrupt:
        print("\n[중단] 사용자 요청으로 실행을 종료했습니다.", file=sys.stderr)
        return 130
    except Exception:
        # 화면에는 상세 스택트레이스를 숨기되 app.log에는 디버깅 정보를 남깁니다.
        logging.getLogger("budget_app").exception("unexpected_error")
        print("[오류] 예상하지 못한 문제가 발생했습니다.", file=sys.stderr)
        print("[힌트] data/app.log를 확인하세요.", file=sys.stderr)
        return 99
