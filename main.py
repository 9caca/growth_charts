import pandas as pd
import streamlit as st
import plotly_express as px
import plotly.graph_objects as go
from datetime import datetime

# Datas de nascimento
nina_birthdate = datetime(2020, 8, 17)
mariana_birthdate = datetime(2018, 3, 18)

#Definir a largura do dashboard para largura total da tela
st.set_page_config(layout="wide")

bmi_df = pd.read_csv("bmi.csv")
weight_df = pd.read_csv("weight.csv")
weight_df = weight_df[weight_df['Sex'] == 2]
weight_df = weight_df.round(2)

# Menu lateral
st.sidebar.title("Opções")
selected_child = st.sidebar.selectbox("Selecione a criança:", ["Mariana", "Nina"])
file_name = "mariana_peso.csv" if selected_child == "Mariana" else "nina_peso.csv"
birthdate = mariana_birthdate if selected_child == "Mariana" else nina_birthdate


# Transformar a idade de meses para anos e meses
def agemos_to_years_months(agemos):
    years = int(agemos // 12)
    months = int(agemos % 12)
    return f"{years}y {months}m"

weight_df['Age (years)'] = weight_df['Agemos'].apply(agemos_to_years_months)

# Dicionário de cores para os percentis
colors = {
    "P5": "black",
    "P10": "orange",
    "P25": "green",
    "P50": "blue",
    "P75": "green",
    "P90": "orange",
    "P95": "black"
}

# Definir o arquivo e a data de nascimento com base na seleção
if selected_child == "Mariana":
    file_name = "mariana_peso.csv"
    birthdate = mariana_birthdate
else:
    file_name = "nina_peso.csv"
    birthdate = nina_birthdate

# Formulário para adicionar peso
st.sidebar.subheader(f"Adicionar peso para {selected_child}")
input_date = st.sidebar.date_input("Data da pesagem:")
input_weight = st.sidebar.number_input("Peso (kg):", min_value=0.0, step=0.1)

if st.sidebar.button("Salvar"):
    # Calcular idade em anos
    try:
        # Converter input_date para datetime.datetime
        input_date_datetime = datetime.combine(input_date, datetime.min.time())

        # Calcular idade em anos
        age_years = (input_date_datetime - birthdate).days / 365.25

        # Adicionar entrada ao arquivo CSV
        new_data = pd.DataFrame({"Date": [input_date], "Age (years)": [age_years], "Weight": [input_weight]})
        try:
            existing_data = pd.read_csv(file_name)
            updated_data = pd.concat([existing_data, new_data])
        except FileNotFoundError:
            updated_data = new_data

        updated_data.to_csv(file_name, index=False)
        st.sidebar.success(f"Dados salvos para {selected_child}!")
    except Exception as e:
        st.sidebar.error(f"Erro ao salvar os dados: {e}")

# Carregar os dados de Nina ou Mariana
try:
    child_data = pd.read_csv(file_name)
except FileNotFoundError:
    child_data = pd.DataFrame(columns=["Date", "Age (years)", "Weight"])

# Criar o gráfico
fig = go.Figure()

# Adicionar curvas de crescimento
for percentile in ["P5", "P10", "P25", "P50", "P75", "P90", "P95"]:
    fig.add_trace(
        go.Scatter(
            x=weight_df['Age (years)'],
            y=weight_df[percentile],
            mode='lines',
            name=percentile,
            line=dict(color=colors[percentile])
        )
    )

# Adicionar os dados de Nina ou Mariana
if not child_data.empty:
    fig.add_trace(
        go.Scatter(
            x=child_data['Age (years)'],
            y=child_data['Weight'],
            mode='markers+lines',
            name=f"{selected_child} (dados)",
            line=dict(color='pink', dash='dot'),
            marker=dict(size=10)
        )
    )

# Configurar layout do gráfico
fig.update_layout(
    title='Curvas de Crescimento - Meninas',
    xaxis_title='Idade (anos)',
    yaxis_title='Peso (kg)',
    height=700,
    yaxis=dict(range=[10, 50]),
    xaxis=dict(range=[24, 96])
)

# Exibir o gráfico
st.plotly_chart(fig)