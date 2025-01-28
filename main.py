import pandas as pd
import streamlit as st
import plotly_express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_card import card

#Definir a largura do dashboard para largura total da tela
st.set_page_config(layout="wide")

# Datas de nascimento
nina_birthdate = datetime(2020, 8, 17)
mariana_birthdate = datetime(2018, 3, 18)

#Importar os dados
altura_df = pd.read_csv("stature.csv")
altura_df = altura_df[altura_df['Sex'] == 2]
bmi_df = pd.read_csv("bmi.csv")
bmi_df = bmi_df[bmi_df['Sex'] == 2]
weight_df = pd.read_csv("weight.csv")
weight_df = weight_df[weight_df['Sex'] == 2]
weight_df = weight_df.round(2)

# Transformar a idade de meses para anos e meses
def agemos_to_years_months(agemos):
    years = int(agemos // 12)
    months = int(agemos % 12)
    return f"{years}y {months}m"

weight_df['Age (years)'] = weight_df['agemos'].apply(agemos_to_years_months)

# Menu lateral
st.sidebar.title("Opções")
selected_child = st.sidebar.selectbox("Selecione a criança:", ["Mariana", "Nina"])
file_name = "mariana_peso.csv" if selected_child == "Mariana" else "nina_peso.csv"
birthdate = mariana_birthdate if selected_child == "Mariana" else nina_birthdate

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
input_stature = st.sidebar.number_input("Altura (cm):", min_value=0.0, step=0.1)

if st.sidebar.button("Salvar"):
    # Calcular idade em meses
    try:
        # Garantir que input_date e birthdate estejam no mesmo formato
        input_date = datetime.combine(input_date, datetime.min.time())  # Converte input_date para datetime.datetime
        birthdate = birthdate.replace(hour=0, minute=0, second=0, microsecond=0)  # Garante que birthdate também está no formato datetime.datetime
        
        # Calcular idade em meses
        age_months = round((input_date - birthdate).days / 30.4375)

        # Calcular BMI
        bmi = round(input_weight / (input_stature / 100) ** 2, 2) if input_stature > 0 else None  # Evitar divisão por zero
        
        # Adicionar entrada ao arquivo CSV
        new_data = pd.DataFrame({
            "Date": [input_date],
            "agemos": [age_months],
            "Weight": [input_weight],
            "stature": [input_stature],
            "BMI": [bmi],
            "Child": [selected_child]
        })
        try:
            existing_data = pd.read_csv(file_name)
            updated_data = pd.concat([existing_data, new_data])
        except FileNotFoundError:
            updated_data = new_data
        
        updated_data.to_csv(file_name, index=False)
        st.sidebar.success(f"Dados salvos para {selected_child} com BMI: {bmi}")
    except Exception as e:
        st.sidebar.error(f"Erro ao salvar os dados: {e}")

# Carregar os dados de Nina ou Mariana
try:
    child_data = pd.read_csv(file_name)
    if child_data.empty:
        child_data = pd.DataFrame(columns=["Date", "agemos", "Weight", "stature", "BMI"])
except (FileNotFoundError, pd.errors.EmptyDataError):
    child_data = pd.DataFrame(columns=["Date", "agemos", "Weight", "stature", "BMI"])

child_data['Age (formatted)'] = child_data['agemos'].apply(agemos_to_years_months)
child_data['Date'] = pd.to_datetime(child_data['Date'])
latest_row = child_data.loc[child_data['Date'].idxmax()]

# Extrair os dados mais recentes
current_date = latest_row['Date'].strftime("%d/%m/%Y")
current_weight = latest_row['Weight']
current_stature = latest_row['stature']
current_bmi = latest_row['BMI']

# Definir a categoria com base no BMI
def define_bmi_category(bmi, agemos, sex, bmi_df):
    row = bmi_df[(bmi_df['agemos'] == agemos) & (bmi_df['Sex'] == sex)]
    if not row.empty:
        p5 = row['P5'].values[0]
        p85 = row['P85'].values[0]
        p95 = row['P95'].values[0]
        if bmi < p5:
            return "Underweight"
        elif 5 <= bmi < p85:
            return "Healthy weight"
        elif p85 <= bmi < p95:
            return "Overweight"
        else:
            return "Obese"
    return "Unknown"

bmi_df['agemos'] = bmi_df['agemos'].astype(float).round(1)
child_data['agemos'] = child_data['agemos'].astype(float).round(1)

# Carregar os dados de referência de BMI
bmi_df = pd.read_csv("bmi.csv")

# Definir o sexo da criança (1 = menina, no dataset de BMI)
sex = 2
bmi_category = define_bmi_category(current_bmi, latest_row['agemos'], sex, bmi_df)

# Layout dos cards com Streamlit
st.write("### Informações mais recentes")
col1, col2, col3 = st.columns(3)

with col1:
    st.write("**Peso e Altura**")
    st.write(f"Peso: {current_weight} kg")
    st.write(f"Altura: {current_stature} cm")

with col2:
    st.write("**BMI**")
    st.write(f"BMI: {current_bmi}")

with col3:
    st.write("**Categoria**")
    st.write(f"{bmi_category}")


# Criar o gráfico
fig_weight = go.Figure()

# Adicionar curvas de crescimento
for percentile in ["P5", "P10", "P25", "P50", "P75", "P90", "P95"]:
    fig_weight.add_trace(
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
    child_data['Age (years)'] = child_data['agemos'].apply(lambda x: x / 12)  # Transformar meses em anos (número decimal)
    fig_weight.add_trace(
        go.Scatter(
            x=child_data['Age (formatted)'],
            y=child_data['Weight'],
            mode='markers+lines',
            name=f"{selected_child} (dados)",
            line=dict(color='pink', dash='dot'),
            marker=dict(size=10)
        )
    )

# Configurar layout do gráfico
fig_weight.update_layout(
    title='Curvas de Crescimento - Meninas',
    xaxis_title='Idade (anos)',
    yaxis_title='Peso (kg)',
    height=700,
    yaxis=dict(range=[13, 45]),
    xaxis=dict(range=[24, 96])
)

# Exibir o gráfico
st.plotly_chart(fig_weight)

altura_df['Age (years)'] = altura_df['agemos'].apply(agemos_to_years_months)
#child_data['Age (formatted)'] = child_data['agemos'].apply(agemos_to_years_months)

# Criar o gráfico
fig_stature = go.Figure()
# Criar o gráfico de altura
if not altura_df.empty:
    fig_stature = go.Figure()
    for col in ['P5', 'P10', 'P25', 'P50', 'P75', 'P90', 'P95']:
        fig_stature.add_trace(
            go.Scatter(
                x=altura_df['Age (years)'],  # Converter idade em meses para anos
                y=altura_df[col],
                mode='lines',
                name=f"{col} - Altura",
                line=dict(
                    color='black' if col in ['P5', 'P95'] else (
                        'orange' if col in ['P10', 'P90'] else (
                        'green' if col in ['P25', 'P75'] else 'blue'
                        )
                    ),
                    dash='solid'
                )
            )
        )
    # Adicionar os dados de Nina ou Mariana
if not child_data.empty:
    child_data['Age (years)'] = child_data['agemos'].apply(lambda x: x / 12)  # Transformar meses em anos (número decimal)
    fig_stature.add_trace(
        go.Scatter(
            x=child_data['Age (formatted)'],
            y=child_data['stature'],
            mode='markers+lines',
            name=f"{selected_child} (dados)",
            line=dict(color='pink', dash='dot'),
            marker=dict(size=10)
        )
    )

    # Adicionar título e ajustar layout
    fig_stature.update_layout(
        title="Curvas de Crescimento - Altura (Meninas)",
        xaxis_title="Idade (anos)",
        yaxis_title="Altura (cm)",
        height=700,
        xaxis=dict(tickmode='linear', dtick=1, range=[24, 96]),
        yaxis=dict(range=[95, 145]),  # Ajustar o limite máximo para altura
        legend_title="Percentis"
        
    )
    st.plotly_chart(fig_stature)
