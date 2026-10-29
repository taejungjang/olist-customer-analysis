"""RFM 기준값(최근 177일, 우수 R$110)이 타당한지 확인하는 코드

run_analysis.py 를 먼저 실행해서 output/ 폴더에 rfm.csv, repurchase_gap.csv 가 있어야 합니다.
확인하는 것
  1. R: 재구매한 고객은 첫 구매 후 며칠 안에 다시 샀나  -> 6개월(180일) 기준이 맞나
  2. F: 구매 횟수 분포                                    -> 왜 점수가 아니라 재구매 여부만 쓰나
  3. M: 구매금액 상위 40% 고객이 매출의 몇 %를 차지하나   -> 우수 기준(R$110)이 맞나
  4. K-means 군집 분석으로 R, M 두 축이 데이터 구조와 맞는지 교차 확인
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

OUTPUT_DIR = Path(__file__).parent / "output"
rfm = pd.read_csv(OUTPUT_DIR / "rfm.csv")
repurchase_gap = pd.read_csv(OUTPUT_DIR / "repurchase_gap.csv")

# ------------------------------------------------------------------
# 1. R: 재구매한 고객이 첫 구매 후 며칠 만에 다시 샀나 (같은 날 추가 주문은 제외)
# ------------------------------------------------------------------
days_to_repurchase = repurchase_gap[repurchase_gap.gap_days > 0].gap_days
share_within_90 = (days_to_repurchase <= 90).mean()
share_within_180 = (days_to_repurchase <= 180).mean()
share_within_270 = (days_to_repurchase <= 270).mean()
print(f"재구매 고객 {len(days_to_repurchase):,}명 중 첫 구매 후")
print(f"  90일 이내 {share_within_90:.1%}, 180일 이내 {share_within_180:.1%}, 270일 이내 {share_within_270:.1%}")
print("마지막 구매가 최근인 순서로 상위 40%의 경계(일):", rfm.recency.quantile(0.4))

# ------------------------------------------------------------------
# 2. F: 구매 횟수 분포
# ------------------------------------------------------------------
bought_once = (rfm.frequency == 1).mean()
bought_repeat = (rfm.frequency >= 2).mean()
print(f"한 번만 구매한 고객 {bought_once:.1%}, 서로 다른 날 2번 이상 구매한 고객 {bought_repeat:.1%}")

# ------------------------------------------------------------------
# 3. M: 구매금액 상위 40% 고객이 차지하는 매출 비중과 경계값
# ------------------------------------------------------------------
amounts_high_to_low = rfm.monetary.sort_values(ascending=False)
top_40_count = int(len(amounts_high_to_low) * 0.4)
top_40_sales = amounts_high_to_low.iloc[:top_40_count].sum()
top_40_share = top_40_sales / amounts_high_to_low.sum()
boundary_amount = amounts_high_to_low.iloc[top_40_count - 1]
print(f"구매금액 상위 40% 고객의 매출 비중 {top_40_share:.1%}, 경계값 R${boundary_amount:.0f}")

# ------------------------------------------------------------------
# 4. 교차 확인: R과 M(로그 변환 후 표준화)으로 K-means 군집 4개 만들기
# ------------------------------------------------------------------
log_values = np.log1p(rfm[["recency", "monetary"]])
scaled_values = StandardScaler().fit_transform(log_values)
kmeans = KMeans(n_clusters=4, n_init=10, random_state=0)
rfm["cluster"] = kmeans.fit_predict(scaled_values)

cluster_summary = rfm.groupby("cluster").agg(
    고객수=("cluster", "size"),
    최근성_중앙값_일=("recency", "median"),
    구매금액_중앙값=("monetary", "median"),
)
print(cluster_summary.round(0).sort_values("최근성_중앙값_일"))
