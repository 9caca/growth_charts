import pandas as pd
import streamlit as st
import plotly_express as px
#Definir a largura do dashboard para largura total da tela
st.set_page_config(layout="wide")

bmi_df = pd.read_csv("bmi.csv")

print(bmi_df)