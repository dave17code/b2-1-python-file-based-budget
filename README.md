# 🧾 B2-1 파일 기반 가계부 프로그램 실행 및 검증 가이드

Python 표준 라이브러리만 사용한 **JSONL 파일 기반 가계부 콘솔 프로그램**입니다.

이 README는 프로그램 소개보다 실제 프로그램 실행과 기능 검증에 초점을 맞춥니다.

## 검증 기준

```text
✅ 기본 데이터 폴더: data/
✅ 정상 CSV 가져오기 검증 폴더: import_test_data/
✅ CSV 내보내기 파일은 프로젝트 루트에 유지
✅ 기본 카테고리는 프로그램 첫 실행 시 자동 생성
✅ category add는 대화형으로 직접 입력
✅ --q는 거래 메모만 키워드 검색
✅ 날짜·유형·카테고리·태그는 각각 조건 필터
✅ 수정과 삭제는 임시 파일 작성 후 원자적 교체
✅ 임시 검증 폴더를 mktemp로 생성하지 않음
✅ 보너스 과제 제외
```

---

## 전체 진행 흐름

```text
프로젝트 초기화
    ↓
프로그램 첫 실행 및 기본 파일 자동 생성
    ↓
7월·8월 예산 설정
    ↓
거래 20건 등록
    ↓
목록·검색·필터 검증
    ↓
월별 요약 검증
    ↓
예산 초과 경고 검증
    ↓
거래 수정·삭제 검증
    ↓
카테고리 추가·조회·삭제 검증
    ↓
CSV 내보내기 검증
    ↓
CSV 가져오기 검증
    ↓
입력 오류와 종료 코드 검증
    ↓
최종 프로젝트 구조 확인
```

---

# 1. 📁 프로젝트 루트 이동 및 초기화

## 실행 위치

```text
~/Desktop/All/B2-1/b2-1-python-file-based-budget
```

VS Code 터미널에서 프로젝트 루트로 이동합니다.

```bash
cd ~/Desktop/All/B2-1/b2-1-python-file-based-budget
```

현재 위치를 확인합니다.

```bash
pwd
```

Python 버전을 확인합니다.

```bash
python3 --version
```

Python 3.10 이상이면 정상입니다.

기존 데이터와 검증 결과를 초기화합니다.

> ⚠️ 기존 거래·카테고리·예산 데이터와 내보낸 CSV 파일이 모두 삭제됩니다.

```bash
rm -rf data import_test_data
find . -maxdepth 1 -type f -name 'export-*.csv' -delete
```

이번 검증에서는 다음 두 데이터 폴더를 사용합니다.

```text
data/
→ 실제 가계부 기능 검증 데이터

import_test_data/
→ 정상 CSV 가져오기 검증 데이터
```

---

# 2. 📦 프로그램 첫 실행 및 기본 데이터 자동 생성 확인

다음 명령으로 프로그램을 처음 실행합니다.

```bash
python3 -m budget_app category list
```

`category list` 명령이 기본 카테고리를 추가하는 것은 아닙니다.

프로그램이 처음 실행되면서 `data/` 폴더와 저장 파일을 만들고, 기본 카테고리 8개를 자동으로 저장합니다.

`category list`는 자동 생성된 카테고리를 조회하는 명령입니다.

첫 실행 후 다음 파일이 생성됩니다.

```text
data/
├── transactions.jsonl
├── categories.jsonl
├── budgets.jsonl
└── app.log
```

기본 카테고리:

```text
education
etc
food
health
rent
salary
transport
utilities
```

카테고리 개수를 확인합니다.

```bash
python3 -m budget_app category list | grep -c '^- '
```

정상 결과:

```text
8
```

저장 파일을 확인합니다.

```bash
find data -maxdepth 1 -type f | sort
```

---

# 3. 💰 7월·8월 예산 설정

2026년 7월과 8월 예산을 각각 `2,000,000원`으로 설정합니다.

