"""포트폴리오 PPT 9장 생성 (python-pptx). 수치는 output/*.csv 의 분석 결과를 그대로 읽어 씀"""
import pathlib
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.oxml.ns import qn
from lxml import etree

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "output"
FONT, MONO = "Malgun Gothic", "Consolas"
GREEN, TEAL, RED, GRAY, DGRAY, INK, MUTE, TINT = "0B3D2E", "2A9D8F", "D9534F", "B4BFBB", "7B8F89", "1F2D29", "5E7069", "F0F4F2"
def rgb(h): return RGBColor.from_string(h)

# ------------------------------------------------------------ 분석 결과 읽기
sizes = pd.read_csv(OUT / "table_sizes.csv", index_col=0).rows
rfm = pd.read_csv(OUT / "rfm.csv"); N = len(rfm)
g = pd.read_csv(OUT / "rfm_groups.csv").set_index("grp")
cmp_ = pd.read_csv(OUT / "group2_vs_4.csv").set_index("grp")
samecat = pd.read_csv(OUT / "same_category.csv").iloc[0]
vt = pd.read_csv(OUT / "voucher_repurchase.csv").set_index("voucher")
hz = pd.read_csv(OUT / "return_hazard.csv"); tg = pd.read_csv(OUT / "targets.csv").iloc[0]
sc = pd.read_csv(OUT / "scenario.csv"); m = pd.read_csv(OUT / "monthly.csv")
rep_n = int(g.customers[1]); rep_pct = rep_n / N * 100
n4 = int(g.customers[4]); avg4 = int(g.avg_amount[4])
v_with, v_without = float(vt.rate_pct[1.0]), float(vt.rate_pct[0.0])
persons = 96096

prs = Presentation(); prs.slide_width = Inches(10); prs.slide_height = Inches(5.625)
blank = prs.slide_layouts[6]

def set_bullet(para, indent=0.16):
    pPr = para._p.get_or_add_pPr()
    pPr.set("marL", str(int(Inches(indent)))); pPr.set("indent", str(-int(Inches(indent))))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for e in pPr.findall(qn(tag)): pPr.remove(e)
    bu = etree.SubElement(pPr, qn("a:buChar")); bu.set("char", "-")

