"""Olist 분석: CSV -> SQLite -> SQL 실행 -> Python으로 계산 -> output/ 에 결과 저장"""
import sqlite3, pathlib, numpy as np, pandas as pd
from scipy import stats

ROOT = pathlib.Path(__file__).parent; DATA = ROOT.parent / "olist_dataset"; OUT = ROOT / "output"; OUT.mkdir(exist_ok=True)

# 1) 데이터 적재 (CSV 파일 -> SQLite 표)
files = {"customers": "olist_customers_dataset.csv", "orders": "olist_orders_dataset.csv", "order_items": "olist_order_items_dataset.csv",
         "order_payments": "olist_order_payments_dataset.csv", "order_reviews": next(f for f in ["olist_order_reviews_dataset.csv", "olist_order_reviews_dataset(5).csv"] if (DATA / f).exists()),
         "products": "olist_products_dataset.csv", "sellers": "olist_sellers_dataset.csv",
         "category_translation": "product_category_name_translation.csv"}
con = sqlite3.connect(OUT / "olist.db")
sizes = {}
for t, f in files.items():
    d = pd.read_csv(DATA / f); sizes[t] = len(d); d.to_sql(t, con, if_exists="replace", index=False)
pd.Series(sizes).rename("rows").to_csv(OUT / "table_sizes.csv"); print(sizes)
for ddl in ["CREATE INDEX IF NOT EXISTS ix_oi ON order_items(order_id)", "CREATE INDEX IF NOT EXISTS ix_o ON orders(order_id)",
            "CREATE INDEX IF NOT EXISTS ix_o_c ON orders(customer_id)", "CREATE INDEX IF NOT EXISTS ix_c ON customers(customer_id)",
            "CREATE INDEX IF NOT EXISTS ix_r ON order_reviews(order_id)", "CREATE INDEX IF NOT EXISTS ix_p ON order_payments(order_id)"]: con.execute(ddl)
con.commit()
sql = lambda f: (ROOT / "sql" / f).read_text(encoding="utf-8")
con.executescript(sql("00_base_views.sql"))
run = lambda f: pd.read_sql_query(sql(f), con)

# 2) 현황: 월별 주문 수
m = run("06_monthly.sql"); m.to_csv(OUT / "monthly.csv", index=False)

# 3) RFM 그룹
rfm = run("01_rfm_groups.sql"); rfm.to_csv(OUT / "rfm.csv", index=False)
names = {1: "재구매", 2: "최근 우수", 3: "최근 일반", 4: "휴면 우수", 5: "휴면 일반"}
g = rfm.groupby("grp").agg(customers=("monetary", "size"), sales=("monetary", "sum"), avg_amount=("monetary", "mean"), avg_days=("recency", "mean"))
g["name"] = g.index.map(names); g["cust_share"] = (g.customers / g.customers.sum() * 100).round(1); g["sales_share"] = (g.sales / g.sales.sum() * 100).round(1)
g[["avg_amount", "avg_days"]] = g[["avg_amount", "avg_days"]].round(0); g.to_csv(OUT / "rfm_groups.csv"); print(g.to_string())
print("전체 고객", len(rfm), "재구매(서로 다른 날 2회 이상)", (rfm.frequency >= 2).sum())
print("R 경계(일):", rfm.groupby("r_score").recency.agg(["min", "max"]).to_dict(), "\nM 경계(R$):", rfm.groupby("m_score").monetary.agg(["min", "max"]).round(0).to_dict())

# 4) 휴면 우수 고객은 불만 때문에 떠났나: 최근 우수(2)와 휴면 우수(4)의 첫 구매 경험 비교
o = pd.read_sql_query("""SELECT v.customer_unique_id, (v.delivered_ts > v.estimated_ts) late, r.score
FROM v_orders v LEFT JOIN (SELECT order_id, AVG(review_score) score FROM order_reviews GROUP BY order_id) r USING(order_id)""", con)
cmp_ = rfm[rfm.grp.isin([2, 4])].merge(o, on="customer_unique_id").groupby("grp").agg(customers=("late", "size"), review=("score", "mean"), late_pct=("late", lambda x: x.mean() * 100)).round(2)
cmp_.to_csv(OUT / "group2_vs_4.csv"); print(cmp_)

# 5) 언제 다시 사는가: 첫 구매 후 재구매까지 걸린 일수
gap = run("08_repurchase_gap.sql"); gap.to_csv(OUT / "repurchase_gap.csv", index=False)
same_day = int((gap.gap_days == 0).sum()); after = gap[gap.gap_days > 0].gap_days
bins = pd.cut(after, [0, 30, 90, 180, 1000], labels=["30일 이내", "31~90일", "91~180일", "180일 초과"])
timing = bins.value_counts(normalize=True).reindex(bins.cat.categories).mul(100).round(1)
timing.rename("share_pct").to_csv(OUT / "repurchase_timing.csv"); print("재구매 일수 분포(%)", timing.to_dict(), "중앙값", after.median(), "n", len(after))
allrep = pd.read_sql_query("SELECT COUNT(DISTINCT customer_unique_id) n FROM v_orders", con).n[0]
print("서로 다른 날 재구매 고객", len(gap), "/ 전체", allrep, "비율", round(len(gap) / allrep * 100, 2))

