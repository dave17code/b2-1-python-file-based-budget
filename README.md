# 🧾 B2-1 Python File-Based Budget

JSONL 파일에 데이터를 영구 저장하는 **터미널 기반 가계부 프로그램**입니다.
Python 3.10 이상과 표준 라이브러리만 사용하며 별도의 패키지 설치가 필요 없습니다.

## 실행

프로젝트 최상위 폴더에서 실행합니다.

```bash
python3 --version
python3 -m budget_app --help
```

거래를 처음 추가하려면 다음 명령을 사용합니다.

```bash
python3 -m budget_app add
```

## 프로젝트 구조

```text
b2-1-python-file-based-budget/
├── budget_app/
│   ├── __init__.py       # 패키지 정보
│   ├── __main__.py       # python3 -m budget_app 실행 시작점
│   ├── cli.py            # 명령어·입력·출력 처리
│   ├── models.py         # 거래·예산 dataclass
│   ├── validators.py     # 날짜·금액·타입 검증
│   ├── repositories.py  # JSONL 읽기·쓰기·원자적 교체
│   ├── services.py       # 가계부 업무 규칙
│   ├── decorators.py     # 로그·실행 시간 측정
│   └── errors.py         # 사용자용 예외
├── README.md
├── TUTORIAL.md
└── .gitignore
```

프로그램 처리 흐름은 다음과 같습니다.

```text
터미널 명령
    ↓
cli.py
    ↓
services.py
    ↓
repositories.py
    ↓
data/*.jsonl
```

## 영구 저장

최초 명령 실행 시 `data` 폴더와 파일이 자동 생성됩니다.

```text
data/
├── transactions.jsonl
├── categories.jsonl
├── budgets.jsonl
└── app.log
```

- `transactions.jsonl`: 수입·지출 거래
- `categories.jsonl`: 카테고리
- `budgets.jsonl`: 월별 예산
- `app.log`: 명령 실행 기록과 실행 시간

기본 카테고리는 최초 실행 시 자동 생성되지만, 거래와 예산은 비어 있는 상태로 시작합니다.

## 주요 명령

```bash
# 거래 추가
python3 -m budget_app add

# 최신 거래 조회
python3 -m budget_app list --limit 10

# 조건 검색
python3 -m budget_app search --type expense
python3 -m budget_app search --category food
python3 -m budget_app search --from 2026-07-01 --to 2026-07-31

# 월별 요약
python3 -m budget_app summary --month 2026-07 --top 3

# 월 예산 설정·조회
python3 -m budget_app budget set --month 2026-07 --amount 500000
python3 -m budget_app budget show --month 2026-07

# 카테고리 관리
python3 -m budget_app category list
python3 -m budget_app category add
python3 -m budget_app category remove --name hobby

# 거래 수정·삭제
python3 -m budget_app update --id TX-000001 --amount 18000
python3 -m budget_app delete --id TX-000001
```

## CSV 가져오기·내보내기

`import` 기능을 사용할 때는 사용자가 CSV 파일을 직접 준비합니다.

CSV 필수 열:

```text
date,type,category,amount
```

선택 열:

```text
memo,tags
```

예시 형식:

```csv
date,type,category,amount,memo,tags
2026-07-22,expense,food,15000,점심,"meal,lunch"
2026-07-25,income,salary,3000000,7월 급여,"salary,monthly"
```

가져오기:

```bash
python3 -m budget_app import --from my_transactions.csv
```

내보내기:

```bash
python3 -m budget_app export --out export-2026-07.csv --month 2026-07
python3 -m budget_app export --out export-range.csv --from 2026-07-01 --to 2026-07-31
```

## 필수 기능

- `add`: 거래 추가
- `list`: 최신순 목록 조회
- `search`: 조건 검색
- `summary`: 월별 요약과 카테고리 리포트
- `budget`: 월별 예산 설정·조회
- `category`: 카테고리 추가·조회·삭제
- `update`: 거래 수정
- `delete`: 거래 삭제
- `import`: CSV 가져오기
- `export`: CSV 내보내기

JSONL 파일 3개 이상, 제너레이터 스트리밍, 데코레이터, 타입 힌트, 예외 처리, 모듈 분리를 적용했습니다.
