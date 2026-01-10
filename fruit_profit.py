import streamlit as st
import pandas as pd
import plotly.express as px
import math

# --- 页面配置 ---
st.set_page_config(page_title="元素果子-财务模型沙盘 (Pro版)", layout="wide")

st.title("🍎 元素果子 | 订阅卡利润沙盘推演系统 (Pro)")
st.markdown("""
本工具用于模拟 **用户在一年中任意一周入场** 时的利润表现。
核心逻辑：**2次常规 + 1次星标** 循环触发。
**升级特性**：常规款将在当月的 A/B/C 三款产品中自动轮询。
""")

# --- 侧边栏：核心参数配置 ---
with st.sidebar:
    st.header("⚙️ 核心参数配置")
    
    st.subheader("1. 财务指标")
    target_margin_pct = st.slider("目标利润率安全线 (%)", 10.0, 40.0, 20.0, 1.0) / 100.0
    logistics_cost = st.number_input("单单履约成本 (物流+包装)", value=12.0)
    
    st.subheader("2. 销售定价 (95折逻辑)")
    price_3 = st.number_input("3次卡售价 (折后)", value=378.1)
    price_6 = st.number_input("6次卡售价 (折后)", value=759.0)
    price_12 = st.number_input("12次卡售价 (原价)", value=1498.0)

    st.subheader("3. 月度产品成本库 (3常规+1星标)")
    st.info("👇 请在表格中完善每月 4 款产品的成本")
    
    # --- 构建新的宽表结构 ---
    # 这里初始化一些默认数据，方便你直接开始
    data_structure = {
        "月份": [f"{i}月" for i in range(1, 13)],
        # 常规 A
        "常规A名": ["粑粑柑", "不知火", "沃柑", "伦晚", "夏橙", "水蜜桃", "黄桃", "蜜桔", "蜜柚", "爱媛", "阿克苏", "果冻橙"],
        "常规A成本": [55, 55, 55, 50, 45, 60, 55, 45, 50, 55, 50, 55],
        # 常规 B
        "常规B名": ["牛奶枣", "春见", "千禧果", "芒果", "荔枝", "翠冠梨", "巨峰", "石榴", "冬枣", "金桔", "赣南橙", "砂糖橘"],
        "常规B成本": [60, 60, 50, 45, 65, 50, 55, 50, 55, 50, 55, 60],
        # 常规 C
        "常规C名": ["草莓", "凤梨", "羊角蜜", "蓝莓", "杨梅", "西瓜", "阳光玫瑰", "猕猴桃", "柿子", "梨", "黑莓", "蓝莓"],
        "常规C成本": [70, 55, 60, 70, 60, 40, 60, 60, 45, 40, 70, 70],
        # 星标款
        "星标名": ["车厘子", "燕窝果", "莲雾", "金煌芒", "大樱桃", "金果", "水蜜桃王", "爱妃苹果", "佳沛金果", "释迦", "褚橙", "车厘子"],
        "星标成本": [150, 140, 130, 120, 150, 140, 130, 120, 140, 150, 130, 160]
    }
    
    df_costs = pd.DataFrame(data_structure)
    edited_df = st.data_editor(df_costs, height=460, use_container_width=True)

# --- 核心计算逻辑 ---

# 1. 将月份数据扩展到52周
# 为了方便查询，我们将 DataFrame 转换为以“月份”为 key 的字典
month_map = edited_df.set_index("月份").to_dict('index')
month_names = edited_df["月份"].tolist()

