"""RFM 기준값(177일, R$110)의 근거 확인. run_analysis.py 를 먼저 실행해 analysis/output/ 을 만든 뒤 실행"""
import pathlib
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

OUT = pathlib.Path(__file__).parent / "output"
rfm = pd.read_csv(OUT / "rfm.csv"); gap = pd.read_csv(OUT / "repurchase_gap.csv")

# R: 재구매한 고객이 첫 구매 후 며칠 안에 다시 샀나
g = gap[gap.gap_days > 0].gap_days
print(f"재구매 고객 {len(g):,}명 중 첫 구매 후 90일 이내 {(g <= 90).mean():.1%}, 180일 이내 {(g <= 180).mean():.1%}, 270일 이내 {(g <= 270).mean():.1%}")
print("최근 순 상위 40% 경계(일):", rfm.recency.quantile(0.4))

# F: 구매 횟수 분포
print(f"한 번만 구매한 고객 {(rfm.frequency == 1).mean():.1%}, 서로 다른 날 2번 이상 {(rfm.frequency >= 2).mean():.1%}")

# M: 구매금액 상위 40% 고객이 차지하는 매출 비중과 경계값
s = rfm.monetary.sort_values(ascending=False); k = int(len(s) * 0.4)
print(f"구매금액 상위 40% 고객의 매출 비중 {s.iloc[:k].sum() / s.sum():.1%}, 경계값 R${s.iloc[k - 1]:.0f}")

# 교차 확인: 로그 변환한 R, M 으로 K-means (k=4)
X = StandardScaler().fit_transform(np.log1p(rfm[["recency", "monetary"]]))
rfm["cluster"] = KMeans(4, n_init=10, random_state=0).fit_predict(X)
print(rfm.groupby("cluster").agg(고객수=("cluster", "size"), 최근성_중앙값_일=("recency", "median"), 구매금액_중앙값=("monetary", "median")).round(0).sort_values("최근성_중앙값_일"))
