import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. 页面配置 (完全去品牌化) ---
st.set_page_config(page_title="财务模型沙盘 Pro", layout="wide")

st.title("🍎 订阅卡利润沙盘推演系统 (Pro)")
st.markdown("""
本工具用于模拟 **用户在一年中任意一周入场** 时的利润表现。
核心逻辑：**2次常规 + 1次星标** 循环触发。
**特性**：常规款将在当月的 A/B/C 三款产品中自动轮询。
""")

# --- 2. 初始化缓存 (防止刷新重置) ---
default_data = {
    "月份": [f"{i}月" for i in range(1, 13)],
    # 为了演示效果，稍微调高一点成本，或者你在侧边栏调高目标利润率，就能看到预警
    "常规A名": ["粑粑柑", "不知火", "沃柑", "伦晚", "夏橙", "水蜜桃", "黄桃", "蜜桔", "蜜柚", "爱媛", "阿克苏", "果冻橙"],
    "常规A成本": [55, 55, 55, 50, 45, 60, 55, 45, 50, 55, 50, 55],
    "常规B名": ["牛奶枣", "春见", "千禧果", "芒果", "荔枝", "翠冠梨", "巨峰", "石榴", "冬枣", "金桔", "赣南橙", "砂糖橘"],
    "常规B成本": [60, 60, 50, 45, 65, 50, 55, 50, 55, 50, 55, 60],
    "常规C名": ["草莓", "凤梨", "羊角蜜", "蓝莓", "杨梅", "西瓜", "阳光玫瑰", "猕猴桃", "柿子", "梨", "黑莓", "蓝莓"],
    "常规C成本": [70, 55, 60, 70, 60, 40, 60, 60, 45, 40, 70, 70],
    "星标名": ["车厘子", "燕窝果", "莲雾", "金煌芒", "大樱桃", "金果", "水蜜桃王", "爱妃苹果", "佳沛金果", "释迦", "褚橙", "车厘子"],
    "星标成本": [150, 140, 130, 120, 150, 140, 130, 120, 140, 150, 130, 160]
}

if "cost_df_cache" not in st.session_state:
    st.session_state["cost_df_cache"] = pd.DataFrame(default_data)

# --- 3. 侧边栏配置 ---
with st.sidebar:
    st.header("⚙️ 核心参数配置")
    
    st.subheader("1. 财务指标")
    # 默认值设为 30%，这样更容易触发红色的预警，让你看到效果
    target_margin_pct = st.slider("目标利润率安全线 (%)", 10.0, 50.0, 30.0, 1.0) / 100.0
    logistics_cost = st.number_input("单单履约成本 (物流+包装)", value=12.0)
    
    st.subheader("2. 销售定价 (95折逻辑)")
    price_3 = st.number_input("3次卡售价 (折后)", value=378.1)
    price_6 = st.number_input("6次卡售价 (折后)", value=759.0)
    price_12 = st.number_input("12次卡售价 (原价)", value=1498.0)

    st.subheader("3. 月度产品成本库")
    
    if st.button("🔄 重置为默认成本库"):
        st.session_state["cost_df_cache"] = pd.DataFrame(default_data)
        st.rerun()

    # 编辑器
    edited_df = st.data_editor(
        st.session_state["cost_df_cache"], 
        height=460, 
        use_container_width=True
    )
    st.session_state["cost_df_cache"] = edited_df

# --- 4. 核心计算逻辑 ---
month_map = edited_df.set_index("月份").to_dict('index')
month_names = edited_df["月份"].tolist()

def simulate_profit(start_week, card_type, price, count, freq_weeks):
    costs = []
    details = []
    current_week_idx = start_week - 1
    reg_counter = 0 
    
    for i in range(count):
        actual_week = (current_week_idx + i * freq_weeks) % 52
        month_idx = int(actual_week / 52 * 12)
        month_name = month_names[month_idx]
        month_data = month_map[month_name]
        
        is_star = ((i + 1) % 3 == 0)
        
        if is_star:
            item_name = month_data["星标名"]
            item_cost = month_data["星标成本"]
            item_type = "★星标"
        else:
            remainder = reg_counter % 3
            if remainder == 0:
                item_name = month_data["常规A名"]
                item_cost = month_data["常规A成本"]
                item_type = "常规A"
            elif remainder == 1:
                item_name = month_data["常规B名"]
                item_cost = month_data["常规B成本"]
                item_type = "常规B"
            else:
                item_name = month_data["常规C名"]
                item_cost = month_data["常规C成本"]
                item_type = "常规C"
            reg_counter += 1
            
        costs.append(item_cost)
        details.append(f"{month_name}{item_type}:{item_name}({item_cost})")
        
    total_product_cost = sum(costs)
    total_logistics = count * logistics_cost
    total_cost = total_product_cost + total_logistics
    profit = price - total_cost
    margin = profit / price if price != 0 else 0
    
    return margin, total_cost, details

