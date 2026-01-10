import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. 页面配置 (去除品牌名) ---
st.set_page_config(page_title="财务模型沙盘 (Pro版)", layout="wide")

st.title("🍎 订阅卡利润沙盘推演系统 (Pro)")
st.markdown("""
本工具用于模拟 **用户在一年中任意一周入场** 时的利润表现。
核心逻辑：**2次常规 + 1次星标** 循环触发。
**特性**：常规款将在当月的 A/B/C 三款产品中自动轮询。
""")

# --- 2. 初始化缓存 (关键步骤：防止刷新重置) ---
# 定义默认数据结构
default_data = {
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

# 检查 session_state 中是否已有数据，如果没有，才加载默认值
if "cost_df_cache" not in st.session_state:
    st.session_state["cost_df_cache"] = pd.DataFrame(default_data)

# --- 3. 侧边栏配置 ---
with st.sidebar:
    st.header("⚙️ 核心参数配置")
    
    st.subheader("1. 财务指标")
    target_margin_pct = st.slider("目标利润率安全线 (%)", 10.0, 40.0, 20.0, 1.0) / 100.0
    logistics_cost = st.number_input("单单履约成本 (物流+包装)", value=12.0)
    
    st.subheader("2. 销售定价 (95折逻辑)")
    price_3 = st.number_input("3次卡售价 (折后)", value=378.1)
    price_6 = st.number_input("6次卡售价 (折后)", value=759.0)
    price_12 = st.number_input("12次卡售价 (原价)", value=1498.0)

    st.subheader("3. 月度产品成本库")
    st.info("👇 修改表格数据会自动保存，操作其他滑块不会丢失数据。")
    
    # 添加一个重置按钮，万一改乱了可以恢复
    if st.button("重置为默认成本库"):
        st.session_state["cost_df_cache"] = pd.DataFrame(default_data)
        st.rerun() # 立即刷新页面

    # 使用 session_state 中的数据进行编辑
    # 这里的关键是：不直接读取 default_data，而是读取缓存
    edited_df = st.data_editor(
        st.session_state["cost_df_cache"], 
        height=460, 
        use_container_width=True
    )
    
    # 将编辑后的结果立刻反写回 session_state
    # 这样下次脚本运行时，用的就是你刚才编辑过的数据
    st.session_state["cost_df_cache"] = edited_df

# --- 4. 核心计算逻辑 ---

# 为了方便查询，转换数据格式
month_map = edited_df.set_index("月份").to_dict('index')
month_names = edited_df["月份"].tolist()

def simulate_profit(start_week, card_type, price, count, freq_weeks):
    costs = []
    details = []
    current_week_idx = start_week - 1
    reg_counter = 0 # 常规款计数器
    
    for i in range(count):
        # 1. 确定时间
        actual_week = (current_week_idx + i * freq_weeks) % 52
        month_idx = int(actual_week / 52 * 12)
        month_name = month_names[month_idx]
        month_data = month_map[month_name]
        
        # 2. 确定类型 (2次常规 1次星标)
        is_star = ((i + 1) % 3 == 0)
        
        # 3. 确定产品
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
    
    return