```bash
python3 -m budget_app budget set --month 2026-07 --amount 2000000
python3 -m budget_app budget set --month 2026-08 --amount 2000000
```

예상 결과:

```text
[저장 완료] 2026-07 예산 2,000,000원
[저장 완료] 2026-08 예산 2,000,000원
```

설정된 예산을 확인합니다.

```bash
python3 -m budget_app budget show --month 2026-07
python3 -m budget_app budget show --month 2026-08
```

정상 결과:

```text
2026-07 예산: 2,000,000원
2026-08 예산: 2,000,000원
```

예산 파일의 줄 수를 확인합니다.

```bash
wc -l data/budgets.jsonl
```

정상 결과:

```text
2 data/budgets.jsonl
```

---

# 4. 🧾 거래 20건 등록

거래 한 건의 대화형 입력 순서는 다음과 같습니다.

```text
날짜
거래 유형
카테고리
금액
메모
태그
```

거래를 직접 입력할 때는 다음 명령을 실행합니다.

```bash
python3 -m budget_app add
```

20건을 한 번에 검증 데이터로 등록할 때는 아래 명령을 VS Code 터미널에 붙여 넣습니다.

```bash
printf '%s\n' '2026-07-01' 'income' 'salary' '3000000' '7월 급여' 'salary,monthly' | python3 -m budget_app add
printf '%s\n' '2026-07-02' 'expense' 'rent' '850000' '7월 원룸 월세' 'housing,monthly,fixed' | python3 -m budget_app add
printf '%s\n' '2026-07-04' 'expense' 'utilities' '110000' '7월 전기 및 가스 요금' 'utilities,electricity' | python3 -m budget_app add
printf '%s\n' '2026-07-06' 'expense' 'food' '220000' '7월 식료품 장보기' 'groceries,home' | python3 -m budget_app add
printf '%s\n' '2026-07-08' 'expense' 'transport' '70000' '7월 대중교통 충전' 'commute,transport' | python3 -m budget_app add
printf '%s\n' '2026-07-11' 'expense' 'food' '18000' '회사 근처 점심 식사' 'meal,lunch,company' | python3 -m budget_app add
printf '%s\n' '2026-07-15' 'expense' 'health' '55000' '감기 병원 진료' 'health,clinic' | python3 -m budget_app add
printf '%s\n' '2026-07-19' 'expense' 'education' '95000' '파이썬 프로그래밍 교재' 'book,study' | python3 -m budget_app add
printf '%s\n' '2026-07-23' 'expense' 'utilities' '85000' '휴대전화 및 인터넷 요금' 'utilities,monthly,communication' | python3 -m budget_app add
printf '%s\n' '2026-07-27' 'expense' 'etc' '120000' '세제와 주방 생활용품' 'household,home' | python3 -m budget_app add
printf '%s\n' '2026-08-01' 'income' 'salary' '3000000' '8월 급여' 'salary,monthly' | python3 -m budget_app add
printf '%s\n' '2026-08-02' 'expense' 'rent' '850000' '8월 원룸 월세' 'housing,monthly,fixed' | python3 -m budget_app add
printf '%s\n' '2026-08-05' 'expense' 'utilities' '135000' '에어컨 사용 전기 및 가스 요금' 'utilities,electricity,summer' | python3 -m budget_app add
printf '%s\n' '2026-08-07' 'expense' 'food' '240000' '8월 식료품과 생필품 장보기' 'groceries,home' | python3 -m budget_app add
printf '%s\n' '2026-08-10' 'expense' 'transport' '80000' '8월 대중교통 충전' 'commute,transport' | python3 -m budget_app add
printf '%s\n' '2026-08-14' 'expense' 'food' '32000' '회사 동료와 저녁 식사' 'meal,dinner,company' | python3 -m budget_app add
printf '%s\n' '2026-08-17' 'expense' 'health' '30000' '상비약 구매' 'health,pharmacy' | python3 -m budget_app add
printf '%s\n' '2026-08-20' 'expense' 'education' '120000' '파이썬 온라인 강의 결제' 'online-course,study' | python3 -m budget_app add
printf '%s\n' '2026-08-23' 'expense' 'utilities' '85000' '휴대전화 및 인터넷 요금' 'utilities,monthly,communication' | python3 -m budget_app add
printf '%s\n' '2026-08-28' 'expense' 'etc' '210000' '원룸 에어컨 수리비' 'repair,home,summer' | python3 -m budget_app add
```

