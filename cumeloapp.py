import streamlit as st
import pandas as pd
import json
import os
from itertools import combinations
import numpy as np

ARCHIVO_DATOS = 'players.json'

# ---- Configuración visual y estilos ----
st.set_page_config(page_title="Perfilador 5v5", page_icon="⚽", layout="wide")
st.markdown("""
    <style>
    body, .stApp { background-color: #111; color: #e8e8e8;}
    .css-18e3th9 { background-color: #003049; }
    .css-1d391kg { background-color: #003049; }
    .st-bb { font-size: 1.1em; }
    .stDataFrame { background-color: #003049; color: #fff;}
    h1, h2, h3, h4, h5 { color: #c1121f; font-size: 1.25em; margin-bottom: 0.25em;}
    .highlight {background: #669bbc22; border-radius: 10px; padding: 0.7em 1em; margin-bottom:1.2em;}
    .stRadio label { font-size: 1.1em;}
    .emoji {font-size: 1.4em;}
    </style>
""", unsafe_allow_html=True)

EMOJI = {
    "Arquero": "🧤",
    "Muralla": "🛡️",
    "Gladiador": "🦾",
    "Orquestador": "🎼",
    "Wildcard": "🎲",
    "Topadora": "🚜"
}

COMPARABLES = {
    "Arquero": ["Emiliano Martínez", "Iker Casillas"],
    "Gladiador": ["Arturo Vidal", "Gennaro Gattuso", "N'Golo Kanté"],
    "Orquestador": ["Toni Kroos", "Andrea Pirlo", "Xavi Hernández"],
    "Wildcard": ["Ángel Di María", "Vinícius Jr", "Eden Hazard"],
    "Muralla": ["Walter Samuel", "Kalidou Koulibaly", "Paolo Maldini"],
    "Topadora": ["Jude Bellingham", "Leon Goretzka", "Sergej Milinković-Savić"],
}

# --- Definición de atributos ---
ATRIBUTOS_CAMPO = [
    ("First_Touch_Control",   "¿Con qué consistencia controla su primer toque?"),
    ("Short_Passing_Accuracy","¿Qué tan precisos son sus pases cortos (<5 m)?"),
    ("Vision_Free_Player",    "¿Qué tan probable es que identifique a un compañero libre al otro lado?"),
    ("Finishing_Precision",   "¿Qué tan preciso es al definir ocasiones de gol?"),
    ("Dribbling_Efficiency",  "¿Qué tan probable es que regatee en espacios reducidos?"),
    ("Power_Dribble_and_Score","¿Qué tan probable es que regatee a tres rivales y marque gol?"),
    ("Ball_Retention",        "¿Qué tan bien conserva la posesión bajo presión?"),
    ("Tactical_Awareness",    "¿Qué tan buena es su comprensión del posicionamiento y la forma de equipo?"),
    ("Marking_Tightness",     "¿Con qué frecuencia pierde al jugador que marca sin balón?"),
    ("Pressing_Consistency",  "¿Con qué constancia presiona fuera de posesión?"),
    ("Recovery_Runs",         "¿Qué tan efectivo es al volver para defender?"),
    ("Acceleration",          "¿Qué tan rápido alcanza su velocidad máxima desde parado?"),
    ("Agility",               "¿Qué tan bien cambia de dirección a gran velocidad?"),
    ("Stamina",               "¿Qué tan bien mantiene esfuerzo intenso todo el partido?"),
    ("Strength_in_Duels",     "¿Qué tan fuerte es en duelos cuerpo a cuerpo?"),
    ("Balance",               "¿Qué tan bien mantiene el equilibrio al desafiarse o regatear?"),
    ("Composure",             "¿Qué tan calmado está bajo presión durante el juego?"),
    ("Decision_Making_Speed", "¿Qué tan rápido toma buenas decisiones en juego veloz?"),
    ("Creativity",            "¿Qué tan creativo es para romper defensas con pase o movimiento?"),
    ("Leadership_Presence",   "¿Qué tan eficaz organiza y motiva al equipo en la cancha?"),
    ("Communication",         "¿Qué tan clara y oportuna es su comunicación con compañeros?"),
    ("Resilience_When_Behind","Cuando van perdiendo ≥4 goles, ¿sigue defendiendo?"),
    ("Attack_Transition",     "¿Qué tan bien transiciona de defensa a ataque?"),
    ("Defense_Transition",    "¿Qué tan bien transiciona de ataque a defensa?"),
    ("Spatial_Awareness",     "¿Qué tan buena es su conciencia del espacio libre alrededor?"),
]

ATRIBUTOS_ARQUERO = [
    ("GK_Foot_Play",    "¿Qué tan habilidoso es jugando con los pies?"),
    ("GK_Agility",      "¿Qué tan ágil es para reaccionar a tiros y cambios de dirección?"),
    ("GK_Reaction",     "¿Qué tan rápida es su reacción para detener disparos?"),
    ("GK_Bravery",      "¿Qué tan valiente es al lanzarse y poner el cuerpo ante un disparo?"),
    ("GK_Positioning",  "¿Qué tan buena es su colocación y lectura de trayectorias?"),
    ("GK_Distribution", "¿Qué precisión tiene al distribuir balones largos y cortos?"),
]

