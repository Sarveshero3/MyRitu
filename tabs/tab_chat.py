import streamlit as st
import requests
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import pandas as pd

from auth import get_user_profile
from db import get_Ritu_history, log_chat_message, get_chat_history_from_db # Import DB chat functions
# from utils import get_age_from_birthdate_chat # Defined below or import if preferred

load_dotenv()
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
PINK_TEXT_COLOR = "#E57396"

CHAT_MODEL_ID = "HuggingFaceH4/zephyr-7b-beta"
API_URL_CHAT = f"https://api-inference.huggingface.co/models/{CHAT_MODEL_ID}"

def query_hf_slm(payload, api_token_to_use):
    headers = {"Authorization": f"Bearer {api_token_to_use}"}
    params = {"wait_for_model": True}
    response = requests.post(API_URL_CHAT, headers=headers, json=payload, params=params)
    response.raise_for_status()
    return response.json()

def get_age_from_birthdate_chat(birth_date_str):
    if not birth_date_str: return None
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except ValueError: return None

def generate_user_Ritu_context(user_id):
    # ... (Context generation logic remains the same as your last provided version)
    profile = get_user_profile(user_id)
    history = get_Ritu_history(user_id)
    context = "User Profile for MyRitu App:\n"
    if profile.get('full_name'): context += f"- Name: {profile['full_name']}\n"
    age = get_age_from_birthdate_chat(profile.get('birth_date'))
    if age is not None: context += f"- Age: {age} years old.\n"
    life_stage = profile.get('life_stage')
    if life_stage: context += f"- Self-identified Life Stage: {life_stage}.\n"
    elif age is not None:
        if age <= 17: context += f"- Estimated Life Stage: Puberty/Adolescence.\n"
        elif age <= 40: context += f"- Estimated Life Stage: Reproductive Years.\n"
        elif age <= 50: context += f"- Estimated Life Stage: Likely Perimenopause or Reproductive Years.\n"
        elif age > 50 : context += f"- Estimated Life Stage: Likely Menopause or Post-menopause.\n"
    avg_Ritu_len_profile = profile.get('avg_Ritu_length', 'N/A')
    context += f"- Average Ritu Length from profile: {avg_Ritu_len_profile} days\n"
    context += f"- Average Period Length: {profile.get('avg_period_length', 'N/A')} days\n"
    if profile.get('last_period_start'): context += f"- Last Period Started: {profile['last_period_start']}\n"
    elif life_stage in ["Menopause", "Post-menopause"] or (age and age > 52):
        context += f"- Note: User may be menopausal/post-menopausal as no recent period is logged.\n"
    if profile.get('medical_conditions'): context += f"- Medical Conditions: {profile['medical_conditions']}\n"
    if profile.get('medications'): context += f"- Medications: {profile['medications']}\n"
    if profile.get('preferences'): context += f"- User Preferences/Concerns: {profile['preferences']}\n"
    context += "\nRecent Ritu History (up to last 3 entries for prompt brevity):\n"
    if history:
        for entry in history[:3]:
            context += f"- Period started: {entry['period_start_date']}, Ended: {entry.get('period_end_date', 'N/A')}\n"
            if entry.get('symptoms'):
                symptoms_str = ", ".join([f"{k}: {v}" for k, v in entry['symptoms'].items()])
                context += f"  Symptoms: {symptoms_str}\n"
    else: context += "- No Ritu history logged yet.\n"
    if len(history) >= 1:
        df = pd.DataFrame(history)
        df['period_start_date'] = pd.to_datetime(df['period_start_date'])
        df = df.sort_values(by='period_start_date', ascending=False)
        if len(history) >=2:
            df_calc = df.sort_values(by='period_start_date')
            df_calc['next_period_start_date'] = df_calc['period_start_date'].shift(-1)
            df_calc['Ritu_length_calculated'] = (df_calc['next_period_start_date'] - df_calc['period_start_date']).dt.days
            df_Ritus_calc = df_calc.dropna(subset=['Ritu_length_calculated'])
            if not df_Ritus_calc.empty:
                avg_calculated_len = df_Ritus_calc['Ritu_length_calculated'].mean()
                min_len, max_len = df_Ritus_calc['Ritu_length_calculated'].min(), df_Ritus_calc['Ritu_length_calculated'].max()
                context += f"\nCalculated Ritu Length Insights (based on {len(df_Ritus_calc)} logged Ritus):\n"
                context += f"- Average calculated Ritu length: {avg_calculated_len:.1f} days.\n"
                context += f"- Shortest Ritu length: {min_len:.0f} days, Longest: {max_len:.0f} days.\n"
                if len(df_Ritus_calc['Ritu_length_calculated']) > 1:
                    recent_lengths = df_Ritus_calc['Ritu_length_calculated'].tail(3).tolist()
                    context += f"- Most recent Ritu lengths: {', '.join(map(str, recent_lengths))} days.\n"
        symptom_summary_data = []
        for entry in history:
            if entry.get('symptoms'):
                symptom_entry = entry['symptoms'].copy(); symptom_entry['date'] = entry['period_start_date']
                symptom_summary_data.append(symptom_entry)
        if symptom_summary_data:
            df_symptoms_summary = pd.DataFrame(symptom_summary_data)
            context += "\nSymptom Summary (from all logged history):\n"
            if 'mood' in df_symptoms_summary.columns:
                common_moods = df_symptoms_summary['mood'].value_counts().nlargest(2)
                if not common_moods.empty: context += f"- Most common moods logged: {', '.join([f'{idx} ({val} times)' for idx, val in common_moods.items()])}.\n"
            if 'pain_cramps' in df_symptoms_summary.columns:
                df_symptoms_summary['pain_cramps_numeric'] = pd.to_numeric(df_symptoms_summary['pain_cramps'], errors='coerce')
                avg_pain = df_symptoms_summary['pain_cramps_numeric'].mean()
                max_pain = df_symptoms_summary['pain_cramps_numeric'].max()
                if pd.notna(avg_pain): context += f"- Average pain/cramp level logged: {avg_pain:.1f} (0-5).\n"
                if pd.notna(max_pain): context += f"- Maximum pain/cramp level logged: {max_pain:.0f}.\n"
    return context