정상적으로 실행되면 거래 ID가 순서대로 생성됩니다.

```text
TX-000001
TX-000002
...
TX-000020
```

---

# 5. ✅ 거래 20건 저장 확인

JSONL 파일의 줄 수를 확인합니다.

```bash
wc -l data/transactions.jsonl
```

정상 결과:

```text
20 data/transactions.jsonl
```

전체 거래 목록을 출력합니다.

```bash
python3 -m budget_app list --limit 20
```

거래는 최신순으로 출력되므로 `TX-000020`부터 표시됩니다.

출력된 거래 개수를 확인합니다.

```bash
python3 -m budget_app list --limit 20 | grep -c '^TX-'
```

정상 결과:

```text
20
```

---

# 6. 🧭 CLI 명령과 도움말 확인

전체 명령을 확인합니다.

```bash
python3 -m budget_app --help
```

다음 명령이 표시되어야 합니다.

```text
add
list
search
summary
budget
category
update
delete
import
export
```

세부 도움말을 확인합니다.

```bash
python3 -m budget_app add --help
python3 -m budget_app list --help
python3 -m budget_app search --help
python3 -m budget_app summary --help
python3 -m budget_app update --help
python3 -m budget_app delete --help
python3 -m budget_app export --help
python3 -m budget_app import --help
```

옵션 이름은 다음과 같이 이중 하이픈 형식으로 표시되어야 합니다.

```text
--limit
--from
--to
--category
--type
--q
--tag
--month
```

---

# 7. 📅 날짜 범위 필터 검증

## 7월 거래

```bash
python3 -m budget_app search \
  --from 2026-07-01 \
  --to 2026-07-31
```

개수 확인:

```bash
python3 -m budget_app search \
  --from 2026-07-01 \
  --to 2026-07-31 \
  | grep -c '^TX-'
```

정상 결과:

```text
10
```

## 8월 거래

```bash
python3 -m budget_app search \
  --from 2026-08-01 \
  --to 2026-08-31
```

개수 확인:

```bash
python3 -m budget_app search \
  --from 2026-08-01 \
  --to 2026-08-31 \
  | grep -c '^TX-'
```

정상 결과:

```text
10
```

## 7월부터 8월까지 전체 거래

```bash
python3 -m budget_app search \
  --from 2026-07-01 \
  --to 2026-08-31 \
  | grep -c '^TX-'
```

정상 결과:

```text
20
```

---

# 8. 🔍 거래 유형과 카테고리 필터 검증

`--type`과 `--category`는 자유 문자열 검색이 아니라 정확한 필드 조건입니다.

## 지출 거래

```bash
python3 -m budget_app search --type expense
```

개수 확인:

```bash
python3 -m budget_app search --type expense | grep -c '^TX-'
```

정상 결과:

```text
18
```

## 수입 거래

```bash
python3 -m budget_app search --type income
```

개수 확인:

```bash
python3 -m budget_app search --type income | grep -c '^TX-'
```

정상 결과:

```text
2
```

## 식비 카테고리

```bash
python3 -m budget_app search --category food
```

개수 확인:

```bash
python3 -m budget_app search --category food | grep -c '^TX-'
```

정상 결과:

```text
4
```

## 공과금 카테고리

```bash
python3 -m budget_app search --category utilities
```

개수 확인:

```bash
python3 -m budget_app search --category utilities | grep -c '^TX-'
```

정상 결과:

```text
4
```

---

# 9. 📝 메모 검색과 태그 필터 검증

## 검색 기능 구분