# 6) 무엇을 다시 사는가: 첫 구매와 두 번째 구매 상품군이 같은 비율
cats = run("09_order_main_category.sql")
od = pd.read_sql_query("SELECT customer_unique_id, order_id, purchase_ts FROM v_orders", con, parse_dates=["purchase_ts"]).sort_values(["customer_unique_id", "purchase_ts"])
od["d"] = od.purchase_ts.dt.date; od["rn"] = od.groupby("customer_unique_id").cumcount()
first = od[od.rn == 0].set_index("customer_unique_id")
second = od.merge(first[["d"]].rename(columns={"d": "d0"}), left_on="customer_unique_id", right_index=True).query("d > d0").groupby("customer_unique_id").first()
pair = first[["order_id"]].join(second[["order_id"]], lsuffix="_1", rsuffix="_2", how="inner").merge(cats.rename(columns={"order_id": "order_id_1", "category": "c1"}), on="order_id_1").merge(cats.rename(columns={"order_id": "order_id_2", "category": "c2"}), on="order_id_2")
same_cat = round((pair.c1 == pair.c2).mean() * 100, 1)
# 비교 기준: 두 번째 구매 상품군을 무작위로 골랐을 때 같은 상품군일 확률
share = pair.c2.value_counts(normalize=True); chance = round(float((pair.c1.map(share)).mean() * 100), 1)
pd.DataFrame({"same_category_pct": [same_cat], "chance_pct": [chance], "n": [len(pair)]}).to_csv(OUT / "same_category.csv", index=False)
print("같은 상품군 재구매", same_cat, "% / 우연 기준", chance, "% / n", len(pair))

# 7) 바우처(할인·적립) 사용 고객이 더 다시 사는가
pay = pd.read_sql_query("SELECT order_id, MAX(payment_type='voucher') voucher FROM order_payments GROUP BY order_id", con)
fo = first.reset_index().merge(pay, on="order_id", how="left"); fo["rep"] = fo.customer_unique_id.isin(gap.customer_unique_id)
vt = fo.groupby("voucher").rep.agg(["mean", "sum", "size"]); vt["rate_pct"] = (vt["mean"] * 100).round(2); vt.to_csv(OUT / "voucher_repurchase.csv"); print(vt)
chi = stats.chi2_contingency(pd.crosstab(fo.voucher, fo.rep)); print("바우처 chi2 p =", round(chi[1], 4))

# 8) 안 산 채로 시간이 지나면 돌아올 가능성: 첫 구매 후 d일까지 안 산 고객이 다음 90일 안에 다시 산 비율
end = od.purchase_ts.max().normalize() + pd.Timedelta(days=1)
fc = first.join(gap.set_index("customer_unique_id").gap_days)
hc = fc[fc.purchase_ts <= end - pd.Timedelta(days=455)]
hz = []
for d in [0, 90, 180, 270, 365]:
    risk = hc[hc.gap_days.isna() | (hc.gap_days > d)]; hit = ((risk.gap_days > d) & (risk.gap_days <= d + 90)).sum()
    hz.append({"from_day": d, "at_risk": len(risk), "returned": int(hit), "rate_pct": round(hit / len(risk) * 100, 2)})
hz = pd.DataFrame(hz); hz.to_csv(OUT / "return_hazard.csv", index=False); print(hz)

# 9) 연락 대상: 휴면 우수 고객 중 마지막 구매 6~12개월 (177~382일)
g4 = rfm[rfm.grp == 4]; target = g4[g4.recency <= 382]
pd.DataFrame({"dormant_all": [len(g4)], "target_6_12m": [len(target)], "over_12m": [len(g4) - len(target)]}).to_csv(OUT / "targets.csv", index=False)
print("휴면 우수", len(g4), "6~12개월", len(target))

# 10) 그룹별 연락 1명당 기대 매출 (가정: 연락으로 추가 3%가 다시 구매) 과 기대 효과 시나리오
ASSUMED = 0.03
g["per_contact"] = (g.avg_amount * ASSUMED).round(1); g.to_csv(OUT / "rfm_groups.csv")
tot_sales = float(rfm.monetary.sum()); a4 = float(g4.monetary.mean())
sc = pd.DataFrame({"rate_pct": [1, 3, 5]}); sc["customers"] = (len(target) * sc.rate_pct / 100).round(0).astype(int); sc["extra_sales"] = (sc.customers * a4).round(0); sc["vs_total_pct"] = (sc.extra_sales / tot_sales * 100).round(1)
sc.to_csv(OUT / "scenario.csv", index=False); print(g[["name", "customers", "sales_share", "avg_amount", "per_contact"]]); print(sc, "평균 구매금액", round(a4), "전체 매출", round(tot_sales))
con.close()
