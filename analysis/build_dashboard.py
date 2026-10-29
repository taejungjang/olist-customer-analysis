"""분석 결과(output/*.csv)를 넣어 대시보드 HTML(olist_dashboard.html)을 만드는 코드

dashboard_template.html 안의 __DATA__ 자리에 아래에서 만든 데이터(JSON)를 끼워 넣습니다.
run_analysis.py 를 먼저 실행해서 output/ 폴더에 CSV 파일이 있어야 합니다.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"

# ------------------------------------------------------------------
# 1. 분석 결과 CSV 읽기
# ------------------------------------------------------------------
rfm = pd.read_csv(OUTPUT_DIR / "rfm.csv")                              # 고객별 RFM 값과 그룹
groups = pd.read_csv(OUTPUT_DIR / "rfm_groups.csv")                    # 그룹별 요약
monthly = pd.read_csv(OUTPUT_DIR / "monthly.csv")                      # 월별 주문 수
hazard = pd.read_csv(OUTPUT_DIR / "return_hazard.csv")                 # 연락 없이 돌아오는 비율
targets = pd.read_csv(OUTPUT_DIR / "targets.csv").iloc[0]              # 연락 대상 수
same_category = pd.read_csv(OUTPUT_DIR / "same_category.csv").iloc[0]  # 같은 상품군 재구매 비율(전체)
by_first_category = pd.read_csv(OUTPUT_DIR / "same_by_first_category.csv")        # 첫 구매 상품군별 비율
target_by_same_rate = pd.read_csv(OUTPUT_DIR / "target_by_same_rate.csv").set_index("group")

# ------------------------------------------------------------------
# 2. 대시보드에 넣을 데이터 만들기 (표 -> 파이썬 목록/사전)
# ------------------------------------------------------------------
group_list = []
for _, row in groups.iterrows():
    group_list.append(
        {
            "grp": int(row.grp),
            "name": row["name"],
            "customers": int(row.customers),
            "cust_share": float(row.cust_share),
            "sales_share": float(row.sales_share),
            "avg_amount": float(row.avg_amount),
        }
    )

monthly_list = []
for row in monthly.itertuples():
    monthly_list.append({"m": row.month, "orders": int(row.orders)})

hazard_list = []
for row in hazard.itertuples():
    hazard_list.append({"from_day": int(row.from_day), "rate_pct": float(row.rate_pct)})

# 같은 상품군 비율이 높은 상위 4개 / 낮은 하위 4개 상품군 (이미 높은 순으로 정렬되어 있음)
high_categories = []
for _, row in by_first_category.head(4).iterrows():
    high_categories.append({"name": row["name"], "pct": float(row.same_pct)})

low_categories = []
for _, row in by_first_category.tail(4).iterrows():
    low_categories.append({"name": row["name"], "pct": float(row.same_pct)})

data = {
    "customers": int(len(rfm)),
    "repeat": int((rfm.frequency >= 2).sum()),
    "total_sales": round(float(rfm.monetary.sum())),
    "groups": group_list,
    "monthly": monthly_list,
    "hazard": hazard_list,
    "targets": {
        "dormant_all": int(targets.dormant_all),
        "target_6_12m": int(targets.target_6_12m),
    },
    "samecat": {"same": float(same_category.same_category_pct)},
    "bycat_high": high_categories,
    "bycat_low": low_categories,
    "target_mix": {
        "high": int(target_by_same_rate.customers["high"]),
        "high_pct": float(target_by_same_rate.share_pct["high"]),
    },
}

# ------------------------------------------------------------------
# 3. 템플릿에 데이터를 끼워 넣어 HTML 저장
# ------------------------------------------------------------------
template_text = (ROOT / "dashboard_template.html").read_text(encoding="utf-8")
html = template_text.replace("__DATA__", json.dumps(data, ensure_ascii=False))

output_file = ROOT.parent / "olist_dashboard.html"
output_file.write_text(html, encoding="utf-8")
print("저장:", output_file, f"({len(html) // 1024} KB)")
