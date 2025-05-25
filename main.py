import streamlit as st
from datetime import datetime
from PIL import Image
from auth import signup_user, login_user, logout_user, get_user_profile, update_user_profile
from db import init_db, delete_user_data, log_chat_message, get_chat_history_from_db
from streamlit_option_menu import option_menu

# Import tab functions
from tabs.tab_home import show_home_tab
from tabs.tab_calendar import show_calendar_tab
from tabs.tab_hormones import show_hormones_tab
from tabs.tab_insights import show_insights_tab
from tabs.tab_chat import show_chat_tab

init_db()

st.set_page_config(page_title="MyRitu", page_icon="🌸", layout="wide", initial_sidebar_state="collapsed")

PINK_TEXT_COLOR = "#E57396"

# --- Session State Initialization ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_view' not in st.session_state: st.session_state.current_view = "login"
if 'initial_profile_setup_required' not in st.session_state: st.session_state.initial_profile_setup_required = False # This flag is still useful
if 'chat_messages_display' not in st.session_state: st.session_state.chat_messages_display = []


# --- Profile Settings Page Function ---
# CORRECTED DEFINITION: Add is_initial_setup parameter
def show_settings_page_section(user_id, is_initial_setup=False):
    profile_data = get_user_profile(user_id)
    
    if is_initial_setup:
        st.markdown(f"<h2 style='color: {PINK_TEXT_COLOR};'>🌸 Complete Your MyRitu Profile 🌸</h2>", unsafe_allow_html=True)
        st.info("Welcome! Please provide some initial details to personalize your experience. This helps MyRitu understand your needs better.")
    else:
        st.markdown(f"<h2 style='color: {PINK_TEXT_COLOR};'>⚙️ MyRitu Settings ⚙️</h2>", unsafe_allow_html=True)
        st.subheader("👤 Profile Information")

    # The expander for editing profile is only relevant if NOT initial setup,
    # or if you want the form directly visible during initial setup.
    # Let's make the form directly visible for initial_setup, and in expander otherwise.

    if not is_initial_setup:
        with st.expander("Edit Your Profile", expanded=True): # Start expanded for easier access
            render_profile_form(user_id, profile_data, is_initial_setup)
    else: # Directly render form for initial setup
        render_profile_form(user_id, profile_data, is_initial_setup)

    if not is_initial_setup: # Account actions only if not initial setup
        st.subheader("🔒 Account Actions")
        if st.button("🚪 Log Out", key="settings_logout"):
            if 'chat_messages_display' in st.session_state:
                del st.session_state['chat_messages_display']
            logout_user()

        st.markdown("---")
        st.subheader("⚠️ Danger Zone")
        st.warning("Deleting your account will permanently erase all your data from this application. This action cannot be undone.")
        if st.checkbox("I understand and wish to proceed with deleting my account and all data.", key="confirm_delete_check_settings"):
            if st.button("Permanently Delete My Account & Data", type="primary", key="confirm_delete_button_settings", help="This is irreversible!"):
                success, message = delete_user_data(user_id)
                if success:
                    st.success(message + " You have been logged out.")
                    logout_user()
                else:
                    st.error(message)
        
        st.markdown("---")
        if st.button("Back to App Dashboard", key="settings_back_to_app_btn"):
            st.session_state.current_view = "app_home"
            st.rerun()

