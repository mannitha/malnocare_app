import streamlit as st
from datetime import date, datetime
import json, os
import pandas as pd
import streamlit.components.v1 as components
from foodscan_module import run_food_scanner
from physical_module import run_physical_attr


# App configuration
st.set_page_config(page_title="MalnoCare", layout="wide")

# Custom CSS styling
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
    .section {
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .critical {
        color: #ff4b4b;
        font-weight: bold;
    }
    .warning {
        color: #ffa500;
        font-weight: bold;
    }
    .success {
        color: #28a745;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Meta and favicon
components.html("""
    <link rel="apple-touch-icon" sizes="180x180" href="https://raw.githubusercontent.com/mannitha/food_scanner_app/main/favicon.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black">
    <meta name="apple-mobile-web-app-title" content="My App">
""", height=0)

# Data handling functions
USER_DATA_FILE = "users.json"
def get_nutrition_file(): return f"nutrition_data_{st.session_state.username}.json"
def get_food_file(): return f"food_data_{st.session_state.username}.json"

def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

def load_nutrition_data():
    file = get_nutrition_file()
    try:
        if os.path.exists(file):
            with open(file, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except:
        pass
    return []

def save_nutrition_data(data):
    with open(get_nutrition_file(), 'w') as f:
        json.dump(data, f, indent=2)

def load_food_data():
    file = get_food_file()
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return []

def save_food_data(data):
    with open(get_food_file(), 'w') as f:
        json.dump(data, f, indent=2)

# Authentication functions
def signup():
    st.title("Sign Up")
    with st.form("signup_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        e = st.text_input("Email")
        if st.form_submit_button("Create Account"):
            users = load_users()
            if u in users:
                st.error("Username already exists.")
            else:
                users[u] = {"password": p, "email": e}
                save_users(users)
                st.success("Account created! Please login.")

def login():
    st.title("Login")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            users = load_users()
            if u not in users:
                st.error("Username doesn't exist.")
            elif users[u]["password"] != p:
                st.error("Incorrect password.")
            else:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.page = "select_flow"
                st.rerun()

def logout():
    st.session_state.clear()
    st.rerun()

# Utility functions
def back_button():
    if st.button("⬅️ Back"):
        nav = {
            "nutrition_choices": "select_flow",
            "nutrimann_choices": "select_flow",
            "physical_assessment": "nutrition_choices",
            "view_old_data": "nutrition_choices",
            "view_data_table": "nutrition_choices",
            "view_old_food": "nutrimann_choices",
            "edit_food_entry": "view_old_food",
            "nutrimann_info": "nutrimann_choices",
            "food_only": "nutrimann_info",
            "food_summary": "food_only"
        }
        st.session_state.page = nav.get(st.session_state.page, "select_flow")
        st.rerun()

def calculate_bmi(w, h):
    return round(w / ((h / 100) ** 2), 2) if w and h else None

def calculate_age(dob):
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def calculate_malnutrition_status(bmi, arm):
    if bmi is None or arm is None:
        return "Unknown"
    if bmi < 13 or arm < 11.5:
        return "Severe Acute Malnutrition"
    elif bmi < 14 or arm < 12.5:
        return "Moderate Acute Malnutrition"
    return "Normal"

def get_bmi_classification(bmi):
    if bmi is None:
        return "N/A", "unknown"
    if bmi < 16:
        return "Severe Thinness", "critical"
    elif bmi < 17:
        return "Moderate Thinness", "warning"
    elif bmi < 18.5:
        return "Mild Thinness", "warning"
    elif bmi < 25:
        return "Normal", "success"
    elif bmi < 30:
        return "Overweight", "warning"
    else:
        return "Obese", "critical"

# Main application pages
def select_flow_step():
    st.title("Select Assessment Type")
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("Food Nutrients Scan", use_container_width=True):
            st.session_state.page = "nutrition_choices"
    with col2: 
        if st.button("Physical Assessment", use_container_width=True):
            st.session_state.page = "physical_assessment"

def nutrition_choices_step():
    st.title("Food Nutrients Scan")
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("➕ New Food Scan", use_container_width=True):
            st.session_state.page = "nutrimann_choices"
    with col2: 
        if st.button("📂 Previous Scan Reports", use_container_width=True):
            st.session_state.page = "view_old_food"
    back_button()

def physical_assessment_step():
    st.title("📋 Comprehensive Physical Assessment")
    
    with st.form("physical_assessment_form"):
        # Personal Information Section
        st.subheader("Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", key="child_name")
            dob = st.date_input("Date of Birth", min_value=date(1900, 1, 1), 
                              max_value=date.today(), key="child_dob")
            age = calculate_age(dob)
            st.write(f"**Age:** {age} years")
        with col2:
            gender = st.radio("Gender", ["Male", "Female"], key="child_gender", horizontal=True)
            weight = st.number_input("Weight (kg)", min_value=0.0, 
                                   format="%.2f", key="child_weight", step=0.1)
        
        # Height Measurement Section
        st.subheader("Height Measurement")
        height_method = st.radio("Measurement Method", 
                                ["Manual Entry", "Height Estimator"], 
                                key="height_method", horizontal=True)
        
        if st.button("Run Height Estimator"):
            estimated_height = run_height_estimator()
            if estimated_height:
                st.session_state.height_result = estimated_height
                st.success(f"Estimated height: {estimated_height} cm")
        
        # Arm Measurement Section
        st.subheader("Arm Circumference (MUAC)")
        arm_method = st.radio("MUAC Measurement Method", 
                            ["Manual Entry", "MUAC Estimator"], 
                            key="arm_method", horizontal=True)
        
        if arm_method == "Manual Entry":
            arm_value = st.number_input("Arm Circumference (cm)", 
                                      min_value=0.0, format="%.2f", 
                                      key="arm_value", step=0.1)
        else:
            if st.button("Run MUAC Estimator"):
                arm_val, muac_status = run_muac()
                if arm_val:
                    st.session_state.arm_value = arm_val
                    st.session_state.muac_status = muac_status
                    st.success(f"MUAC: {arm_val} cm - Status: {muac_status}")
        
        # Submit button for the entire form
        submitted = st.form_submit_button("Generate Assessment Report")
        
        if submitted:
            # Validate required fields
            required_fields = ['child_name', 'child_dob', 'child_weight']
            if not all(st.session_state.get(field) for field in required_fields):
                st.error("Please complete all required fields (Name, Date of Birth, Weight)")
            elif not st.session_state.get('height_result'):
                st.error("Please complete height measurement")
            elif not st.session_state.get('arm_value'):
                st.error("Please complete arm circumference measurement")
            else:
                # Calculate assessment metrics
                bmi = calculate_bmi(st.session_state.child_weight, st.session_state.height_result)
                malnutrition_status = calculate_malnutrition_status(bmi, st.session_state.arm_value)
                bmi_class, bmi_class_type = get_bmi_classification(bmi)
                
                # Compile assessment data
                assessment_data = {
                    "Name": st.session_state.child_name,
                    "Date of Birth": st.session_state.child_dob.strftime("%Y-%m-%d"),
                    "Age": calculate_age(st.session_state.child_dob),
                    "Gender": st.session_state.child_gender,
                    "Weight (kg)": st.session_state.child_weight,
                    "Height (cm)": st.session_state.height_result,
                    "Arm Circumference (cm)": st.session_state.arm_value,
                    "BMI": bmi,
                    "BMI Classification": bmi_class,
                    "Malnutrition Status": malnutrition_status,
                    "Assessment Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Save the assessment
                data = load_nutrition_data()
                data.append(assessment_data)
                save_nutrition_data(data)
                
                # Display the report
                st.session_state.assessment_data = assessment_data
                st.session_state.page = "assessment_report"
                st.rerun()
    back_button()

def assessment_report_step():
    st.title("Nutrition Assessment Report")
    
    if 'assessment_data' not in st.session_state:
        st.error("No assessment data found. Please complete an assessment first.")
        st.session_state.page = "physical_assessment"
        st.rerun()
    
    data = st.session_state.assessment_data
    
    # Report header
    st.subheader(f"Assessment for {data['Name']}")
    st.write(f"**Date:** {data['Assessment Date']}")
    
    # Display in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Personal Information")
        st.markdown(f"""
        - **Date of Birth:** {data['Date of Birth']}
        - **Age:** {data['Age']} years
        - **Gender:** {data['Gender']}
        """)
        
        st.markdown("### Physical Measurements")
        st.markdown(f"""
        - **Weight:** {data['Weight (kg)']} kg
        - **Height:** {data['Height (cm)']} cm
        - **Arm Circumference:** {data['Arm Circumference (cm)']} cm
        """)
    
    with col2:
        st.markdown("### Nutritional Assessment")
        
        # BMI display
        bmi_class_style = get_bmi_classification(data['BMI'])[1]
        st.markdown(f"""
        - **BMI:** <span class="{bmi_class_style}">{data['BMI']:.1f}</span>
        - **BMI Classification:** <span class="{bmi_class_style}">{data['BMI Classification']}</span>
        """, unsafe_allow_html=True)
        
        # Malnutrition status
        malnutrition_style = "success"
        if "Severe" in data['Malnutrition Status']:
            malnutrition_style = "critical"
        elif "Moderate" in data['Malnutrition Status']:
            malnutrition_style = "warning"
            
        st.markdown(f"""
        - **Malnutrition Status:** <span class="{malnutrition_style}">{data['Malnutrition Status']}</span>
        """, unsafe_allow_html=True)
        
        # Recommendations
        st.markdown("### Recommendations")
        if malnutrition_style == "critical":
            st.error("""
            **Immediate intervention required:**  
            - Refer to healthcare provider immediately  
            - Nutritional supplementation needed  
            - Close monitoring required  
            """)
        elif malnutrition_style == "warning":
            st.warning("""
            **Nutritional support recommended:**  
            - Dietary counseling advised  
            - Regular monitoring suggested  
            - Consider nutritional supplements  
            """)
        else:
            st.success("""
            **Normal nutritional status:**  
            - Maintain balanced diet  
            - Continue regular check-ups  
            - Monitor growth patterns  
            """)
    back_button()
    
    # Navigation buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Print Report", use_container_width=True):
            st.warning("Print functionality would be implemented in a production app")
    with col2:
        if st.button("New Assessment", use_container_width=True):
            st.session_state.page = "physical_assessment"
            st.rerun()
    with col3:
        if st.button("Back to Menu", use_container_width=True):
            st.session_state.page = "nutrition_choices"
            st.rerun()

# [Rest of your existing food-related functions remain unchanged]
def nutrimann_choices_step():
    st.title("Food Nutrients Scan")
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("➕ Food Scan", use_container_width=True): 
            st.session_state.page = "nutrimann_info"
    with col2: 
        if st.button("📂 View Food Reports", use_container_width=True): 
            st.session_state.page = "view_old_food"
    back_button()

def nutrimann_info_step():
    st.title("Enter Meal Details")
    st.session_state.food_name = st.text_input("Name")
    st.session_state.food_time = st.selectbox("Meal Time", ["Breakfast", "Lunch", "Dinner", "Snack", "Other"])
    if st.button("Continue"): 
        st.session_state.page = "food_only"
    back_button()

def food_only_step():
    st.title("Scan Food")
    run_food_scanner()
    if st.button("Show Summary"):
        if "food_result" in st.session_state:
            st.session_state.page = "food_summary"
        else: 
            st.error("Please scan the food first.")
    back_button()

def food_summary_step():
    st.title("Food Summary")
    name = st.session_state.food_name
    time = st.session_state.food_time
    result = st.session_state.get("food_result", pd.DataFrame())
    st.subheader(f"{name} — {time}")
    st.table(result)
    data = load_food_data()
    if any(d["Name"] == name and d["Meal Timing"] == time for d in data): 
        st.warning("Duplicate scan exists!")
    else:
        data.append({"Name": name, "Meal Timing": time, "Nutrition Table": result.to_dict()})
        save_food_data(data)
        st.success("Saved!")
    if st.button("Back to Menu"): 
        st.session_state.page = "nutrimann_choices"
    back_button()

def view_old_food_step():
    st.title("Food Reports")
    data = load_food_data()
    if not data:
        st.info("No records")
        return
    idx = st.selectbox("Select", range(len(data)), format_func=lambda i: f"{data[i]['Name']} - {data[i]['Meal Timing']}")
    entry = data[idx]
    st.table(pd.DataFrame(entry["Nutrition Table"]))
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Edit"):
            st.session_state.edit_index = idx
            st.session_state.page = "edit_food_entry"
    with col2:
        if st.button("Delete"):
            del data[idx]
            save_food_data(data)
            st.success("Deleted!")
            st.rerun()
    back_button()

def edit_food_entry_step():
    st.title("Edit Food Entry")
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

def view_old_data_step():
    st.title("Previous Assessments")
    data = load_nutrition_data()
    if not data:
        st.info("No records found.")
        return
    back_button()
    
    df = pd.DataFrame(data)
    
    # Sort by date (newest first)
    if 'Assessment Date' in df.columns:
        df['Assessment Date'] = pd.to_datetime(df['Assessment Date'])
        df = df.sort_values('Assessment Date', ascending=False)
    
    st.dataframe(df, use_container_width=True)
    
    # Option to delete records
    st.subheader("Delete Records")
    if not df.empty:
        record_to_delete = st.selectbox(
            "Select record to delete",
            options=df.index,
            format_func=lambda x: f"{df.loc[x, 'Name']} - {df.loc[x, 'Assessment Date']}"
        )
        
        if st.button("Delete Selected Record", type="primary"):
            df = df.drop(record_to_delete).reset_index(drop=True)
            save_nutrition_data(df.to_dict('records'))
            st.success("Record deleted successfully!")
            st.rerun()

def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "page" not in st.session_state:
        st.session_state.page = "login"
    
    if st.session_state.logged_in:
        st.sidebar.title(f"👤 {st.session_state.username}")
        st.sidebar.button("Logout", on_click=logout)
        
        # Page routing
        if st.session_state.page == "login":
            login()
        elif st.session_state.page == "select_flow":
            select_flow_step()
        elif st.session_state.page == "nutrition_choices":
            nutrition_choices_step()
        elif st.session_state.page == "physical_assessment":
            physical_assessment_step()
        elif st.session_state.page == "assessment_report":
            assessment_report_step()
        elif st.session_state.page == "view_old_data":
            view_old_data_step()
        elif st.session_state.page == "nutrimann_choices":
            nutrimann_choices_step()
        elif st.session_state.page == "nutrimann_info":
            nutrimann_info_step()
        elif st.session_state.page == "food_only":
            food_only_step()
        elif st.session_state.page == "food_summary":
            food_summary_step()
        elif st.session_state.page == "view_old_food":
            view_old_food_step()
        elif st.session_state.page == "edit_food_entry":
            edit_food_entry_step()
    else:
        st.sidebar.title("Account")
        option = st.sidebar.selectbox("Login or Signup", ["Login", "Sign Up"])
        if option == "Login":
            login()
        else:
            signup()

if __name__ == "__main__":
    main()