import streamlit as st
import re
import matplotlib.pyplot as plt
from datetime import datetime
import fitz  # PyMuPDF

st.set_page_config(page_title="Kilo y Cuarto - Control", layout="centered")

st.title("🍗 Kilo y Cuarto - Control de Empleados")

uploaded_files = st.file_uploader("Sube los PDFs del mes", accept_multiple_files=True)

# -------- FUNCIONES --------

def parse_time_to_minutes(text):
    h = 0
    m = 0
    if "hora" in text:
        h = int(re.search(r'(\d+)\s*hora', text).group(1))
    if "minuto" in text:
        m = int(re.search(r'(\d+)\s*minuto', text).group(1))
    return h * 60 + m

def clean_work_time(minutes):
    return 240 <= minutes <= 480

def clean_break(minutes):
    return 5 <= minutes <= 40

def parse_start_time(line):
    try:
        return datetime.strptime(line.strip(), "%H:%M")
    except:
        return None

# -------- PROCESAMIENTO --------

if uploaded_files:

    employees_data = {}

    for file in uploaded_files:

        name = file.name.split(" ")[0].replace(".pdf", "")

        employees_data[name] = {
            "work": [],
            "break": [],
            "delay": []
        }

        pdf = fitz.open(stream=file.read(), filetype="pdf")

        text = ""
        for page in pdf:
            text += page.get_text()

        lines = text.split("\n")

        for i, line in enumerate(lines):

            # -------- INICIO JORNADA (ROBUSTO) --------
            if "Inicio de jornada" in line:

                time_str = None

                # Caso normal
                parts = line.split(" ")
                if len(parts) > 0 and ":" in parts[0]:
                    time_str = parts[0]

                # Caso roto (hora en línea anterior)
                elif i > 0:
                    prev_line = lines[i-1].strip()
                    if ":" in prev_line:
                        time_str = prev_line

                start_time = parse_start_time(time_str) if time_str else None

                if start_time:
                    target = datetime.strptime("09:30", "%H:%M") if name.lower() == "diana" else datetime.strptime("09:00", "%H:%M")
                    delay = (start_time - target).total_seconds() / 60
                    employees_data[name]["delay"].append(delay)

            # -------- HORAS TRABAJADAS --------
            if "Total tiempo trabajado" in line:
                try:
                    minutes = parse_time_to_minutes(line)
                    if clean_work_time(minutes):
                        employees_data[name]["work"].append(minutes / 60)
                except:
                    pass

            # -------- DESCANSO --------
            if "Total tiempo en pausa" in line:
                try:
                    if "Menos de un minuto" in line:
                        minutes = 1
                    else:
                        minutes = parse_time_to_minutes(line)

                    if clean_break(minutes):
                        employees_data[name]["break"].append(minutes)
                except:
                    pass

    # -------- CALCULAR MEDIAS --------

    names = []
    avg_work = []
    avg_break = []
    avg_delay = []

    for name, data in employees_data.items():

        if len(data["work"]) == 0:
            continue

        names.append(name)

        avg_work.append(
            sum(data["work"]) / len(data["work"]) if len(data["work"]) > 0 else 0
        )

        avg_break.append(
            sum(data["break"]) / len(data["break"]) if len(data["break"]) > 0 else 0
        )

        avg_delay.append(
            sum(data["delay"]) / len(data["delay"]) if len(data["delay"]) > 0 else 0
        )

    colors = ["#d4ad24", "#263D4B", "#8c1c13", "#3a7d44", "#6a4c93", "#ff8800"]

    # -------- GRAFICO 1: HORAS --------
    fig1, ax1 = plt.subplots()
    bars = ax1.bar(names, avg_work, color=colors[:len(names)])
    ax1.set_ylim(5.5, 6.6)
    ax1.set_title("Horas trabajadas")

    for bar, val in zip(bars, avg_work):
        ax1.text(
            bar.get_x() + bar.get_width()/2,
            val + 0.01,
            f"{val:.2f}h",
            ha='center'
        )

    st.pyplot(fig1)

    # -------- GRAFICO 2: DESCANSO --------
    fig2, ax2 = plt.subplots()
    bars = ax2.bar(names, avg_break, color=colors[:len(names)])
    ax2.set_ylim(10, 20)
    ax2.set_title("Descanso medio")

    for bar, val in zip(bars, avg_break):
        ax2.text(
            bar.get_x() + bar.get_width()/2,
            val + 0.3,
            f"{val:.1f}m",
            ha='center'
        )

    st.pyplot(fig2)

    # -------- GRAFICO 3: RETRASOS --------
    fig3, ax3 = plt.subplots()
    bars = ax3.bar(names, avg_delay, color=colors[:len(names)])
    ax3.set_title("Retrasos")

    for bar, val in zip(bars, avg_delay):
        ax3.text(
            bar.get_x() + bar.get_width()/2,
            val + 0.5 if val >= 0 else val - 0.5,
            f"{val:.1f}m",
            ha='center'
        )

    st.pyplot(fig3)
