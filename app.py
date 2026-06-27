import streamlit as st
import pandas as pd
import datetime
from FinMind.data import DataLoader
import time

st.set_page_config(page_title="大戶與主力極速選股雷達", layout="wide")
st.title("📊 我的專屬台股籌碼選股雷達")
st.subheader("設定你的選股邏輯，一鍵篩選隔日佈局標的")

st.sidebar.header("🛠 篩選條件開關")
vol_check = st.sidebar.checkbox("1. 當日成交量 > 1000 張", value=True)
large_up_check = st.sidebar.checkbox("2. 千張大戶持股比率上升 (與上週相比)", value=True)
retail_down_check = st.sidebar.checkbox("3. 百張散戶持股比率下降 (與上週相比)", value=True)
main_buy_check = st.sidebar.checkbox("4. 主力買賣超連 3 天買", value=True)
retail_sell_check = st.sidebar.checkbox("5. 散戶買賣超連 3 天賣", value=True)

start_button = st.sidebar.button("🚀 開始極速選股", type="primary")

if start_button:
    with st.spinner("正在從 FinMind 抓取最新數據，請稍候..."):
        try:
            api = DataLoader()
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            last_week = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            three_days_ago = (datetime.date.today() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")

            stock_info = api.taiwan_stock_info()
            daily_data = api.taiwan_stock_daily(start_date=today_str, end_date=today_str)

            if daily_data.empty:
                st.error("今日數據尚未更新，請稍後再試")
                st.stop()

            daily_data = daily_data.merge(stock_info[['stock_id', 'stock_name']], on='stock_id', how='left')
            candidates = daily_data[daily_data['Trading_Volume'] > 1000].copy() if vol_check else daily_data.copy()

            results = []
            progress_bar = st.progress(0)
            total = len(candidates)

            for idx, row in candidates.iterrows():
                stock_id = row['stock_id']
                progress_bar.progress((idx + 1) / total)
                
                try:
                    holding = api.taiwan_stock_holding_shares_per(stock_id=stock_id, start_date=last_week, end_date=today_str)
                    if holding.empty:
                        continue
                    holding = holding.sort_values('date')
                    latest = holding.iloc[-1]
                    prev = holding.iloc[-2] if len(holding) > 1 else latest

                    large_up = True
                    retail_down = True
                    if large_up_check or retail_down_check:
                        large_up = latest.get('Shareholding_1000', 0) > prev.get('Shareholding_1000', 0)
                        retail_down = latest.get('Shareholding_100', 0) < prev.get('Shareholding_100', 0)

                    institutional = api.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=three_days_ago, end_date=today_str)
                    main_buy_days = 0
                    if not institutional.empty:
                        institutional = institutional.sort_values('date').tail(3)
                        net_buy = (institutional['Foreign_Investor_Buy'] + institutional['Investment_Trust_Buy'] + institutional['Dealer_Buy'] - 
                                   institutional['Foreign_Investor_Sell'] - institutional['Investment_Trust_Sell'] - institutional['Dealer_Sell'])
                        main_buy_days = (net_buy > 0).sum()

                    main_buy_ok = main_buy_days >= 3 if main_buy_check else True

                    if large_up and retail_down and main_buy_ok:
                        results.append({
                            "股票代號": stock_id,
                            "股票名稱": row.get('stock_name', 'N/A'),
                            "今日成交量(張)": int(row['Trading_Volume']),
                            "千張大戶變動": f"+{latest.get('Shareholding_1000',0) - prev.get('Shareholding_1000',0):.2f}%",
                            "百張散戶變動": f"-{prev.get('Shareholding_100',0) - latest.get('Shareholding_100',0):.2f}%",
                            "主力連買天數": f"{main_buy_days}天",
                            "散戶連賣天數": "3+天"
                        })
                except:
                    continue
                time.sleep(0.1)

            if results:
                df_result = pd.DataFrame(results)
                st.success(f"🎉 找到 {len(df_result)} 檔符合條件的標的！")
                st.dataframe(df_result.style.background_gradient(cmap="Reds", subset=["今日成交量(張)"]), use_container_width=True)
                st.info("💡 以上為參考，實際交易請自行判斷風險")
            else:
                st.warning("本次沒有完全符合的股票，試著放寬條件再試")
        except Exception as e:
            st.error(f"錯誤：{str(e)}")
else:
    st.warning("👈 請在左側勾選條件後點擊按鈕")

st.caption("Powered by FinMind + Streamlit")