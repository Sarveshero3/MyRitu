import streamlit as st
from datetime import datetime # Keep only one import
# from datetime import timedelta # Not directly used here
from utils import calculate_next_period, get_Ritu_phase, format_date, get_hormone_info

PINK_TEXT_COLOR = "#E57396" # Define it here or import from main if centralized

def show_home_tab():
    st.markdown(f"<h1 style='color: {PINK_TEXT_COLOR};'>🌸 Welcome to MyRitu! 🌸</h1>", unsafe_allow_html=True)
    
    if 'username' not in st.session_state or not st.session_state.username:
        st.error("User not identified. Please log in again.")
        return

    st.write(f"Hello, **{st.session_state.username}**! Let's check your Ritu.")

    profile = st.session_state.get('profile_info', {})
    last_period_start = profile.get('last_period_start')
    avg_Ritu_length = profile.get('avg_Ritu_length')
    avg_period_length = profile.get('avg_period_length')

    if not last_period_start or not avg_Ritu_length or not avg_period_length:
        st.warning("Please complete your profile via the '⚙️ Settings' tab to get personalized insights.")
        if st.button("Go to Profile Settings Now"):
            st.session_state.selected_menu_option = "⚙️ Settings" # Navigate via menu state
            st.session_state.current_view = "profile_edit"
            st.rerun()
        return

    today = datetime.now().date()
    next_pred, ovulation_pred, fertile_window_pred = calculate_next_period(last_period_start, avg_Ritu_length)

    st.subheader("Your Ritu At a Glance")
    # ... (rest of the home tab logic as before) ...
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Last Period Started", value=format_date(last_period_start))
        if next_pred:
            next_period_date_obj = datetime.strptime(next_pred, '%Y-%m-%d').date()
            days_to_next_period = (next_period_date_obj - today).days
            if days_to_next_period >=0:
                 st.metric(label="Predicted Next Period In", value=f"{days_to_next_period} days", delta=f"on {format_date(next_pred)}")
            else:
                 st.metric(label="Next Period Was Predicted For", value=format_date(next_pred), help="You might be late, or your Ritu length varied. Please log your new period.")
        else:
            st.write("Next period prediction unavailable.")
    with col2:
        st.metric(label="Average Ritu Length", value=f"{avg_Ritu_length} days")
        st.metric(label="Average Period Length", value=f"{avg_period_length} days")

    st.markdown("---")
    current_phase = get_Ritu_phase(today, last_period_start, avg_period_length, avg_Ritu_length)
    st.subheader(f"Today's Phase: {current_phase}")
    hormone_details = get_hormone_info(current_phase)
    st.write(hormone_details['Description'])
    
    with st.expander("Dominant Hormones & Levels Today:"):
        for hormone, level in hormone_details.items():
            if hormone != "Description":
                st.markdown(f"**{hormone}:** {level}")
    
    st.markdown("---")
    st.info("💡 Remember: These are estimations. Your body is unique! Track symptoms and consult a healthcare professional for medical advice.")