```text
--q
→ 거래 메모 키워드 검색

--tag
→ 거래 태그 포함 여부 필터

--category
→ 카테고리 정확히 일치

--type
→ 거래 유형 정확히 일치

--from, --to
→ 날짜 범위 조건
```

`--q`는 거래 ID·카테고리·태그를 검색하지 않고 **메모만 검색**합니다.

## 월세 메모 검색

```bash
python3 -m budget_app search --q 월세
```

예상 거래:

```text
7월 원룸 월세
8월 원룸 월세
```

## 파이썬 메모 검색

```bash
python3 -m budget_app search --q 파이썬
```

예상 거래:

```text
파이썬 프로그래밍 교재
파이썬 온라인 강의 결제
```

## `monthly` 태그 필터

```bash
python3 -m budget_app search --tag monthly
```

개수 확인:

```bash
python3 -m budget_app search --tag monthly | grep -c '^TX-'
```

정상 결과:

```text
6
```

대상 거래:

```text
7월 급여
7월 원룸 월세
7월 휴대전화 및 인터넷 요금
8월 급여
8월 원룸 월세
8월 휴대전화 및 인터넷 요금
```

## `summer` 태그 필터

```bash
python3 -m budget_app search --tag summer
```

개수 확인:

```bash
python3 -m budget_app search --tag summer | grep -c '^TX-'
```

정상 결과:

```text
2
```

예상 거래:

```text
에어컨 사용 전기 및 가스 요금
원룸 에어컨 수리비
```

---

# 10. 🧩 검색 조건 조합 검증

여러 조건을 함께 입력하면 모든 조건을 동시에 만족하는 거래만 출력되어야 합니다.

## 8월 식비 지출

```bash
python3 -m budget_app search \
  --from 2026-08-01 \
  --to 2026-08-31 \
  --category food \
  --type expense
```

예상 거래:

```text
8월 식료품과 생필품 장보기
회사 동료와 저녁 식사
```

개수 확인:

```bash
python3 -m budget_app search \
  --from 2026-08-01 \
  --to 2026-08-31 \
  --category food \
  --type expense \
  | grep -c '^TX-'
```

정상 결과:

```text
2
```

## 7월 반복 지출

```bash
python3 -m budget_app search \
  --from 2026-07-01 \
  --to 2026-07-31 \
  --type expense \
  --tag monthly
```

예상 거래:

```text
7월 원룸 월세
7월 휴대전화 및 인터넷 요금
```

## 메모와 필터 조합

```bash
python3 -m budget_app search \
  --q 식사 \
  --category food \
  --type expense
```

의미:

```text
메모에 "식사" 포함
AND 카테고리가 food
AND 거래 유형이 expense
```

---

# 11. 📊 7월 월별 요약 검증

```bash
python3 -m budget_app summary --month 2026-07 --top 3
```

정상 핵심 결과:

```text
총 수입: 3,000,000원
총 지출: 1,623,000원
잔액: 1,377,000원
예산: 2,000,000원 (사용률 81.2%)

지출 카테고리 TOP
1) rent 850,000원
2) food 238,000원
3) utilities 195,000원
```

카테고리별 계산:

```text
food
220,000원 + 18,000원
= 238,000원

utilities
110,000원 + 85,000원
= 195,000원
```

총지출 검산:

```text
850,000
+ 110,000
+ 220,000
+ 70,000
+ 18,000
+ 55,000
+ 95,000
+ 85,000
+ 120,000
= 1,623,000원
```

잔액 검산:

```text
3,000,000원 - 1,623,000원
= 1,377,000원
```

예산 사용률:

```text
1,623,000 ÷ 2,000,000 × 100
= 81.15%

소수점 첫째 자리 반올림
= 81.2%
```

---

# 12. 📈 8월 월별 요약 검증

```bash
python3 -m budget_app summary --month 2026-08 --top 3
```

정상 핵심 결과:

```text
총 수입: 3,000,000원
총 지출: 1,782,000원
잔액: 1,218,000원
예산: 2,000,000원 (사용률 89.1%)

지출 카테고리 TOP
1) rent 850,000원
2) food 272,000원
3) utilities 220,000원
```

