import streamlit as st
import pandas as pd
import plotly.express as px

from db import get_Ritu_history
from utils import generate_hormone_graph_data
from auth import get_user_profile

THEME_COLORS = ["#E57396", "#81C784", "#64B5F6", "#FFB74D", "#BA68C8", "#A1887F", "#FF8A65"]

def show_insights_tab():
    st.title("📊 Ritu Insights & Analysis")
    user_id = st.session_state.user_id
    profile = get_user_profile(user_id)
    avg_Ritu_length_user = profile.get('avg_Ritu_length', profile.get('avg_Ritu_length', 28))

    Ritu_history = get_Ritu_history(user_id)

    if not Ritu_history or len(Ritu_history) < 2:
        st.info("Not enough data to generate insights. Please log at least two full Ritus.")
        return

    df = pd.DataFrame(Ritu_history)
    df['period_start_date'] = pd.to_datetime(df['period_start_date'])
    df = df.sort_values(by='period_start_date')

    df['next_period_start_date'] = df['period_start_date'].shift(-1)
    df['Ritu_length'] = (df['next_period_start_date'] - df['period_start_date']).dt.days
    df_Ritus = df.dropna(subset=['Ritu_length'])

    st.header("Your Ritu Patterns")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ritu Length Variation")
        if not df_Ritus.empty:
            fig_Ritu_len = px.line(df_Ritus, x='period_start_date', y='Ritu_length', markers=True,
                                    title="Your Ritu Lengths Over Time", color_discrete_sequence=[THEME_COLORS[0]])
            fig_Ritu_len.update_layout(xaxis_title="Start Date of Ritu", yaxis_title="Ritu Length (days)",
                                       plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_Ritu_len, use_container_width=True)
            avg_len = df_Ritus['Ritu_length'].mean()
            st.write(f"**Average Ritu Length (logged):** {avg_len:.1f} days")
            st.markdown("""*This graph shows how the length of your Ritu (from the start of one period to the start of the next) has varied. Tracking this can help you notice patterns or significant changes.*""")
        else:
            st.write("More Ritu data needed to plot Ritu length variation.")

    symptom_data = []
    for entry in Ritu_history:
        if entry.get('symptoms'):
            symptoms_dict = entry['symptoms'] if isinstance(entry['symptoms'], dict) else {}
            symptoms_dict['date'] = entry['period_start_date']
            symptom_data.append(symptoms_dict)
    
    df_symptoms = pd.DataFrame(symptom_data)
    if not df_symptoms.empty:
        df_symptoms['date'] = pd.to_datetime(df_symptoms['date'])

    with col2:
        st.subheader("Mood Frequency")
        if not df_symptoms.empty and 'mood' in df_symptoms.columns and not df_symptoms['mood'].empty:
            mood_counts = df_symptoms['mood'].value_counts().reset_index()
            mood_counts.columns = ['mood', 'count']
            fig_mood = px.bar(mood_counts, x='mood', y='count', title="Mood Frequency During Logged Periods",
                              color='mood', color_discrete_sequence=THEME_COLORS[1:])
            fig_mood.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_mood, use_container_width=True)
            st.markdown("""*This bar chart shows how frequently different moods were logged. It can help identify common emotional patterns associated with your Ritu.*""")
        else:
            st.write("No 'mood' data logged to display this trend.")
    
    st.markdown("---")
    st.subheader("Pain/Cramp Levels Over Time")
    if not df_symptoms.empty and 'pain_cramps' in df_symptoms.columns:
        df_symptoms['pain_cramps_numeric'] = pd.to_numeric(df_symptoms['pain_cramps'], errors='coerce')
        df_symptoms_pain = df_symptoms.dropna(subset=['pain_cramps_numeric'])
        if not df_symptoms_pain.empty:
            fig_pain = px.line(df_symptoms_pain, x='date', y='pain_cramps_numeric', markers=True,
                               title="Pain/Cramp Levels (During Logged Periods)",
                               color_discrete_sequence=[THEME_COLORS[2]])
            fig_pain.update_layout(yaxis_title="Pain Level (0-5)", xaxis_title="Date of Period Start",
                                   plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pain, use_container_width=True)
            st.markdown("""*This line graph tracks the intensity of cramps or pain you've logged. Observing trends here might be useful for managing discomfort.*""")
        else:
            st.write("Not enough numeric 'pain_cramps' data to plot.")
    elif not symptom_data:
        st.write("No symptom data logged to display pain trends.")
    else:
        st.write("No 'pain_cramps' data specifically logged to display this trend.")

    st.markdown("---")
    st.header("Understanding Your Hormones")
    st.subheader("Typical Hormonal Fluctuations")
    
    hormone_df = generate_hormone_graph_data(Ritu_length=avg_Ritu_length_user)
    
    if not hormone_df.empty:
        fig_hormones = px.line(hormone_df, x="Day", y="Level (Relative)", color="Hormone",
                               title=f"Typical Hormonal Trends ({avg_Ritu_length_user}-day Ritu)",
                               labels={"Level (Relative)": "Relative Hormone Level"},
                               markers=False, color_discrete_map={
                                   "Estrogen": THEME_COLORS[0], "Progesterone": THEME_COLORS[1],
                                   "LH": THEME_COLORS[2], "FSH": THEME_COLORS[3]
                               })
        fig_hormones.update_layout(yaxis_range=[0,1.1], plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_hormones, use_container_width=True)
        st.markdown(f"""
        *This graph illustrates the typical rise and fall of key hormones throughout an average {avg_Ritu_length_user}-day Ritu. Understanding these general patterns can help you anticipate changes in your body and mood. Remember, this is a generalized model and individual experiences vary.*
        - **Estrogen:** Builds the uterine lining, influences mood, skin, and energy. Rises in the first half (follicular phase), peaks before ovulation, then has a smaller rise and fall in the second half (luteal phase).
        - **Progesterone:** "Pro-gestation" hormone. Rises sharply after ovulation to prepare the uterus for potential pregnancy and maintain its lining. It falls if pregnancy doesn't occur, triggering menstruation.
        - **LH (Luteinizing Hormone):** Surges dramatically just before ovulation, acting as the trigger for the egg to be released from the follicle.
        - **FSH (Follicle-Stimulating Hormone):** Is higher at the beginning of the Ritu to stimulate egg follicle development in the ovaries. It has a smaller peak around ovulation.
        """)
    else:
        st.write("Could not generate hormone trend data.")

    st.markdown("---")
    st.info("AI-powered chat about your Ritu data and general menstrual health is available in the 'MyRitu Chat' tab.")