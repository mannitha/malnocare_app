import streamlit as st
from supabase import create_client, Client
import uuid

# Supabase setup
SUPABASE_URL = "https://YOUR_SUPABASE_URL.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_API_KEY"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Utility: Check login
def login(username, password):
    result = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
    return len(result.data) > 0

# Utility: Check duplicate nutrition entry
def is_duplicate_nutrition(username, name):
    result = supabase.table("nutrition_data").select("*").eq("username", username).eq("name", name).execute()
    return len(result.data) > 0

# Utility: Check duplicate food scan
def is_duplicate_food(username, name, meal_time):
    result = supabase.table("food_data").select("*").eq("username", username).eq("name", name).eq("meal_time", meal_time).execute()
    return len(result.data) > 0

# Nutrition status logic
def get_status(bmi):
    if bmi < 16:
        return "Severe Malnutrition"
    elif bmi < 17:
        return "Moderate Malnutrition"
    elif bmi < 18.5:
        return "Mild Malnutrition"
    elif bmi < 25:
        return "Normal"
    else:
        return "Overweight"

# Login screen
st.title("Malnutrition Detection App with Supabase")
menu = ["Login", "Sign Up"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Sign Up":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_email = st.text_input("Email")
    new_pass = st.text_input("Password", type='password')

    if st.button("Sign Up"):
        existing = supabase.table("users").select("*").eq("username", new_user).execute()
        if existing.data:
            st.warning("Username already exists!")
        else:
            supabase.table("users").insert({"username": new_user, "email": new_email, "password": new_pass}).execute()
            st.success("Account created! Go to Login.")

elif choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        if login(username, password):
            st.success(f"Welcome {username}!")
            app_mode = st.sidebar.selectbox("Choose Function", ["Nutrition Input", "NutriMann Food Scan", "View Data"])

            if app_mode == "Nutrition Input":
                st.header("Nutrition Entry")
                name = st.text_input("Child Name")
                age = st.number_input("Age", min_value=0)
                weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
                height = st.number_input("Height (cm)", min_value=0.0, step=0.1)
                arm = st.number_input("Arm Circumference (cm)", min_value=0.0, step=0.1)

                if st.button("Submit Nutrition Data"):
                    if is_duplicate_nutrition(username, name):
                        st.warning("Duplicate entry detected for this child.")
                    else:
                        height_m = height / 100
                        bmi = weight / (height_m ** 2)
                        status = get_status(bmi)
                        entry = {
                            "id": str(uuid.uuid4()),
                            "username": username,
                            "name": name,
                            "age": age,
                            "weight": weight,
                            "height": height,
                            "arm": arm,
                            "bmi": round(bmi, 2),
                            "status": status
                        }
                        supabase.table("nutrition_data").insert(entry).execute()
                        st.success("Data saved.")

            elif app_mode == "NutriMann Food Scan":
                st.header("Food Scan Entry")
                name = st.text_input("Child Name for Food Log")
                meal_time = st.selectbox("Meal Time", ["Breakfast", "Lunch", "Dinner", "Snack"])

                st.subheader("Enter Nutritional Info")
                calories = st.number_input("Calories", min_value=0)
                protein = st.number_input("Protein (g)", min_value=0.0)
                fat = st.number_input("Fat (g)", min_value=0.0)
                carbs = st.number_input("Carbs (g)", min_value=0.0)

                if st.button("Submit Food Scan"):
                    if is_duplicate_food(username, name, meal_time):
                        st.warning("Duplicate food scan for this meal.")
                    else:
                        food_entry = {
                            "id": str(uuid.uuid4()),
                            "username": username,
                            "name": name,
                            "meal_time": meal_time,
                            "nutrition_table": {
                                "calories": calories,
                                "protein": protein,
                                "fat": fat,
                                "carbs": carbs
                            }
                        }
                        supabase.table("food_data").insert(food_entry).execute()
                        st.success("Food data saved.")

            elif app_mode == "View Data":
                st.header("Your Child Nutrition Records")
                nutri_data = supabase.table("nutrition_data").select("*").eq("username", username).execute().data
                if nutri_data:
                    st.dataframe(nutri_data)
                else:
                    st.info("No nutrition data available.")

                st.header("Your Food Scan Records")
                food_data = supabase.table("food_data").select("*").eq("username", username).execute().data
                if food_data:
                    st.dataframe(food_data)
                else:
                    st.info("No food data available.")
        else:
            st.error("Incorrect Username or Password")
