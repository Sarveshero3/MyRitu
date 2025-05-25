import streamlit as st
from utils import get_hormone_info

def show_hormones_tab():
    st.title("🧬 Hormone Hub")
    st.write("Understanding the key hormones involved in your menstrual Ritu.")

    phases = ["Menstruation", "Follicular Phase", "Ovulation / Fertile Window", "Luteal Phase"]

    for phase in phases:
        st.subheader(f" Hormone Levels During: {phase}")
        info = get_hormone_info(phase)
        
        st.markdown(f"**Description:** {info['Description']}")
        
        cols = st.columns(len(info) -1) # One column per hormone
        idx = 0
        for hormone, level in info.items():
            if hormone != "Description":
                with cols[idx]:
                    st.metric(label=hormone, value=level)
                idx += 1
        st.markdown("---")

    st.info("""
    **Key Hormones:**
    - **Estrogen:** Builds the uterine lining, influences mood and energy. Peaks before ovulation.
    - **Progesterone:** Prepares the uterus for pregnancy, maintains lining. Peaks after ovulation.
    - **Follicle-Stimulating Hormone (FSH):** Stimulates ovarian follicles to grow and mature eggs.
    - **Luteinizing Hormone (LH):** Triggers ovulation (release of the egg).
    """)