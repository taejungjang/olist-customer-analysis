# 코드 설명서 (Olist 고객 분석)

이 문서는 **어떤 파일이 무엇을 하는지, 어떤 순서로 실행되는지, 숫자가 어느 코드에서 나오는지** 정리한 문서입니다.

## 1. 한눈에 보는 실행 흐름

```
Kaggle CSV 8개 (olist_dataset/ 폴더)
      │
      │  python analysis/run_analysis.py          <- 분석의 전부. 아래 9단계를 순서대로 실행
      ▼
  ① CSV를 SQLite DB(analysis/output/olist.db)에 넣기
  ② SQL 5개 실행 (analysis/sql/01 ~ 05)  : 분석 대상 주문 정하기, 고객 그룹 나누기, 월별 주문, 재구매 간격, 대표 상품군
  ③ Python으로 계산 (그룹 요약, 재구매 시점, 상품군 비교, 연락 대상, 기대 효과)
      │
      ▼
  analysis/output/*.csv  (결과 파일 12개, 표 3번 참고)
      │
      ├── python analysis/build_dashboard.py        -> olist_dashboard.html (대시보드)
      └── python analysis/rfm_criteria_check.py     -> 화면에 출력 (RFM 기준값 177일, R$110의 근거 확인)
```

## 2. 실행 방법 (이 순서로)

| 순서 | 명령어 | 하는 일 | 걸리는 시간 |
|---|---|---|---|
| 0 | `pip install -r requirements.txt` | 필요한 라이브러리 설치 | |
| 1 | `python analysis/run_analysis.py` | 분석 전체 실행, `analysis/output/`에 결과 저장 | 1분 안팎 |
| 2 | `python analysis/build_dashboard.py` | 결과로 `olist_dashboard.html` 생성 | 몇 초 |
| 3 | `python analysis/rfm_criteria_check.py` | RFM 기준값 근거 확인 (선택) | 몇 초 |

## 3. 파일별 역할

| 파일 | 역할 | 입력 | 출력 |
|---|---|---|---|
| `analysis/run_analysis.py` | 분석 전체. 1~9단계 (아래 4번) | `olist_dataset/*.csv`, `analysis/sql/*.sql` | `analysis/output/*.csv`, `olist.db` |
| `analysis/sql/01_base_view.sql` | 분석 대상 주문(배송 완료)만 모은 뷰 `v_orders` 만들기 | orders, customers, order_items | 뷰 `v_orders` (DB 안) |
| `analysis/sql/02_rfm_groups.sql` | 고객별 R, F, M 계산 -> 점수 -> 5개 그룹 | `v_orders` | `rfm.csv` |
| `analysis/sql/03_monthly_orders.sql` | 월별 주문 수 | orders | `monthly.csv` |
| `analysis/sql/04_repurchase_gap.sql` | 재구매 고객의 첫 구매 ~ 두 번째 구매 간격(일) | `v_orders` | `repurchase_gap.csv` |
| `analysis/sql/05_order_main_category.sql` | 주문별 대표 상품군 (가장 비싼 상품 기준) | order_items, products | (Python 안에서 사용) |
| `analysis/build_dashboard.py` | 결과 CSV를 대시보드 HTML에 끼워 넣기 | `output/*.csv`, `dashboard_template.html` | `olist_dashboard.html` |
| `analysis/dashboard_template.html` | 대시보드 화면 틀 (HTML, CSS, JavaScript). 데이터 자리에 `__DATA__` | | |
| `analysis/rfm_criteria_check.py` | RFM 기준값이 타당한지 확인 (재구매 시점, 매출 비중, K-means) | `rfm.csv`, `repurchase_gap.csv` | 화면 출력 |
| `olist_dashboard.html` | 완성된 대시보드 (GitHub Pages로 공개) | | |
| `images/` | README에 넣는 그림 | | |

## 4. run_analysis.py 단계별 설명

SQL은 "데이터를 모으는 일", Python은 "계산하고 비교하는 일"을 맡습니다.