def text(slide, x, y, w, h, paras, size=12, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=FONT, gap=0, bullets=False, name=None):
    """paras: 문자열 또는 문단 목록. 문단은 문자열 또는 [(글, {size,color,bold}), ...]"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name: tb.name = name
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    if isinstance(paras, str): paras = [paras]
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        if gap and i: para.space_before = Pt(gap)
        if bullets: set_bullet(para)
        for t, o in ([(p, {})] if isinstance(p, str) else p):
            r = para.add_run(); r.text = t; f = r.font
            f.name = o.get("font", font); f.size = Pt(o.get("size", size)); f.bold = o.get("bold", bold); f.color.rgb = rgb(o.get("color", color))
    return tb

def box(slide, x, y, w, h, fill, name):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)); s.name = name
    s.fill.solid(); s.fill.fore_color.rgb = rgb(fill); s.line.fill.background(); s.shadow.inherit = False
    return s

def outline(slide, x, y, w, h, name):
    """강조할 행이나 영역에 빨간 테두리"""
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)); s.name = name
    s.fill.background(); s.line.color.rgb = rgb(RED); s.line.width = Pt(2.25); s.shadow.inherit = False
    return s

def frame(slide, n, eyebrow, title):
    text(slide, 0.5, 0.28, 9, 0.25, eyebrow, size=12, color=TEAL, bold=True, name="Section")
    text(slide, 0.5, 0.55, 9, 0.7, title, size=24, color=GREEN, bold=True, name="Title")
    text(slide, 0.5, 5.28, 6, 0.2, "Olist 주문 데이터 분석", size=9, color=GRAY, name="Footer")
    text(slide, 9.0, 5.28, 0.5, 0.2, str(n), size=9, color=GRAY, align=PP_ALIGN.RIGHT, name="Page")

def code(slide, x, y, w, h, lines, name, size=8.5):
    box(slide, x, y, w, h, "1E2B28", name)
    text(slide, x + 0.15, y + 0.1, w - 0.3, h - 0.15, lines, size=size, color="E4EEEA", font=MONO, name=name + "-text")

def style_chart(ch, title, legend=False, vmax=None, axis=False):
    ch.font.name = FONT; ch.font.size = Pt(10); ch.font.color.rgb = rgb("3C4A46")
    ch.has_title = True; ch.chart_title.text_frame.text = title
    r = ch.chart_title.text_frame.paragraphs[0].runs[0]; r.font.size = Pt(11); r.font.bold = True; r.font.name = FONT; r.font.color.rgb = rgb(INK)
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(10)
    if ch.chart_type in (XL_CHART_TYPE.PIE, XL_CHART_TYPE.DOUGHNUT): return
    va = ch.value_axis; va.minimum_scale = 0
    if vmax: va.maximum_scale = vmax
    va.has_major_gridlines = axis; va.visible = axis
    if axis:
        va.major_gridlines.format.line.color.rgb = rgb("E3E8E6"); va.format.line.fill.background(); va.tick_labels.font.size = Pt(9)
    ch.category_axis.has_major_gridlines = False; ch.category_axis.format.line.color.rgb = rgb("C9D5D0"); ch.category_axis.tick_labels.font.size = Pt(10)

def labels(plot, fmt, pos=XL_LABEL_POSITION.OUTSIDE_END):
    plot.has_data_labels = True; dl = plot.data_labels
    dl.number_format = fmt; dl.number_format_is_linked = False; dl.position = pos; dl.font.size = Pt(10)

def paint(series, colors):
    for i, c in enumerate(colors):
        pt = series.points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(c)

def bar(slide, x, y, w, h, cats, vals, title, name, vmax=None, fmt="0.0", colors=None, gap=50, axis=False):
    cd = CategoryChartData(); cd.categories = cats; cd.add_series("값", [float(a) for a in vals])
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd); gf.name = name
    ch = gf.chart; style_chart(ch, title, vmax=vmax, axis=axis); ch.plots[0].gap_width = gap; labels(ch.plots[0], fmt)
    if colors: paint(ch.plots[0].series[0], colors)
    return ch

def pie(slide, x, y, w, h, cats, vals, colors, title, name):
    cd = CategoryChartData(); cd.categories = cats; cd.add_series("비율", [float(a) for a in vals])
    gf = slide.shapes.add_chart(XL_CHART_TYPE.PIE, Inches(x), Inches(y), Inches(w), Inches(h), cd); gf.name = name
    ch = gf.chart; style_chart(ch, title, legend=True); labels(ch.plots[0], '0.0"%"', XL_LABEL_POSITION.OUTSIDE_END)
    for i, c in enumerate(colors):
        pt = ch.plots[0].series[0].points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(c)
        pt.format.line.color.rgb = rgb("FFFFFF"); pt.format.line.width = Pt(1.5)
    return ch

def table(slide, x, y, colw, rows, name, size=10, rowh=0.36, align_right=(), first_col_bold=False):
    t = slide.shapes.add_table(len(rows), len(colw), Inches(x), Inches(y), Inches(sum(colw)), Inches(rowh * len(rows))); t.name = name
    tbl = t.table
    sid = tbl._tbl.tblPr.find(qn("a:tableStyleId"))
    if sid is not None: sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # 스타일 없음
    for j, cw in enumerate(colw): tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(rowh)
        for j, v in enumerate(row):
            c = tbl.cell(i, j); c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.margin_left = c.margin_right = Inches(0.08); c.margin_top = c.margin_bottom = Inches(0.02)
            c.fill.solid(); c.fill.fore_color.rgb = rgb(GREEN if i == 0 else (TINT if i % 2 == 1 else "FFFFFF"))
            tf = c.text_frame; tf.word_wrap = True; tf.text = ""
            r = tf.paragraphs[0].add_run(); r.text = str(v); r.font.name = FONT; r.font.size = Pt(size)
            r.font.bold = i == 0 or (first_col_bold and j == 0); r.font.color.rgb = rgb("FFFFFF" if i == 0 else INK)
            tf.paragraphs[0].alignment = PP_ALIGN.RIGHT if j in align_right else PP_ALIGN.LEFT
    return t

# ============================================================ 1. 표지
s = prs.slides.add_slide(blank)
text(s, 0.8, 1.7, 8.4, 0.9, "Olist 쇼핑몰 주문 데이터 분석", size=34, color=GREEN, bold=True, name="Title")
text(s, 0.8, 2.7, 8.4, 0.5, "어떤 고객에게 먼저 투자해야 할까?", size=18, color=MUTE, name="Subtitle")
text(s, 0.8, 4.4, 8.4, 0.3, "SQL, Python  |  Olist 공개 주문 데이터 2016.9 ~ 2018.10", size=12, color=GRAY, name="Meta")
s.notes_slide.notes_text_frame.text = "Kaggle 공개 데이터(Olist Brazilian E-Commerce)."

# ============================================================ 2. 배경과 문제
s = prs.slides.add_slide(blank)
frame(s, 2, "배경과 문제", "주문은 늘지 않고, 대부분의 고객은 한 번만 샀음")
cd = CategoryChartData(); cd.categories = [f"{r[2:4]}.{int(r[5:])}" for r in m.month]; cd.add_series("월별 주문 수", [int(v) for v in m.orders])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.4), Inches(1.4), Inches(5.3), Inches(3.4), cd); gf.name = "chart-monthly"
ch = gf.chart; style_chart(ch, "월별 주문 수 (건)", vmax=8000, axis=True); ch.plots[0].gap_width = 40
paint(ch.plots[0].series[0], [TEAL if i < 12 else GREEN for i in range(len(m))])
ch.value_axis.tick_labels.number_format = "#,##0"; ch.value_axis.tick_labels.number_format_is_linked = False
text(s, 0.5, 4.85, 5.2, 0.3, "연한 색: 2017년, 진한 색: 2018년", size=9.5, color=MUTE)
steps = [("배경", TEAL, "2018년부터 주문이 월 6천 ~ 7천 건에서 늘지 않음"),
         ("문제", RED, f"고객 100명 중 {100 - round(rep_pct)}명은 한 번만 샀음. 모든 고객에게 연락하면 비용이 크므로 어디에 집중할지 정해야 함"),
         ("분석", GREEN, "고객을 구매 방식(RFM)으로 나눠, 그룹별로 집중할 곳과 방법을 정함")]
for i, (h, c, d) in enumerate(steps):
    y = 1.45 + i * 1.2
    text(s, 6.0, y, 3.5, 0.3, h, size=13, color=c, bold=True)
    text(s, 6.0, y + 0.32, 3.5, 0.8, d, size=11)
s.notes_slide.notes_text_frame.text = "SQL 06_monthly.sql, 재구매 = 서로 다른 날 2번 이상 구매(같은 날 추가 주문은 한 번으로 셈, 2.2%)."

# ============================================================ 3. 데이터
s = prs.slides.add_slide(blank)
frame(s, 3, "데이터", "브라질 온라인 쇼핑몰 Olist의 실제 주문 기록")
text(s, 0.5, 1.3, 9, 0.5, ["여러 판매자가 입점해 물건을 파는 쇼핑몰에서, 고객이 주문한 내용과 배송, 결제, 리뷰가 기록됨 (2016.9 ~ 2018.10, 고객 정보는 익명 처리)"], size=11.5)
rows = [["표", "한 줄이 뜻하는 것", "건수", "주요 항목"],
        ["주문", "고객이 한 번 주문한 기록", f"{sizes.orders:,}", "주문 상태, 구매 시각, 배송 시각"], ["주문 상품", "주문에 담긴 상품 1개", f"{sizes.order_items:,}", "상품, 판매자, 가격, 배송비"],
        ["고객", "주문한 고객 정보", f"{sizes.customers:,}", "고객 구분 번호, 지역"], ["결제", "주문의 결제 내용", f"{sizes.order_payments:,}", "결제 수단, 할부 개월, 바우처"],
        ["리뷰", "고객이 남긴 평점", f"{sizes.order_reviews:,}", "평점 1~5점"], ["상품", "판매 상품 정보", f"{sizes.products:,}", "상품군"]]
table(s, 0.5, 1.9, [1.2, 2.9, 1.0, 3.9], rows, "table-data", size=10, rowh=0.37, align_right=(2,))
text(s, 0.5, 4.6, 9.0, 0.6, [[("주의  ", {"bold": True, "color": RED}), (f"주문할 때마다 고객 번호가 새로 생겨서, 같은 사람은 '고객 구분 번호'로 묶음 ({sizes.customers:,}건 → {persons:,}명)", {})],
                             [("분석 대상  ", {"bold": True, "color": GREEN}), (f"취소를 뺀 배송 완료 주문 96,470건, 고객 {N:,}명", {})]], size=10.5, gap=3)
s.notes_slide.notes_text_frame.text = "표 8개 중 6개 사용(판매자, 우편번호 좌표 표는 제외). Kaggle 공개 데이터. 고객은 customer_unique_id 기준."

# ============================================================ 4. RFM 방법
s = prs.slides.add_slide(blank)
frame(s, 4, "분석. 고객 그룹", "고객을 구매 방식으로 5개 그룹으로 나눔 (RFM)")
text(s, 0.5, 1.35, 9, 0.3, [[("한 번 산 고객이 대부분이라, 마지막 구매 시점과 구매금액으로 나눔", {"bold": True, "color": GREEN})]], size=12)
text(s, 0.5, 1.75, 4.9, 0.25, [[("R", {"bold": True, "color": GREEN}), (" 마지막 구매 후 일수    ", {}), ("F", {"bold": True, "color": GREEN}), (" 구매한 날 수    ", {}), ("M", {"bold": True, "color": GREEN}), (" 총 구매금액", {})]], size=11)
rows = [["그룹", "조건"], ["1  재구매", "서로 다른 날 2번 이상 구매"], ["2  최근 우수", "6개월 안에 구매, 금액 R$110 이상"], ["3  최근 일반", "6개월 안에 구매, 금액 R$110 미만"],
        ["4  휴면 우수", "6개월 넘게 구매 없음, 금액 R$110 이상"], ["5  휴면 일반", "6개월 넘게 구매 없음, 금액 R$110 미만"]]
table(s, 0.5, 2.1, [1.4, 3.5], rows, "table-groups", size=10, rowh=0.4)
text(s, 0.5, 4.6, 4.9, 0.5, ["우수 = 총 구매금액 상위 40%", "R$ = 브라질 화폐 헤알"], size=10, color=MUTE, gap=2, bullets=True)
text(s, 5.65, 1.75, 3.9, 0.25, "SQL로 점수를 매기고 그룹을 나눔", size=12, color=GREEN, bold=True)
code(s, 5.65, 2.1, 3.85, 1.75, ["NTILE(5) OVER (ORDER BY monetary)    AS m_score,", "6 - NTILE(5) OVER (ORDER BY recency) AS r_score", "",
    "CASE", "  WHEN frequency >= 2                THEN 1", "  WHEN r_score >= 4 AND m_score >= 4 THEN 2", "  WHEN r_score >= 4                  THEN 3",
    "  WHEN m_score >= 4                  THEN 4", "  ELSE 5", "END AS grp"], "code-rfm", size=7.5)
s.notes_slide.notes_text_frame.text = "sql/01_rfm_groups.sql. R, M은 NTILE(5)로 5등분(5점이 좋음). 최근 = 마지막 구매 후 177일 이내, 우수 = R$110 이상. 같은 날 추가 주문은 한 번으로 셈."

# ============================================================ 5. RFM 결과
s = prs.slides.add_slide(blank)
frame(s, 5, "분석. 고객 그룹", "휴면 우수 고객이 매출의 절반 가까이를 차지함")
cats = [f"{k} {g.name[k]}" for k in g.index]; pc = [DGRAY, "9AAAA5", "C3CCC9", RED, "E3E8E6"]
pie(s, 0.4, 1.3, 4.5, 3.0, cats, g.cust_share, pc, "고객 구성 (%)", "chart-pie-customers")
pie(s, 5.0, 1.3, 4.6, 3.0, cats, g.sales_share, pc, "매출 구성 (%)", "chart-pie-sales")
text(s, 0.7, 4.47, 8.6, 0.72, [[("휴면 우수 고객 ", {"bold": True, "color": RED}), (f"{n4:,}명: 고객의 {g.cust_share[4]:.0f}%, 매출의 {g.sales_share[4]:.0f}%, 평균 {int(g.avg_days[4])}일째 구매 없음", {})],
                              [("불만 때문은 아님: ", {"bold": True, "color": RED}), (f"첫 구매 평점 {cmp_.review[4]:.2f}점 (최근 우수 {cmp_.review[2]:.2f}점), 늦은 주문 {cmp_.late_pct[4]:.0f}% (최근 우수 {cmp_.late_pct[2]:.0f}%)", {})]], size=11.5, gap=4, bullets=True)
outline(s, 0.5, 4.4, 9.0, 0.82, "highlight-callout")
s.notes_slide.notes_text_frame.text = f"고객 {N:,}명(배송 완료 주문 기준). 평점과 늦은 주문 비율은 두 그룹 고객의 주문 전체 기준 비교."

# ============================================================ 6. 그룹별 우선순위
s = prs.slides.add_slide(blank)
frame(s, 6, "분석. 어디에 집중할까", "휴면 우수 고객에 먼저, 다음은 최근 우수 고객")
order = [(4, "1순위", "마지막 구매 6~12개월부터 연락, 같은 상품군 추천 + 바우처"), (2, "2순위", "휴면이 되기 전에 같은 상품군 추천"),
         (1, "유지", "별도 투자 없이 유지"), (3, "낮음", "자동 메일 등 비용이 낮은 방식만"), (5, "제외", "투자하지 않음")]
rows = [["순위", "그룹", "고객 수(명)", "매출 비중", "평균 금액(R$)", "연락 1명당\n기대 매출(R$)", "방법"]]
for k, rank, how in order:
    rows.append([rank, f"{k} {g.name[k]}", f"{int(g.customers[k]):,}", f"{g.sales_share[k]:.0f}%", f"{int(g.avg_amount[k])}", f"{g.per_contact[k]:.1f}", how])
table(s, 0.5, 1.4, [0.7, 1.2, 1.0, 0.9, 1.0, 1.1, 3.1], rows, "table-priority", size=10, rowh=0.47, align_right=(2, 3, 4, 5))
outline(s, 0.5, 1.4 + 0.47, 9.0, 0.47, "highlight-priority1")
text(s, 0.5, 4.5, 9.0, 0.7, [[("연락 1명당 기대 매출 = 평균 금액 x 3%", {"bold": True, "color": GREEN}), (" (연락하면 3%가 다시 산다고 가정, 3%를 다르게 잡아도 순위는 같음)", {})],
                             [("일반 그룹은 ", {}), ("연락 1명당 비용이 R$1.7보다 크면 손해", {"bold": True, "color": RED}), (", 우수 그룹은 R$8까지 남음", {})]], size=10.5, gap=4, bullets=True)
s.notes_slide.notes_text_frame.text = "기대 매출은 평균 구매금액 x 가정한 추가 재구매율 3%. 비용은 포함하지 않았고, 순위는 평균 금액과 고객 수로 정해져 가정 비율이 바뀌어도 변하지 않음."

# ============================================================ 7. 휴면 우수 안에서 누구부터
s = prs.slides.add_slide(blank)
frame(s, 7, "분석. 어디에 집중할까", "휴면 우수 고객 중에서는 6~12개월 구간부터 연락함")
bar(s, 0.4, 1.3, 5.6, 2.9, ["0~90일", "91~180일", "181~270일", "271~360일", "361~450일"], hz.rate_pct, "첫 구매 후 기간별, 아직 안 산 고객이 다음 90일 안에 다시 산 비율 (%)", "chart-hazard", vmax=1.7, fmt="0.00", colors=[GRAY, GRAY, TEAL, TEAL, DGRAY], gap=45)
outline(s, 2.78, 2.65, 1.95, 1.55, "highlight-window")
text(s, 6.3, 1.45, 3.2, 3.6, [[("6~12개월 구간", {"bold": True, "color": TEAL, "size": 12})], f"연락 없이도 90일마다 약 {min(hz.rate_pct[2], hz.rate_pct[3]):.1f}~{max(hz.rate_pct[2], hz.rate_pct[3]):.1f}%가 돌아옴",
                              [("12개월이 지나면", {"bold": True, "color": MUTE, "size": 12})], f"{hz.rate_pct[4]:.1f}%로 낮아짐, 연락 효과도 낮을 것으로 봄",
                              [("연락 대상", {"bold": True, "color": RED, "size": 12})], f"휴면 우수 {int(tg.dormant_all):,}명 중 6~12개월 {int(tg.target_6_12m):,}명"], size=11, gap=6)
code(s, 0.5, 4.4, 5.5, 0.8, ["risk = hc[hc.gap_days.isna() | (hc.gap_days > d)]            # d일까지 안 산 고객", "hit = ((risk.gap_days > d) & (risk.gap_days <= d + 90)).sum()   # 다음 90일 안에 산 고객"], "code-hazard", size=7.5)
s.notes_slide.notes_text_frame.text = "첫 구매 후 d일까지 다시 사지 않은 고객 중 다음 90일 안에 다시 산 비율. 첫 구매 후 455일 이상 지난 고객만 사용. 한 번만 산 고객은 첫 구매 후 일수와 마지막 구매 후 일수가 같음. 마지막 구매 177~382일 = 6~12개월."

# ============================================================ 8. 제안
s = prs.slides.add_slide(blank)
frame(s, 8, "제안", "그래서 이렇게 연락함")
rows = [["", "내용", "근거"],
        ["누구에게", f"휴면 우수 고객 중 마지막 구매가 6~12개월 전인 {int(tg.target_6_12m):,}명", "1년이 지나면 돌아올 확률이 낮아짐"],
        ["무엇을", "첫 구매와 같은 상품군 추천 + 바우처", f"다시 살 때 {samecat.same_category_pct:.0f}%가 같은 상품군 (우연이면 {samecat.chance_pct:.0f}%), 바우처 사용 고객이 {v_with / v_without:.1f}배 더 다시 삼"],
        ["확인", "대상을 절반씩 나눠 한쪽에만 발송하고 재구매 비율 비교", "효과는 아직 알 수 없으므로 실험으로 확인"]]
table(s, 0.5, 1.3, [1.1, 4.3, 3.6], rows, "table-actions", size=10.5, rowh=0.5, first_col_bold=True)
text(s, 0.5, 3.5, 9, 0.3, f"기대 효과 (가정): 연락 없이 돌아오는 고객에 더해, 연락으로 {int(tg.target_6_12m):,}명 중 N%가 더 돌아오면", size=11.5, color=GREEN, bold=True)
rows = [["더 돌아오는 비율", "다시 산 고객", "추가 매출(R$)", "전체 매출 대비"]] + [[f"{r.rate_pct}%", f"{int(r.customers):,}명", f"{int(r.extra_sales):,}", f"{r.vs_total_pct}%"] for r in sc.itertuples()]
table(s, 0.5, 3.82, [2.25, 2.25, 2.25, 2.25], rows, "table-scenario", size=10, rowh=0.28, align_right=(1, 2, 3))
outline(s, 0.5, 3.82 + 0.28 * 2, 9.0, 0.28, "highlight-scenario")
text(s, 0.5, 4.98, 9, 0.2, "쿠폰 비용은 뺀 금액, 추가 매출 = 더 돌아온 고객 수 x 평균 구매금액", size=8.5, color=MUTE)
s.notes_slide.notes_text_frame.text = f"평균 구매금액 R${avg4}(1회 재구매 가정). 비율 1, 3, 5%는 가정이며 연락 없이 돌아오는 비율(90일에 약 0.6~0.7%)보다 높게 잡은 값. 전체 매출 R${rfm.monetary.sum():,.0f}."

# ============================================================ 9. 결론
s = prs.slides.add_slide(blank)
frame(s, 9, "정리", "결론, 한계, 더 나아갈 점")
blocks = [("결론", GREEN, [f"매출의 {g.sales_share[4]:.0f}%가 6개월 넘게 안 산 우수 고객, 불만 때문은 아님", "집중 순서: 휴면 우수, 최근 우수", "일반 그룹은 연락 비용이 크면 손해라 투자하지 않음", "휴면 우수는 6~12개월부터 같은 상품군 추천 + 바우처"]),
          ("한계", RED, ["2년치 자료, 떠난 이유는 데이터에 없음", "연락 효과(3%)는 가정, 순위는 변하지 않음", "상품군, 바우처 결과는 연관성이지 효과가 아님", "우수 기준(R$110)은 직접 정한 값"]),
          ("더 나아갈 점", TEAL, ["A/B 테스트로 실제 효과 측정", "연락 비용 대비 이익 계산", "설문 등으로 떠난 이유 확인"])]
for i, (h, c, items) in enumerate(blocks):
    x = 0.5 + i * 3.05
    box(s, x, 1.4, 2.85, 3.5, TINT, f"summary-{i+1}")
    text(s, x + 0.2, 1.55, 2.45, 0.3, h, size=15, color=c, bold=True)
    text(s, x + 0.2, 2.05, 2.5, 2.8, items, size=11.5, gap=9, bullets=True)
s.notes_slide.notes_text_frame.text = "제안은 데이터에서 읽은 방향이며 효과는 검증하지 않음."

prs.core_properties.title = "Olist 쇼핑몰 주문 데이터 분석"
out = ROOT.parent / "olist_분석_포트폴리오.pptx"; prs.save(out); print("saved", out)
