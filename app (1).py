import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DW Bánh Kẹo – Dashboard Sản Xuất",
    page_icon="🍫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'Be Vietnam Pro', sans-serif; }
    .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }

    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 14px 18px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    div[data-testid="metric-container"] label { color: #a0a0c0 !important; font-size: 12px !important; letter-spacing: 0.05em; }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #f0f0ff !important; font-family: 'DM Mono', monospace; font-size: 1.5rem !important; }
    div[data-testid="metric-container"] [data-testid="stMetricDelta"] { font-size: 11px !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 4px; background: #1a1a2e; border-radius: 10px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 18px; color: #8888aa; font-size: 13px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #7c3aed, #4f46e5) !important; color: white !important; }

    .section-header {
        font-family: 'DM Mono', monospace;
        font-size: 11px;
        font-weight: 500;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #7c3aed;
        border-left: 3px solid #7c3aed;
        padding-left: 10px;
        margin: 16px 0 12px 0;
    }
    .mdx-badge {
        display: inline-block;
        background: rgba(124,58,237,0.15);
        color: #a78bfa;
        font-family: 'DM Mono', monospace;
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid rgba(124,58,237,0.3);
        margin-left: 8px;
        vertical-align: middle;
    }

    .stDataFrame { border-radius: 10px; overflow: hidden; }
    .stSidebar { background: #13131f !important; }
    h1 { font-size: 1.55rem !important; color: #f0f0ff; letter-spacing: -0.02em; }
    h3 { font-size: 1rem !important; color: #c0c0e0; }

    .insight-box {
        background: rgba(124,58,237,0.08);
        border: 1px solid rgba(124,58,237,0.25);
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 13px;
        color: #c0c0e0;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ─── GENERATE SIMULATED DATA (2020–2024) ────────────────────────────────────
@st.cache_data
def load_data():
    np.random.seed(42)

    dim_branch = pd.DataFrame({
        'branch_id':   ['E001', 'E002', 'E003'],
        'branch_name': ['Central_Factory', 'DC_Curitiba', 'DC_Recife'],
        'city':        ['São Paulo', 'Curitiba', 'Recife'],
        'monthly_capacity_t': [500, 200, 180],
        'unit_type':   ['Production', 'Distribution', 'Distribution'],
    })

    dim_product = pd.DataFrame({
        'product_id':   [f'P{i:03d}' for i in range(1, 21)],
        'product_name': [f'SKU_{i:03d}' for i in range(1, 21)],
        'category':     ['Tablet','Bonbon','Tablet','Tablet','Diet_Tablet',
                         'Bonbon','Linha_Sazonal','Bonbon','Bonbon','Tablet',
                         'Beverage','Linha_Sazonal','Tablet','Beverage','Tablet',
                         'Bonbon','Linha_Sazonal','Beverage','Tablet','Diet_Tablet'],
        'product_line': ['Diet','Premium','Gourmet','Premium','Gourmet',
                         'Gourmet','Gourmet','Filled','Traditional','Filled',
                         'Gourmet','Gourmet','Gourmet','Gourmet','Traditional',
                         'Premium','Diet','Traditional','Gourmet','Traditional'],
        'base_price':   [11.24,19.1,6.43,4.28,16.22,3.45,21.31,7.0,9.69,12.5,
                         16.46,9.43,13.03,7.39,16.03,16.37,4.43,24.24,9.7,18.05],
        'avg_cost':     [6.61,9.54,2.5,2.42,8.55,2.04,8.59,2.77,4.66,5.29,
                         6.34,4.16,7.12,3.54,5.8,6.43,2.6,13.38,3.63,8.3],
    })

    dim_shift = pd.DataFrame({
        'shift_id':   ['S1','S2','S3'],
        'shift_name': ['Ca Sáng (06–14h)', 'Ca Chiều (14–22h)', 'Ca Đêm (22–06h)'],
    })

    dim_machine = pd.DataFrame({
        'machine_id':   ['M01','M02','M03','M04','M05'],
        'machine_name': ['Cocoa Roasting','Industrial Mixer',
                         'Tempering System','Molding Line','Shrink Wrapping'],
    })

    dim_defect = pd.DataFrame({
        'reason_id':          ['R00','R1','R2','R3','R4','R5'],
        'reason_description': ['No Defect / N/A','Machine Calibration','Material Issue',
                               'Operator Error','Power Fluctuations','Overheating'],
    })

    # Fact_Production: 50k rows — 2020–2024
    n = 50_000
    years  = np.random.choice([2020,2021,2022,2023,2024], n, p=[0.17,0.18,0.20,0.22,0.23])
    months = np.random.randint(1, 13, n)

    branch_ids  = np.random.choice(['E001','E002','E003'], n, p=[0.55,0.22,0.23])
    product_ids = np.random.choice(dim_product['product_id'].tolist(), n)
    shift_ids   = np.random.choice(['S1','S2','S3'], n, p=[0.37,0.35,0.28])
    machine_ids = np.random.choice(['M01','M02','M03','M04','M05'], n)
    reason_ids  = np.random.choice(['R00','R1','R2','R3','R4','R5'], n, p=[0.58,0.14,0.12,0.08,0.05,0.03])

    year_factor = {2020:0.82, 2021:0.88, 2022:0.94, 2023:1.0, 2024:1.07}
    yf = np.array([year_factor[y] for y in years])

    prod_qty   = (np.random.randint(20, 100, n) * yf).astype(int)
    prod_hours = np.random.uniform(0.5, 8, n).round(2)
    prod_cost  = (prod_qty * np.random.uniform(5, 14, n)).round(2)

    scrap_base = np.where(shift_ids=='S3', 0.038, np.where(shift_ids=='S2', 0.031, 0.029))
    scrap_pct  = np.clip(np.random.normal(scrap_base, 0.008, n), 0.005, 0.12).round(4) * 100

    defect_qty = (prod_qty * scrap_pct / 100).astype(int)
    defect_qty = np.where(reason_ids=='R00', 0, defect_qty)
    downtime   = np.random.randint(0, 60, n)

    fact = pd.DataFrame({
        'year': years, 'month': months,
        'branch_id': branch_ids, 'product_id': product_ids,
        'shift_id': shift_ids, 'machine_id': machine_ids, 'reason_id': reason_ids,
        'produced_qty': prod_qty, 'production_time_hours': prod_hours,
        'production_cost': prod_cost, 'scrap_rate_pct': scrap_pct,
        'defect_quantity': defect_qty, 'downtime_minutes': downtime,
    })

    fact = fact.merge(dim_branch[['branch_id','branch_name','city','monthly_capacity_t']], on='branch_id', how='left')
    fact = fact.merge(dim_product[['product_id','product_name','category','product_line','avg_cost']], on='product_id', how='left')
    fact = fact.merge(dim_shift[['shift_id','shift_name']], on='shift_id', how='left')
    fact = fact.merge(dim_machine[['machine_id','machine_name']], on='machine_id', how='left')
    fact = fact.merge(dim_defect[['reason_id','reason_description']], on='reason_id', how='left')

    return fact, dim_branch, dim_product

fact, dim_branch, dim_product = load_data()

# ─── SIDEBAR FILTERS ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🍫 DW Bánh Kẹo")
    st.markdown("**Bộ lọc dữ liệu**")

    sel_years = st.multiselect(
        "Năm", options=[2020,2021,2022,2023,2024],
        default=[2020,2021,2022,2023,2024]
    )
    sel_branches = st.multiselect(
        "Nhà máy", options=dim_branch['branch_name'].tolist(),
        default=dim_branch['branch_name'].tolist()
    )
    sel_cats = st.multiselect(
        "Danh mục sản phẩm",
        options=sorted(dim_product['category'].unique().tolist()),
        default=sorted(dim_product['category'].unique().tolist())
    )

    st.markdown("---")
    st.caption("Cube: DW Banh Keo\nFact: Fact_Production\nDữ liệu: 2020–2024\nStar Schema · Kimball")

# ─── FILTER DATA ─────────────────────────────────────────────────────────────
df = fact[
    fact['year'].isin(sel_years) &
    fact['branch_name'].isin(sel_branches) &
    fact['category'].isin(sel_cats)
].copy()

if df.empty:
    st.warning("Không có dữ liệu với bộ lọc hiện tại.")
    st.stop()

year_range_str = f"{min(sel_years)}–{max(sel_years)}" if len(sel_years) > 1 else str(sel_years[0])

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown(f"# 🍫 Dashboard Phân Tích Sản Xuất — DW Bánh Kẹo")
st.caption(f"Cube: **DW Banh Keo** · Fact: **Fact_Production** · Giai đoạn: **{year_range_str}**")

# ─── KPI ROW ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total_qty    = df['produced_qty'].sum()
total_cost   = df['production_cost'].sum()
avg_scrap    = df['scrap_rate_pct'].mean()
total_defect = df['defect_quantity'].sum()
productivity = df['produced_qty'].sum() / df['production_time_hours'].sum()

if len(sel_years) >= 2:
    max_y = max(sel_years); prev_y = max_y - 1
    cur  = df[df['year']==max_y]['produced_qty'].sum()
    prev = df[df['year']==prev_y]['produced_qty'].sum() if prev_y in sel_years else None
    delta_qty = f"{(cur-prev)/prev*100:+.1f}% so với {prev_y}" if prev else None
else:
    delta_qty = None

col1.metric("📦 Tổng sản lượng",      f"{total_qty/1e6:.2f}M đvị", delta_qty)
col2.metric("💰 Chi phí SX",           f"${total_cost/1e6:.1f}M")
col3.metric("♻️ Phế phẩm TB",          f"{avg_scrap:.2f}%",
            delta=f"{avg_scrap-3.5:.2f}% vs ngưỡng 3.5%", delta_color="inverse")
col4.metric("❌ Tổng lỗi",             f"{total_defect:,}")
col5.metric("⚡ Năng suất (đvị/h)",    f"{productivity:.1f}")

st.markdown("---")

# ─── PLOT THEME ──────────────────────────────────────────────────────────────
PLOT_BG   = "rgba(0,0,0,0)"
PAPER_BG  = "rgba(0,0,0,0)"
FONT_CLR  = "#c0c0e0"
GRID_CLR  = "rgba(255,255,255,0.06)"
PALETTE   = ['#7c3aed','#2563eb','#059669','#d97706','#dc2626','#0891b2','#7c3aed']

def base_layout(title, h=340):
    return dict(
        title=dict(text=title, font=dict(size=13, color=FONT_CLR), x=0),
        height=h, margin=dict(t=44,b=8,l=8,r=8),
        plot_bgcolor=PLOT_BG, paper_bgcolor=PAPER_BG,
        font=dict(color=FONT_CLR, size=11),
        xaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR),
        yaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )

# ─── TABS ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Sản Lượng & Năng Suất",
    "🔍 Chất Lượng & Phế Phẩm",
    "💵 Chi Phí Sản Xuất",
    "📈 Tổng Hợp & So Sánh",
    "🔎 Phân Tích Bổ Sung",
])

# ══════════════════════════════════════════════════════════
# TAB 1: SẢN LƯỢNG & NĂNG SUẤT  (MDX 1.1–1.4)
# ══════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Nhóm 1 — Phân tích sản lượng & năng suất <span class="mdx-badge">MDX 1.1–1.4</span></div>', unsafe_allow_html=True)

    # 1.1 Monthly production grouped by year
    c1, c2 = st.columns(2)
    with c1:
        monthly = df.groupby(['year','month'])['produced_qty'].sum().reset_index()
        fig = px.bar(monthly, x='month', y='produced_qty', color='year',
                     barmode='group',
                     labels={'produced_qty':'Sản lượng', 'month':'Tháng', 'year':'Năm'},
                     color_discrete_sequence=PALETTE)
        fig.update_layout(**base_layout('1.1 Sản lượng theo Tháng/Quý/Năm (2020–2024)'))
        st.plotly_chart(fig, use_container_width=True)

    # 1.2 By branch — bar + line dual axis
    with c2:
        branch_agg = df.groupby('branch_name').agg(
            produced_qty=('produced_qty','sum'),
            production_cost=('production_cost','sum')
        ).reset_index().sort_values('produced_qty', ascending=False)

        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Bar(name='Sản lượng', x=branch_agg['branch_name'],
                              y=branch_agg['produced_qty'], marker_color=PALETTE[0]), secondary_y=False)
        fig2.add_trace(go.Scatter(name='Chi phí SX', x=branch_agg['branch_name'],
                                  y=branch_agg['production_cost'], mode='lines+markers',
                                  line=dict(color=PALETTE[3], width=2)), secondary_y=True)
        fig2.update_layout(**base_layout('1.2 Sản lượng & Chi phí theo Nhà máy'))
        fig2.update_yaxes(title_text="Sản lượng", secondary_y=False,
                          gridcolor=GRID_CLR, color=FONT_CLR)
        fig2.update_yaxes(title_text="Chi phí SX", secondary_y=True, color=FONT_CLR)
        st.plotly_chart(fig2, use_container_width=True)

    # 1.3 Productivity by branch × shift
    c3, c4 = st.columns(2)
    with c3:
        prod_shift = df.groupby(['branch_name','shift_name']).agg(
            produced_qty=('produced_qty','sum'),
            prod_hours=('production_time_hours','sum'),
        ).reset_index()
        prod_shift['productivity'] = (prod_shift['produced_qty'] / prod_shift['prod_hours']).round(2)

        fig3 = px.bar(prod_shift, x='branch_name', y='productivity', color='shift_name',
                      barmode='group',
                      labels={'productivity':'Năng suất','branch_name':'Nhà máy','shift_name':'Ca'},
                      color_discrete_sequence=PALETTE)
        fig3.update_layout(**base_layout('1.3 Năng suất (đvị/giờ) theo Nhà máy × Ca'))
        st.plotly_chart(fig3, use_container_width=True)

    # 1.4 Capacity utilisation by year
    with c4:
        cap = df.groupby(['branch_name','year'])['produced_qty'].sum().reset_index()
        cap_map = {'Central_Factory':500*1000*12,'DC_Curitiba':200*1000*12,'DC_Recife':180*1000*12}
        cap['design_capacity'] = cap['branch_name'].map(cap_map)
        cap['used_pct'] = (cap['produced_qty'] / cap['design_capacity'] * 100).round(1)

        fig4 = px.bar(cap, x='year', y='used_pct', color='branch_name', barmode='group',
                      labels={'used_pct':'Capacity Used %','year':'Năm'},
                      color_discrete_sequence=PALETTE)
        fig4.add_hline(y=100, line_dash="dash", line_color="#dc2626",
                       annotation_text="Công suất thiết kế", annotation_font_color="#dc2626")
        fig4.update_layout(**base_layout('1.4 Tỷ lệ sử dụng công suất (%) 2020–2024'))
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 2: CHẤT LƯỢNG  (MDX 2.1–2.5)
# ══════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Nhóm 2 — Phân tích chất lượng <span class="mdx-badge">MDX 2.1–2.5</span></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    # 2.1 Scrap by category
    with c1:
        cat_q = df.groupby('category').agg(
            scrap_rate_pct=('scrap_rate_pct','mean'),
            defect_quantity=('defect_quantity','sum'),
            produced_qty=('produced_qty','sum'),
        ).reset_index().sort_values('scrap_rate_pct', ascending=False)
        cat_q['scrap_rate_pct'] = cat_q['scrap_rate_pct'].round(2)

        fig = px.bar(cat_q, x='scrap_rate_pct', y='category', orientation='h',
                     labels={'scrap_rate_pct':'Scrap Rate %','category':'Danh mục'},
                     color='scrap_rate_pct', color_continuous_scale='RdYlGn_r')
        fig.update_layout(**base_layout('2.1 Tỷ lệ phế phẩm theo Category (BDESC)'),
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # 2.3 Defect reason pie
    with c2:
        reason_q = df.groupby('reason_description').agg(
            defect_quantity=('defect_quantity','sum'),
        ).reset_index().sort_values('defect_quantity', ascending=False)
        reason_no_ok = reason_q[reason_q['reason_description'] != 'No Defect / N/A']

        fig2 = px.pie(reason_no_ok, values='defect_quantity', names='reason_description',
                      color_discrete_sequence=PALETTE, hole=0.4)
        fig2.update_layout(**base_layout('2.3 Nguyên nhân lỗi (Defect Reason)'))
        st.plotly_chart(fig2, use_container_width=True)

    # 2.2 Scrap by product line × category scatter
    c3, c4 = st.columns(2)
    with c3:
        line_q = df.groupby(['product_line','category']).agg(
            scrap_rate_pct=('scrap_rate_pct','mean'),
            defect_quantity=('defect_quantity','sum'),
        ).reset_index().sort_values('scrap_rate_pct', ascending=False).head(15)

        fig3 = px.scatter(line_q, x='defect_quantity', y='scrap_rate_pct',
                          color='product_line', size='defect_quantity',
                          hover_data=['category'],
                          labels={'scrap_rate_pct':'Scrap Rate %','defect_quantity':'Tổng lỗi'},
                          color_discrete_sequence=PALETTE)
        fig3.update_layout(**base_layout('2.2 Tỷ lệ phế phẩm × Product Line'))
        st.plotly_chart(fig3, use_container_width=True)

    # 2.5 Scrap by branch × month
    with c4:
        bm = df.groupby(['branch_name','month'])['scrap_rate_pct'].mean().reset_index()
        fig4 = px.line(bm, x='month', y='scrap_rate_pct', color='branch_name',
                       markers=True,
                       labels={'scrap_rate_pct':'Scrap Rate %','month':'Tháng'},
                       color_discrete_sequence=PALETTE)
        fig4.update_layout(**base_layout('2.5 Tỷ lệ phế phẩm theo Nhà máy × Tháng'))
        st.plotly_chart(fig4, use_container_width=True)

    # 2.4 Shift correlation table
    st.markdown('<div class="section-header">2.4 Tương quan Ca sản xuất × Tỷ lệ lỗi <span class="mdx-badge">MDX 2.4</span></div>', unsafe_allow_html=True)
    shift_tbl = df.groupby('shift_name').agg(
        Giờ_SX_TB=('production_time_hours','mean'),
        Tỷ_lệ_lỗi=('scrap_rate_pct','mean'),
        Tổng_lỗi=('defect_quantity','sum'),
        Sản_lượng=('produced_qty','sum'),
    ).reset_index().rename(columns={'shift_name':'Ca sản xuất'})
    shift_tbl['Giờ_SX_TB'] = shift_tbl['Giờ_SX_TB'].round(3)
    shift_tbl['Tỷ_lệ_lỗi'] = shift_tbl['Tỷ_lệ_lỗi'].round(3)
    st.dataframe(shift_tbl, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# TAB 3: CHI PHÍ  (MDX 3.1–3.4)
# ══════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Nhóm 3 — Phân tích chi phí <span class="mdx-badge">MDX 3.1–3.4</span></div>', unsafe_allow_html=True)

    df_cost = df.copy()
    df_cost['unit_cost'] = df_cost['production_cost'] / df_cost['produced_qty'].replace(0, np.nan)

    c1, c2 = st.columns(2)
    # 3.1 Unit cost by product line
    with c1:
        ul = df_cost.groupby('product_line').agg(
            production_cost=('production_cost','sum'),
            produced_qty=('produced_qty','sum'),
        ).reset_index()
        ul['unit_cost'] = (ul['production_cost'] / ul['produced_qty']).round(2)
        ul = ul.sort_values('unit_cost', ascending=False)

        fig = px.bar(ul, x='product_line', y='unit_cost', text_auto='.2f',
                     labels={'unit_cost':'Unit Cost ($)','product_line':'Dòng SP'},
                     color='unit_cost', color_continuous_scale='Blues')
        fig.update_layout(**base_layout('3.1 Chi phí đơn vị theo Product Line'), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # 3.2 Unit cost by category
    with c2:
        uc = df_cost.groupby('category').agg(
            production_cost=('production_cost','sum'),
            produced_qty=('produced_qty','sum'),
        ).reset_index()
        uc['unit_cost'] = (uc['production_cost'] / uc['produced_qty']).round(2)
        uc = uc.sort_values('unit_cost', ascending=False)

        fig2 = px.bar(uc, x='category', y=['production_cost','produced_qty'],
                      barmode='group',
                      labels={'value':'Giá trị','category':'Danh mục','variable':''},
                      color_discrete_sequence=[PALETTE[4], PALETTE[1]])
        fig2.update_layout(**base_layout('3.2 Chi phí SX và Sản lượng theo Category'))
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    # 3.3 Cost trend — last 6 months of latest year
    with c3:
        last_year = df_cost['year'].max()
        trend = df_cost[df_cost['year']==last_year].groupby('month').agg(
            production_cost=('production_cost','sum'),
            produced_qty=('produced_qty','sum'),
        ).reset_index().tail(6)
        trend['unit_cost'] = (trend['production_cost'] / trend['produced_qty']).round(2)

        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(go.Bar(name='Tổng chi phí', x=trend['month'].astype(str),
                              y=trend['production_cost'], marker_color=PALETTE[1]), secondary_y=False)
        fig3.add_trace(go.Scatter(name='Unit Cost', x=trend['month'].astype(str),
                                  y=trend['unit_cost'], mode='lines+markers',
                                  line=dict(color=PALETTE[4], width=2), marker=dict(size=7)), secondary_y=True)
        fig3.update_layout(**base_layout(f'3.3 Xu hướng chi phí {last_year} (6 tháng cuối)'))
        st.plotly_chart(fig3, use_container_width=True)

    # 3.4 Cost heatmap branch × month
    with c4:
        bm_cost = df_cost.groupby(['branch_name','month']).agg(
            production_cost=('production_cost','sum'),
        ).reset_index()
        pivot = bm_cost.pivot(index='branch_name', columns='month', values='production_cost')
        fig4 = go.Figure(go.Heatmap(
            z=pivot.values, x=[f'T{m}' for m in pivot.columns],
            y=pivot.index.tolist(),
            colorscale='Purples',
            text=np.round(pivot.values/1e3,0).astype(int),
            texttemplate="%{text}K", showscale=True,
        ))
        fig4.update_layout(**base_layout('3.4 Chi phí SX theo Nhà máy × Tháng (Heatmap)'))
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 4: TỔNG HỢP  (MDX 4.1–4.5)
# ══════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Nhóm 4 — Phân tích tổng hợp & Cross-Dimension <span class="mdx-badge">MDX 4.1–4.5</span></div>', unsafe_allow_html=True)

    # 4.1 KPI by year table
    year_kpi = df.copy()
    year_kpi['unit_cost']    = year_kpi['production_cost'] / year_kpi['produced_qty'].replace(0, np.nan)
    year_kpi['productivity'] = year_kpi['produced_qty'] / year_kpi['production_time_hours'].replace(0, np.nan)

    kpi_yr = year_kpi.groupby('year').agg(
        Sản_lượng=('produced_qty','sum'),
        Chi_phí_SX=('production_cost','sum'),
        Unit_Cost=('unit_cost','mean'),
        Scrap_Rate_pct=('scrap_rate_pct','mean'),
        Tổng_lỗi=('defect_quantity','sum'),
        Giờ_SX=('production_time_hours','sum'),
        Năng_suất=('productivity','mean'),
    ).reset_index().round(2)

    st.markdown("**4.1 Dashboard KPI tổng hợp theo Năm (2020–2024)**")
    st.dataframe(kpi_yr, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    # 4.4 YoY
    with c1:
        yoy = df.groupby('year')['produced_qty'].sum().reset_index()
        yoy['prev_qty'] = yoy['produced_qty'].shift(1)
        yoy['yoy_pct']  = ((yoy['produced_qty'] - yoy['prev_qty']) / yoy['prev_qty'] * 100).round(2)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(name='Năm hiện tại', x=yoy['year'].astype(str),
                             y=yoy['produced_qty'], marker_color=PALETTE[0]), secondary_y=False)
        fig.add_trace(go.Bar(name='Năm trước', x=yoy['year'].astype(str),
                             y=yoy['prev_qty'], marker_color=PALETTE[1], opacity=0.5), secondary_y=False)
        fig.add_trace(go.Scatter(name='YoY Growth %', x=yoy['year'].astype(str),
                                 y=yoy['yoy_pct'], mode='lines+markers',
                                 line=dict(color=PALETTE[3], width=2)), secondary_y=True)
        fig.update_layout(**base_layout('4.4 YoY Sản lượng — 2020 → 2024'), barmode='group')
        st.plotly_chart(fig, use_container_width=True)

    # 4.3 TOP 5 products
    with c2:
        top5 = df.groupby('product_name').agg(
            produced_qty=('produced_qty','sum'),
            production_cost=('production_cost','sum'),
            scrap_rate_pct=('scrap_rate_pct','mean'),
        ).reset_index().sort_values('produced_qty', ascending=False).head(5)

        fig2 = px.bar(top5, x='produced_qty', y='product_name', orientation='h',
                      text_auto=True,
                      labels={'produced_qty':'Sản lượng','product_name':'Sản phẩm'},
                      color='produced_qty', color_continuous_scale='Greens')
        fig2.update_layout(**base_layout('4.3 TOP 5 sản phẩm sản lượng cao nhất (TOPCOUNT)'),
                           coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    # 4.5 Machine performance scatter
    with c3:
        mach = df.copy()
        mach['productivity'] = mach['produced_qty'] / mach['production_time_hours'].replace(0, np.nan)
        mach_agg = mach.groupby('machine_name').agg(
            produced_qty=('produced_qty','sum'),
            scrap_rate_pct=('scrap_rate_pct','mean'),
            productivity=('productivity','mean'),
        ).reset_index().round(2)

        fig3 = px.scatter(mach_agg, x='productivity', y='scrap_rate_pct',
                          size='produced_qty', color='machine_name', text='machine_name',
                          labels={'productivity':'Năng suất (đvị/h)','scrap_rate_pct':'Scrap Rate %'},
                          color_discrete_sequence=PALETTE)
        fig3.update_traces(textposition='top center')
        fig3.update_layout(**base_layout('4.5 Hiệu suất Máy móc: Năng suất vs Tỷ lệ lỗi'))
        st.plotly_chart(fig3, use_container_width=True)

    # 4.2 City × Category treemap
    with c4:
        cross = df.groupby(['city','category']).agg(
            produced_qty=('produced_qty','sum'),
            scrap_rate_pct=('scrap_rate_pct','mean'),
        ).reset_index()

        fig4 = px.treemap(cross, path=['city','category'], values='produced_qty',
                          color='scrap_rate_pct', color_continuous_scale='RdYlGn_r',
                          labels={'scrap_rate_pct':'Scrap %','produced_qty':'Sản lượng'})
        fig4.update_layout(**base_layout(f'4.2 Sản lượng Thành phố × Category ({year_range_str})'))
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 5: PHÂN TÍCH BỔ SUNG  (MDX 5.1–5.6)
# ══════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Nhóm 5 — Phân tích bổ sung (2020–2024) <span class="mdx-badge">MDX 5.1–5.6</span></div>', unsafe_allow_html=True)

    # ── 5.1 Thống kê lỗi theo Defect Reason (toàn bộ) ──────────────────────
    st.markdown("#### 5.1 Thống kê số lượng lỗi theo nguyên nhân `[Dim Defect Reason]`")
    c1, c2 = st.columns([3,2])
    with c1:
        reason_full = df.groupby('reason_description').agg(
            defect_quantity=('defect_quantity','sum'),
            scrap_rate_pct=('scrap_rate_pct','mean'),
        ).reset_index().sort_values('defect_quantity', ascending=False)
        reason_full['scrap_rate_pct'] = reason_full['scrap_rate_pct'].round(3)

        fig51 = px.bar(reason_full, x='defect_quantity', y='reason_description',
                       orientation='h', text_auto=True,
                       labels={'defect_quantity':'Số lượng lỗi','reason_description':'Nguyên nhân'},
                       color='defect_quantity', color_continuous_scale='Reds')
        fig51.update_layout(**base_layout('5.1 Số lượng lỗi theo Defect Reason (BDESC, 2020–2024)'),
                             coloraxis_showscale=False)
        st.plotly_chart(fig51, use_container_width=True)

    with c2:
        st.markdown("**Bảng chi tiết**")
        st.dataframe(reason_full.rename(columns={
            'reason_description':'Nguyên nhân',
            'defect_quantity':'Tổng lỗi',
            'scrap_rate_pct':'Scrap Rate %'
        }), use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── 5.2 Lỗi tháng 12 theo từng năm 2020–2024 ───────────────────────────
    st.markdown("#### 5.2 Tổng lỗi trong tháng 12 theo từng năm (2020–2024) `WHERE Month=12`")
    dec_df = df[df['month'] == 12].groupby(['year','reason_description']).agg(
        defect_quantity=('defect_quantity','sum'),
        scrap_rate_pct=('scrap_rate_pct','mean'),
        produced_qty=('produced_qty','sum'),
    ).reset_index()
    dec_df['scrap_rate_pct'] = dec_df['scrap_rate_pct'].round(3)

    c1, c2 = st.columns(2)
    with c1:
        dec_yr = dec_df.groupby('year').agg(
            defect_quantity=('defect_quantity','sum'),
            produced_qty=('produced_qty','sum'),
        ).reset_index()
        dec_yr['scrap_rate_pct'] = (dec_yr['defect_quantity'] / dec_yr['produced_qty'] * 100).round(2)

        fig52a = px.bar(dec_yr, x='year', y='defect_quantity', text_auto=True,
                        labels={'defect_quantity':'Tổng lỗi','year':'Năm'},
                        color='year', color_discrete_sequence=PALETTE)
        fig52a.update_layout(**base_layout('5.2a Tổng lỗi tháng 12 theo Năm'))
        st.plotly_chart(fig52a, use_container_width=True)

    with c2:
        dec_reason = dec_df.groupby('reason_description').agg(
            defect_quantity=('defect_quantity','sum'),
        ).reset_index().sort_values('defect_quantity', ascending=False)
        dec_reason = dec_reason[dec_reason['reason_description'] != 'No Defect / N/A']

        fig52b = px.bar(dec_reason, x='reason_description', y='defect_quantity',
                        labels={'defect_quantity':'Số lỗi','reason_description':'Nguyên nhân'},
                        color='defect_quantity', color_continuous_scale='Oranges', text_auto=True)
        fig52b.update_layout(**base_layout('5.2b Nguyên nhân lỗi tháng 12 (2020–2024)'),
                              coloraxis_showscale=False)
        st.plotly_chart(fig52b, use_container_width=True)

    st.markdown("---")

    # ── 5.3 YTD Sản lượng lũy kế theo chi nhánh × năm ─────────────────────
    st.markdown("#### 5.3 Sản lượng lũy kế YTD theo Chi nhánh × Năm (2020–2024) `SUM(YTD(...))`")

    ytd_rows = []
    for yr in sorted(df['year'].unique()):
        for br in df['branch_name'].unique():
            sub = df[(df['year']==yr) & (df['branch_name']==br)]
            for m in range(1, 13):
                ytd_qty = sub[sub['month'] <= m]['produced_qty'].sum()
                ytd_rows.append({'year':yr, 'month':m, 'branch_name':br, 'ytd_qty':ytd_qty})

    ytd_df = pd.DataFrame(ytd_rows)

    sel_yr_5 = st.selectbox("Chọn năm xem YTD:", options=sorted(df['year'].unique()), index=4, key='ytd_yr')
    ytd_plot = ytd_df[ytd_df['year'] == sel_yr_5]

    fig53 = px.line(ytd_plot, x='month', y='ytd_qty', color='branch_name',
                    markers=True,
                    labels={'ytd_qty':'Sản lượng lũy kế YTD','month':'Tháng','branch_name':'Chi nhánh'},
                    color_discrete_sequence=PALETTE)
    fig53.update_layout(**base_layout(f'5.3 YTD Sản lượng lũy kế theo Chi nhánh — Năm {sel_yr_5}', h=340))
    st.plotly_chart(fig53, use_container_width=True)

    st.markdown("---")

    # ── 5.4 DrillDown Chi nhánh → Máy → Sản phẩm ──────────────────────────
    st.markdown("#### 5.4 Phân tích sản lượng theo phân cấp: Chi nhánh → Máy → Sản phẩm `DRILLDOWNLEVEL`")
    c1, c2, c3_col = st.columns(3)

    with c1:
        branch_lvl = df.groupby('branch_name')['produced_qty'].sum().reset_index().sort_values('produced_qty', ascending=False)
        fig54a = px.bar(branch_lvl, x='branch_name', y='produced_qty', text_auto=True,
                        labels={'produced_qty':'Sản lượng','branch_name':'Chi nhánh'},
                        color='branch_name', color_discrete_sequence=PALETTE)
        fig54a.update_layout(**base_layout('Cấp 1: Chi nhánh'), showlegend=False)
        st.plotly_chart(fig54a, use_container_width=True)

    sel_branch_drill = st.selectbox("Chọn chi nhánh để drill down:", df['branch_name'].unique(), key='drill_br')

    c2, c3_col = st.columns(2)
    with c2:
        mach_lvl = df[df['branch_name']==sel_branch_drill].groupby('machine_name')['produced_qty'].sum().reset_index().sort_values('produced_qty', ascending=False)
        fig54b = px.bar(mach_lvl, x='machine_name', y='produced_qty', text_auto=True,
                        labels={'produced_qty':'Sản lượng','machine_name':'Máy móc'},
                        color='produced_qty', color_continuous_scale='Blues')
        fig54b.update_layout(**base_layout(f'Cấp 2: Máy — {sel_branch_drill}'), coloraxis_showscale=False)
        st.plotly_chart(fig54b, use_container_width=True)

    with c3_col:
        prod_lvl = df[df['branch_name']==sel_branch_drill].groupby('category')['produced_qty'].sum().reset_index().sort_values('produced_qty', ascending=False)
        fig54c = px.bar(prod_lvl, x='category', y='produced_qty', text_auto=True,
                        labels={'produced_qty':'Sản lượng','category':'Danh mục SP'},
                        color='produced_qty', color_continuous_scale='Purples')
        fig54c.update_layout(**base_layout(f'Cấp 3: Sản phẩm — {sel_branch_drill}'), coloraxis_showscale=False)
        st.plotly_chart(fig54c, use_container_width=True)

    st.markdown("---")

    # ── 5.5 Sản phẩm không có lỗi (Defect Quantity = 0) ────────────────────
    st.markdown("#### 5.5 Sản phẩm không có lỗi (Defect Quantity = 0) `FILTER(..., Defect Quantity = 0)`")

    no_defect = df.groupby('product_name').agg(
        produced_qty=('produced_qty','sum'),
        defect_quantity=('defect_quantity','sum'),
        production_cost=('production_cost','sum'),
    ).reset_index()
    no_defect_filter = no_defect[no_defect['defect_quantity'] == 0].sort_values('produced_qty', ascending=False)

    c1, c2 = st.columns([2,3])
    with c1:
        total_products = df['product_name'].nunique()
        st.markdown(f"""
        <div class="insight-box">
            📦 <b>{len(no_defect_filter)}</b> / {total_products} sản phẩm <b>không có lỗi</b><br>
            trong giai đoạn <b>{year_range_str}</b>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(no_defect_filter.rename(columns={
            'product_name':'Sản phẩm',
            'produced_qty':'Sản lượng',
            'defect_quantity':'Tổng lỗi',
            'production_cost':'Chi phí SX',
        }), use_container_width=True, hide_index=True)

    with c2:
        if not no_defect_filter.empty:
            fig55 = px.bar(no_defect_filter, x='product_name', y='produced_qty', text_auto=True,
                           labels={'produced_qty':'Sản lượng','product_name':'Sản phẩm'},
                           color='produced_qty', color_continuous_scale='Greens')
            fig55.update_layout(**base_layout('5.5 Sản phẩm không có lỗi — Sản lượng'),
                                coloraxis_showscale=False,
                                xaxis_tickangle=-30)
            st.plotly_chart(fig55, use_container_width=True)
        else:
            st.info("Không có sản phẩm nào có Defect Quantity = 0 với bộ lọc hiện tại.")

    st.markdown("---")

    # ── 5.6 Sản lượng trung bình mỗi ngày theo tuần ─────────────────────────
    st.markdown("#### 5.6 Sản lượng trung bình mỗi ngày theo tuần `AVG(DESCENDANTS([Week],[Day]))`")

    df['week'] = ((df['month'] - 1) * 4 + np.random.randint(1, 5, len(df))).clip(1, 52)
    df_week = df.copy()

    weekly_daily = df_week.groupby(['year','week']).agg(
        total_qty=('produced_qty','sum'),
        total_cost=('production_cost','sum'),
    ).reset_index()
    # approximate: avg daily = total / 7
    weekly_daily['avg_daily_qty']  = (weekly_daily['total_qty'] / 7).round(0)
    weekly_daily['avg_daily_cost'] = (weekly_daily['total_cost'] / 7).round(2)

    sel_yr_w = st.selectbox("Chọn năm:", sorted(df['year'].unique()), index=4, key='wk_yr')
    wk_plot = weekly_daily[weekly_daily['year'] == sel_yr_w]

    fig56 = make_subplots(specs=[[{"secondary_y": True}]])
    fig56.add_trace(go.Bar(name='Avg Daily Sản lượng',
                           x=wk_plot['week'], y=wk_plot['avg_daily_qty'],
                           marker_color=PALETTE[0], opacity=0.8), secondary_y=False)
    fig56.add_trace(go.Scatter(name='Avg Daily Chi phí',
                               x=wk_plot['week'], y=wk_plot['avg_daily_cost'],
                               mode='lines', line=dict(color=PALETTE[3], width=1.5)),
                    secondary_y=True)
    fig56.update_layout(**base_layout(f'5.6 Sản lượng & Chi phí TB mỗi ngày theo Tuần — {sel_yr_w}', h=360))
    fig56.update_xaxes(title_text="Tuần", color=FONT_CLR)
    fig56.update_yaxes(title_text="Avg Daily Sản lượng", secondary_y=False, gridcolor=GRID_CLR, color=FONT_CLR)
    fig56.update_yaxes(title_text="Avg Daily Chi phí ($)", secondary_y=True, color=PALETTE[3])
    st.plotly_chart(fig56, use_container_width=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("📊 DW Bánh Kẹo — Cube: DW Banh Keo · Fact_Production · Star Schema · Kimball Dimensional Modeling · 2020–2024")
