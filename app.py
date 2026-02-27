import streamlit as st
import pandas as pd
import os
from streamlit_chat import message  # Chat interface

# -----------------------
# COLORFUL BACKGROUND
# -----------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to right, #c2e9fb, #a1c4fd);
        color: #1f2937;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #667eea, #764ba2);
        color: #ffffff;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #1f2937;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------
# LOAD DATASETS
# -----------------------
try:
    workout_df = pd.read_csv("workout_dataset_500.csv")
    diet_df = pd.read_csv("diet_dataset_500.csv")
except Exception as e:
    st.error(f"Error loading datasets: {e}")

# -----------------------
# SIDEBAR USER INPUT
# -----------------------
st.sidebar.title("📝 User Input")
age = st.sidebar.number_input("Age", 10, 80)
gender = st.sidebar.selectbox("Gender", ["Male", "Female"])
height = st.sidebar.number_input("Height (cm)", 120, 220)
weight = st.sidebar.number_input("Weight (kg)", 30, 150)
activity = st.sidebar.selectbox("Activity Level", ["Sedentary", "Light", "Moderate", "Active"])
goal = st.sidebar.selectbox("Goal", ["Weight Loss", "Muscle Gain", "Maintenance"])
diet_type = st.sidebar.selectbox("Diet Type", ["Veg", "Non-Veg", "Vegan"])

# -----------------------
# CALORIE & BMI CALCULATION
# -----------------------
if gender == "Male":
    bmr = 10*weight + 6.25*height - 5*age + 5
else:
    bmr = 10*weight + 6.25*height - 5*age - 161

activity_factors = {"Sedentary":1.2, "Light":1.375, "Moderate":1.55, "Active":1.725}
calories = bmr * activity_factors[activity]

if goal == "Weight Loss":
    calories -= 500
elif goal == "Muscle Gain":
    calories += 300

height_m = height / 100
bmi = weight / (height_m**2)
protein_target = weight*1.6 if goal=="Muscle Gain" else weight*1.0

# -----------------------
# METRICS CARDS
# -----------------------
st.subheader("📊 Health Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Calories (kcal)", f"{int(calories)}")
col2.metric("BMI", f"{round(bmi,2)}")
col3.metric("Protein (g/day)", f"{int(protein_target)}")

if bmi < 18.5:
    st.write("BMI Category: Underweight")
elif bmi < 24.9:
    st.write("BMI Category: Normal")
else:
    st.write("BMI Category: Overweight")

# -----------------------
# TABS: Workouts & Diet
# -----------------------
tab1, tab2 = st.tabs(["🏋️ Workouts", "🥗 Diet"])

# --- Workouts Tab with Logging ---
with tab1:
    st.subheader("Recommended Workouts")
    filtered_workouts = workout_df[workout_df["goal"] == goal]

    if "calories_burned" in filtered_workouts.columns:
        filtered_workouts = filtered_workouts.sort_values(by="calories_burned", ascending=False)

    # Create a daily log file for workouts
    workout_log_file = "workout_log.csv"
    if os.path.exists(workout_log_file):
        workout_log_df = pd.read_csv(workout_log_file)
    else:
        workout_log_df = pd.DataFrame(columns=["exercise_name", "completed"])

    completed_count = 0  # To count checked workouts

    # Show checkboxes and store completion
    for index, row in filtered_workouts.head(5).iterrows():
        is_done = st.checkbox(
            f"{row['exercise_name']} ({row['duration_minutes']} min, {row['calories_burned']} kcal)", 
            key=f"workout_{index}"
        )
        if is_done:
            completed_count += 1
            # Add to log if not already logged
            if not ((workout_log_df["exercise_name"] == row['exercise_name']) & (workout_log_df["completed"] == True)).any():
                workout_log_df = pd.concat([workout_log_df, pd.DataFrame([{"exercise_name": row['exercise_name'], "completed": True}])], ignore_index=True)

    # Save the log
    workout_log_df.to_csv(workout_log_file, index=False)

    # Show daily completion stats
    st.info(f"✅ You completed {completed_count}/{min(5, len(filtered_workouts))} workouts today!")

    # Celebrate if all workouts are done
    if completed_count == min(5, len(filtered_workouts)) and completed_count > 0:
        st.balloons()

# --- Diet Tab ---
with tab2:
    st.subheader("Recommended Diet")
    filtered_diet = diet_df[(diet_df["goal"] == goal) & (diet_df["diet_type"] == diet_type)]

    if "calories" in filtered_diet.columns:
        filtered_diet = filtered_diet[filtered_diet["calories"] <= calories/3]
    if "protein_g" in filtered_diet.columns:
        filtered_diet = filtered_diet.sort_values(by="protein_g", ascending=False)

    st.dataframe(filtered_diet.head(5))

# -----------------------
# WEEKLY PROGRESS TRACKER
# -----------------------
st.subheader("📈 Weekly Progress Tracker")
weekly_weight = st.number_input("Enter Current Weight", 30.0, 200.0, step=0.1)

progress_file = "progress.csv"
if os.path.exists(progress_file):
    progress_df = pd.read_csv(progress_file)
else:
    progress_df = pd.DataFrame(columns=["week", "weight"])

if st.button("Track Progress"):
    week_num = len(progress_df) + 1
    new_row = pd.DataFrame([{"week": week_num, "weight": weekly_weight}])
    progress_df = pd.concat([progress_df, new_row], ignore_index=True)
    progress_df.to_csv(progress_file, index=False)

    diff = weight - weekly_weight
    if diff > 0:
        st.success(f"You lost {round(diff,2)} kg! 🎉")
    elif diff < 0:
        st.info(f"You gained {round(abs(diff),2)} kg.")
    else:
        st.warning("No change in weight.")

    # Show line chart
    st.line_chart(progress_df.set_index("week")["weight"])

    # Celebrate logging weight
    st.balloons()

# -----------------------
# SIMPLE RULE-BASED CHATBOT
# -----------------------
st.subheader("💬 Fitness Assistant Chatbot")
user_input = st.text_input("Ask your Fitness Assistant:")

if user_input:
    user_lower = user_input.lower()
    if "workout" in user_lower:
        answer = "🏋️ Try push-ups, squats, lunges, and jogging for your goal."
    elif "diet" in user_lower or "meal" in user_lower:
        answer = "🥗 Eat high protein, low sugar meals, and include vegetables & whole grains."
    elif "bmi" in user_lower:
        answer = f"Your BMI is {round(bmi,2)}. Normal: 18.5-24.9"
    elif "protein" in user_lower:
        answer = f"Your daily protein target is {int(protein_target)} g/day."
    else:
        answer = "I can help with workouts, diet suggestions, BMI & protein info!"
    
    message(user_input, is_user=True)
    message(answer, is_user=False)