TIPOS_JUGADOR = ["Campo", "Arquero"]
ATR_GK_CAMPO = ["GK_Foot_Play", "GK_Agility", "GK_Bravery"]

# ----------------- FUNCIONES DE DATOS -----------------

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, 'r') as f:
            return json.load(f)
    return {}

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, 'w') as f:
        json.dump(datos, f, indent=4)

def obtener_usuario():
    if "usuario" not in st.session_state:
        st.session_state["usuario"] = ""
    usuario = st.sidebar.text_input("🧑‍💻 Tu nombre de usuario:", value=st.session_state["usuario"])
    st.session_state["usuario"] = usuario.strip()
    if not usuario:
        st.warning("Debes ingresar un nombre de usuario para continuar.")
        st.stop()
    return usuario

def promedio_atributos(votaciones):
    if not votaciones:
        return {}
    df = pd.DataFrame([d for d in votaciones.values()])
    return df.mean(axis=0).to_dict()

def obtener_rol(pr):
    if not pr: return "Orquestador", {"Orquestador": 1.0}
    score_wildcard = (
        pr.get("Finishing_Precision", 0)
        + pr.get("Attack_Transition", 0)
        + pr.get("Dribbling_Efficiency", 0)
        + pr.get("Power_Dribble_and_Score", 0)
        + pr.get("Acceleration", 0)
        - pr.get("Pressing_Consistency", 0)
        - pr.get("Marking_Tightness", 0)
        - pr.get("Recovery_Runs", 0)
        - pr.get("Strength_in_Duels", 0)
        - pr.get("Composure", 0)
        - pr.get("Decision_Making_Speed", 0)
    )
    score_muralla = (
        pr.get("Strength_in_Duels", 0) * 2
        + pr.get("Defense_Transition", 0)
        + pr.get("Leadership_Presence", 0)
        + pr.get("Recovery_Runs", 0)
        + pr.get("Pressing_Consistency", 0)
        + pr.get("Marking_Tightness", 0)
        + pr.get("Tactical_Awareness", 0)
    )
    score_gladiador = (
        pr.get("Resilience_When_Behind", 0)
        + pr.get("Composure", 0)
        + pr.get("Strength_in_Duels", 0)
        + pr.get("Stamina", 0)
        + pr.get("Recovery_Runs", 0)
        + pr.get("Pressing_Consistency", 0)
        + pr.get("Marking_Tightness", 0)
    )
    score_orquestador = (
        pr.get("First_Touch_Control", 0)
        + pr.get("Short_Passing_Accuracy", 0)
        + pr.get("Vision_Free_Player", 0)
        + pr.get("Ball_Retention", 0)
        + pr.get("Tactical_Awareness", 0)
        + pr.get("Balance", 0)
        + pr.get("Decision_Making_Speed", 0)
        + pr.get("Creativity", 0)
        + pr.get("Leadership_Presence", 0)
        + pr.get("Communication", 0)
        + pr.get("Spatial_Awareness", 0)
    )
    score_topadora = (
        pr.get("Finishing_Precision", 0)
        + pr.get("Power_Dribble_and_Score", 0)
        + pr.get("Short_Passing_Accuracy", 0)
        + pr.get("Ball_Retention", 0)
        + pr.get("Creativity", 0)
        + pr.get("Leadership_Presence", 0)
        + pr.get("Vision_Free_Player", 0)
    )
    roles = {
        "Wildcard": score_wildcard,
        "Muralla": score_muralla,
        "Gladiador": score_gladiador,
        "Orquestador": score_orquestador,
        "Topadora": score_topadora
    }
    if pr.get("GK_Reaction", 0) >= 3:
        return "Arquero", {"Arquero": 1.0}
    total = sum(abs(s) for s in roles.values())
    dist = {k: (max(0, v)/total if total else 0) for k,v in roles.items()}
    rol_princ = max(dist, key=dist.get)
    return rol_princ, dist

def descripcion_jugador(rol):
    if rol == "Muralla":
        return "Imponente en defensa, fuerte físicamente, con buena recuperación y siempre dispuesto a frenar ataques rivales."
    elif rol == "Gladiador":
        return "Incansable, comprometido en la presión y capaz de mantener el esfuerzo incluso cuando el equipo va perdiendo."
    elif rol == "Orquestador":
        return "Es quien organiza y da fluidez al juego, destacando en visión, control y creatividad en la circulación."
    elif rol == "Wildcard":
        return "Impredecible y desequilibrante, puede cambiar un partido en una jugada para bien o para mal."
    elif rol == "Topadora":
        return "Potente llegada al área, combina pase y definición, mentalidad ofensiva y llegada."
    elif rol == "Arquero":
        return "Especialista bajo los tres palos, seguro en reflejos, colocación y salida de balón."
    return "Jugador versátil."

# --- UI & Lógica Principal ---

