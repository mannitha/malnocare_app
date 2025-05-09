import streamlit as st
from PIL import Image
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

def food_scanner():
    def get_nutrition_response(image, prompt):
        try:
            response = model.generate_content([image, prompt])
            return response.text
        except Exception as e:
            st.error(f"⚠ Error: {e}")
            return None

    # Custom CSS with centered buttons, styled header, and rounded image
    st.markdown("""
    <style>
        /* Main header style */
        .big-header {
            font-size: 36px !important;
            font-weight: bold !important;
            text-align: center !important;
            margin-bottom: 20px !important;
            color: #2c3e50 !important;
        }
        
        /* Rounded image styling */
        .rounded-image {
            display: block;
            margin-left: auto;
            margin-right: auto;
            border-radius: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            width: 100%;
            max-width: 600px;
            height: auto;
            margin-bottom: 25px;
        }

        /* Centered container for buttons */
        .button-container {
            display: flex;
            justify-content: center;
            margin: 20px 0;
        }

        /* Upload Image button (green) */
        .upload-button button {
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
            padding: 12px 28px !important;
            font-size: 18px !important;
            cursor: pointer !important;
            border-radius: 8px !important;
            min-width: 220px;
            margin: 0 auto !important;
            transition: all 0.3s ease !important;
        }

        .upload-button button:hover {
            background-color: #45a049 !important;
            transform: scale(1.05) !important;
        }

        /* Get Nutrition button (blue) */
        .nutrition-button button {
            background-color: #1889cb !important;
            color: white !important;
            border: none !important;
            padding: 12px 28px !important;
            font-size: 18px !important;
            cursor: pointer !important;
            border-radius: 8px !important;
            min-width: 220px;
            margin: 0 auto !important;
            transition: all 0.3s ease !important;
        }

        .nutrition-button button:hover {
            background-color: #1578b0 !important;
            transform: scale(1.05) !important;
        }
        
        /* Table styling to prevent header repetition */
        .stDataFrame {
            width: 100%;
        }
        
        thead tr th:first-child {
            display:none;
        }
        
        .stDataFrame thead tr {
            position: sticky;
            top: 0;
            background-color: white;
            z-index: 100;
        }
    </style>
    """, unsafe_allow_html=True)

    # Main header with custom styling
    st.markdown('<div class="big-header">Food Nutrition Scan</div>', unsafe_allow_html=True)

    # Initialize session state
    if 'show_uploader' not in st.session_state:
        st.session_state.show_uploader = False
    if 'uploaded_image' not in st.session_state:
        st.session_state.uploaded_image = None

    # Upload Image button (green) - Centered
    with st.container():
        st.markdown('<div class="button-container"><div class="upload-button">', unsafe_allow_html=True)
        upload_clicked = st.button("Upload Image", key="upload_button")
        st.markdown('</div></div>', unsafe_allow_html=True)

    if upload_clicked:
        st.session_state.show_uploader = True

    # Show file uploader only if button clicked
    if st.session_state.show_uploader:
        uploaded_file = st.file_uploader("Take a photo of your food", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            st.success("Image uploaded successfully!")
            st.session_state.uploaded_image = image

    # Show Get Nutrition Quantity button only if image uploaded
    if st.session_state.uploaded_image is not None:
        with st.container():
            st.markdown('<div class="button-container"><div class="nutrition-button">', unsafe_allow_html=True)
            get_nutrition_clicked = st.button("Get Nutrition Quantity", key="nutrition_button")
            st.markdown('</div></div>', unsafe_allow_html=True)

        if get_nutrition_clicked:
            nutrition_prompt = """
            Analyze the uploaded image and extract detailed nutritional information for each food item detected, including the quantity of each item.
            Provide a structured output with the following format:

            Food Item | Quantity | Calories (kcal) | Protein (g) | Carbs (g) | Fats (g) | Vitamins & Minerals
            -----------|----------|----------------|-------------|-----------|---------|---------------------
            """

            response = get_nutrition_response(st.session_state.uploaded_image, nutrition_prompt)

            if response:
                # Split the response into lines
                lines = response.strip().split("\n")
                
                # Define expected columns
                expected_columns = ["Food Item", "Quantity", "Calories (kcal)", "Protein (g)", "Carbs (g)", "Fats (g)", "Vitamins & Minerals"]
                
                # Clean lines: remove all header-like rows and separator lines
                clean_lines = []
                header_keywords = ["Food Item", "Quantity", "Calories", "Protein", "Carbs", "Fats", "Vitamins", "Minerals"]
                
                for line in lines:
                    # Skip empty lines or separator lines
                    if not line.strip() or set(line.strip()).issubset(set('-| ')):
                        continue
                    
                    # Skip lines that contain header keywords
                    if any(keyword in line for keyword in header_keywords):
                        continue
                    
                    # Only process lines that contain pipe characters (table rows)
                    if '|' in line:
                        clean_lines.append(line)
                
                # Process the remaining lines
                if clean_lines:
                    # Split into rows and clean data
                    data = []
                    for line in clean_lines:
                        parts = [p.strip() for p in line.split('|')]
                        # Ensure we have at least the main columns (Food Item through Carbs)
                        if len(parts) >= 5:
                            # Pad with empty strings if needed
                            while len(parts) < len(expected_columns):
                                parts.append("")
                            data.append(parts[:len(expected_columns)])
                    
                    if data:
                        # Create DataFrame
                        df = pd.DataFrame(data, columns=expected_columns)
                        df.index = df.index + 1  # Start index at 1
                        
                        # Display using st.dataframe with fixed header
                        st.subheader("Nutrition Analysis:")
                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=False,
                            column_config={col: st.column_config.TextColumn(col) for col in expected_columns}
                        )
                        
                        st.session_state.food_result = df
                    else:
                        st.error("⚠ Could not parse nutritional data from response.")
                else:
                    st.error("⚠ No valid data found in the response.")
            else:
                st.error("⚠ Could not retrieve nutritional data. Try again or check the image quality.")

#if __name__ == "__main__":
#    food_scanner()