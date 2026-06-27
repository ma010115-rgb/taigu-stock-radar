import streamlit as st
import pandas as pd

st.set_page_config(page_title="台股選股雷達", layout="wide")
st.title("📊 台股籌碼選股雷達")
st.subheader("測試版本 - 簡化後")

st.success("✅ 部署成功！現在可以慢慢加功能。")

if st.button("點我測試"):
    data = {"股票": ["2330", "2603"], "名稱": ["台積電", "長榮"]}
    st.dataframe(pd.DataFrame(data))
