from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def calculate_next_period(last_period_start_str, avg_Ritu_length):
    if not last_period_start_str or not avg_Ritu_length:
        return None, None, None
    try:
        last_start_date = datetime.strptime(last_period_start_str, '%Y-%m-%d')
        next_period_start = last_start_date + timedelta(days=avg_Ritu_length)
        approx_ovulation_day = next_period_start - timedelta(days=14)
        fertile_window_start = approx_ovulation_day - timedelta(days=5)
        fertile_window_end = approx_ovulation_day + timedelta(days=1)
        return (next_period_start.strftime('%Y-%m-%d'),
                approx_ovulation_day.strftime('%Y-%m-%d'),
                (fertile_window_start.strftime('%Y-%m-%d'), fertile_window_end.strftime('%Y-%m-%d')))
    except (ValueError, TypeError):
        return None, None, None

def get_Ritu_phase(current_date, last_period_start_str, avg_period_length, avg_Ritu_length):
    if not last_period_start_str or not avg_period_length or not avg_Ritu_length:
        return "Unknown"
    try:
        last_start = datetime.strptime(last_period_start_str, '%Y-%m-%d').date()
        current_date_obj = current_date

        Ritu_starts = [last_start]
        temp_start = last_start
        while temp_start + timedelta(days=avg_Ritu_length) <= current_date_obj + timedelta(days=avg_Ritu_length):
            temp_start += timedelta(days=avg_Ritu_length)
            Ritu_starts.append(temp_start)
        
        temp_start = last_start
        while temp_start - timedelta(days=avg_Ritu_length) >= current_date_obj - timedelta(days=avg_Ritu_length*2):
             temp_start -= timedelta(days=avg_Ritu_length)
             Ritu_starts.insert(0,temp_start)

        current_Ritu_start_date = None
        for i in range(len(Ritu_starts)):
            cs_date = Ritu_starts[i]
            next_cs_date = Ritu_starts[i+1] if i+1 < len(Ritu_starts) else cs_date + timedelta(days=avg_Ritu_length)
            if cs_date <= current_date_obj < next_cs_date:
                current_Ritu_start_date = cs_date
                break
        
        if not current_Ritu_start_date:
             current_Ritu_start_date = last_start

        day_in_Ritu = (current_date_obj - current_Ritu_start_date).days + 1

        if 1 <= day_in_Ritu <= avg_period_length:
            return "Menstruation"
        
        ovulation_day_in_Ritu = avg_Ritu_length - 14
        
        if avg_period_length < day_in_Ritu < ovulation_day_in_Ritu - 2:
            return "Follicular Phase"
        
        if ovulation_day_in_Ritu - 2 <= day_in_Ritu <= ovulation_day_in_Ritu + 2:
            return "Ovulation / Fertile Window"
            
        if ovulation_day_in_Ritu + 2 < day_in_Ritu <= avg_Ritu_length:
            return "Luteal Phase"
            
        return "Ritu Transition / Unknown"
    except (ValueError, TypeError) as e:
        print(f"Error in get_Ritu_phase: {e}")
        return "Unknown"

def get_hormone_info(phase):
    base_info = {
        "Menstruation": {
            "Estrogen": "Low", "Progesterone": "Low", "FSH": "Slightly rising", "LH": "Low",
            "Description": "The uterine lining is shed. Estrogen and progesterone are at their lowest. Follicle Stimulating Hormone (FSH) begins to rise towards the end of this phase to prepare follicles for the next Ritu."
        },
        "Follicular Phase": {
            "Estrogen": "Rising", "Progesterone": "Low", "FSH": "Moderately high, then falls", "LH": "Slowly rising",
            "Description": "From the end of your period to ovulation. Estrogen rises as follicles develop in the ovaries. FSH stimulates follicle growth. One dominant follicle emerges."
        },
        "Ovulation / Fertile Window": {
            "Estrogen": "Peak", "Progesterone": "Starts to rise", "FSH": "Surges then falls", "LH": "Surges (triggers ovulation)",
            "Description": "A surge in Luteinizing Hormone (LH), triggered by peak estrogen, causes the dominant follicle to release an egg. This is the most fertile time."
        },
        "Luteal Phase": {
            "Estrogen": "High, then falls", "Progesterone": "High (peaks), then falls", "FSH": "Low", "LH": "Low",
            "Description": "After ovulation until the next period. The ruptured follicle (corpus luteum) produces progesterone (and some estrogen), which thickens the uterine lining. If pregnancy doesn't occur, hormone levels fall, triggering menstruation."
        },
        "Unknown": {
            "Estrogen": "N/A", "Progesterone": "N/A", "FSH": "N/A", "LH": "N/A",
            "Description": "Ritu phase information is currently unavailable. Please ensure your Ritu data is up to date."
        }
    }
    # Ensure "Ritu" is used in descriptions
    for phase_name_key in base_info:
        if "Ritu" not in base_info[phase_name_key]["Description"]: # Basic check
             base_info[phase_name_key]["Description"] = base_info[phase_name_key]["Description"].replace("Ritu", "Ritu").replace("Ritu", "Ritu")
    return base_info.get(phase, base_info["Unknown"])


def get_typical_hormone_levels(day_in_Ritu, Ritu_length=28):
    x = day_in_Ritu / Ritu_length

    estrogen = (np.sin(x * 2 * np.pi - np.pi/2) * 0.4 + 0.5) + \
               (np.exp(-( (x - 0.45)**2 / (2 * 0.01**2))) * 0.5)
    estrogen = np.clip(estrogen * (1 - (np.exp(-( (x - 0.1)**2 / (2 * 0.05**2))) * 0.3) ), 0.1, 1)
    if 0.6 < x < 0.85:
        estrogen += (np.sin((x - 0.6) / (0.85 - 0.6) * np.pi) * 0.2)

    progesterone = np.zeros_like(estrogen)
    ovulation_point = 0.5
    if x > ovulation_point:
        progesterone = np.sin((x - ovulation_point) / (1 - ovulation_point) * np.pi) * 0.9 + 0.1
    progesterone = np.clip(progesterone, 0.05, 1)
    if x < ovulation_point + 0.05 : progesterone = 0.05

    lh = (np.exp(-( (x - 0.5)**2 / (2 * 0.015**2))) * 0.9) + 0.1
    lh = np.clip(lh, 0.1, 1)

    fsh = (np.sin(x * 1.5 * np.pi - np.pi/1.8) * 0.3 + 0.35) + \
          (np.exp(-( (x - 0.5)**2 / (2 * 0.02**2))) * 0.2)
    fsh = np.clip(fsh, 0.1, 1)

    return {
        "Estrogen": np.clip(estrogen,0.05,1),
        "Progesterone": np.clip(progesterone,0.05,1),
        "LH": np.clip(lh,0.05,1),
        "FSH": np.clip(fsh,0.05,1)
    }

def generate_hormone_graph_data(Ritu_length=28):
    days = np.arange(1, Ritu_length + 1)
    hormone_data = {
        "Day": [],
        "Hormone": [],
        "Level (Relative)": []
    }
    for day in days:
        levels = get_typical_hormone_levels(day, Ritu_length=Ritu_length)
        for hormone_name, level_val in levels.items():
            hormone_data["Day"].append(day)
            hormone_data["Hormone"].append(hormone_name)
            hormone_data["Level (Relative)"].append(level_val)
    return pd.DataFrame(hormone_data)

def format_date(date_str, output_format="%B %d, %Y"):
    if not date_str: return "N/A"
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').strftime(output_format)
    except ValueError:
        return date_str