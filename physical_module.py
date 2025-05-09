import streamlit as st
import cv2
import numpy as np
from PIL import Image
import mediapipe as mp
from streamlit_image_coordinates import streamlit_image_coordinates
from datetime import datetime, date
import pandas as pd

mp_pose = mp.solutions.pose

# --- Custom CSS ---
st.markdown("""
<style>
    /* Green upload button */
    div.stButton > button:first-child {
        background-color: #69AE43;
        color: white;
        border: none;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    }

    div.stButton > button:first-child:hover {
        background-color: #45a049;
    }

    .nutrition-header {
        font-size: 18px !important;
        margin-bottom: 10px !important;
    }

    /* Extra button styles */
    .green-button {
        background-color: #69ae43 !important;
    }

    .blue-button {
        background-color: #1889cb !important;
    }
</style>
""", unsafe_allow_html=True)

# --- MUAC Calibration Factors ---
MUAC_CALIBRATION_FACTORS = {
    '4-6': 0.085,   # Calibration for 4-6 years old
    '7-9': 0.088,   # Calibration for 7-9 years old
    '10-12': 0.092, # Calibration for 10-12 years old
    '13-15': 0.096  # Calibration for 13-15 years old
}

def detect_keypoints(image):
    with mp_pose.Pose(static_image_mode=True) as pose:
        results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if results.pose_landmarks:
            h, w, _ = image.shape
            landmarks = results.pose_landmarks.landmark
            head_y = int(landmarks[mp_pose.PoseLandmark.NOSE].y * h)
            foot_left_y = int(landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y * h)
            foot_right_y = int(landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y * h)
            foot_y = max(foot_left_y, foot_right_y)
            return head_y, foot_y
    return None, None

def draw_landmarks(image, head_y, foot_y):
    annotated = image.copy()
    center_x = image.shape[1] // 2
    cv2.line(annotated, (center_x, head_y), (center_x, foot_y), (0, 255, 0), 2)
    cv2.circle(annotated, (center_x, head_y), 5, (255, 0, 0), -1)
    cv2.circle(annotated, (center_x, foot_y), 5, (0, 0, 255), -1)
    return annotated

def get_pixel_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def load_image(uploaded_file):
    img = Image.open(uploaded_file)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def calculate_age(dob):
    today = date.today()
    age_years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    age_months = (today.year - dob.year) * 12 + today.month - dob.month
    if today.day < dob.day:
        age_months -= 1
    return age_years, age_months

def calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)

def get_malnutrition_status(bmi, age_years, gender):
    if age_years < 5:
        if bmi < 14: return "Severely Underweight"
        elif bmi < 16: return "Underweight"
        elif bmi < 18: return "Normal weight"
        else: return "Overweight"
    elif age_years < 10:
        if bmi < 15: return "Severely Underweight"
        elif bmi < 17: return "Underweight"
        elif bmi < 20: return "Normal weight"
        else: return "Overweight"
    else:  # 10-15 years
        if gender == "Male":
            if bmi < 16: return "Severely Underweight"
            elif bmi < 18.5: return "Underweight"
            elif bmi < 25: return "Normal weight"
            else: return "Overweight"
        else:  # Female
            if bmi < 15.5: return "Severely Underweight"
            elif bmi < 18: return "Underweight"
            elif bmi < 24: return "Normal weight"
            else: return "Overweight"

def detect_arm_keypoints(image):
    with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
        results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if results.pose_landmarks:
            h, w, _ = image.shape
            landmarks = results.pose_landmarks.landmark
            
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
            
            left_shoulder_point = (int(left_shoulder.x * w), int(left_shoulder.y * h))
            left_elbow_point = (int(left_elbow.x * w), int(left_elbow.y * h))
            right_shoulder_point = (int(right_shoulder.x * w), int(right_shoulder.y * h))
            right_elbow_point = (int(right_elbow.x * w), int(right_elbow.y * h))
            
            return left_shoulder_point, left_elbow_point, right_shoulder_point, right_elbow_point
    return None, None, None, None