def show_chat_tab():
    st.markdown(f"<h2 style='color: {PINK_TEXT_COLOR};'>💬 MyRitu Chat 💬</h2>", unsafe_allow_html=True)
    st.write("Talk about your Ritu, concerns, and health. I'm here to listen and provide general information.")
    st.caption("⚠️ This chat is for informational purposes only and NOT a substitute for professional medical advice.")

    user_id = st.session_state.user_id

    if not HF_API_TOKEN:
        st.warning("MyRitu's AI features are currently unavailable.")
        return

    # Load chat history from DB for the session if not already loaded for display
    if 'chat_loaded_from_db' not in st.session_state or not st.session_state.chat_loaded_from_db:
        st.session_state.chat_messages_display = get_chat_history_from_db(user_id)
        st.session_state.chat_loaded_from_db = True # Mark as loaded for this session

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_messages_display:
            sender, message_content = msg["sender"], msg["message"]
            if sender == "user":
                st.markdown(f"<div style='display: flex; justify-content: flex-end; margin-bottom: 10px;'><div style='background-color: #F8BBD0; color: #383838; padding: 10px 15px; border-radius: 15px 15px 0 15px; max-width: 70%; font-size: 1em; line-height: 1.5;'><b>You:</b><br>{message_content}</div></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='display: flex; justify-content: flex-start; margin-bottom: 10px;'><div style='background-color: #E3F2FD; color: #383838; padding: 10px 15px; border-radius: 15px 15px 15px 0; max-width: 70%; font-size: 1em; line-height: 1.5;'><b>MyRitu Bot:</b><br>{message_content}</div></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    user_input = st.text_input("Ask something about your Ritu or health:", key="Ritu_chat_input_main_v5", placeholder="Type your message here...")

    if st.button("Send", key="Ritu_chat_send_btn_main_v5") and user_input:
        # Add to UI display list and log to DB
        st.session_state.chat_messages_display.append({"sender": "user", "message": user_input})
        log_chat_message(user_id, "user", user_input)
        st.rerun() # Rerun to show user message immediately

    # Process last user message for bot response
    if st.session_state.chat_messages_display and st.session_state.chat_messages_display[-1]["sender"] == "user":
        # Check if this user message already has a subsequent bot response in the display list
        # This is a simple check; more robust would be to track message IDs or a "waiting_for_bot" flag
        needs_bot_response = True
        if len(st.session_state.chat_messages_display) > 1:
            if st.session_state.chat_messages_display[-2]["sender"] == "user" and \
               st.session_state.chat_messages_display[-1]["sender"] == "user": # Two user messages in a row (unlikely with rerun)
                 pass # Only respond to the latest one
            elif st.session_state.chat_messages_display[-2]["sender"] == "bot": # Last interaction was bot responding
                 needs_bot_response = False # Bot already responded to previous user message

        # More direct: if the last message is user, and it's the *only* message or the one before it was bot, then respond.
        if len(st.session_state.chat_messages_display) == 0: # Should not happen if user message was just added
            needs_bot_response = False
        elif st.session_state.chat_messages_display[-1]["sender"] == "user":
            if len(st.session_state.chat_messages_display) == 1: # First user message
                needs_bot_response = True
            elif st.session_state.chat_messages_display[-2]["sender"] == "bot": # User replied to bot
                needs_bot_response = True
            else: # This implies user sent multiple messages before bot could reply, respond to latest
                needs_bot_response = True # Or false if you only want to respond once per button click cycle

        # Simplified logic: if the last message is 'user', assume we need a bot response
        # This might lead to multiple bot responses if user types fast and reruns happen.
        # A flag `st.session_state.waiting_for_bot_response = True` set on Send button click,
        # and cleared after bot responds, would be more robust.

        # For now, let's use a simpler check: if the very last message is 'user', try to get a bot response.
        # This means the previous logic for `needs_bot_response` is complex.
        # Let's assume if the last message is 'user', we process it.
        # To prevent re-processing, we can add a temporary flag or check message count.

        # Let's refine: only process if the last message is 'user' AND we haven't just processed it.
        # A simple way is to check if the total number of messages is odd (user sent last).
        if len(st.session_state.chat_messages_display) % 2 != 0: # Odd number means user sent last
            user_context_summary = generate_user_Ritu_context(user_id)
            last_user_message = st.session_state.chat_messages_display[-1]["message"]

            system_prompt = f"""<|system|>
You are MyRitu Chat... (rest of your detailed system prompt from previous version) ...

User's Context:
{user_context_summary}</s>
<|user|>
My question is: "{last_user_message}"</s>
<|assistant|>
"""
            payload = {"inputs": system_prompt, "parameters": {"max_new_tokens": 450, "return_full_text": False, "temperature": 0.7, "top_p": 0.9, "do_sample": True, "repetition_penalty": 1.1}}

            with st.spinner("MyRitu is thinking with care..."):
                try:
                    api_result = query_hf_slm(payload, HF_API_TOKEN)
                    bot_response = "Oh dear, I'm having a little trouble gathering my thoughts right now."
                    # ... (API result parsing as before) ...
                    if isinstance(api_result, list) and api_result and "generated_text" in api_result[0]:
                        bot_response = api_result[0]["generated_text"].strip()
                    elif isinstance(api_result, dict) and "generated_text" in api_result:
                         bot_response = api_result["generated_text"].strip()
                    if "<|assistant|>" in bot_response: bot_response = bot_response.split("<|assistant|>")[-1].strip()
                    if not bot_response: bot_response = "I seem to be at a loss for words. Could you try rephrasing, dear?"

                    # Add to UI display list and log to DB
                    st.session_state.chat_messages_display.append({"sender": "bot", "message": bot_response})
                    log_chat_message(user_id, "bot", bot_response)
                    st.rerun()
                except requests.exceptions.HTTPError as e:
                    # ... (error handling as before) ...
                    error_message = f"API Error: {e.response.status_code}."
                    st.error(error_message)
                    # Log the error attempt for the bot, but don't show API error to user directly in chat
                    st.session_state.chat_messages_display.append({"sender": "bot", "message": "Oh dear, my connection seems a bit weak. Could you try asking again in a moment?"})
                    log_chat_message(user_id, "bot", "API Connection Error (User was shown a generic message)") # Log internal error
                    st.rerun()
                except Exception as e:
                    st.error(f"An unexpected hiccup occurred: {e}")
                    st.session_state.chat_messages_display.append({"sender": "bot", "message": "Goodness, something unexpected happened on my end!"})
                    log_chat_message(user_id, "bot", f"Unexpected Error: {e} (User was shown a generic message)")
                    st.rerun()