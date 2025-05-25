import streamlit as st
from streamlit_calendar import calendar
import datetime
from db import log_period_data, get_Ritu_history
from auth import get_user_profile, update_user_profile
from utils import calculate_next_period

def show_calendar_tab():
    st.title("🗓️ MyRitu Calendar & Logger")

    user_id = st.session_state.user_id
    profile = get_user_profile(user_id)
    st.session_state.profile_info = profile

    Ritu_history = get_Ritu_history(user_id)

    calendar_events = []
    avg_period_len_profile = profile.get('avg_period_length', 5)

    for entry in Ritu_history:
        start_date = datetime.datetime.strptime(entry['period_start_date'], '%Y-%m-%d')
        end_date_str = entry.get('period_end_date')
        if end_date_str:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = start_date + datetime.timedelta(days=avg_period_len_profile - 1)

        calendar_events.append({
            "title": "🩸 Period", "start": start_date.strftime('%Y-%m-%d'),
            "end": (end_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
            "color": "#D32F2F", "textColor": "#FFFFFF", "resourceId": "period"
        })
        if entry.get('symptoms'):
             calendar_events.append({
                "title": f"Symptoms Logged", "start": start_date.strftime('%Y-%m-%d'),
                "color": "#C2185B", "textColor": "#FFFFFF", "resourceId": "symptoms"
            })

    latest_period_start_str = profile.get('last_period_start')
    avg_Ritu_length_profile = profile.get('avg_Ritu_length', profile.get('avg_Ritu_length', 28))

    if latest_period_start_str and avg_Ritu_length_profile:
        current_pred_start_str = latest_period_start_str
        for _ in range(3):
            next_p, next_o, next_fw = calculate_next_period(current_pred_start_str, avg_Ritu_length_profile)
            if next_p:
                next_p_date = datetime.datetime.strptime(next_p, '%Y-%m-%d')
                calendar_events.append({
                    "title": "Predicted Period", "start": next_p_date.strftime('%Y-%m-%d'),
                    "end": (next_p_date + datetime.timedelta(days=avg_period_len_profile)).strftime('%Y-%m-%d'),
                    "color": "#F06292", "borderColor": "#C2185B", "textColor": "#FFFFFF", "resourceId": "predicted_period"
                })
            if next_o and next_fw:
                next_o_date = datetime.datetime.strptime(next_o, '%Y-%m-%d')
                fw_start_date = datetime.datetime.strptime(next_fw[0], '%Y-%m-%d')
                fw_end_date = datetime.datetime.strptime(next_fw[1], '%Y-%m-%d')
                calendar_events.append({"title": "🥚 Predicted Ovulation", "start": next_o_date.strftime('%Y-%m-%d'), 
                                        "end": (next_o_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d'), 
                                        "color": "#00796B", "textColor": "#FFFFFF", "resourceId": "ovulation"})
                calendar_events.append({"title": "💚 Predicted Fertile Window", "start": fw_start_date.strftime('%Y-%m-%d'), 
                                        "end": (fw_end_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d'), 
                                        "backgroundColor": "#388E3C", "borderColor": "#1B5E20", "textColor": "#FFFFFF", "resourceId": "fertile_window"})
            if next_p: current_pred_start_str = next_p
            else: break

    calendar_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek,timeGridDay"},
        "initialView": "dayGridMonth", "selectable": True, "editable": False, "height": 650,
        "resources": [
            {"id": "period", "title": "Period"}, {"id": "predicted_period", "title": "Predicted Period"},
            {"id": "ovulation", "title": "Ovulation"}, {"id": "fertile_window", "title": "Fertile Window"},
            {"id": "symptoms", "title": "Symptoms"},
        ]
    }
    selected_event = calendar(events=calendar_events, options=calendar_options, key="Ritu_calendar_main_v2")

    st.markdown("---")
    st.subheader("Log New Period / Symptoms")
    with st.form("log_Ritu_form_v2"): # Changed key
        # ... (rest of the form as before, ensure keys are unique if needed)
        new_period_start_date = st.date_input("Period Start Date", datetime.date.today(), key="log_start_date_v2")
        new_period_end_date_check = st.checkbox("Log Period End Date?", key="log_end_date_check_v2")
        new_period_end_date = None
        if new_period_end_date_check:
            new_period_end_date = st.date_input("Period End Date", new_period_start_date + datetime.timedelta(days=avg_period_len_profile-1), key="log_end_date_v2")

        st.write("Symptoms (optional):")
        symptoms = {}
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            symptoms['mood'] = st.selectbox("Mood", ["Neutral", "Happy", "Sad", "Irritable", "Anxious"], key="mood_log_cal_v2")
            symptoms['flow'] = st.selectbox("Flow", ["Not Applicable","Light", "Medium", "Heavy"], key="flow_log_cal_v2")
        with col_s2:
            symptoms['pain_cramps'] = st.select_slider("Cramps/Pain (0=None, 5=Severe)", options=list(range(6)), key="cramps_log_cal_v2")
            symptoms['bloating'] = st.checkbox("Bloating?", key="bloating_log_cal_v2")
        with col_s3:
            symptoms['skin_issues'] = st.checkbox("Skin Issues (Acne)?", key="skin_log_cal_v2")
            symptoms['fatigue'] = st.select_slider("Fatigue (0=None, 5=High)", options=list(range(6)), key="fatigue_log_cal_v2")
        
        notes = st.text_area("Additional Notes", key="notes_log_cal_v2")
        submit_log = st.form_submit_button("Log Data")

        if submit_log:
            start_date_str = new_period_start_date.strftime('%Y-%m-%d')
            end_date_str = new_period_end_date.strftime('%Y-%m-%d') if new_period_end_date else None
            final_symptoms = {k: v for k, v in symptoms.items() if v not in [False, "Neutral", "Not Applicable", 0] or k in ['mood', 'flow', 'pain_cramps', 'fatigue']}

            success, message = log_period_data(user_id, start_date_str, end_date_str, final_symptoms, notes)
            if success:
                st.success(message)
                if not profile.get('last_period_start') or start_date_str > profile['last_period_start']:
                    update_user_profile(user_id, {'last_period_start': start_date_str})
                    st.session_state.profile_info = get_user_profile(user_id) # Refresh profile
                st.rerun()
            else:
                st.error(message)
    # ... (Ritu History display as before) ...
    st.markdown("---")
    st.subheader("Ritu History (Last 5)")
    if Ritu_history:
        for entry in Ritu_history[:5]:
            st.text(f"Period: {entry['period_start_date']} to {entry.get('period_end_date', 'N/A')}")
            if entry.get('symptoms'): st.text(f"  Symptoms: {entry['symptoms']}")
            if entry.get('notes'): st.text(f"  Notes: {entry['notes']}")
            st.markdown("---")
    else:
        st.info("No Ritu data logged yet.")