def main():
    usuario = obtener_usuario()
    datos = cargar_datos()
    if 'menu' not in st.session_state:
        st.session_state.menu = "Agregar o editar jugador"
    with st.sidebar:
        st.title("⚽ Menú")
        menu = st.radio("Selecciona opción", ["Agregar o editar jugador", "Perfiles de jugadores", "Análisis"])
        st.session_state.menu = menu

        st.markdown("---")
        st.markdown("#### Jugadores")
        for n, info in datos.items():
            proms = promedio_atributos(info.get("votaciones", {}))
            rol, dist = obtener_rol(proms)
            convocado = info.get("convocado", True)
            emoji = EMOJI.get(rol, "")
            if st.checkbox(f"{emoji} {n}", value=convocado, key=f"convoc_{n}"):
                datos[n]["convocado"] = True
            else:
                datos[n]["convocado"] = False
        guardar_datos(datos)

    if menu == "Agregar o editar jugador":
        st.header("Editar o agregar jugador")
        nombre = st.text_input("Nombre del jugador")
        tipo = st.radio("Tipo", TIPOS_JUGADOR, horizontal=True)
        attrs = {}
        for k, q in ATRIBUTOS_CAMPO:
            attrs[k] = st.slider(q, 0, 5, 2, key=k+"_slider")
        if tipo == "Campo":
            for k in ATR_GK_CAMPO:
                preg = dict(ATRIBUTOS_ARQUERO)[k]
                attrs[k] = st.slider(preg, 0, 5, 2, key=k+"_slider")
        else:
            for k, q in ATRIBUTOS_ARQUERO:
                attrs[k] = st.slider(q, 0, 5, 2, key=k+"_slider")
        if st.button("Guardar/Actualizar jugador"):
            if nombre not in datos:
                datos[nombre] = {"Tipo": tipo, "votaciones": {}, "convocado": True}
            datos[nombre]["Tipo"] = tipo
            datos[nombre]["convocado"] = True
            datos[nombre]["votaciones"][usuario] = attrs
            guardar_datos(datos)
            st.success("¡Guardado correctamente!")

    elif menu == "Perfiles de jugadores":
        st.header("Perfiles de jugadores")
        datos = cargar_datos()
        if not datos:
            st.info("No hay jugadores registrados todavía.")
            return
        perfiles = []
        for nombre, info in datos.items():
            proms = promedio_atributos(info.get("votaciones", {}))
            rol, dist = obtener_rol(proms)
            secundarios = sorted(dist.items(), key=lambda x: x[1], reverse=True)
            sec_rol = secundarios[1][0] if len(secundarios)>1 else ""
            sec_pct = secundarios[1][1]*100 if len(secundarios)>1 else 0
            perfiles.append({
                "Nombre": f"{EMOJI.get(rol, '')} {nombre}",
                "Rol principal": rol,
                "Secundario": f"{sec_rol} ({sec_pct:.0f}%)",
                **{k: round(proms.get(k, 0), 1) for k, _ in ATRIBUTOS_CAMPO},
                "Descripción": descripcion_jugador(rol),
                "Comparables": ", ".join(COMPARABLES.get(rol, []))
            })
        st.dataframe(pd.DataFrame(perfiles).fillna(0), use_container_width=True)
        st.markdown("---")
        st.markdown("### Descripciones de jugadores")
        for p in perfiles:
            st.markdown(f"**{p['Nombre']}**: {p['Descripción']}  \nComparables: {p['Comparables']}")

    elif menu == "Análisis":
        st.header("Análisis de equipos y compatibilidades")
        datos = cargar_datos()
        convocados = [n for n in datos if datos[n].get("convocado", True)]
        proms = {n: promedio_atributos(datos[n].get("votaciones", {})) for n in convocados}
        jugadores_campo = [n for n in convocados if datos[n]["Tipo"]=="Campo"]
        arqueros = [n for n in convocados if datos[n]["Tipo"]=="Arquero"]
        if len(jugadores_campo)<4 or not arqueros:
            st.info("Debe haber al menos 4 jugadores de campo y un arquero convocado.")
            return

        def equipo_score(equipo):
            return sum([sum(proms[p].values()) for p in equipo if proms.get(p)])

        equipos = []
        for combo in combinations(jugadores_campo, 4):
            for gk in arqueros:
                eq = list(combo) + [gk]
                equipos.append( (equipo_score(eq), eq) )
        equipos = sorted(equipos, reverse=True)[:3]
        st.markdown("#### 🏆 Mejores equipos 5v5")
        for i, (punt, team) in enumerate(equipos):
            st.markdown(f"<div class='highlight'><b>Equipo {i+1}</b>: {' | '.join(team)} <br> Total puntos: {punt:.1f}</div>", unsafe_allow_html=True)
        st.caption("Lógica: suma de todos los atributos promediados de los convocados.")

        # Repite esto para ruleta rusa, catenaccio, tiki-taka, contraataque... usando distintas fórmulas de equipo_score.
        # Aquí puedes insertar explicaciones y lógica.

if __name__ == "__main__":
    main()
