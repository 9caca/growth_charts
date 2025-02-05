import pandas as pd
import streamlit as st
import plotly_express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_card import card
import uuid

# Set the dashboard width to full screen width
st.set_page_config(layout="wide")

# Import data
stature_df = pd.read_csv("stature.csv").round(2)
bmi_df = pd.read_csv("bmi.csv").round(2)
weight_df = pd.read_csv("weight.csv").round(2)
child_df = pd.read_csv("child.csv")
data_df = pd.read_csv("data.csv")

# Sidebar menu
st.sidebar.title("Options")
# Menu to add measurements
with st.sidebar.expander("📏 Add New Measurements"):
    try:
        # Check if there are any registered children
        if len(child_df) == 0:
            st.error("No children registered yet. Please add a child first.")
        else:
            children_names = child_df[['id_child', 'name']].values.tolist()
            children_options = {f"{name}": id for id, name in children_names}
            
            selected_child = st.selectbox(
                "Select Child:",
                options=list(children_options.keys())
            )
            
            selected_child_id = children_options[selected_child]
            
            input_date = st.date_input("Measurement Date:")
            input_date = pd.to_datetime(input_date)
            input_weight = st.number_input("Weight (kg):", min_value=0.0, step=0.1, value=0.0)
            input_height = st.number_input("Height (cm):", min_value=0.0, step=0.1, value=0.0)
            #Convert to None if zero
            weight_val = float('nan') if input_weight == 0.0 else input_weight
            height_val = float('nan') if input_height == 0.0 else input_height
            
            # Calculate BMI only if both values exist
            if weight_val > 0 and height_val > 0:
                bmi = round(weight_val / (height_val / 100) ** 2, 2)
            else:
                bmi = float('nan')
            
            child_info = child_df[child_df['id_child'] == selected_child_id].iloc[0]
            birthdate = pd.to_datetime(child_info['birthdate'])
            age_months = round((input_date - birthdate).days / 30.44, 1)
            
            if st.button("Save Measurements"):
                new_measurement = pd.DataFrame({
                    "id_child": [selected_child_id],
                    "date": [input_date],
                    "agemos": [age_months],
                    "weight": [weight_val],
                    "height": [height_val],
                    "BMI": [bmi]
                })

                try:
                    existing_data = pd.read_csv("data.csv")
                    updated_data = pd.concat([existing_data, new_measurement])
                except FileNotFoundError:
                    updated_data = new_measurement
                
                updated_data.to_csv("data.csv", index=False)
                st.success("Measurements saved successfully!")

    except FileNotFoundError:
        st.error("No children registered yet. Please add a child first.")
#  Menu to add a new child
with st.sidebar.expander("➕ Add a New Child"):
    input_name = st.text_input("Child's Name:")
    input_sex = st.selectbox("Sex:", ["Female", "Male"])
    input_birthdate = pd.to_datetime(st.date_input("Birthdate:"))
    
    if st.button("Save Child"):
        id_child = str(uuid.uuid4())[:8]
        sex = 1 if input_sex == "Male" else 2

        new_child = pd.DataFrame({
            "id_child": [id_child],
            "name": [input_name],
            "sex": [sex],
            "birthdate": [input_birthdate]
        })

        try:
            existing_data = pd.read_csv("child.csv")
            updated_data = pd.concat([existing_data, new_child])
        except FileNotFoundError:
            updated_data = new_child

        updated_data.to_csv("child.csv", index=False)
        st.success(f"{input_name} has been added!")
 
# CSS Styling
st.markdown(
    """
    <style>
        .card {
            width: 300px;
            border-radius: 15px;
            padding: 15px;
            margin: 10px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
        }
        .girl { background-color: #FFC0CB; }
        .boy { background-color: #ADD8E6; }
        }
        .trend-up { color: green; }
        .trend-down { color: red; }
    </style>
    """,
    unsafe_allow_html=True
)

# Dashboard Cards
st.title("Children's Health Dashboard")

for _, child in child_df.iterrows():
    child_id = child['id_child']
    name = child['name']
    sex = "girl" if child['sex'] == 2 else "boy"
    birthdate = pd.to_datetime(child['birthdate'])
    
    # Get latest measurements
    child_data = data_df[data_df['id_child'] == child_id].sort_values(by='date', ascending=False)
    last_entry = child_data.iloc[0] if not child_data.empty else None
    last_weight = last_entry['weight'] if last_entry is not None else "Unknown"
    
    # Get last valid height & BMI
    last_valid_height = child_data['height'].dropna().iloc[0] if not child_data['height'].dropna().empty else "Unknown"
    last_valid_bmi = child_data['BMI'].dropna().iloc[0] if not child_data['BMI'].dropna().empty else "Unknown"
    
    # Calculate Age
    age_months = round((datetime.today() - birthdate).days / 30.44, 1)
    age_years = int(age_months // 12)
    age_months = int(age_months % 12)
    
    # Determine BMI Status
    if last_valid_bmi == "Unknown":
        bmi_status = "Unknown"
        color = "black"
    elif last_valid_bmi < 18.5:
        bmi_status = "Underweight"
        color = "blue"
    elif 18.5 <= last_valid_bmi < 25:
        bmi_status = "Normal"
        color = "green"
    elif 25 <= last_valid_bmi < 30:
        bmi_status = "Overweight"
        color = "orange"
    else:
        bmi_status = "Obese"
        color = "red"
    
    # Calculate weight trend
    if len(child_data) > 1:
        prev_weight = child_data.iloc[1]['weight']
        trend = "up" if last_weight > prev_weight else "down"
    else:
        trend = "unknown"
    
    # Display Card
    st.markdown(
        f"""
        <div class="card {sex}">
            <div>
                <h3>{name} ({age_years}y {age_months}m)</h3>
                <p>📏 Height: {last_valid_height} cm</p>
                <p>⚖️ Weight: {last_weight} kg</p>
                <p>🩺 BMI: {last_valid_bmi} (<span style="color:{color}">{bmi_status}</span>)</p>
                <p>Tendência: <span class="trend-{trend}">{'↑' if trend == 'up' else '↓'}</span></p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
