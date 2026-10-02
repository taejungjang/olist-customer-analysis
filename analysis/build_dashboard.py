"""output/*.csv 의 분석 결과를 담은 대시보드 HTML(olist_dashboard.html) 생성"""
import json, pathlib, pandas as pd

ROOT = pathlib.Path(__file__).parent; OUT = ROOT / "output"
rfm = pd.read_csv(OUT / "rfm.csv"); g = pd.read_csv(OUT / "rfm_groups.csv")
m = pd.read_csv(OUT / "monthly.csv"); hz = pd.read_csv(OUT / "return_hazard.csv")
tg = pd.read_csv(OUT / "targets.csv").iloc[0]; sc = pd.read_csv(OUT / "same_category.csv").iloc[0]
vt = pd.read_csv(OUT / "voucher_repurchase.csv").set_index("voucher")

data = {
    "customers": int(len(rfm)), "repeat": int((rfm.frequency >= 2).sum()), "total_sales": round(float(rfm.monetary.sum())),
    "groups": [{"grp": int(r.grp), "name": r["name"], "customers": int(r.customers), "cust_share": float(r.cust_share),
                "sales_share": float(r.sales_share), "avg_amount": float(r.avg_amount)} for _, r in g.iterrows()],
    "monthly": [{"m": r.month, "orders": int(r.orders)} for r in m.itertuples()],
    "hazard": [{"from_day": int(r.from_day), "rate_pct": float(r.rate_pct)} for r in hz.itertuples()],
    "targets": {"dormant_all": int(tg.dormant_all), "target_6_12m": int(tg.target_6_12m)},
    "samecat": {"same": float(sc.same_category_pct), "chance": float(sc.chance_pct)},
    "voucher": {"with": float(vt.rate_pct[1.0]), "without": float(vt.rate_pct[0.0])},
}
html = (ROOT / "dashboard_template.html").read_text(encoding="utf-8").replace("__DATA__", json.dumps(data, ensure_ascii=False))
out = ROOT.parent / "olist_dashboard.html"; out.write_text(html, encoding="utf-8"); print("saved", out, len(html) // 1024, "KB")