카테고리별 계산:

```text
food
240,000원 + 32,000원
= 272,000원

utilities
135,000원 + 85,000원
= 220,000원
```

총지출 검산:

```text
850,000
+ 135,000
+ 240,000
+ 80,000
+ 32,000
+ 30,000
+ 120,000
+ 85,000
+ 210,000
= 1,782,000원
```

잔액 검산:

```text
3,000,000원 - 1,782,000원
= 1,218,000원
```

## 월별 비교

| 비교 항목 | 7월 | 8월 |
|---|---:|---:|
| 총수입 | 3,000,000원 | 3,000,000원 |
| 총지출 | 1,623,000원 | 1,782,000원 |
| 잔액 | 1,377,000원 | 1,218,000원 |
| 예산 | 2,000,000원 | 2,000,000원 |
| 예산 사용률 | 81.2% | 89.1% |
| 남은 예산 | 377,000원 | 218,000원 |

---

# 13. 🚨 예산 초과 경고 검증

8월 예산을 잠시 `1,700,000원`으로 변경합니다.

```bash
python3 -m budget_app budget set --month 2026-08 --amount 1700000
```

8월 요약을 다시 실행합니다.

```bash
python3 -m budget_app summary --month 2026-08 --top 3
```

정상 핵심 결과:

```text
총 지출: 1,782,000원
예산: 1,700,000원 (사용률 104.8%)
[예산 초과 경고] 예산을 82,000원 초과했습니다.
```

초과 금액 검산:

```text
1,782,000원 - 1,700,000원
= 82,000원
```

검증 후 예산을 원래 값으로 복원합니다.

```bash
python3 -m budget_app budget set --month 2026-08 --amount 2000000
```

복원 결과를 확인합니다.

```bash
python3 -m budget_app budget show --month 2026-08
```

정상 결과:

```text
2026-08 예산: 2,000,000원
```

---

# 14. ✏️ 거래 수정 기능 검증

기존 거래 20건을 직접 수정하지 않고 검증용 거래를 추가합니다.

```bash
python3 -m budget_app add
```

다음 값을 순서대로 직접 입력합니다.

```text
날짜: 2026-08-31
타입: expense
카테고리: etc
금액: 1000
메모: 기능검증 임시 거래
태그: test
```

순서대로 진행했다면 거래 ID는 다음과 같습니다.

```text
TX-000021
```

추가된 거래를 검색합니다.

```bash
python3 -m budget_app search --q 기능검증
```

금액·메모·태그를 수정합니다.

```bash
python3 -m budget_app update \
  --id TX-000021 \
  --amount 2000 \
  --memo "수정 완료 테스트" \
  --tags "test,updated"
```

수정 결과를 확인합니다.

```bash
python3 -m budget_app search --q "수정 완료 테스트"
```

정상 판정:

```text
ID
TX-000021 유지

금액
1,000원 → 2,000원

메모
수정 완료 테스트

태그
test,updated
```

거래 ID는 변경되지 않고 지정한 필드만 수정되어야 합니다.

---

# 15. 🗑️ 거래 삭제 기능 검증

앞 단계에서 추가한 검증용 거래를 삭제합니다.

```bash
python3 -m budget_app delete --id TX-000021
```

정상 결과:

```text
[삭제 완료] id=TX-000021
```

삭제된 거래를 검색합니다.

```bash
python3 -m budget_app search --q "수정 완료 테스트"
```

정상 결과:

```text
[검색 결과 없음] 조건에 맞는 거래가 없습니다.
```

최종 거래 개수를 확인합니다.

```bash
wc -l data/transactions.jsonl
```

정상 결과:

```text
20 data/transactions.jsonl
```

전체 목록에서도 거래 수를 확인합니다.

```bash
python3 -m budget_app list --limit 30 | grep -c '^TX-'
```

정상 결과:

```text
20
```

---

