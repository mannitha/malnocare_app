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
def load_users():
    if os.path.exists(user_data_file):
        with open(user_data_file, "r") as f:
            return json.load(f)
    return {}

# Save users to JSON file
def save_users(users):
    with open(user_data_file, "w") as f:
        json.dump(users, f, indent=4)
def load_users():
    try:
        if os.path.exists(user_data_file):
            with open(user_data_file, "r") as f:
                return json.load(f)
    except json.JSONDecodeError:
        st.error("User data file is corrupted.")
        return {}
    return {}


def load_nutrition_data():
    file = get_nutrition_file()
    try:
        data = json.load(open(file)) if os.path.exists(file) else []
        return data if isinstance(data, list) else []
    except:
        return []

def save_nutrition_data(data): json.dump(data, open(get_nutrition_file(), "w"), indent=2)
def load_food_data(): return json.load(open(get_food_file())) if os.path.exists(get_food_file()) else []
def save_food_data(data): json.dump(data, open(get_food_file(), "w"), indent=2)
def save_users(users):
    existing = load_users()
    existing.update(users)
    with open(USER_DATA_FILE, "w") as f:
        json.dump(existing, f, indent=2)

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
        st.rerun()

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

    # Run the MUAC estimation logic and capture the result
    muac_value = run_muac_estimator()

    # Store values into session_state if valid
    if muac_value is not None:
        status, _ = classify_muac(muac_value)
        st.session_state["arm_val"] = muac_value
        st.session_state["muac_status"] = status

    # Display saved values
    arm_val = st.session_state.get("arm_val")
    muac_status = st.session_state.get("muac_status")

    if arm_val is not None and muac_status is not None:
        st.markdown(f"**Saved MUAC:** {arm_val} cm &nbsp;&nbsp;|&nbsp;&nbsp; **Status:** {muac_status}")

    # Style buttons using full width and rounded corners
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

    # Back button
    if st.button("⬅️ Back"):
        st.session_state.page = "height"
        st.rerun()

    # Continue button
    if st.button("Continue"):
        st.session_state["arm_value"] = arm_val
        st.session_state.page = "done"
        st.rerun()


def done_step():
    st.title("✅ Summary")

    # Build entry dictionary
    entry = {
        "Name": st.session_state.child_name,
        "Age": st.session_state.child_age,
        "Weight (kg)": st.session_state.child_weight,
        "Height (cm)": st.session_state.height_result,
        "Arm Circumference (MUAC, cm)": st.session_state.arm_value,
    }
    entry["BMI"] = calculate_bmi(entry["Weight (kg)"], entry["Height (cm)"])
    entry["Malnutrition Status"] = calculate_malnutrition_status(entry["BMI"], entry["Arm Circumference (MUAC, cm)"])

    # Load data and save if not duplicate
    data = load_nutrition_data()
    if any(d["Name"] == entry["Name"] and d["Age"] == entry["Age"] for d in data):
        st.warning("Duplicate detected. Entry was not saved.")
    else:
        data.append(entry)
        save_nutrition_data(data)
        st.success("Saved!")

    # Show new entry
    st.markdown("### 📌 New Entry")
    st.table(pd.DataFrame([entry]))

    # Show file location (for debug)
    st.info(f"Data saved in: `{get_nutrition_file()}`")

    # Show all saved entries
    st.markdown("### 📋 All Previous Entries")
    all_data = load_nutrition_data()
    if all_data:
        st.dataframe(pd.DataFrame(all_data), use_container_width=True)
    else:
        st.info("No previous entries yet.")

    # Navigation
    back_button()
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("🔒 Logout"): logout()
    with col2: 
        if st.button("🏠 Back to Menu"): st.session_state.page = "nutrition_choices"


def view_old_data_step():
    st.title("🗑️ Delete Records")
    data = load_nutrition_data()
    if not data:
        st.info("No records.")
        return
    df = pd.DataFrame(data)
    if df.empty:
        st.info("No records.")
        return
    for i, row in df.iterrows():
        with st.expander(f"{row['Name']} - Age {row['Age']}"):
            st.write(row)
            if st.button(f"🗑️ Delete {row['Name']} (Age {row['Age']})", key=f"del_{i}"):
                df = df.drop(index=i).reset_index(drop=True)
                save_nutrition_data(df.to_dict(orient="records"))
                st.success(f"Deleted entry for {row['Name']}")
                st.rerun()
    back_button()

