# 🎮 빠른 실행 튜토리얼

VS Code에서 이 프로젝트 폴더를 연 뒤 **Terminal → New Terminal**을 선택합니다.
명령은 항상 프로젝트 최상위 폴더에서 실행합니다.

## 1. 프로그램 확인

```bash
python3 -m budget_app --help
```

## 2. 첫 거래 추가

```bash
python3 -m budget_app add
```

입력 예시:

```text
날짜(YYYY-MM-DD): 2026-07-01
타입(income/expense): income
카테고리: salary
금액(양수 정수): 3000000
메모(선택): 7월 급여
태그(쉼표로 구분, 없으면 엔터): salary,monthly
```

같은 명령을 여러 번 실행하여 지출도 추가합니다.

```bash
python3 -m budget_app add
```

두 번째 입력 예시:

```text
날짜(YYYY-MM-DD): 2026-07-02
타입(income/expense): expense
카테고리: rent
금액(양수 정수): 700000
메모(선택): 7월 월세
태그(쉼표로 구분, 없으면 엔터): housing,monthly
```

세 번째 입력 예시:

```text
날짜(YYYY-MM-DD): 2026-07-03
타입(income/expense): expense
카테고리: food
금액(양수 정수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal,lunch
```

## 3. 저장 결과 확인

```bash
python3 -m budget_app list
```

거래는 자동으로 다음 파일에 저장됩니다.

```text
data/transactions.jsonl
```

VS Code를 종료한 뒤 다시 실행해도 거래는 유지됩니다.

## 4. 검색과 요약

```bash
python3 -m budget_app search --type expense
python3 -m budget_app search --category food
python3 -m budget_app summary --month 2026-07 --top 3
```

## 5. 예산 경고 확인

```bash
python3 -m budget_app budget set --month 2026-07 --amount 500000
python3 -m budget_app summary --month 2026-07 --top 3
```

등록한 지출이 예산보다 크면 초과 경고가 표시됩니다.

## 6. 수정과 삭제

먼저 거래 ID를 확인합니다.

```bash
python3 -m budget_app list
```

화면에 표시된 실제 ID를 사용합니다.

```bash
python3 -m budget_app update --id TX-000003 --amount 18000 --memo "점심과 커피"
python3 -m budget_app delete --id TX-000003
```

## 핵심 사용 순서

```text
add 여러 번
→ list
→ search
→ summary
→ budget
→ update/delete
```

처음에는 이 순서만 실행해도 가계부 프로그램의 핵심 기능과 JSONL 영구 저장 구조를 확인할 수 있습니다.
