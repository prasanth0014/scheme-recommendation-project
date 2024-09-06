import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import os
from twilio.rest import Client

# Twilio credentials
TWILIO_ACCOUNT_SID = ''
TWILIO_AUTH_TOKEN = ''
TWILIO_PHONE_NUMBER = ''

# File paths
USER_PROFILES_FILE = 'user_profiles.csv'
SCHEMES_FILE = 'ds1.csv'


# Initialize files if they don't exist
def initialize_files():
    if not os.path.isfile(USER_PROFILES_FILE):
        pd.DataFrame(columns=['username', 'email', 'gender', 'state', 'student', 'married']).to_csv(USER_PROFILES_FILE,
                                                                                                    index=False)
    if not os.path.isfile(SCHEMES_FILE):
        pd.DataFrame(
            columns=['NAME', 'STATE', 'GENDER', 'START AGE', 'END AGE', 'INCOME', 'STUDENT', 'MARRIED']).to_csv(
            SCHEMES_FILE, index=False)


initialize_files()

# Temporary dictionaries to store user credentials
user_db = {'user': 'pass'}
admin_credentials = {'admin': 'admin123'}
user_interactions = []  # To track user interactions

# Set page config
st.set_page_config(page_title="GovSchemes", page_icon="🏛️", layout="wide")