def draw_arm_landmarks(image, shoulder_point, elbow_point):
    annotated = image.copy()
    cv2.line(annotated, shoulder_point, elbow_point, (0, 255, 0), 3)
    cv2.circle(annotated, shoulder_point, 8, (255, 0, 0), -1)
    cv2.circle(annotated, elbow_point, 8, (0, 0, 255), -1)
    return annotated

def classify_muac(muac_cm, age_group):
    if age_group in ['4-6', '7-9']:
        if muac_cm < 12.5:
            return "Acute Malnutrition", "red"
        elif muac_cm < 13.5:
            return "Risk of Malnutrition", "orange"
        else:
            return "Normal Nutrition Status", "green"
    else:  # 10-15 years
        if muac_cm < 13.5:
            return "Acute Malnutrition", "red"
        elif muac_cm < 14.5:
            return "Risk of Malnutrition", "orange"
        else:
            return "Normal Nutrition Status", "green"

def get_age_group(age_years):
    if age_years <= 6:
        return '4-6'
    elif age_years <= 9:
        return '7-9'
    elif age_years <= 12:
        return '10-12'
    else:
        return '13-15'

def run_physical_attr():
    st.title("Child Growth Assessment")

    # Personal Information Section
    st.header("Child Information")
    
    name = st.text_input("Full Name")
    dob = st.date_input("Date of Birth", 
        min_value=date.today() - pd.DateOffset(years=15),
        max_value=date.today() - pd.DateOffset(years=4))
    age_years, age_months = calculate_age(dob)
    st.write(f"Age: {age_years} years and {age_months % 12} months")
    if age_years < 4 or age_years > 15:
        st.error("This tool is only for children between 4-15 years old")
        return None
    gender = st.selectbox("Gender", ["Male", "Female"])
    weight = st.number_input("Weight (kg)", min_value=10.0, max_value=100.0, step=0.1)
    
    # Initialize session state variables
    if "input_mode" not in st.session_state:
        st.session_state.input_mode = None
    if "points" not in st.session_state:
        st.session_state.points = []
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "muac_image" not in st.session_state:
        st.session_state.muac_image = None

    # Height Measurement Section
    st.markdown("### Height Measurement")
    if st.button("Upload Image for Height Measurement", use_container_width=True, key="height_upload"):
        st.session_state.input_mode = "height"
        st.session_state.points = []

    if st.session_state.input_mode == "height":
        uploaded_file = st.file_uploader(
            "Upload a full-body image with a visible reference object", 
            type=["jpg", "jpeg", "png"],
            key="height_file_uploader"
        )
        
        if uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            image = load_image(uploaded_file)
            img_np = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image_copy = img_np.copy()

            st.image(image_copy, caption="Uploaded Image", use_column_width=True)

            reference_length = st.number_input(
                "Enter the real-world length of the reference object (in cm)", 
                min_value=1.0, 
                step=0.5,
                key="ref_length"
            )

            st.markdown("**Click two points on the reference object**")

            for i, (x, y) in enumerate(st.session_state.points):
                cv2.circle(image_copy, (x, y), 8, (0, 0, 255), -1)
                cv2.putText(image_copy, f"P{i+1}", (x+10, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            coords = streamlit_image_coordinates(
                Image.fromarray(image_copy), 
                key="click_img"
            )

            if coords and len(st.session_state.points) < 2:
                st.session_state.points.append((int(coords['x']), int(coords['y'])))
                st.rerun()

            if st.button("Reset Points", key="reset_height_points"):
                st.session_state.points = []
                st.rerun()

            if len(st.session_state.points) == 2 and reference_length > 0:
                x1, y1 = st.session_state.points[0]
                x2, y2 = st.session_state.points[1]
                pixel_dist = get_pixel_distance((x1, y1), (x2, y2))
                calibration_factor = reference_length / pixel_dist
                st.success(f"Calibration: {calibration_factor:.4f} cm/pixel")

                head_y, foot_y = detect_keypoints(image)
                
                if head_y is not None and foot_y is not None:
                    pixel_height = abs(foot_y - head_y)
                    estimated_height = calibration_factor * pixel_height
                    annotated_img = draw_landmarks(image, head_y, foot_y)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(annotated_img, caption="Height Measurement", channels="BGR")
                    with col2:
                        st.metric("Estimated Height", f"{estimated_height:.2f} cm")
                    
                    bmi = calculate_bmi(weight, estimated_height)
                    malnutrition_status = get_malnutrition_status(bmi, age_years, gender)
                    
                    st.subheader("BMI Assessment")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("BMI", f"{bmi:.1f}")
                    with col2:
                        st.metric("BMI Category", malnutrition_status)
                    with col3:
                        st.metric("Weight Status", malnutrition_status)
                    
                    # MUAC Measurement Section
                    st.markdown("MUAC Measurement")
                    
                    if st.button("Upload Image", use_container_width=True, key="muac_upload"):
                        st.session_state.input_mode = "muac"
                    
                    if st.session_state.input_mode == "muac":
                        muac_file = st.file_uploader(
                            "Upload an image of the child's arm (shoulder to elbow visible)", 
                            type=["jpg", "jpeg", "png"],
                            key="muac_file_uploader"
                        )
                        
                        if muac_file:
                            st.session_state.muac_image = muac_file
                            muac_img = load_image(muac_file)
                            
                            age_group = get_age_group(age_years)
                            left_shoulder, left_elbow, right_shoulder, right_elbow = detect_arm_keypoints(muac_img)
                            
                            shoulder_point, elbow_point = None, None
                            if left_shoulder and left_elbow:
                                shoulder_point, elbow_point = left_shoulder, left_elbow
                            elif right_shoulder and right_elbow:
                                shoulder_point, elbow_point = right_shoulder, right_elbow

                            if shoulder_point and elbow_point:
                                pixel_distance = np.linalg.norm(np.array(shoulder_point) - np.array(elbow_point))
                                annotated_muac_image = draw_arm_landmarks(muac_img, shoulder_point, elbow_point)
                                st.image(annotated_muac_image, caption="Detected Shoulder and Elbow Points", use_column_width=True)

                                cal_factor = MUAC_CALIBRATION_FACTORS[age_group]
                                estimated_muac = cal_factor * pixel_distance
                                
                                st.success(f"Estimated MUAC: {estimated_muac:.2f} cm")
                                muac_status, color = classify_muac(estimated_muac, age_group)
                                st.markdown(f'<div class="nutrition-header"> MUAC Status: 'f'<span style="color: {color};">{muac_status}</span></div>', unsafe_allow_html=True)
                                
                                # Final Comprehensive Report
                                st.subheader("Comprehensive Growth Assessment")
                                summary_data = {
                                    "Name": [name],
                                    "Age": [f"{age_years}y {age_months % 12}m"],
                                    "Gender": [gender],
                                    "Weight (kg)": [weight],
                                    "Height (cm)": [round(estimated_height, 2)],
                                    "BMI": [round(bmi, 1)],
                                    "BMI Status": [malnutrition_status],
                                    "MUAC (cm)": [round(estimated_muac, 2)],
                                    "MUAC Status": [muac_status]
                                }
                                st.dataframe(pd.DataFrame(summary_data), hide_index=True)
                                
                                return {
                                    "height": round(estimated_height, 2),
                                    "bmi": round(bmi, 1),
                                    "muac": round(estimated_muac, 2),
                                    "bmi_status": malnutrition_status,
                                    "muac_status": muac_status
                                }
                            else:
                                st.error("Could not detect arm landmarks. Please ensure the arm is clearly visible.")
                else:
                    st.error("Could not detect body landmarks. Try another image with clear full-body view.")
    return None

#if __name__ == "__main__":
#   run_physical_attr()