# --- 5. 运行模拟 ---
scenarios = [
    {"Name": "3次卡(季卡)", "Price": price_3, "Count": 3},
    {"Name": "6次卡(半年)", "Price": price_6, "Count": 6},
    {"Name": "12次卡(年卡)", "Price": price_12, "Count": 12}
]
frequencies = {"周配": 1, "双周配": 2, "月配": 4}

results = []
for w in range(1, 53):
    m_idx = int((w - 1) / 52 * 12)
    month = month_names[m_idx]
    for sc in scenarios:
        for freq_name, freq_val in frequencies.items():
            margin, tot_cost, flow = simulate_profit(w, sc["Name"], sc["Price"], sc["Count"], freq_val)
            results.append({
                "入场周": w,
                "入场月": month,
                "卡种": sc["Name"],
                "配送频率": freq_name,
                "场景": f"{sc['Name']}-{freq_name}",
                "利润率": margin,
                "总成本": tot_cost,
                "发货详情": flow
            })

df_res = pd.DataFrame(results)

# --- 6. 可视化 ---
st.subheader("📈 全年利润趋势分析")
selected_cards = st.multiselect("选择显示的卡种", df_res["卡种"].unique(), default=["3次卡(季卡)", "12次卡(年卡)"])
df_chart = df_res[df_res["卡种"].isin(selected_cards)].copy()
df_chart["详情文本"] = df_chart["发货详情"].apply(lambda x: "<br>".join(x))

fig = px.line(df_chart, x="入场周", y="利润率", color="场景", 
              hover_data={"入场月":True, "详情文本":True, "利润率":':.1%', "入场周":False},
              markers=True)
fig.add_hline(y=target_margin_pct, line_dash="dash", line_color="red", annotation_text="安全线")
fig.update_layout(yaxis_tickformat=".1%")
st.plotly_chart(fig, use_container_width=True)

# --- 7. 风险详情 (修复：始终显示列表) ---
st.subheader("🚨 利润表现与建议")

# 计算逻辑
df_res["需降本金额"] = df_res.apply(
    lambda row: row["总成本"] - (
        (price_3 if "3次" in row["卡种"] else (price_6 if "6次" in row["卡种"] else price_12)) 
        * (1 - target_margin_pct)
    ), axis=1
)

risk_df = df_res[df_res["利润率"] < target_margin_pct].copy()

# 即使没有风险，也展示利润最低的几个，防止用户以为功能丢失
if risk_df.empty:
    st.success(f"🎉 当前配置下，所有场景利润均高于 {target_margin_pct*100:.0f}%！")
    st.markdown("👇 **虽然全部达标，但以下是利润相对最低的 Top 5 场景：**")
    display_df = df_res.sort_values("利润率").head(5) # 取最低的5个
else:
    st.warning(f"发现 {len(risk_df)} 个场景低于目标线 {target_margin_pct*100:.0f}%。以下是风险最大的 Top 10：")
    display_df = risk_df.sort_values("利润率").head(10)

# 循环展示详情卡片 (这就是你觉得丢失的部分)
for _, row in display_df.iterrows():
    # 根据是否达标显示不同的图标
    icon = "⚠️" if row['利润率'] < target_margin_pct else "✅"
    
    with st.expander(f"{icon} {row['入场月']}入场 - {row['场景']} (利润: {row['利润率']*100:.1f}%)"):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**📦 发货路径：**")
            st.info(" ➔ ".join(row["发货详情"]))
            st.write(f"总成本: ¥{row['总成本']:.1f}")
        with col2:
            if row['需降本金额'] > 0:
                st.metric("建议整单降本", f"¥ {row['需降本金额']:.1f}")
                st.caption("建议优化路径中最高成本单品")
            else:
                st.metric("安全溢价", f"¥ {-row['需降本金额']:.1f}")
                st.caption("当前利润已超标")

# --- 8. 底部图表 ---
with st.expander("📊 查看当前生效的成本库图表"):
    st.bar_chart(edited_df.set_index("月份")[["常规A成本", "常规B成本", "常规C成本", "星标成本"]])