# 2. 模拟函数
def simulate_profit(start_week, card_type, price, count, freq_weeks):
    """
    start_week: 入场周 (1-52)
    card_type: 卡种名称
    price: 总售价
    count: 发货总次数
    freq_weeks: 发货频率 (1=周配, 2=双周, 4=月配)
    """
    costs = []
    details = []
    
    current_week_idx = start_week - 1
    
    # 计数器
    reg_counter = 0 # 记录这是第几次发常规款，用于在 A/B/C 之间轮询
    
    for i in range(count):
        # --- 1. 确定当前发货的时间 ---
        actual_week = (current_week_idx + i * freq_weeks) % 52
        # 简单映射：第几周 -> 第几月 (0-11)
        month_idx = int(actual_week / 52 * 12)
        month_name = month_names[month_idx]
        month_data = month_map[month_name]
        
        # --- 2. 确定是 星标 还是 常规 ---
        # 逻辑：2次常规 + 1次星标 (第3, 6, 9...次是星标)
        is_star = ((i + 1) % 3 == 0)
        
        # --- 3. 确定具体产品和成本 ---
        item_name = ""
        item_cost = 0.0
        item_type = ""
        
        if is_star:
            # 是星标款
            item_name = month_data["星标名"]
            item_cost = month_data["星标成本"]
            item_type = "★星标"
        else:
            # 是常规款：在 A -> B -> C 之间轮询
            # 使用 reg_counter % 3 来决定用哪一款
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
            
            reg_counter += 1 # 常规计数器+1
            
        # 记录
        costs.append(item_cost)
        # 格式复刻：1月常规A:粑粑柑(55)
        details.append(f"{month_name}{item_type}:{item_name}({item_cost})")
        
    total_product_cost = sum(costs)
    total_logistics = count * logistics_cost
    total_cost = total_product_cost + total_logistics
    profit = price - total_cost
    margin = profit / price if price != 0 else 0
    
    return margin, total_cost, details

# 3. 运行全量模拟
scenarios = [
    {"Name": "3次卡(季卡)", "Price": price_3, "Count": 3},
    {"Name": "6次卡(半年)", "Price": price_6, "Count": 6},
    {"Name": "12次卡(年卡)", "Price": price_12, "Count": 12}
]
frequencies = {"周配": 1, "双周配": 2, "月配": 4}

results = []

# 遍历入场周 (1-52周)
for w in range(1, 53):
    # 计算当周属于哪个月
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
                "发货详情": flow # 这是一个列表，后面展示时再join
            })

df_res = pd.DataFrame(results)

# --- 可视化展示区 ---

st.subheader("📈 全年利润趋势分析 (按入场时间)")
st.caption("模拟逻辑：每3次发货含1次星标；常规发货在当月A/B/C三款中轮换。")

selected_cards = st.multiselect("选择显示的卡种", df_res["卡种"].unique(), default=["3次卡(季卡)", "12次卡(年卡)"])
df_chart = df_res[df_res["卡种"].isin(selected_cards)].copy()

# 为了图表hover显示好看，把详情列表转为字符串
df_chart["详情文本"] = df_chart["发货详情"].apply(lambda x: "<br>".join(x))

fig = px.line(df_chart, x="入场周", y="利润率", color="场景", 
              hover_data={"入场月":True, "详情文本":True, "利润率":':.1%', "入场周":False},
              markers=True)
fig.add_hline(y=target_margin_pct, line_dash="dash", line_color="red", annotation_text="安全线")
fig.update_layout(yaxis_tickformat=".1%")
st.plotly_chart(fig, use_container_width=True)

# --- 风险详情与建议 ---
st.subheader("🚨 利润预警与调价建议")
risk_df = df_res[df_res["利润率"] < target_margin_pct].copy()

if risk_df.empty:
    st.success("🎉 恭喜！当前成本配置下，全年所有场景利润均达标！")
else:
    # 计算需降本金额
    risk_df["需降本金额"] = risk_df.apply(
        lambda row: row["总成本"] - (
            (price_3 if "3次" in row["卡种"] else (price_6 if "6次" in row["卡种"] else price_12)) 
            * (1 - target_margin_pct)
        ), axis=1
    )
    
    top_risks = risk_df.sort_values("利润率").head(10)
    
    st.warning(f"共有 {len(risk_df)} 个入场周期的场景未达标（低于 {target_margin_pct*100:.0f}%）。以下是风险最大的前10个场景：")
    
    for _, row in top_risks.iterrows():
        with st.expander(f"⚠️ {row['入场月']}入场 - {row['场景']} (利润: {row['利润率']*100:.1f}%)"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("**发货路径复盘：**")
                # 漂亮的路径展示
                path_str = " ➔ ".join(row["发货详情"])
                st.info(path_str)
                st.write(f"当前总成本: ¥{row['总成本']:.1f}")
            with col2:
                st.metric("建议整单降本", f"¥ {row['需降本金额']:.1f}")
                st.caption("建议优化路径中最高成本单品")

# --- 成本库概览 ---
with st.expander("查看当前生效的成本库图表"):
    st.bar_chart(edited_df.set_index("月份")[["常规A成本", "常规B成本", "常规C成本", "星标成本"]])