# 16. 🗂️ 카테고리 추가·조회·삭제 검증

## 16-1. 사용 중인 카테고리 삭제 차단

`food` 카테고리는 현재 여러 거래에서 사용 중입니다.

```bash
python3 -m budget_app category remove --name food
echo $?
```

정상 결과:

```text
[오류] 사용 중인 카테고리는 삭제할 수 없습니다: food
[힌트] 해당 거래의 카테고리를 update로 변경한 뒤 다시 삭제하세요.
1
```

`food`가 그대로 존재하는지 확인합니다.

```bash
python3 -m budget_app category list
```

목록에 다음 값이 남아 있어야 합니다.

```text
- food
```

## 16-2. 사용자 카테고리 추가

카테고리 추가는 대화형 입력 방식입니다.

```bash
python3 -m budget_app category add
```

프로그램이 이름을 요청하면 다음 값을 직접 입력합니다.

```text
카테고리 이름: hobby
```

정상 결과:

```text
[저장 완료] category=hobby
```

추가 결과를 확인합니다.

```bash
python3 -m budget_app category list
```

목록에 다음 값이 표시되어야 합니다.

```text
- hobby
```

카테고리 개수를 확인합니다.

```bash
python3 -m budget_app category list | grep -c '^- '
```

정상 결과:

```text
9
```

## 16-3. 사용하지 않는 카테고리 삭제

```bash
python3 -m budget_app category remove --name hobby
```

정상 결과:

```text
[삭제 완료] category=hobby
```

최종 카테고리 개수를 확인합니다.

```bash
python3 -m budget_app category list | grep -c '^- '
```

정상 결과:

```text
8
```

---

# 17. 📤 CSV 내보내기 검증

CSV 파일은 프로젝트 루트에 실제 파일로 생성합니다.

## 7월 거래 내보내기

```bash
python3 -m budget_app export \
  --out ./export-2026-07.csv \
  --month 2026-07
```

정상 결과:

```text
[완료] export-2026-07.csv (10 records)
```

## 8월 거래 내보내기

```bash
python3 -m budget_app export \
  --out ./export-2026-08.csv \
  --month 2026-08
```

정상 결과:

```text
[완료] export-2026-08.csv (10 records)
```

VS Code 탐색기에서 다음 파일을 확인합니다.

```text
b2-1-python-file-based-budget/
├── data/
├── export-2026-07.csv
└── export-2026-08.csv
```

CSV 줄 수를 확인합니다.

```bash
wc -l export-2026-07.csv export-2026-08.csv
```

정상 결과:

```text
11 export-2026-07.csv
11 export-2026-08.csv
22 total
```

각 CSV 파일의 구성:

```text
헤더 1줄
거래 데이터 10줄
총 11줄
```

CSV 헤더를 확인합니다.

```bash
head -n 1 export-2026-07.csv
head -n 1 export-2026-08.csv
```

정상 헤더:

```text
date,type,category,amount,memo,tags
```

CSV 앞부분을 확인합니다.

```bash
head -n 3 export-2026-07.csv
head -n 3 export-2026-08.csv
```

CSV 마지막 부분을 확인합니다.

```bash
tail -n 3 export-2026-07.csv
tail -n 3 export-2026-08.csv
```

---

# 18. 📥 정상 CSV 가져오기 검증

정상 CSV 가져오기 전용 폴더는 다음과 같습니다.

```text
./import_test_data
```

7월 CSV를 별도 데이터 폴더로 가져옵니다.

```bash
python3 -m budget_app \
  --data-dir ./import_test_data \
  import \
  --from ./export-2026-07.csv
```

`--data-dir`은 `import` 명령보다 앞에 작성해야 합니다.

```text
올바른 순서

python3 -m budget_app
→ --data-dir ./import_test_data
→ import
→ --from ./export-2026-07.csv
```

정상 결과:

```text
[완료] imported=10, skipped=0
```

생성된 파일을 확인합니다.

```text
import_test_data/
├── transactions.jsonl
├── categories.jsonl
├── budgets.jsonl
└── app.log
```