# --- Helper function to render the profile form ---
def render_profile_form(user_id, profile_data, is_initial_setup):
    with st.form("profile_form_main_settings"): # Unique key for the form
        # ... (Full profile form fields: full_name, birth_date, avg_Ritu_length, etc. as before)
        st.subheader("General Information")
        full_name = st.text_input("Full Name", value=profile_data.get('full_name', ''), key="profile_full_name")
        birth_date_val = profile_data.get('birth_date')
        birth_date_dt = None
        if birth_date_val:
            try: birth_date_dt = datetime.strptime(birth_date_val, '%Y-%m-%d').date()
            except ValueError: pass
        birth_date = st.date_input("Birth Date", value=birth_date_dt, min_value=datetime(1920,1,1).date(), max_value=datetime.now().date(), key="profile_birth_date")
        
        st.subheader("Ritu & Period Details")
        avg_Ritu_length = st.number_input("Average Ritu (Cycle) Length (days)", min_value=15, max_value=90, value=profile_data.get('avg_Ritu_length', 28), key="profile_avg_ritu")
        avg_period_length = st.number_input("Average Period Length (days)", min_value=1, max_value=15, value=profile_data.get('avg_period_length', 5), key="profile_avg_period")
        
        last_period_val = profile_data.get('last_period_start')
        last_period_start_dt = None
        if last_period_val:
            try: last_period_start_dt = datetime.strptime(last_period_val, '%Y-%m-%d').date()
            except ValueError: pass
        last_period_start = st.date_input("First Day of Your Last Menstrual Period", value=last_period_start_dt, max_value=datetime.now().date(), help="Leave blank if not applicable.", key="profile_last_period")
        
        st.subheader("Health & Lifestyle")
        life_stage_options = ["Select...", "Puberty/Adolescence", "Reproductive Years", "Perimenopause", "Menopause", "Post-menopause"]
        current_life_stage = profile_data.get('life_stage', 'Select...')
        life_stage = st.selectbox("Current Life Stage (Optional)", options=life_stage_options, 
                                  index=life_stage_options.index(current_life_stage) if current_life_stage in life_stage_options else 0, key="profile_life_stage")
        medical_conditions = st.text_area("Known Medical Conditions", value=profile_data.get('medical_conditions', ''), height=100, key="profile_med_conditions")
        medications = st.text_area("Current Medications or Supplements", value=profile_data.get('medications', ''), height=100, key="profile_medications")
        preferences = st.text_area("Any specific concerns or preferences?", value=profile_data.get('preferences', ''), height=100, key="profile_preferences")

        form_submit_label = "Save Profile" if is_initial_setup else "Save Profile Changes"
        submitted = st.form_submit_button(form_submit_label)

        if submitted:
            updated_data = {
                'full_name': full_name, 'birth_date': birth_date.strftime('%Y-%m-%d') if birth_date else None,
                'avg_Ritu_length': avg_Ritu_length, 'avg_period_length': avg_period_length,
                'last_period_start': last_period_start.strftime('%Y-%m-%d') if last_period_start else None,
                'medical_conditions': medical_conditions, 'medications': medications,
                'preferences': preferences, 'life_stage': life_stage if life_stage != "Select..." else None
            }
            success, message = update_user_profile(user_id, updated_data) # Use user_id passed to render_profile_form
            if success:
                st.success(message)
                st.session_state.profile_info = get_user_profile(user_id)
                if is_initial_setup:
                    st.session_state.initial_profile_setup_required = False # Mark as done
                st.session_state.current_view = "app_home" # Go to main app view
                st.rerun()
            else:
                st.error(message)

# --- Initial Profile Setup Page ---
def show_initial_profile_setup(user_id):
    # This function now correctly calls show_settings_page_section
    show_settings_page_section(user_id, is_initial_setup=True)


