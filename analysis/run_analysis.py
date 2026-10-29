"""Olist 고객 분석: CSV -> SQLite -> SQL 실행 -> Python 계산 -> output/ 폴더에 결과 CSV 저장

실행 순서
  1. CSV 파일을 SQLite 데이터베이스에 넣기
  2. 월별 주문 수 (현황)
  3. 고객을 RFM 기준 5개 그룹으로 나누기
  4. 휴면 우수 고객의 첫 구매 경험 확인 (불만 때문에 떠났나?)
  5. 재구매 고객이 첫 구매 후 며칠 만에 다시 샀나
  6. 다시 살 때 같은 상품군을 샀나 (전체, 첫 구매 상품군별)
  7. 시간이 지나면 연락 없이도 돌아오나 (연락 시점 정하기)
  8. 연락 대상 정하기 (휴면 우수 중 마지막 구매 6~12개월)
  9. 연락 1명당 기대 매출과 기대 효과 (가정)
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

# ------------------------------------------------------------------
# 설정값
# ------------------------------------------------------------------
ROOT = Path(__file__).parent
DATA_DIR = ROOT.parent / "olist_dataset"      # Kaggle에서 받은 CSV를 넣는 폴더
OUTPUT_DIR = ROOT / "output"                  # 결과 파일이 저장되는 폴더
OUTPUT_DIR.mkdir(exist_ok=True)

GROUP_NAMES = {1: "재구매", 2: "최근 우수", 3: "최근 일반", 4: "휴면 우수", 5: "휴면 일반"}
ASSUMED_REPURCHASE_RATE = 0.03        # 연락하면 3%가 다시 산다는 가정 (측정한 값이 아님)
SCENARIO_RATES_PCT = [1, 3, 5]        # 위 가정을 1%, 3%, 5%로 바꿔 보는 시나리오
TARGET_MAX_RECENCY_DAYS = 382         # 연락 대상: 마지막 구매 후 382일(약 12개월) 이내 (177일 초과는 휴면 정의)
HAZARD_START_DAYS = [0, 90, 180, 270, 365]   # 첫 구매 후 이 날수까지 안 산 고객을 본다
HAZARD_WINDOW_DAYS = 90                      # 그 뒤 90일 안에 다시 샀는지 본다
HAZARD_MIN_FOLLOWUP_DAYS = 455               # 365 + 90일: 끝까지 지켜볼 수 있는 고객만 사용
MIN_CUSTOMERS_PER_CATEGORY = 50       # 상품군별 비교는 고객 50명 이상인 상품군만
HIGH_SAME_RATE_PCT = 45               # 같은 상품군 비율이 이 값 이상이면 "높음"
LOW_SAME_RATE_PCT = 35                # 같은 상품군 비율이 이 값 미만이면 "낮음"

# 상품군 영어 이름 -> 한글 이름 (그래프와 대시보드에 표시용)
CATEGORY_KOREAN_NAMES = {
    "watches_gifts": "시계·선물",
    "sports_leisure": "스포츠·레저",
    "health_beauty": "건강·미용",
    "computers_accessories": "컴퓨터 액세서리",
    "fashion_bags_accessories": "패션 가방·잡화",
    "bed_bath_table": "침구·욕실",
    "auto": "자동차용품",
    "telephony": "통신기기",
    "perfumery": "향수",
    "furniture_decor": "가구·장식",
    "housewares": "생활용품",
    "toys": "완구",
    "garden_tools": "정원용품",
    "cool_stuff": "이색 상품",
}


# ------------------------------------------------------------------
# 1. CSV 파일을 SQLite에 넣기
# ------------------------------------------------------------------
def find_review_file():
    """리뷰 파일은 내려받은 방식에 따라 이름이 조금 다를 수 있어서 둘 중 있는 것을 사용"""
    candidates = ["olist_order_reviews_dataset.csv", "olist_order_reviews_dataset(5).csv"]
    for file_name in candidates:
        if (DATA_DIR / file_name).exists():
            return file_name
    raise FileNotFoundError("리뷰 CSV 파일이 olist_dataset 폴더에 없습니다")


TABLE_FILES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": find_review_file(),
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

connection = sqlite3.connect(OUTPUT_DIR / "olist.db")

for table_name, file_name in TABLE_FILES.items():
    table = pd.read_csv(DATA_DIR / file_name)
    table.to_sql(table_name, connection, if_exists="replace", index=False)
    print(f"{table_name}: {len(table):,}행")

# 조회 속도를 높이기 위한 색인
index_statements = [
    "CREATE INDEX IF NOT EXISTS ix_order_items ON order_items(order_id)",
    "CREATE INDEX IF NOT EXISTS ix_orders ON orders(order_id)",
    "CREATE INDEX IF NOT EXISTS ix_orders_customer ON orders(customer_id)",
    "CREATE INDEX IF NOT EXISTS ix_customers ON customers(customer_id)",
    "CREATE INDEX IF NOT EXISTS ix_reviews ON order_reviews(order_id)",
    "CREATE INDEX IF NOT EXISTS ix_payments ON order_payments(order_id)",
]
for statement in index_statements:
    connection.execute(statement)
connection.commit()


def read_sql_file(file_name):
    """sql 폴더의 SQL 파일 내용을 읽기"""
    return (ROOT / "sql" / file_name).read_text(encoding="utf-8")


def run_sql_file(file_name):
    """sql 폴더의 SQL 파일을 실행하고 결과를 표(DataFrame)로 돌려주기"""
    return pd.read_sql_query(read_sql_file(file_name), connection)


# 분석 대상 주문만 모아 둔 뷰(v_orders) 만들기: 배송 완료 주문 + 고객 번호 + 배송 정보
connection.executescript(read_sql_file("01_base_view.sql"))


# ------------------------------------------------------------------
# 2. 현황: 월별 주문 수
# ------------------------------------------------------------------
monthly_orders = run_sql_file("03_monthly_orders.sql")
monthly_orders.to_csv(OUTPUT_DIR / "monthly.csv", index=False)


# ------------------------------------------------------------------
# 3. 고객을 RFM 기준 5개 그룹으로 나누기
#    (그룹을 나누는 규칙은 sql/02_rfm_groups.sql 에 있음)
# ------------------------------------------------------------------
rfm = run_sql_file("02_rfm_groups.sql")
rfm.to_csv(OUTPUT_DIR / "rfm.csv", index=False)

# 그룹별 고객 수, 매출 합계, 평균 구매금액, 마지막 구매 후 평균 일수
group_summary = rfm.groupby("grp").agg(
    customers=("monetary", "size"),
    sales=("monetary", "sum"),
    avg_amount=("monetary", "mean"),
    avg_days=("recency", "mean"),
)
group_summary["name"] = group_summary.index.map(GROUP_NAMES)
group_summary["cust_share"] = (group_summary.customers / group_summary.customers.sum() * 100).round(1)
group_summary["sales_share"] = (group_summary.sales / group_summary.sales.sum() * 100).round(1)
group_summary["avg_amount"] = group_summary.avg_amount.round(0)
group_summary["avg_days"] = group_summary.avg_days.round(0)
print(group_summary.to_string())

# 5등분 점수(1~5점)별 경계값: 177일, R$110 이 어디서 나왔는지 확인용
print("R 점수별 마지막 구매 후 일수(최소~최대):")
print(rfm.groupby("r_score").recency.agg(["min", "max"]))
print("M 점수별 총 구매금액(최소~최대, R$):")
print(rfm.groupby("m_score").monetary.agg(["min", "max"]).round(0))


# ------------------------------------------------------------------
# 4. 휴면 우수 고객은 불만 때문에 떠났나?
#    최근 우수(2)와 휴면 우수(4) 고객의 첫 구매 평점과 늦은 배송 비율 비교
# ------------------------------------------------------------------
orders_with_review = pd.read_sql_query(
    """
    SELECT v.customer_unique_id,
           (v.delivered_ts > v.estimated_ts) AS late,
           r.score
    FROM v_orders v
    LEFT JOIN (SELECT order_id, AVG(review_score) AS score
               FROM order_reviews GROUP BY order_id) r USING (order_id)
    """,
    connection,
)
good_customers = rfm[rfm.grp.isin([2, 4])]
experience = good_customers.merge(orders_with_review, on="customer_unique_id")
group2_vs_4 = experience.groupby("grp").agg(
    customers=("late", "size"),
    review=("score", "mean"),
    late_ratio=("late", "mean"),
)
group2_vs_4["late_pct"] = group2_vs_4.late_ratio * 100
group2_vs_4 = group2_vs_4.drop(columns="late_ratio").round(2)
group2_vs_4.to_csv(OUTPUT_DIR / "group2_vs_4.csv")
print(group2_vs_4)


# ------------------------------------------------------------------
# 5. 재구매 고객은 첫 구매 후 며칠 만에 다시 샀나
# ------------------------------------------------------------------
repurchase_gap = run_sql_file("04_repurchase_gap.sql")   # 고객별 (첫 구매 ~ 두 번째 구매일) 간격
repurchase_gap.to_csv(OUTPUT_DIR / "repurchase_gap.csv", index=False)
print(f"서로 다른 날 2번 이상 산 고객: {len(repurchase_gap):,}명")


# ------------------------------------------------------------------
# 6. 다시 살 때 같은 상품군을 샀나
# ------------------------------------------------------------------
# 6-1. 고객별 첫 구매 주문과 두 번째 구매 주문 찾기
order_main_category = run_sql_file("05_order_main_category.sql")   # 주문별 대표 상품군(가장 비싼 상품)

orders = pd.read_sql_query(
    "SELECT customer_unique_id, order_id, purchase_ts FROM v_orders",
    connection,
    parse_dates=["purchase_ts"],
)
orders = orders.sort_values(["customer_unique_id", "purchase_ts"])
orders["purchase_date"] = orders.purchase_ts.dt.date
orders["order_number"] = orders.groupby("customer_unique_id").cumcount()   # 0이면 첫 구매

first_orders = orders[orders.order_number == 0].set_index("customer_unique_id")

# 두 번째 구매 = 첫 구매일보다 늦은 날의 주문 중 가장 빠른 것 (같은 날 추가 주문은 제외)
first_dates = first_orders[["purchase_date"]].rename(columns={"purchase_date": "first_date"})
later_orders = orders.merge(first_dates, left_on="customer_unique_id", right_index=True)
later_orders = later_orders[later_orders.purchase_date > later_orders.first_date]
second_orders = later_orders.groupby("customer_unique_id").first()

# 6-2. 첫 구매 상품군(first_category)과 두 번째 구매 상품군(second_category)을 한 줄에 놓기
first_category = order_main_category.rename(columns={"order_id": "first_order_id", "category": "first_category"})
second_category = order_main_category.rename(columns={"order_id": "second_order_id", "category": "second_category"})

pairs = first_orders[["order_id"]].rename(columns={"order_id": "first_order_id"})
pairs = pairs.join(second_orders[["order_id"]].rename(columns={"order_id": "second_order_id"}), how="inner")
pairs = pairs.merge(first_category, on="first_order_id")
pairs = pairs.merge(second_category, on="second_order_id")
pairs["is_same_category"] = pairs.first_category == pairs.second_category

# 6-3. 전체에서 같은 상품군을 산 비율
same_category_pct = round(pairs.is_same_category.mean() * 100, 1)
pd.DataFrame({"same_category_pct": [same_category_pct], "n": [len(pairs)]}).to_csv(
    OUTPUT_DIR / "same_category.csv", index=False
)
print(f"다시 산 고객 {len(pairs):,}명 중 같은 상품군 {same_category_pct}%")

# 6-4. 첫 구매 상품군별로 같은 상품군을 산 비율 (고객 50명 이상인 상품군만)
by_first_category = pairs.groupby("first_category").agg(
    customers=("is_same_category", "size"),
    same_ratio=("is_same_category", "mean"),
)
by_first_category["same_pct"] = (by_first_category.same_ratio * 100).round(1)
by_first_category = by_first_category[by_first_category.customers >= MIN_CUSTOMERS_PER_CATEGORY]
by_first_category = by_first_category.drop(columns="same_ratio")
by_first_category = by_first_category.sort_values("same_pct", ascending=False)
korean_names = []
for category in by_first_category.index:
    korean_names.append(CATEGORY_KOREAN_NAMES.get(category, category))
by_first_category["name"] = korean_names
by_first_category.to_csv(OUTPUT_DIR / "same_by_first_category.csv")
print(by_first_category[["name", "customers", "same_pct"]].to_string())


# ------------------------------------------------------------------
# 7. 시간이 지나면 연락 없이도 돌아오나 (연락 시점 정하기)
#    첫 구매 후 d일까지 안 산 고객이, 그 뒤 90일 안에 다시 산 비율
# ------------------------------------------------------------------
data_end = orders.purchase_ts.max().normalize() + pd.Timedelta(days=1)

# 첫 구매 정보에 "첫 구매 후 재구매까지 며칠" 붙이기 (재구매 안 했으면 비어 있음)
gap_by_customer = repurchase_gap.set_index("customer_unique_id").gap_days
customers = first_orders.join(gap_by_customer)

# 끝까지 지켜볼 수 있는 고객만 사용: 첫 구매가 데이터 끝에서 455일 이상 전인 고객
last_allowed_date = data_end - pd.Timedelta(days=HAZARD_MIN_FOLLOWUP_DAYS)
followed_customers = customers[customers.purchase_ts <= last_allowed_date]

hazard_rows = []
for start_day in HAZARD_START_DAYS:
    end_day = start_day + HAZARD_WINDOW_DAYS
    # 첫 구매 후 start_day일이 지나도록 아직 안 산 고객
    not_yet_bought = followed_customers[
        followed_customers.gap_days.isna() | (followed_customers.gap_days > start_day)
    ]
    # 그중 start_day ~ end_day 사이에 다시 산 고객
    bought_in_window = (not_yet_bought.gap_days > start_day) & (not_yet_bought.gap_days <= end_day)
    returned = int(bought_in_window.sum())
    hazard_rows.append(
        {
            "from_day": start_day,
            "at_risk": len(not_yet_bought),
            "returned": returned,
            "rate_pct": round(returned / len(not_yet_bought) * 100, 2),
        }
    )
hazard = pd.DataFrame(hazard_rows)
hazard.to_csv(OUTPUT_DIR / "return_hazard.csv", index=False)
print(hazard)


# ------------------------------------------------------------------
# 8. 연락 대상: 휴면 우수 고객 중 마지막 구매가 6~12개월(177~382일)인 고객
# ------------------------------------------------------------------
dormant_good = rfm[rfm.grp == 4]                                    # 휴면 우수 전체
target = dormant_good[dormant_good.recency <= TARGET_MAX_RECENCY_DAYS]  # 그중 12개월 이내

pd.DataFrame(
    {
        "dormant_all": [len(dormant_good)],
        "target_6_12m": [len(target)],
        "over_12m": [len(dormant_good) - len(target)],
    }
).to_csv(OUTPUT_DIR / "targets.csv", index=False)
print(f"휴면 우수 {len(dormant_good):,}명 중 6~12개월 {len(target):,}명")


def classify_same_rate(same_pct):
    """첫 구매 상품군의 '같은 상품군 재구매 비율'을 높음/보통/낮음으로 나누기"""
    if pd.isna(same_pct):
        return "other"      # 비율을 계산하지 못한 상품군 (고객 50명 미만)
    if same_pct >= HIGH_SAME_RATE_PCT:
        return "high"
    if same_pct < LOW_SAME_RATE_PCT:
        return "low"
    return "mid"


# 연락 대상 고객이 처음 산 상품군을 찾아, 높음/보통/낮음 중 어디에 속하는지 세기
target_first_orders = target[["customer_unique_id"]].merge(
    first_orders.reset_index()[["customer_unique_id", "order_id"]], on="customer_unique_id"
)
target_first_orders = target_first_orders.merge(order_main_category, on="order_id", how="left")
same_pct_by_category = by_first_category.same_pct.to_dict()
target_first_orders["same_pct"] = target_first_orders.category.map(same_pct_by_category)
target_first_orders["same_rate_group"] = target_first_orders.same_pct.map(classify_same_rate)

target_by_same_rate = target_first_orders.same_rate_group.value_counts()
target_by_same_rate = target_by_same_rate.rename_axis("group").rename("customers").reset_index()
target_by_same_rate["share_pct"] = (target_by_same_rate.customers / len(target_first_orders) * 100).round(1)
target_by_same_rate.to_csv(OUTPUT_DIR / "target_by_same_rate.csv", index=False)
print(target_by_same_rate)


# ------------------------------------------------------------------
# 9. 연락 1명당 기대 매출과 기대 효과 (모두 가정)
#    기대 매출 = 그룹 평균 구매금액 x 연락받은 고객이 다시 살 확률(3%로 가정)
# ------------------------------------------------------------------
group_summary["per_contact"] = (group_summary.avg_amount * ASSUMED_REPURCHASE_RATE).round(1)
group_summary.to_csv(OUTPUT_DIR / "rfm_groups.csv")

# 연락 대상 14,237명 중 1%, 3%, 5%가 더 돌아오면 추가 매출은?
total_sales = float(rfm.monetary.sum())
target_avg_amount = float(dormant_good.monetary.mean())   # 휴면 우수 고객 평균 구매금액

scenario = pd.DataFrame({"rate_pct": SCENARIO_RATES_PCT})
scenario["customers"] = (len(target) * scenario.rate_pct / 100).round(0).astype(int)
scenario["extra_sales"] = (scenario.customers * target_avg_amount).round(0)
scenario["vs_total_pct"] = (scenario.extra_sales / total_sales * 100).round(1)
scenario.to_csv(OUTPUT_DIR / "scenario.csv", index=False)

print(group_summary[["name", "customers", "sales_share", "avg_amount", "per_contact"]])
print(scenario)
print(f"휴면 우수 평균 구매금액 R${target_avg_amount:.0f}, 전체 매출 R${total_sales:,.0f}")

connection.close()