| 단계 | 하는 일 | 쓰는 SQL | 저장하는 파일 | 어디에 쓰이나 |
|---|---|---|---|---|
| 1 | CSV 8개를 SQLite DB에 넣고 `v_orders` 뷰 만들기 | 01 | `olist.db` | 이후 모든 단계 |
| 2 | 월별 주문 수 | 03 | `monthly.csv` | 대시보드 월별 그래프 |
| 3 | RFM으로 고객을 5개 그룹으로 나누고 그룹별 요약 | 02 | `rfm.csv`, `rfm_groups.csv` | 대시보드, README |
| 4 | 최근 우수(2)와 휴면 우수(4)의 첫 구매 평점, 늦은 배송 비율 비교 | | `group2_vs_4.csv` | README (평점 4.05 vs 4.15) |
| 5 | 재구매 고객이 첫 구매 후 며칠 만에 다시 샀나 | 04 | `repurchase_gap.csv` | 7단계, `rfm_criteria_check.py` |
| 6 | 다시 살 때 같은 상품군을 샀나 (전체, 첫 구매 상품군별) | 05 | `same_category.csv`, `same_by_first_category.csv` | 대시보드, README |
| 7 | 첫 구매 후 일정 기간 안 산 고객이 그 뒤 90일 안에 연락 없이 다시 산 비율 | | `return_hazard.csv` | 대시보드, README (연락 시점) |
| 8 | 연락 대상(휴면 우수 중 마지막 구매 6~12개월) 정하고, 상품군 기준으로 분류 | | `targets.csv`, `target_by_same_rate.csv` | 대시보드, README |
| 9 | 그룹별 연락 1명당 기대 매출, 기대 효과 시나리오 (모두 가정) | | `rfm_groups.csv`(열 추가), `scenario.csv` | 대시보드, README |

## 5. README의 주요 숫자는 어디서 나오나

| 숫자 | 의미 | 나오는 곳 |
|---|---|---|
| 99,441건 / 96,096명 / 93,350명 | 전체 주문 / 고유 고객 / 분석 고객(배송 완료 주문 보유) | 01 `v_orders` 뷰 + `customers` 표 |
| 177일, R$110 | 최근/휴면 경계, 우수/일반 경계 | `02_rfm_groups.sql` 의 `r_score >= 4`, `m_score >= 4` (5등분 중 상위 40%). 근거는 `rfm_criteria_check.py` |
| 2.2% | 서로 다른 날 2번 이상 산 고객 | `rfm.csv`의 frequency |
| 21,198명 / 23% / 43% | 휴면 우수 고객 수, 고객 비중, 매출 비중 | 3단계 `rfm_groups.csv` |
| 14,237명 | 연락 대상 (휴면 우수 중 마지막 구매 6~12개월) | 8단계 `targets.csv` (`TARGET_MAX_RECENCY_DAYS = 382`) |
| 0.6~0.7%, 0.37% | 연락 없이 90일 안에 돌아오는 비율 | 7단계 `return_hazard.csv` |
| R$268 x 3% = R$8.0 | 연락 1명당 기대 매출 | 9단계 `rfm_groups.csv` (`ASSUMED_REPURCHASE_RATE = 0.03`는 가정) |
| 38.9%, 상품군별 19~54% | 다시 산 고객이 같은 상품군을 산 비율 | 6단계 `same_category.csv`, `same_by_first_category.csv` |
| 47% (6,663명) | 연락 대상 중 같은 상품군 추천이 유리한 상품군을 처음 산 고객 | 8단계 `target_by_same_rate.csv` |

## 6. SQL 파일을 읽는 순서 (쉬운 것부터)

1. `01_base_view.sql` : 조건 2개로 거르는 가장 단순한 뷰
2. `03_monthly_orders.sql` : 월별로 세기
3. `05_order_main_category.sql` : 주문마다 가장 비싼 상품 1개 고르기 (`ROW_NUMBER`)
4. `04_repurchase_gap.sql` : 같은 고객의 1번째/2번째 구매일 간격 (`ROW_NUMBER` + 자기 자신과 합치기)
5. `02_rfm_groups.sql` : 가장 긴 파일. 기준일 -> R, F, M -> 점수(`NTILE`) -> 그룹(`CASE`) 단계별로 읽기

각 SQL 맨 위 주석에 "무엇을 구하는지, 어떤 표를 쓰는지, 결과가 한 줄에 무엇인지"가 적혀 있습니다.
