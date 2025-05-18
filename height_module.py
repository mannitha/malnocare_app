# height_module.py
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import mediapipe as mp
from streamlit_image_coordinates import streamlit_image_coordinates

mp_pose = mp.solutions.pose

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

def run_height_estimator():
    st.markdown("Upload a full-body image **with a visible reference object**, and specify its real-world length.")
    img_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])

    if img_file:
        image = Image.open(img_file).convert("RGB")
        img_np = np.array(image)
        image_copy = img_np.copy()

        reference_length = st.number_input("Enter the real-world length of the reference object (in cm)", min_value=1.0, step=0.5)

        st.subheader("Step 1: Click two points on the reference object")

        if "points" not in st.session_state:
            st.session_state.points = []

        for i, (x, y) in enumerate(st.session_state.points):
            cv2.circle(image_copy, (x, y), 8, (0, 0, 255), -1)
            cv2.putText(image_copy, f"P{i+1}", (x+10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        coords = streamlit_image_coordinates(Image.fromarray(image_copy), key="click_img")

        if coords and len(st.session_state.points) < 2:
            st.session_state.points.append((int(coords['x']), int(coords['y'])))

        if st.button("🔄 Reset Points"):
            st.session_state.points = []

        if len(st.session_state.points) == 2:
            x1, y1 = st.session_state.points[0]
            x2, y2 = st.session_state.points[1]
            pixel_dist = get_pixel_distance((x1, y1), (x2, y2))
            calibration_factor = reference_length / pixel_dist
            st.success(f"Calibration: {calibration_factor:.4f} cm/pixel")

            st.subheader("Step 2: Estimating height from landmarks")
            image_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            head_y, foot_y = detect_keypoints(image_bgr)

            if head_y is not None and foot_y is not None:
                pixel_height = abs(foot_y - head_y)
                estimated_height = calibration_factor * pixel_height
                annotated_img = draw_landmarks(image_bgr, head_y, foot_y)
                st.image(annotated_img, caption="Estimated Height", channels="BGR")
                st.success(f"Estimated Height: **{estimated_height:.2f} cm**")
                return round(estimated_height, 2)
            else:
                st.error("❌ Could not detect landmarks. Try another image.")
    return None