가져온 거래 수를 확인합니다.

```bash
wc -l import_test_data/transactions.jsonl
```

정상 결과:

```text
10 import_test_data/transactions.jsonl
```

가져온 거래 목록을 확인합니다.

```bash
python3 -m budget_app \
  --data-dir ./import_test_data \
  list \
  --limit 20
```

출력된 거래 개수를 확인합니다.

```bash
python3 -m budget_app \
  --data-dir ./import_test_data \
  list \
  --limit 20 \
  | grep -c '^TX-'
```

정상 결과:

```text
10
```

가져온 거래의 월별 요약을 확인합니다.

```bash
python3 -m budget_app \
  --data-dir ./import_test_data \
  summary \
  --month 2026-07 \
  --top 3
```

정상 핵심 결과:

```text
총 수입: 3,000,000원
총 지출: 1,623,000원
잔액: 1,377,000원
예산: 설정되지 않음
```

CSV에는 거래 데이터만 들어 있고 예산 데이터는 포함되지 않습니다.

따라서 다음 결과는 정상입니다.

```text
예산: 설정되지 않음
```

`import_test_data` 폴더는 검증 결과로 유지합니다.

---

# 19. 🛡️ 잘못된 입력과 종료 코드 검증

## 19-1. 존재하지 않는 날짜

대화형 거래 추가를 실행합니다.

```bash
python3 -m budget_app add
```

날짜 입력 단계에서 다음 값을 입력합니다.

```text
2026-13-40
```

정상 결과:

```text
[오류] 존재하지 않는 날짜입니다.
[힌트] 실제 달력에 있는 날짜를 입력하세요. 예: 2026-07-22
```

프로그램은 즉시 종료되지 않고 날짜를 다시 요청해야 합니다.

```text
날짜(YYYY-MM-DD):
```

`Control + C`로 프로그램을 종료합니다.

종료 코드를 확인합니다.

```bash
echo $?
```

정상 결과:

```text
130
```

## 19-2. 존재하지 않는 거래 삭제

```bash
python3 -m budget_app delete --id TX-999999
echo $?
```

정상 결과:

```text
[오류] 거래를 찾을 수 없습니다: TX-999999
[힌트] list 또는 search 명령으로 거래 id를 확인하세요.
1
```

## 19-3. 잘못된 날짜 범위

```bash
python3 -m budget_app search \
  --from 2026-08-31 \
  --to 2026-08-01

echo $?
```

정상 결과:

```text
[오류] 검색 시작일이 종료일보다 늦습니다.
[힌트] --from 날짜가 --to 날짜보다 빠르거나 같아야 합니다.
1
```

## 19-4. 잘못된 목록 개수

```bash
python3 -m budget_app list --limit 0
echo $?
```

정상 결과:

```text
[오류] --limit은 0보다 커야 합니다.
[힌트] 예: --limit 10
1
```

## 19-5. 정상 명령 종료 코드

```bash
python3 -m budget_app category list
echo $?
```

정상 결과:

```text
0
```

## 종료 코드 기준

| 실행 상황 | 종료 코드 |
|---|---:|
| 정상 종료 | `0` |
| 입력·데이터·파일 오류 | `1` |
| `Control + C` 사용자 중단 | `130` |
| 예상하지 못한 내부 오류 | `99` |

종료 코드는 바로 직전에 실행한 명령의 결과를 나타냅니다.

```bash
echo $?
```

따라서 종료 코드를 확인하기 전에 다른 명령을 실행하지 않습니다.

---

# 20. 📂 최종 프로젝트 구조 확인

VS Code 탐색기에서 다음 구조를 확인합니다.

```text
b2-1-python-file-based-budget/
├── budget_app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── decorators.py
│   ├── errors.py
│   ├── models.py
│   ├── repositories.py
│   ├── services.py
│   └── validators.py
├── data/
│   ├── transactions.jsonl
│   ├── categories.jsonl
│   ├── budgets.jsonl
│   └── app.log
├── import_test_data/
│   ├── transactions.jsonl
│   ├── categories.jsonl
│   ├── budgets.jsonl
│   └── app.log
├── sample_data/
│   └── import_sample.csv
├── export-2026-07.csv
├── export-2026-08.csv
├── README.md
└── .gitignore
```