# Custom CSS to improve the interface
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    .stSelectbox>div>div>input {
        border-radius: 5px;
    }
    .main {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    h1, h2, h3 {
        color: #0e1117;
    }
    .stAlert > div {
        padding: 10px 16px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


def sign_up():
    st.header("🖊️ Sign Up")
    with st.form("signup_form"):
        username = st.text_input("Choose a Username:", key="sign_up_username", help="Enter a username for your account")
        password = st.text_input("Choose a Password:", type="password", key="sign_up_password",
                                 help="Enter a password for your account")
        confirm_password = st.text_input("Confirm Password:", type="password", key="confirm_password",
                                         help="Re-enter your password for confirmation")
        submit_button = st.form_submit_button("Sign Up")

        if submit_button:
            if username in user_db:
                st.error("Username already taken. Choose another.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                user_db[username] = password
                # Initialize user profile
                pd.DataFrame([[username, '', '', '', '']],
                             columns=['username', 'gender', 'state', 'student', 'married']).to_csv(USER_PROFILES_FILE,
                                                                                                   mode='a',
                                                                                                   header=False,
                                                                                                   index=False)
                st.success("You have successfully signed up! Please log in.")
                st.session_state["page"] = "login"


twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_sms(to_phone_number, message_body):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        return True
    except Exception as e:
        print(f"Failed to send SMS. Error: {e}")
        return False


def login():
    st.header("🔐 Login")

    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username:", key="login_username", help="Enter your username")
        password = st.text_input("Password:", type="password", key="login_password", help="Enter your password")

        if st.button("🚪 Login", key="login_button"):
            if username in user_db and user_db[username] == password:
                st.success("You have successfully logged in!")
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["page"] = "recommendation"
            else:
                st.error("Invalid username or password")

    with col2:
        st.write("New user?")
        if st.button("📝 Sign Up", key="signup_button"):
            st.session_state["page"] = "sign_up"

        st.write("Admin?")
        if st.button("👑 Admin Login", key="admin_button"):
            if username in admin_credentials and admin_credentials[username] == password:
                st.success("Admin login successful!")
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["page"] = "admin_dashboard"
            else:
                st.error("Invalid admin credentials")


def manage_profile():
    st.header("👤 Manage Profile")
    st.write("Update your profile preferences here.")

    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("Email:", key="profile_email", help="Enter your email address")
        gender = st.selectbox("Preferred Gender:", ["any", "male", "female"], key="profile_gender")
        state = st.text_input("Preferred State:", key="profile_state", help="Enter your preferred state").lower()
    with col2:
        student = st.selectbox("Student Status:", ["any", "yes", "no"], key="profile_student")
        married = st.selectbox("Marital Status:", ["any", "yes", "no"], key="profile_married")

    if st.button("💾 Save Profile", key="save_profile"):
        profile_data = {
            'username': st.session_state["username"],
            'email': email,
            'gender': gender,
            'state': state,
            'student': student,
            'married': married
        }

        # Check if the CSV file exists and read it
        if os.path.isfile(USER_PROFILES_FILE):
            df = pd.read_csv(USER_PROFILES_FILE)
            # Check if the user profile already exists and update or append accordingly
            if profile_data['username'] in df['username'].values:
                df.loc[df['username'] == profile_data['username'], ['email', 'gender', 'state', 'student', 'married']] = \
                    profile_data['email'], profile_data['gender'], profile_data['state'], profile_data['student'], \
                        profile_data['married']
            else:
                # Create DataFrame for new profile and concatenate
                new_profile_df = pd.DataFrame([profile_data])
                df = pd.concat([df, new_profile_df], ignore_index=True)
        else:
            # Create a new DataFrame if file does not exist
            df = pd.DataFrame([profile_data])

        df.to_csv(USER_PROFILES_FILE, index=False)
        st.success("Profile updated successfully!")

    # Add a Back button to return to the recommendation page
    if st.button("🔙 Back", key="back_to_recommendation"):
        st.session_state["page"] = "recommendation"


def recommendation_page():
    st.title("🏛️ Government Scheme Recommendation System")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col3:
        st.write(f"Welcome, {st.session_state['username']}!")
        if st.button("👤 Manage Profile", key="manage_profile"):
            st.session_state["page"] = "manage_profile"
        if st.button("🚪 Logout", key="logout"):
            st.session_state["logged_in"] = False
            st.session_state["page"] = "login"

    with st.form("recommendation_form"):
        st.subheader("📋 Enter Your Details")
        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("Select Gender:", ["any", "male", "female"])
            age = st.number_input("Enter Age:", min_value=0, max_value=100, value=25)
            state = st.text_input("Enter State:").lower()
        with col2:
            income = st.number_input("Enter Annual Income:", min_value=0, value=0)
            student = st.selectbox("Are you a student?", ["any", "yes", "no"])
            married = st.selectbox("Marital Status:", ["any", "yes", "no"])

        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("🔍 Find Schemes")
        with col2:
            view_all_button = st.form_submit_button("📊 View All Schemes")

    if submit_button:
        user_input = {
            'gender': gender,
            'age': age,
            'state': state,
            'income': income,
            'student': student,
            'married': married
        }

        # Load and update user profile preferences
        df_profiles = pd.read_csv(USER_PROFILES_FILE)
        profile_preferences = df_profiles[df_profiles['username'] == st.session_state["username"]].iloc[0].to_dict()
        for key in profile_preferences:
            if profile_preferences[key] != 'any' and key in user_input:
                user_input[key] = profile_preferences[key]

        df = load_data(SCHEMES_FILE)
        recommendations = recommend_schemes(user_input, df)

        if not recommendations.empty:
            st.success("Schemes you are eligible for:")
            st.dataframe(recommendations.style.highlight_max(axis=0))
        else:
            st.warning("No schemes found matching your criteria.")

        # Log user interaction
        user_interactions.append({
            'username': st.session_state["username"],
            'action': 'find_schemes',
            'details': user_input,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    if view_all_button:
        df = load_data(SCHEMES_FILE)
        st.subheader("📚 All Available Schemes")
        st.dataframe(df[['NAME', 'STATE', 'GENDER', 'START AGE', 'END AGE', 'INCOME', 'STUDENT', 'MARRIED']])

    if st.button("🔙 Back", key="back_recommendation"):
        st.session_state["page"] = "login"


# Email settings
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'praveenproject521@gmail.com'
SENDER_PASSWORD = 'Welcome@123'


def send_email(to_email, scheme_name):
    subject = 'New Government Scheme Added'
    body = (f'Hello,\n\nA new government scheme "{scheme_name}" has been added that may interest you.\n\nBest regards,'
            f'\nYour Scheme Recommendation System')

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            text = msg.as_string()
            server.sendmail(SENDER_EMAIL, to_email, text)
    except Exception as e:
        st.error(f"Failed to send email to {to_email}. Error: {e}")


def add_new_scheme(scheme_name, scheme_state, gender, start_age, end_age, income, student_status, marital_status):
    # Load existing schemes
    df_schemes = pd.read_csv('ds1.csv')

    # Create new scheme entry
    new_scheme = pd.DataFrame([{
        'NAME': scheme_name,
        'STATE': scheme_state.lower(),
        'GENDER': gender,
        'START AGE': start_age,
        'END AGE': end_age,
        'INCOME': income,
        'STUDENT': student_status,
        'MARRIED': marital_status
    }])

    # Append new scheme to the existing schemes
    df_schemes = pd.concat([df_schemes, new_scheme], ignore_index=True)
    df_schemes.to_csv('ds1.csv', index=False)

    # Load user profiles to notify them
    df_profiles = pd.read_csv('user_profiles.csv')

    # Notify users who match the new scheme criteria
    for _, profile in df_profiles.iterrows():
        #if (profile['gender'].lower() == gender.lower() and
               # profile['state'].lower() == scheme_state.lower() and
              #  int(profile['start_age']) <= start_age <= int(profile['end_age']) and
               # (profile['student'] == student_status) and
               # (profile['married'] == marital_status)):
            # Send SMS notification
        message_body = (f"Hello {profile['username']}, a new scheme '{scheme_name}' has been added "
                            f"that might be of interest to you. Check it out!")
        send_sms(profile['phone'], message_body)

        print("Scheme added and notifications sent.")


# Admin Dashboard Function
def admin_dashboard():
    st.title("Admin Dashboard")

    tab1, tab2, tab3 = st.tabs(["Add New Scheme", "User Profiles", "User Interactions"])

    with tab1:
        st.header("Add New Scheme")

        with st.form(key='scheme_form'):
            scheme_name = st.text_input("Scheme Name")
            scheme_state = st.text_input("State")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            start_age = st.number_input("Start Age", min_value=0)
            end_age = st.number_input("End Age", min_value=0)
            income = st.text_input("Income")
            student_status = st.selectbox("Student", ["Yes", "No"])
            marital_status = st.selectbox("Married", ["Yes", "No"])

            submit_button = st.form_submit_button("Add Scheme")

            if submit_button:
                if all([scheme_name, scheme_state]):
                    add_new_scheme(
                        scheme_name=scheme_name,
                        scheme_state=scheme_state,
                        gender=gender,
                        start_age=start_age,
                        end_age=end_age,
                        income=income,
                        student_status=student_status,
                        marital_status=marital_status
                    )
                    st.success("New scheme added and notifications sent!")
                else:
                    st.error("Please fill out all required fields.")

    with tab2:
        st.header("User Profiles")
        df_profiles = pd.read_csv('user_profiles.csv')
        st.write(df_profiles)

    with tab3:
        st.header("User Interactions")
        st.write("Here you can manage user interactions.")


# Run the application

def load_data(filepath):
    df = pd.read_csv(filepath)
    df['GENDER'] = df['GENDER'].str.lower()
    df['STATE'] = df['STATE'].str.lower()
    df['STUDENT'] = df['STUDENT'].str.lower()
    df['MARRIED'] = df['MARRIED'].str.lower()
    return df


def recommend_schemes(user_input, df):
    filtered_df = df.copy()
    filtered_df = filtered_df[(filtered_df['GENDER'] == user_input['gender']) | (filtered_df['GENDER'] == 'any')]
    filtered_df = filtered_df[
        (filtered_df['START AGE'] <= user_input['age']) & (filtered_df['END AGE'] >= user_input['age'])]
    filtered_df = filtered_df[(filtered_df['STATE'] == user_input['state']) | (filtered_df['STATE'] == 'central')]
    filtered_df = filtered_df[(filtered_df['INCOME'] == 0) | (filtered_df['INCOME'] >= user_input['income'])]
    filtered_df = filtered_df[(filtered_df['STUDENT'] == user_input['student']) | (filtered_df['STUDENT'] == 'any')]
    filtered_df = filtered_df[(filtered_df['MARRIED'] == user_input['married']) | (filtered_df['MARRIED'] == 'any')]
    return filtered_df[['NAME', 'STATE']]


def main():
    if "page" not in st.session_state:
        st.session_state["page"] = "login"

    if st.session_state["page"] == "login":
        login()
    elif st.session_state["page"] == "sign_up":
        sign_up()
    elif st.session_state["page"] == "recommendation" and st.session_state.get("logged_in"):
        recommendation_page()
    elif st.session_state["page"] == "manage_profile" and st.session_state.get("logged_in"):
        manage_profile()
    elif st.session_state["page"] == "admin_dashboard" and st.session_state.get("logged_in"):
        admin_dashboard()
    else:
        st.session_state["page"] = "login"


if __name__ == "__main__":
    main()
