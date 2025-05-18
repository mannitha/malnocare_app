# muac_module.py
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import mediapipe as mp
from streamlit_image_coordinates import streamlit_image_coordinates

mp_pose = mp.solutions.pose

def load_image(uploaded_file):
    img = Image.open(uploaded_file)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

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

def draw_landmarks(image, p1, p2):
    annotated = image.copy()
    cv2.circle(annotated, p1, 8, (255, 0, 0), -1)
    cv2.circle(annotated, p2, 8, (0, 0, 255), -1)
    cv2.line(annotated, p1, p2, (0, 255, 0), 2)
    return annotated

def get_pixel_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def classify_muac(muac_cm):
    if muac_cm < 12.5:
        return "Severe Acute Malnutrition", "red"
    elif muac_cm < 13.5:
        return "Moderate Acute Malnutrition", "orange"
    else:
        return "Normal Nutrition Status", "green"

def run_muac_estimator():
    st.title("MUAC Measurement Tool")

    if "points" not in st.session_state:
        st.session_state.points = []
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

    uploaded_file = st.file_uploader(
        "Upload an image showing the arm with a visible reference object", 
        type=["jpg", "jpeg", "png"]
    )
    
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        image = load_image(uploaded_file)
        img_np = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_copy = img_np.copy()

        reference_length = st.number_input(
            "Enter the real-world length of the reference object (in cm)", 
            min_value=1.0, 
            step=0.5
        )

        st.markdown("**Click two points on the reference object**")

        # Draw existing points
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

        if st.button("Reset Points"):
            st.session_state.points = []

        if len(st.session_state.points) == 2 and reference_length > 0:
            x1, y1 = st.session_state.points[0]
            x2, y2 = st.session_state.points[1]
            pixel_dist = get_pixel_distance((x1, y1), (x2, y2))
            calibration_factor = reference_length / pixel_dist
            st.success(f"Calibration: {calibration_factor:.4f} cm/pixel")

            # Detect arm keypoints
            l_shoulder, l_elbow, r_shoulder, r_elbow = detect_arm_keypoints(image)

            # Use whichever arm is clearer
            shoulder_point, elbow_point = None, None
            if l_shoulder and l_elbow:
                shoulder_point, elbow_point = l_shoulder, l_elbow
            elif r_shoulder and r_elbow:
                shoulder_point, elbow_point = r_shoulder, r_elbow

            if shoulder_point and elbow_point:
                pixel_arm_dist = get_pixel_distance(shoulder_point, elbow_point)
                estimated_muac = calibration_factor * pixel_arm_dist

                annotated_image = draw_landmarks(image, shoulder_point, elbow_point)

                col1, col2 = st.columns(2)
                with col1:
                    st.image(annotated_image, caption="Arm Measurement", channels="BGR")
                with col2:
                    st.metric("Estimated MUAC", f"{estimated_muac:.2f} cm")

                status, color = classify_muac(estimated_muac)
                st.markdown(f'<div style="font-size:18px;"> Nutrition Status: <b><span style="color:{color};">{status}</span></b></div>', unsafe_allow_html=True)

                st.info("""
                **Interpretation Guide:**
                - <12.5 cm: Severe Acute Malnutrition
                - 12.5–13.5 cm: Moderate Acute Malnutrition
                - >13.5 cm: Normal Nutrition Status
                """)
                return round(estimated_muac, 2)
            else:
                st.error("Could not detect arm landmarks. Ensure arm visibility (shoulder to elbow) with no obstructions.")
                return None
    return None

if __name__ == "__main__":
    run_muac_estimator()