---

# 🔄 프로그램 내부 실행 흐름

```text
사용자 터미널 명령
        ↓
python3 -m budget_app
        ↓
budget_app/__main__.py
        ↓
cli.py의 main()
        ↓
build_parser()
        ↓
argparse.parse_args()
        ↓
argparse.Namespace 생성
        ↓
명령에 연결된 handler 함수 실행
        ↓
BudgetService
        ↓
Repository
        ↓
data/*.jsonl 읽기 또는 쓰기
        ↓
CLI가 결과를 터미널에 출력
```

검색 명령의 흐름:

```text
python3 -m budget_app search --q 월세 --type expense
        ↓
argparse가 옵션 분석
        ↓
SearchCriteria 생성
        ↓
TransactionRepository가 JSONL을 최신순 스트리밍
        ↓
거래 유형이 expense인지 검사
        ↓
메모에 "월세"가 포함되는지 검사
        ↓
모든 조건을 만족한 거래만 yield
        ↓
터미널 출력
```

---

# 💾 JSONL 저장 방식

프로그램은 영구 데이터를 다음 세 개 이상의 파일로 분리합니다.

```text
transactions.jsonl
→ 거래 내역

categories.jsonl
→ 카테고리

budgets.jsonl
→ 월별 예산
```

거래 한 건은 JSON 객체 한 줄로 저장됩니다.

```json
{"id":"TX-000001","type":"expense","date":"2026-07-02","amount":850000,"category":"rent","memo":"7월 원룸 월세","tags":["housing","monthly","fixed"]}
```

---

# ♻️ 제너레이터 스트리밍

거래 목록과 검색은 전체 파일을 한 번에 리스트로 읽지 않습니다.

```text
JSONL 한 줄 읽기
    ↓
JSON 객체 변환
    ↓
Transaction 객체 생성
    ↓
검색 조건 검사
    ↓
조건 일치 시 yield
```

장점:

```text
✅ 전체 거래를 메모리에 적재하지 않음
✅ 거래를 한 건씩 처리
✅ 최신 목록은 필요한 개수에서 중단
✅ 대용량 데이터에서 메모리 사용량 유지
```

제너레이터는 메모리 사용량을 줄이지만 검색이나 요약의 전체 파일 순회 시간까지 없애는 것은 아닙니다.

# 🎯 최종 완료 판정

```text
✅ 프로그램 첫 실행 시 저장 파일 자동 생성

✅ 기본 카테고리 8개 자동 생성

✅ add 명령으로 대화형 거래 등록

✅ list 명령으로 최신순 거래 조회

✅ --limit으로 출력 개수 제한

✅ --q로 거래 메모 키워드 검색

✅ 날짜·유형·카테고리·태그 조건 필터링

✅ 여러 검색 조건 조합

✅ 월별 총수입·총지출·잔액 계산

✅ 카테고리별 지출 TOP N 계산

✅ 월별 예산 설정과 조회

✅ 예산 사용률과 초과 경고 출력

✅ category add로 사용자 카테고리 추가

✅ category list로 카테고리 조회

✅ category remove로 미사용 카테고리 삭제

✅ 사용 중인 카테고리 삭제 차단

✅ update로 지정한 거래 필드 수정

✅ 수정 후 거래 ID 유지

✅ delete로 지정한 거래 삭제

✅ 수정·삭제 시 안전한 전체 파일 재작성

✅ 월별 거래 CSV 내보내기

✅ 별도 데이터 폴더로 CSV 가져오기

✅ JSONL 파일 세 개 이상으로 영구 저장

✅ 제너레이터 기반 스트리밍 처리

✅ 정상·오류·사용자 중단 종료 코드 구분
```
