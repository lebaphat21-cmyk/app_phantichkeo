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
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .stMetric { background: #f8f9fa; border-radius: 10px; padding: 12px; }
    .stMetric label { font-size: 13px !important; }
    div[data-testid="metric-container"] { background-color: #f8f9fa; border-radius: 10px; padding: 12px 16px; }
    h1 { font-size: 1.6rem !important; }
    h2 { font-size: 1.2rem !important; }
    .badge-green  { background:#d4edda; color:#155724; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:600; }
    .badge-amber  { background:#fff3cd; color:#856404; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:600; }
    .badge-red    { background:#f8d7da; color:#721c24; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:600; }
    .badge-blue   { background:#cce5ff; color:#004085; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:600; }
    .section-title { font-weight: 600; font-size: 14px; color: #333; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

# ─── GENERATE SIMULATED DATA ─────────────────────────────────────────────────
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
        'machine_name': ['Cocoa Roasting & Grinding','Industrial Mixer (Conching)',
                         'Tempering System','Automated Molding Line','Shrink Wrapping Machine'],
    })

    dim_defect = pd.DataFrame({
        'reason_id':          ['R00','R1','R2','R3','R4','R5'],
        'reason_description': ['No Defect / N/A','Machine Calibration','Material Issue',
                               'Operator Error','Power Fluctuations','Overheating'],
    })

    # Dim_Time: 2020–2024 daily
    dim_time = pd.DataFrame({
        'time_id':    pd.date_range('2020-01-01','2024-12-31'),
    })
    dim_time['date']        = dim_time['time_id']
    dim_time['year']        = dim_time['date'].dt.year
    dim_time['month']       = dim_time['date'].dt.month
    dim_time['month_name']  = dim_time['date'].dt.strftime('%B')
    dim_time['quarter']     = dim_time['date'].dt.quarter
    dim_time['time_id']     = dim_time['date'].dt.strftime('%Y%m%d').astype(int)

    # Fact_Production: 50k rows
    n = 50_000
    years  = np.random.choice([2020,2021,2022,2023,2024], n, p=[0.17,0.18,0.20,0.22,0.23])
    months = np.random.randint(1, 13, n)

    branch_ids  = np.random.choice(['E001','E002','E003'], n, p=[0.55,0.22,0.23])
    product_ids = np.random.choice(dim_product['product_id'].tolist(), n)
    shift_ids   = np.random.choice(['S1','S2','S3'], n, p=[0.37,0.35,0.28])
    machine_ids = np.random.choice(['M01','M02','M03','M04','M05'], n)
    reason_ids  = np.random.choice(['R00','R1','R2','R3','R4','R5'], n, p=[0.58,0.14,0.12,0.08,0.05,0.03])

    # base metrics with year trend
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

    # join dimensions
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
        default=[2023,2024]
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
    st.caption("Cube: DW Banh Keo\nFact: Fact_Production\nDữ liệu: 2020–2024")

# ─── FILTER DATA ─────────────────────────────────────────────────────────────
df = fact[
    fact['year'].isin(sel_years) &
    fact['branch_name'].isin(sel_branches) &
    fact['category'].isin(sel_cats)
].copy()

if df.empty:
    st.warning("Không có dữ liệu với bộ lọc hiện tại.")
    st.stop()

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("# 🍫 Dashboard Phân Tích Sản Xuất — DW Bánh Kẹo")

# ─── KPI ROW ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total_qty     = df['produced_qty'].sum()
total_cost    = df['production_cost'].sum()
avg_scrap     = df['scrap_rate_pct'].mean()
total_defect  = df['defect_quantity'].sum()
productivity  = df['produced_qty'].sum() / df['production_time_hours'].sum()

# YoY comparison
if len(sel_years) >= 2:
    max_y = max(sel_years); prev_y = max_y - 1
    cur  = df[df['year']==max_y]['produced_qty'].sum()
    prev = df[df['year']==prev_y]['produced_qty'].sum() if prev_y in sel_years else None
    delta_qty = f"{(cur-prev)/prev*100:+.1f}% so với {prev_y}" if prev else None
else:
    delta_qty = None

col1.metric("📦 Tổng sản lượng", f"{total_qty/1e6:.2f}M đvị", delta_qty)
col2.metric("💰 Chi phí SX", f"${total_cost/1e6:.1f}M")
col3.metric("♻️ Tỷ lệ phế phẩm TB", f"{avg_scrap:.2f}%",
            delta=f"{avg_scrap-3.5:.2f}% vs ngưỡng 3.5%", delta_color="inverse")
col4.metric("❌ Tổng lỗi", f"{total_defect:,}")
col5.metric("⚡ Năng suất (đvị/h)", f"{productivity:.1f}")

st.markdown("---")

# ─── TABS ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Sản Lượng & Năng Suất",
    "🔍 Chất Lượng & Phế Phẩm",
    "💵 Chi Phí Sản Xuất",
    "📈 Tổng Hợp & So Sánh",
])

COLORS = {
    'E001': '#1f77b4', 'E002': '#2ca02c', 'E003': '#ff7f0e',
    'S1': '#17becf', 'S2': '#bcbd22', 'S3': '#9467bd',
}

# ══════════════════════════════════════════════════════════
# TAB 1: SẢN LƯỢNG & NĂNG SUẤT
# ══════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Nhóm 1 — Phân tích sản lượng & năng suất (MDX 1.1–1.4)")

    # 1.1 Monthly production
    c1, c2 = st.columns(2)
    with c1:
        monthly = df.groupby(['year','month'])['produced_qty'].sum().reset_index()
        monthly['label'] = monthly['year'].astype(str) + '-T' + monthly['month'].astype(str).str.zfill(2)
        fig = px.bar(monthly, x='month', y='produced_qty', color='year',
                     barmode='group', labels={'produced_qty':'Sản lượng', 'month':'Tháng'},
                     title='1.1 Sản lượng theo Tháng/Năm',
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=350, margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

    # 1.2 By branch
    with c2:
        branch_agg = df.groupby('branch_name').agg(
            produced_qty=('produced_qty','sum'),
            production_cost=('production_cost','sum')
        ).reset_index().sort_values('produced_qty', ascending=False)

        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Bar(name='Sản lượng', x=branch_agg['branch_name'],
                              y=branch_agg['produced_qty'], marker_color='#4C72B0'), secondary_y=False)
        fig2.add_trace(go.Scatter(name='Chi phí SX', x=branch_agg['branch_name'],
                                  y=branch_agg['production_cost'], mode='lines+markers',
                                  line=dict(color='#DD8452', width=2)), secondary_y=True)
        fig2.update_layout(title='1.2 Sản lượng & Chi phí theo Nhà máy',
                           height=350, margin=dict(t=40,b=10,l=10,r=10))
        fig2.update_yaxes(title_text="Sản lượng", secondary_y=False)
        fig2.update_yaxes(title_text="Chi phí SX", secondary_y=True)
        st.plotly_chart(fig2, use_container_width=True)

    # 1.3 Productivity by branch x shift
    c3, c4 = st.columns(2)
    with c3:
        prod_shift = df.groupby(['branch_name','shift_name']).agg(
            produced_qty=('produced_qty','sum'),
            prod_hours=('production_time_hours','sum'),
            scrap=('scrap_rate_pct','mean')
        ).reset_index()
        prod_shift['productivity'] = (prod_shift['produced_qty'] / prod_shift['prod_hours']).round(2)

        fig3 = px.bar(prod_shift, x='branch_name', y='productivity', color='shift_name',
                      barmode='group', title='1.3 Năng suất (đvị/giờ) theo Nhà máy × Ca',
                      labels={'productivity':'Năng suất','branch_name':'Nhà máy','shift_name':'Ca'},
                      color_discrete_sequence=['#4878D0','#EE854A','#6ACC64'])
        fig3.update_layout(height=350, margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig3, use_container_width=True)

    # 1.4 Capacity utilisation
    with c4:
        cap = df.groupby(['branch_name','year'])['produced_qty'].sum().reset_index()
        # Monthly capacity × 12
        cap_map = {'Central_Factory':500*1000*12,'DC_Curitiba':200*1000*12,'DC_Recife':180*1000*12}
        cap['design_capacity'] = cap['branch_name'].map(cap_map)
        cap['used_pct'] = (cap['produced_qty'] / cap['design_capacity'] * 100).round(1)

        fig4 = px.bar(cap, x='year', y='used_pct', color='branch_name',
                      barmode='group', title='1.4 Tỷ lệ sử dụng công suất (%)',
                      labels={'used_pct':'Capacity Used %','year':'Năm'},
                      color_discrete_sequence=['#4878D0','#EE854A','#6ACC64'])
        fig4.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Công suất thiết kế")
        fig4.update_layout(height=350, margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 2: CHẤT LƯỢNG
# ══════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Nhóm 2 — Phân tích chất lượng (MDX 2.1–2.5)")

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
                     title='2.1 Tỷ lệ phế phẩm theo Category (xếp BDESC)',
                     labels={'scrap_rate_pct':'Scrap Rate %','category':'Danh mục'},
                     color='scrap_rate_pct',
                     color_continuous_scale='RdYlGn_r')
        fig.update_layout(height=320, margin=dict(t=40,b=10,l=10,r=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # 2.3 Defect reason
    with c2:
        reason_q = df.groupby('reason_description').agg(
            defect_quantity=('defect_quantity','sum'),
            scrap_rate_pct=('scrap_rate_pct','mean'),
        ).reset_index().sort_values('defect_quantity', ascending=False)

        fig2 = px.pie(reason_q[reason_q['reason_description']!='No Defect / N/A'],
                      values='defect_quantity', names='reason_description',
                      title='2.3 Nguyên nhân lỗi (Defect Reason)',
                      color_discrete_sequence=px.colors.qualitative.Set3,
                      hole=0.35)
        fig2.update_layout(height=320, margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig2, use_container_width=True)

    # 2.2 Scrap by product line
    c3, c4 = st.columns(2)
    with c3:
        line_q = df.groupby(['product_line','category']).agg(
            scrap_rate_pct=('scrap_rate_pct','mean'),
            defect_quantity=('defect_quantity','sum'),
        ).reset_index().sort_values('scrap_rate_pct', ascending=False).head(15)

        fig3 = px.scatter(line_q, x='defect_quantity', y='scrap_rate_pct',
                          color='product_line', size='defect_quantity',
                          hover_data=['category'],
                          title='2.2 Tỷ lệ phế phẩm × Product Line',
                          labels={'scrap_rate_pct':'Scrap Rate %','defect_quantity':'Tổng lỗi'})
        fig3.update_layout(height=320, margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig3, use_container_width=True)

    # 2.5 Scrap by branch × month
    with c4:
        bm = df.groupby(['branch_name','month'])['scrap_rate_pct'].mean().reset_index()
        bm['scrap_rate_pct'] = bm['scrap_rate_pct'].round(3)
        fig4 = px.line(bm, x='month', y='scrap_rate_pct', color='branch_name',
                       markers=True, title='2.5 Tỷ lệ phế phẩm theo Nhà máy × Tháng',
                       labels={'scrap_rate_pct':'Scrap Rate %','month':'Tháng'},
                       color_discrete_sequence=['#4878D0','#EE854A','#6ACC64'])
        fig4.update_layout(height=320, margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig4, use_container_width=True)

    # 2.4 Shift correlation table
    st.markdown("**2.4 Tương quan Ca sản xuất × Tỷ lệ lỗi**")
    shift_tbl = df.groupby('shift_name').agg(
        Giờ_SX_TB=('production_time_hours','mean'),
        Tỷ_lệ_lỗi=('scrap_rate_pct','mean'),
        Tổng_lỗi=('defect_quantity','sum'),
        Sản_lượng=('produced_qty','sum'),
    ).reset_index().rename(columns={'shift_name':'Ca sản xuất'})
    Giờ_SX_TB = Giờ_SX_TB = Giờ_SX_TB = None  # avoid lint
    for col in ['Giờ_SX_TB','Tỷ_lệ_lỗi']:
        Giờ_SX_TB = col
        shift_tbl[col] = shift_tbl[col].round(3)
    st.dataframe(shift_tbl, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# TAB 3: CHI PHÍ
# ══════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Nhóm 3 — Phân tích chi phí (MDX 3.1–3.4)")

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

        fig = px.bar(ul, x='product_line', y='unit_cost',
                     title='3.1 Chi phí đơn vị (Unit Cost) theo Product Line',
                     labels={'unit_cost':'Unit Cost ($)','product_line':'Dòng SP'},
                     color='unit_cost', color_continuous_scale='Blues',
                     text_auto='.2f')
        fig.update_layout(height=350, margin=dict(t=40,b=10,l=10,r=10), coloraxis_showscale=False)
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
                      barmode='group', title='3.2 Chi phí SX và Sản lượng theo Category',
                      labels={'value':'Giá trị','category':'Danh mục','variable':''},
                      color_discrete_sequence=['#D55E00','#0072B2'])
        fig2.update_layout(height=350, margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig2, use_container_width=True)

    # 3.3 Cost trend last 3 months of latest year
    c3, c4 = st.columns(2)
    with c3:
        last_year = df_cost['year'].max()
        trend = df_cost[df_cost['year']==last_year].groupby('month').agg(
            production_cost=('production_cost','sum'),
            produced_qty=('produced_qty','sum'),
        ).reset_index().tail(6)
        trend['unit_cost'] = (trend['production_cost'] / trend['produced_qty']).round(2)

        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(go.Bar(name='Tổng chi phí', x=trend['month'].astype(str),
                              y=trend['production_cost'], marker_color='#4878D0'), secondary_y=False)
        fig3.add_trace(go.Scatter(name='Unit Cost', x=trend['month'].astype(str),
                                  y=trend['unit_cost'], mode='lines+markers',
                                  line=dict(color='red',width=2), marker=dict(size=7)), secondary_y=True)
        fig3.update_layout(title=f'3.3 Xu hướng chi phí {last_year} (6 tháng cuối)',
                           height=350, margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig3, use_container_width=True)

    # 3.4 Cost by branch × month heatmap
    with c4:
        bm_cost = df_cost.groupby(['branch_name','month']).agg(
            production_cost=('production_cost','sum'),
        ).reset_index()
        pivot = bm_cost.pivot(index='branch_name', columns='month', values='production_cost')
        fig4 = go.Figure(go.Heatmap(
            z=pivot.values, x=[f'T{m}' for m in pivot.columns],
            y=pivot.index.tolist(),
            colorscale='Blues', text=np.round(pivot.values/1e3,0).astype(int),
            texttemplate="%{text}K", showscale=True,
        ))
        fig4.update_layout(title='3.4 Chi phí SX theo Nhà máy × Tháng (heatmap)',
                           height=350, margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 4: TỔNG HỢP
# ══════════════════════════════════════════════════════════
with tab4:
    st.markdown("### Nhóm 4 — Phân tích tổng hợp & Cross-Dimension (MDX 4.1–4.5)")

    # 4.1 KPI summary by year
    year_kpi = df.copy()
    year_kpi['unit_cost'] = year_kpi['production_cost'] / year_kpi['produced_qty'].replace(0, np.nan)
    year_kpi['productivity'] = year_kpi['produced_qty'] / year_kpi['production_time_hours'].replace(0, np.nan)

    kpi_yr = year_kpi.groupby('year').agg(
        Sản_lượng=('produced_qty','sum'),
        Chi_phí_SX=('production_cost','sum'),
        Unit_Cost=('unit_cost','mean'),
        Scrap_Rate=('scrap_rate_pct','mean'),
        Tổng_lỗi=('defect_quantity','sum'),
        Giờ_SX=('production_time_hours','sum'),
        Năng_suất=('productivity','mean'),
    ).reset_index()
    kpi_yr = kpi_yr.round(2)
    st.markdown("**4.1 Dashboard KPI tổng hợp theo Năm**")
    st.dataframe(kpi_yr, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    # 4.4 YoY comparison
    with c1:
        yoy = df.groupby('year')['produced_qty'].sum().reset_index()
        yoy['prev_qty'] = yoy['produced_qty'].shift(1)
        yoy['yoy_pct'] = ((yoy['produced_qty'] - yoy['prev_qty']) / yoy['prev_qty'] * 100).round(2)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(name='Năm hiện tại', x=yoy['year'].astype(str),
                             y=yoy['produced_qty'], marker_color='#4878D0'), secondary_y=False)
        fig.add_trace(go.Bar(name='Năm trước', x=yoy['year'].astype(str),
                             y=yoy['prev_qty'], marker_color='#B5CDE9', opacity=0.6), secondary_y=False)
        fig.add_trace(go.Scatter(name='YoY Growth %', x=yoy['year'].astype(str),
                                 y=yoy['yoy_pct'], mode='lines+markers',
                                 line=dict(color='#DD8452',width=2)), secondary_y=True)
        fig.update_layout(title='4.4 YoY Sản lượng — Năm hiện tại vs Năm trước',
                          barmode='group', height=360, margin=dict(t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)

    # 4.3 TOP 5 products
    with c2:
        top5 = df.groupby('product_name').agg(
            produced_qty=('produced_qty','sum'),
            production_cost=('production_cost','sum'),
            scrap_rate_pct=('scrap_rate_pct','mean'),
        ).reset_index().sort_values('produced_qty', ascending=False).head(5)

        fig2 = px.bar(top5, x='produced_qty', y='product_name', orientation='h',
                      title='4.3 TOP 5 sản phẩm sản lượng cao nhất (TOPCOUNT)',
                      labels={'produced_qty':'Sản lượng','product_name':'Sản phẩm'},
                      color='produced_qty', color_continuous_scale='Greens',
                      text_auto=True)
        fig2.update_layout(height=360, margin=dict(t=40,b=10), coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # 4.5 Machine performance
    c3, c4 = st.columns(2)
    with c3:
        mach = df.copy()
        mach['productivity'] = mach['produced_qty'] / mach['production_time_hours'].replace(0, np.nan)
        mach_agg = mach.groupby('machine_name').agg(
            produced_qty=('produced_qty','sum'),
            prod_hours=('production_time_hours','sum'),
            scrap_rate_pct=('scrap_rate_pct','mean'),
            productivity=('productivity','mean'),
        ).reset_index().sort_values('productivity', ascending=False)
        mach_agg = mach_agg.round(2)

        fig3 = px.scatter(mach_agg, x='productivity', y='scrap_rate_pct',
                          size='produced_qty', color='machine_name',
                          text='machine_name',
                          title='4.5 Hiệu suất Máy móc: Năng suất vs Tỷ lệ lỗi',
                          labels={'productivity':'Năng suất (đvị/h)','scrap_rate_pct':'Scrap Rate %'})
        fig3.update_traces(textposition='top center')
        fig3.update_layout(height=360, margin=dict(t=40,b=10))
        st.plotly_chart(fig3, use_container_width=True)

    # 4.2 City × Category drill-through (năm cuối cùng)
    with c4:
        max_yr = df['year'].max()
        cross = df[df['year']==max_yr].groupby(['city','category']).agg(
            produced_qty=('produced_qty','sum'),
            scrap_rate_pct=('scrap_rate_pct','mean'),
        ).reset_index()

        fig4 = px.treemap(cross, path=['city','category'], values='produced_qty',
                          color='scrap_rate_pct',
                          color_continuous_scale='RdYlGn_r',
                          title=f'4.2 Sản lượng Thành phố × Category ({max_yr})',
                          labels={'scrap_rate_pct':'Scrap %','produced_qty':'Sản lượng'})
        fig4.update_layout(height=360, margin=dict(t=40,b=10))
        st.plotly_chart(fig4, use_container_width=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("📊 DW Bánh Kẹo — Cube: DW Banh Keo · Fact_Production · Schema: Star Schema · Nhóm 4")
