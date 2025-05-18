import streamlit as st
st.set_page_config(page_title="Malnutrition App", layout="wide")

# ✅ Mobile-Friendly Styling
st.markdown("""
    <style>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    .main .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    button[kind="primary"], .stButton > button {
        width: 100%;
        margin-top: 0.5rem;
    }
    .stTextInput > div > input, .stNumberInput input {
        font-size: 16px;
        padding: 0.75rem;
    }
    .stSelectbox > div {
        font-size: 16px;
    }
    .stDataFrame, .stTable {
        overflow-x: auto;
    }
    h1 {
        font-size: 1.8rem;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

import json, os
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components
from food_module import run_food_scanner
from muac_module import run_muac_estimator, classify_muac
from height_module import run_height_estimator

# Meta and favicon
components.html("""
    <link rel="apple-touch-icon" sizes="180x180" href="https://raw.githubusercontent.com/mannitha/food_scanner_app/main/favicon.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black">
    <meta name="apple-mobile-web-app-title" content="My App">
""", height=0)

user_data_file = os.path.join(os.getcwd(), "users.json")

def get_nutrition_file(): return f"nutrition_data_{st.session_state.username}.json"
def get_food_file(): return f"food_data_{st.session_state.username}.json"

# Only one load_users() with error handling
def load_users():
    try:
        if os.path.exists(user_data_file):
            with open(user_data_file, "r") as f:
                return json.load(f)
    except json.JSONDecodeError:
        st.error("User data file is corrupted.")
        return {}
    return {}

# Save users to JSON file (fixed variable name)
def save_users(users):
    existing = load_users()
    existing.update(users)
    with open(user_data_file, "w") as f:
        json.dump(existing, f, indent=2)

def load_nutrition_data():
    file = get_nutrition_file()
    try:
        data = json.load(open(file)) if os.path.exists(file) else []
        return data if isinstance(data, list) else []
    except:
        return []

def save_nutrition_data(data): 
    json.dump(data, open(get_nutrition_file(), "w"), indent=2)

def load_food_data(): 
    return json.load(open(get_food_file())) if os.path.exists(get_food_file()) else []

def save_food_data(data): 
    json.dump(data, open(get_food_file(), "w"), indent=2)

# Auth
def signup():
    st.title("🔐 Sign Up")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    e = st.text_input("Email")
    if st.button("Create Account"):
        users = load_users()
        if u in users: st.error("Username already exists.")
        else:
            users[u] = {"password": p, "email": e}
            save_users(users)
            st.success("Account created!")

def login():
    st.title("🔑 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        users = load_users()
        
        if u not in users: st.error("Username doesn't exist.")
        elif users[u]["password"] != p: st.error("Incorrect password.")
        else:
            st.session_state.logged_in = True
            st.session_state.username = u
            st.session_state.page = "select_flow"

def logout(): st.session_state.clear()

def back_button():
    if st.button("⬅️ Back"):
        nav = {
            "nutrition_choices": "select_flow",
            "nutrimann_choices": "select_flow",
            "child_info": "nutrition_choices",
            "height": "child_info",
            "arm": "height",
            "done": "arm",
            "nutrimann_info": "nutrimann_choices",
            "food_only": "nutrimann_info",
            "food_summary": "food_only",
            "view_old_data": "nutrition_choices",
            "view_data_table": "nutrition_choices",
            "view_old_food": "nutrimann_choices",
            "edit_food_entry": "view_old_food"
        }
        st.session_state.page = nav.get(st.session_state.page, "select_flow")
        st.experimental_rerun()

def calculate_bmi(w, h): return round(w / ((h / 100) ** 2), 2) if w and h else None
def calculate_malnutrition_status(bmi, arm):
    if bmi is None or arm is None: return "Unknown"
    if bmi < 13 or arm < 11.5: return "Severe Acute Malnutrition"
    elif bmi < 14 or arm < 12.5: return "Moderate Acute Malnutrition"
    return "Normal"

# Flow pages
def select_flow_step():
    st.title("MalnoCare")
    st.write("Scan Track Grow")
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("👶 Physical Attributres"): st.session_state.page = "nutrition_choices"
    with col2: 
        if st.button("🍽 Food Nutrients Scan"): st.session_state.page = "nutrimann_choices"

def nutrition_choices_step():
    st.title("Child Growth Assessment")
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("➕ New Entry"): st.session_state.page = "child_info"
    with col2: 
        if st.button("🗑️ Delete Records"): st.session_state.page = "view_old_data"
    with st.container():
        if st.button("📊 View Previous Data Summary"): st.session_state.page = "view_data_table"
    back_button()

def child_info_step():
    st.title("📋 Child Information")
    st.session_state.child_name = st.text_input("Child's Name")
    st.session_state.child_age = st.number_input("Age", min_value=0)
    st.session_state.child_weight = st.number_input("Weight (kg)", min_value=0.0)
    back_button()
    if st.button("Continue"): st.session_state.page = "height"
    

def height_step():
    st.markdown("Height")
    height_result = run_height_estimator()
    if height_result:
        st.session_state.height_result = height_result
    back_button()
    if st.button("Next"):
            st.session_state.page = "arm"

def arm_step():
    st.markdown("### MUAC Estimation")

    muac_value = run_muac_estimator()

    if muac_value is not None:
        status, _ = classify_muac(muac_value)
        st.session_state["arm_val"] = muac_value
        st.session_state["muac_status"] = status

    arm_val = st.session_state.get("arm_val")
    muac_status = st.session_state.get("muac_status")

    if arm_val is not None and muac_status is not None:
        st.markdown(f"**Saved MUAC:** {arm_val} cm &nbsp;&nbsp;|&nbsp;&nbsp; **Status:** {muac_status}")

    st.markdown("""
        <style>
            .stButton > button {
                width: 100%;
                border-radius: 10px;
                padding: 0.5em;
                margin-bottom: 0.5em;
                font-weight: 500;
            }
        </style>
    """, unsafe_allow_html=True)

    if st.button("⬅️ Back"):
        st.session_state.page = "height"
        st.experimental_rerun()

    if st.button("Continue"):
        st.session_state["arm_value"] = arm_val
        st.session_state.page = "done"
        st.experimental_rerun()


def done_step():
    st.title("✅ Summary")

    entry = {
        "Name": st.session_state.child_name,
        "Age": st.session_state.child_age,
        "Weight (kg)": st.session_state.child_weight,
        "Height (cm)": st.session_state.height_result,
        "Arm Circumference (MUAC, cm)": st.session_state.arm_value,
    }
    entry["BMI"] = calculate_bmi(entry["Weight (kg)"], entry["Height (cm)"])
    entry["Malnutrition Status"] = calculate_malnutrition_status(entry["BMI"], entry["Arm Circumference (MUAC, cm)"])

    data = load_nutrition_data()
    if any(d["Name"] == entry["Name"] and d["Age"] == entry["Age"] for d in data):
        st.warning("Duplicate detected. Entry was not saved.")
    else:
        data.append(entry)
        save_nutrition_data(data)
        st.success("Saved!")

    st.markdown("### 📌 New Entry")
    st.table(pd.DataFrame([entry]))

    st.info(f"Data saved in: `{get_nutrition_file()}`")

    st.markdown("### 📋 All Previous Entries")
    all_data = load_nutrition_data()
    if all_data:
        st.dataframe(pd.DataFrame(all_data), use_container_width=True)
    else:
        st.info("No previous entries yet.")

    back_button()
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("🔒 Logout"): logout()
    with col2: 
        if st.button("🏠 Back to Menu"): st.session_state.page = "nutrition_choices"


def view_old_data_step():
    st.title("🗑 Delete Previous Data")
    data = load_nutrition_data()
    if not data:
        st.info("No data to delete.")
        if st.button("⬅️ Back"):
            st.session_state.page = "nutrition_choices"
        return

    names = [f"{d['Name']} (Age: {d['Age']})" for d in data]
    choice = st.selectbox("Select record to delete", options=names)

    if st.button("Delete Selected"):
        idx = names.index(choice)
        data.pop(idx)
        save_nutrition_data(data)
        st.success("Deleted.")

    if st.button("⬅️ Back"):
        st.session_state.page = "nutrition_choices"

def view_data_table_step():
    st.title("📊 All Saved Nutrition Data")
    data = load_nutrition_data()
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No data saved yet.")

    if st.button("⬅️ Back"):
        st.session_state.page = "nutrition_choices"

# NutriMann flow
def nutrimann_choices_step():
    st.title("🍽 Food Nutrient Scanner")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ New Food Scan"): st.session_state.page = "nutrimann_info"
    with col2:
        if st.button("🗑 Delete Food Records"): st.session_state.page = "view_old_food"
    back_button()

def nutrimann_info_step():
    st.title("🍽 Food Scan Info")
    st.session_state.food_name = st.text_input("Food Name")
    st.session_state.food_quantity = st.number_input("Quantity (grams)", min_value=0)
    back_button()
    if st.button("Scan Nutrients"):
        st.session_state.page = "food_only"

def food_only_step():
    st.title("🔍 Scanning Food Nutrients")
    result = run_food_scanner()
    if result:
        data = load_food_data()
        entry = {
            "Food": st.session_state.food_name,
            "Quantity (g)": st.session_state.food_quantity,
            "Scanned Nutrients": result,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        data.append(entry)
        save_food_data(data)
        st.success("Food scan saved!")
        st.table(pd.DataFrame([entry]))
    back_button()
    if st.button("Continue to Summary"): st.session_state.page = "food_summary"

def food_summary_step():
    st.title("📋 Food Scan Summary")
    data = load_food_data()
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No food data found.")
    if st.button("⬅️ Back"):
        st.session_state.page = "nutrimann_choices"

def view_old_food_step():
    st.title("🗑 Delete Previous Food Scans")
    data = load_food_data()
    if not data:
        st.info("No food records to delete.")
        if st.button("⬅️ Back"):
            st.session_state.page = "nutrimann_choices"
        return

    names = [f"{d['Food']} ({d['Date']})" for d in data]
    choice = st.selectbox("Select food scan to delete", options=names)

    if st.button("Delete Selected"):
        idx = names.index(choice)
        data.pop(idx)
        save_food_data(data)
        st.success("Deleted.")

    if st.button("⬅️ Back"):
        st.session_state.page = "nutrimann_choices"

# ROUTER
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.page = "login"
    if "username" not in st.session_state:
        st.session_state.username = ""

    if not st.session_state.logged_in:
        st.sidebar.title("User Access")
        auth_option = st.sidebar.selectbox("Choose option", ["Login", "Sign Up"])
        if auth_option == "Login":
            login()
        else:
            signup()
        return

    # Main app flow routing
    page = st.session_state.page
    if page == "select_flow": select_flow_step()
    elif page == "nutrition_choices": nutrition_choices_step()
    elif page == "child_info": child_info_step()
    elif page == "height": height_step()
    elif page == "arm": arm_step()
    elif page == "done": done_step()
    elif page == "view_old_data": view_old_data_step()
    elif page == "view_data_table": view_data_table_step()
    elif page == "nutrimann_choices": nutrimann_choices_step()
    elif page == "nutrimann_info": nutrimann_info_step()
    elif page == "food_only": food_only_step()
    elif page == "food_summary": food_summary_step()
    elif page == "view_old_food": view_old_food_step()
    else:
        st.error(f"Unknown page: {page}")

if __name__ == "__main__":
    main()