def view_data_table_step():
    st.title("📊 Previous Data Summary")
    data = load_nutrition_data()
    if not data:
        st.info("No records.")
        return
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    back_button()

def nutrimann_choices_step():
    st.title("🍴 Food Nutrients Data")
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("➕ New Food Scan"): st.session_state.page = "nutrimann_info"
    with col2: 
        if st.button("📂 View Old Scans"): st.session_state.page = "view_old_food"
    back_button()

def nutrimann_info_step():
    st.title("🍛 Enter Meal Details")
    st.session_state.food_name = st.text_input("Name")
    st.session_state.food_time = st.selectbox("Meal Time", ["Breakfast", "Lunch", "Dinner", "Snack", "Other"])
    if st.button("Continue"): st.session_state.page = "food_only"
    back_button()

def food_only_step():
    st.title("📸 Scan Food")
    run_food_scanner()
    if st.button("Show Summary"):
        if "food_result" in st.session_state:
            st.session_state.page = "food_summary"
        else: st.error("Please scan the food first.")
    back_button()

def food_summary_step():
    st.title("🥗 Food Summary")
    name = st.session_state.food_name
    time = st.session_state.food_time
    result = st.session_state.get("food_result", pd.DataFrame())
    st.subheader(f"{name} — {time}")
    st.table(result)
    data = load_food_data()
    back_button()
    if any(d["Name"] == name and d["Meal Timing"] == time for d in data): st.warning("Duplicate scan exists!")
    else:
        data.append({"Name": name, "Meal Timing": time, "Nutrition Table": result.to_dict()})
        save_food_data(data)
        st.success("Saved!")
    if st.button("🏠 Back to Menu"): st.session_state.page = "nutrimann_choices"

def view_old_food_step():
    st.title("📂 Old Food Scans")
    data = load_food_data()
    if not data:
        st.info("No records")
        return
    back_button()
    idx = st.selectbox("Select", range(len(data)), format_func=lambda i: f"{data[i]['Name']} - {data[i]['Meal Timing']}")
    entry = data[idx]
    st.table(pd.DataFrame(entry["Nutrition Table"]))
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✏️ Edit"):
            st.session_state.edit_index = idx
            st.session_state.page = "edit_food_entry"
    with col2:
        if st.button("🗑 Delete"):
            del data[idx]
            save_food_data(data)
            st.success("Deleted!")
            st.rerun()

def edit_food_entry_step():
    st.title("📝 Edit Food Entry")
    idx = st.session_state.edit_index
    data = load_food_data()
    entry = data[idx]
    name = st.text_input("Name", entry["Name"])
    time = st.selectbox("Meal Timing", ["Breakfast", "Lunch", "Dinner", "Snack", "Other"],
                        index=["Breakfast", "Lunch", "Dinner", "Snack", "Other"].index(entry["Meal Timing"]))
    df = pd.DataFrame(entry["Nutrition Table"])
    st.table(df)
    if st.button("Save Changes"):
        data[idx]["Name"] = name
        data[idx]["Meal Timing"] = time
        save_food_data(data)
        st.success("Updated!")
        st.session_state.page = "view_old_food"
    back_button()

def main():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if "page" not in st.session_state: st.session_state.page = "login"
    if st.session_state.logged_in:
        st.sidebar.title(f"👤 {st.session_state.username}")
        st.sidebar.button("Logout", on_click=logout)
        match st.session_state.page:
            case "select_flow": select_flow_step()
            case "nutrition_choices": nutrition_choices_step()
            case "view_old_data": view_old_data_step()
            case "view_data_table": view_data_table_step()
            case "child_info": child_info_step()
            case "height": height_step()
            case "arm": arm_step()
            case "done": done_step()
            case "nutrimann_choices": nutrimann_choices_step()
            case "nutrimann_info": nutrimann_info_step()
            case "food_only": food_only_step()
            case "food_summary": food_summary_step()
            case "view_old_food": view_old_food_step()
            case "edit_food_entry": edit_food_entry_step()
    else:
        st.sidebar.title("🔐 Account")
        option = st.sidebar.selectbox("Login or Signup", ["Login", "Sign Up"])
        login() if option == "Login" else signup()

if __name__ == "__main__":
    main()