# --- Main App Logic ---
if not st.session_state.logged_in:
    # ... (Login/Signup UI as before) ...
    st.markdown("<br><br>", unsafe_allow_html=True)
    login_cols = st.columns([1, 1.5, 1])
    with login_cols[1]:
        try:
            logo = Image.open("assets/logo.png")
            st.image(logo, width=150, use_column_width='auto')
        except FileNotFoundError:
            st.markdown(f"<h1 style='text-align: center; color: {PINK_TEXT_COLOR};'>MyRitu 🌸</h1>", unsafe_allow_html=True)

        st.markdown("<p style='text-align: center; font-size: 1.2em;'>Track your Ritu, understand your body.</p>", unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.current_view == "signup":
            st.subheader("Create New Account")
            with st.form("signup_form_main_v3"):
                new_username = st.text_input("Username", key="signup_username")
                new_email = st.text_input("Email (Optional)", key="signup_email")
                new_password = st.text_input("Password", type="password", key="signup_pass1")
                confirm_password = st.text_input("Confirm Password", type="password", key="signup_pass2")
                signup_button = st.form_submit_button("Sign Up")
                if signup_button:
                    if new_password == confirm_password:
                        if new_username and new_password:
                            success, message = signup_user(new_username, new_password, new_email)
                            if success:
                                st.success(message + " Please log in.")
                                st.session_state.current_view = "login"
                                st.rerun()
                            else: st.error(message)
                        else: st.error("Username and Password cannot be empty.")
                    else: st.error("Passwords do not match.")
            if st.button("Already have an account? Log In", key="signup_to_login_btn"):
                st.session_state.current_view = "login"
                st.rerun()
        else: 
            st.session_state.current_view = "login"
            st.subheader("Welcome Back! Log In")
            with st.form("login_form_main_v3"):
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                login_button = st.form_submit_button("Log In")
                if login_button:
                    success, message = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.profile_info = get_user_profile(st.session_state.user_id)
                        profile = st.session_state.profile_info
                        if not profile.get('avg_Ritu_length') or not profile.get('birth_date'):
                            st.session_state.initial_profile_setup_required = True # Flag still useful
                            st.session_state.current_view = "initial_profile_setup"
                        else:
                            st.session_state.initial_profile_setup_required = False
                            st.session_state.current_view = "app_home" # Go to home after login if profile is complete
                        st.rerun()
                    else: st.error(message)
            st.markdown("---")
            st.write("Don't have an account?")
            if st.button("Sign Up Here", key="login_to_signup_btn"):
                st.session_state.current_view = "signup"
                st.rerun()

elif st.session_state.current_view == "initial_profile_setup": # This is the view that was causing the error
    show_initial_profile_setup(st.session_state.user_id)
elif st.session_state.current_view == "settings":
    show_settings_page_section(st.session_state.user_id, is_initial_setup=False) # Explicitly False
else: # Main app view (app_home, app_calendar, etc.)
    # --- Horizontal Navigation Menu ---
    menu_options = ["🏠 Home", "🗓️ Calendar", "🧬 Hormones", "📊 Insights", "💬 RituChat", "⚙️ Settings"]
    icons = ['house', 'calendar3', 'heart-pulse', 'graph-up', 'chat-dots', 'gear-fill']
    
    # Determine default index based on current_view
    # Ensure current_view maps to one of the menu_options or "Settings"
    current_menu_option_label = "🏠 Home" # Default
    if st.session_state.current_view == "app_home": current_menu_option_label = "🏠 Home"
    elif st.session_state.current_view == "app_calendar": current_menu_option_label = "🗓️ Calendar"
    elif st.session_state.current_view == "app_hormones": current_menu_option_label = "🧬 Hormones"
    elif st.session_state.current_view == "app_insights": current_menu_option_label = "📊 Insights"
    elif st.session_state.current_view == "app_rituchat": current_menu_option_label = "💬 RituChat"
    # Note: "settings" view is handled by the elif above, so menu should reflect last app tab

    try:
        default_idx = menu_options.index(current_menu_option_label)
    except ValueError:
        default_idx = 0 

    selected = option_menu(
        menu_title=None, options=menu_options, icons=icons,
        default_index=default_idx, orientation="horizontal",
        key="main_horizontal_menu_v3", # New key
        styles={
            "container": {"padding": "3px 0px", "background-color": "transparent", "border-bottom": "1px solid #ddd"},
            "icon": {"color": PINK_TEXT_COLOR, "font-size": "18px"}, 
            "nav-link": {"font-size": "14px", "text-align": "center", "margin":"0px 3px", "--hover-color": "#f0f2f6"},
            "nav-link-selected": {"background-color": PINK_TEXT_COLOR, "color": "white", "font-weight": "600"},
        }
    )

    # Logic to update current_view based on menu selection and re-run if changed
    new_view = st.session_state.current_view # Assume no change initially
    if selected == "🏠 Home": new_view = "app_home"
    elif selected == "🗓️ Calendar": new_view = "app_calendar"
    elif selected == "🧬 Hormones": new_view = "app_hormones"
    elif selected == "📊 Insights": new_view = "app_insights"
    elif selected == "💬 RituChat": new_view = "app_rituchat"
    elif selected == "⚙️ Settings": new_view = "settings" # This will trigger the settings page display

    if st.session_state.current_view != new_view:
        st.session_state.current_view = new_view
        st.rerun() # Rerun only if the view actually changed

    # --- Display content based on current_view ---
    # The settings view is handled by the main 'elif' block for st.session_state.current_view == "settings"
    if st.session_state.current_view == "app_home": show_home_tab()
    elif st.session_state.current_view == "app_calendar": show_calendar_tab()
    elif st.session_state.current_view == "app_hormones": show_hormones_tab()
    elif st.session_state.current_view == "app_insights": show_insights_tab()
    elif st.session_state.current_view == "app_rituchat": show_chat_tab()