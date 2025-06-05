import streamlit as st
import pandas as pd
import json
import os
from itertools import combinations
import numpy as np

# ---- EMOJIS Y COMPARABLES ----
EMOJI = {
    "Arquero":"🧤",
    "Muralla":"🛡️",
    "Gladiador":"🦾",
    "Orquestador":"🎼",
    "Wildcard":"🎲",
    "Topadora":"🚜"
}

COMPARABLES = {
    "Arquero": ["Emiliano Martínez", "Iker Casillas"],
    "Gladiador": ["Arturo Vidal", "Gennaro Gattuso", "N'Golo Kanté"],
    "Orquestador": ["Toni Kroos", "Andrea Pirlo", "Xavi Hernández"],
    "Wildcard": ["Ángel Di María", "Vinícius Jr", "Eden Hazard"],
    "Muralla": ["Walter Samuel", "Kalidou Koulibaly", "Paolo Maldini"],
    "Topadora":["Jude Bellingham", "Leon Goretzka", "Sergej Milinković-Savić"],
}

ARCHIVO_DATOS = 'players.json'

if 'editing' not in st.session_state:
    st.session_state.editing = None

# ---- FUNCIONES DE DATOS ----
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, 'r') as f:
            return json.load(f)
    return {}

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, 'w') as f:
        json.dump(datos, f, indent=4)

# --- ATRIBUTOS ---
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

# --- SCORING REFINADO DE ROLES ---
def score_wildcard(a):
    ataque = (
        a.get("Finishing_Precision",0) +
        a.get("Power_Dribble_and_Score",0) +
        a.get("Attack_Transition",0) +
        a.get("Dribbling_Efficiency",0) +
        a.get("Agility",0)
    )
    defensa = (
        a.get("Pressing_Consistency",0) +
        a.get("Marking_Tightness",0) +
        a.get("Strength_in_Duels",0) +
        a.get("Defense_Transition",0) +
        a.get("Recovery_Runs",0)
    )
    mental = (
        a.get("Composure",0) +
        a.get("Decision_Making_Speed",0) +
        a.get("Leadership_Presence",0)
    )
    return ataque*2 - defensa - mental

def score_gladiador(a):
    return (
        a.get("Resilience_When_Behind",0)*2 +
        a.get("Composure",0) +
        a.get("Strength_in_Duels",0)*2 +
        a.get("Stamina",0)*2 +
        a.get("Recovery_Runs",0)*2 +
        a.get("Pressing_Consistency",0) +
        a.get("Marking_Tightness",0)*2
    )

def score_topadora(a):
    ataque = (
        a.get("Finishing_Precision",0) +
        a.get("Power_Dribble_and_Score",0) +
        a.get("Attack_Transition",0) +
        a.get("Dribbling_Efficiency",0) +
        a.get("Short_Passing_Accuracy",0) +
        a.get("Ball_Retention",0) +
        a.get("Creativity",0)
    )
    return ataque*2 + a.get("Leadership_Presence",0) + a.get("Vision_Free_Player",0) + a.get("Balance",0)

def score_orquestador(a):
    return (
        a.get("First_Touch_Control",0)*2 +
        a.get("Short_Passing_Accuracy",0)*2 +
        a.get("Vision_Free_Player",0) +
        a.get("Ball_Retention",0) +
        a.get("Tactical_Awareness",0) +
        a.get("Balance",0) +
        a.get("Decision_Making_Speed",0) +
        a.get("Creativity",0) +
        a.get("Leadership_Presence",0) +
        a.get("Communication",0) +
        a.get("Spatial_Awareness",0)
    )

def score_muralla(a):
    return (
        a.get("Strength_in_Duels",0)*2 +
        a.get("Defense_Transition",0)*2 +
        a.get("Leadership_Presence",0) +
        a.get("Recovery_Runs",0) +
        a.get("Pressing_Consistency",0) +
        a.get("Marking_Tightness",0)*2 +
        a.get("Tactical_Awareness",0)
    )

def score_arquero(a):
    return a.get("GK_Reaction",0)*2 + a.get("GK_Positioning",0) + a.get("GK_Foot_Play",0) + a.get("GK_Agility",0) + a.get("GK_Bravery",0) + a.get("GK_Distribution",0)

ROLES = [
    ("Arquero", score_arquero),
    ("Muralla", score_muralla),
    ("Gladiador", score_gladiador),
    ("Orquestador", score_orquestador),
    ("Wildcard", score_wildcard),
    ("Topadora", score_topadora),
]

# --- ROL PRIMARIO Y SECUNDARIO ---
def rol_primario(nombre, datos):
    info = datos[nombre]
    if info["Tipo"]=="Arquero":
        return "Arquero"
    a = info["Atributos"]
    scores = {rol:sc(a) for rol,sc in ROLES if rol!="Arquero"}
    return max(scores,key=scores.get)

def rol_secundario(nombre, datos):
    info = datos[nombre]
    if info["Tipo"]=="Arquero":
        return ""
    a = info["Atributos"]
    scores = {rol:sc(a) for rol,sc in ROLES if rol!="Arquero"}
    sorted_scores = sorted(scores.items(), key=lambda x:x[1], reverse=True)
    return sorted_scores[1][0] if len(sorted_scores)>1 else ""

def porcentaje_roles(nombre, datos):
    info = datos[nombre]
    if info["Tipo"]=="Arquero":
        return 100, 0
    a = info["Atributos"]
    scores = {rol:sc(a) for rol,sc in ROLES if rol!="Arquero"}
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) < 2 or sorted_scores[0]==0:
        return 100, 0
    p1 = int(100 * sorted_scores[0] / (sorted_scores[0]+sorted_scores[1]))
    p2 = 100-p1
    return p1, p2

# --- DESCRIPCIÓN DE JUGADOR ---
def descripcion_jugador(nombre, rol):
    base = f"{nombre} es un jugador del tipo {rol} ({EMOJI.get(rol,'')}). "
    if rol == "Muralla":
        return base + "Imponente en defensa, fuerte físicamente, con buena recuperación y siempre dispuesto a frenar ataques rivales."
    elif rol == "Gladiador":
        return base + "Incansable, comprometido en la presión y capaz de mantener el esfuerzo incluso cuando el equipo va perdiendo."
    elif rol == "Orquestador":
        return base + "Es quien organiza y da fluidez al juego, destacando en visión, control y creatividad en la circulación."
    elif rol == "Wildcard":
        return base + "Impredecible y desequilibrante, puede cambiar un partido en una jugada para bien o para mal."
    elif rol == "Topadora":
        return base + "Potente llegada al área, combina pase y definición, mentalidad ofensiva y llegada."
    elif rol == "Arquero":
        return base + "Seguro bajo los tres palos, buen juego de pies y grandes reflejos."
    return base

# --- APP ---
def main():
    st.set_page_config(page_title="Perfilador 5v5", layout="wide")
    st.markdown(
        """
        <style>
            body {background-color: #f5f6fa;}
            .stApp {background-color: #f5f6fa;}
            .titulo {font-size:1.5em; font-weight:700;}
            .seccion {border:2px solid #669bbc; border-radius:1em; background:#f1f1f8; padding:1em 2em; margin-bottom:2em;}
            .emoji {font-size:1.5em;}
        </style>
        """,
        unsafe_allow_html=True
    )

    datos = cargar_datos()
    menu = st.columns([1,1,1])
    opcion = None
    if menu[0].button("Editar o agregar jugador"):
        opcion = "agregar"
    elif menu[1].button("Perfiles de jugadores"):
        opcion = "ver"
    elif menu[2].button("Análisis"):
        opcion = "analizar"
    else:
        opcion = "ver"

    # --- AGREGAR / EDITAR JUGADOR ---
    if opcion == "agregar":
        nombre_edit = st.session_state.editing
        es_edicion = nombre_edit is not None

        if es_edicion:
            st.header(f"Editando perfil de {nombre_edit}")
            tipo = datos[nombre_edit]["Tipo"]
        else:
            st.header("Agregar nuevo jugador")
            tipo = st.radio("Tipo de jugador:", TIPOS_JUGADOR)

        # Rotación arquero
        if tipo == "Arquero":
            rot_idx = 0
            if es_edicion:
                rot_idx = 0 if datos[nombre_edit].get("GK_Rotacion", "Titular") == "Titular" else 1
            rot = st.selectbox("Arquero:", ["Titular", "Rotativo"], index=rot_idx)

        default_name = nombre_edit if es_edicion else ""
        nombre = st.text_input("Nombre del Jugador", value=default_name, key="player_name")

        if nombre:
            st.markdown("### Evalúa cada atributo (0–5)")
            attrs = {}

            for clave, preg in ATRIBUTOS_CAMPO:
                default = datos[nombre_edit]["Atributos"].get(clave, 2) if es_edicion else 2
                attrs[clave] = st.slider(preg, 0, 5, default, key=clave)

            if tipo == "Campo":
                for clave in ATR_GK_CAMPO:
                    preg = dict(ATRIBUTOS_ARQUERO)[clave]
                    default = datos[nombre_edit]["Atributos"].get(clave, 2) if es_edicion else 2
                    attrs[clave] = st.slider(preg, 0, 5, default, key=clave)
            else:
                for clave, preg in ATRIBUTOS_ARQUERO:
                    default = datos[nombre_edit]["Atributos"].get(clave, 2) if es_edicion else 2
                    attrs[clave] = st.slider(preg, 0, 5, default, key=clave)
                attrs["GK_Rotacion"] = rot

            if st.button("Guardar Perfil"):
                datos[nombre] = {"Tipo": tipo, "Atributos": attrs}
                if tipo == "Arquero":
                    datos[nombre]["GK_Rotacion"] = rot
                guardar_datos(datos)
                st.session_state.editing = None
                st.success("Perfil guardado")
                return
        else:
            st.info("Ingresa un nombre para comenzar.")

    # --- PERFILES ---
    elif opcion == "ver":
        st.header("Perfiles de Jugadores Guardados")
        if datos:
            filas = []
            for jug, info in datos.items():
                fila = {"Nombre": jug, "Tipo": info["Tipo"]}
                rol = rol_primario(jug, datos)
                sec = rol_secundario(jug, datos)
                p1, p2 = porcentaje_roles(jug, datos)
                fila["Rol Principal"] = f"{EMOJI[rol]} {rol} ({p1}%)"
                fila["Rol Secundario"] = f"{EMOJI.get(sec,'')} {sec} ({p2}%)" if sec else ""
                fila["Comparables"] = ", ".join(COMPARABLES.get(rol, []))
                fila.update(info["Atributos"])
                filas.append(fila)
            df = pd.DataFrame(filas).set_index("Nombre")
            st.dataframe(df, use_container_width=True)

            st.subheader("Descripciones individuales")
            for jug in datos:
                rol = rol_primario(jug, datos)
                st.markdown(
                    f"<div class='seccion'><span class='emoji'>{EMOJI.get(rol,'')}</span> <b>{jug}</b>: {descripcion_jugador(jug, rol)}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No hay perfiles aún. Añade un jugador primero.")

    # --- ANÁLISIS ---
    elif opcion == "analizar":
        st.header("Análisis de equipos y jugadores")
        nombres = [n for n in datos if datos[n]["Tipo"] != "Arquero" or rol_primario(n, datos)=="Arquero"]
        # Calcula promedios
        proms = {}
        for n in nombres:
            proms[n] = datos[n]["Atributos"]

        # Equipos/top roles
        st.markdown("#### Top 3 por rol")
        for rol, sc in ROLES:
            if rol == "Arquero": continue
            scores = sorted([(n, sc(proms[n])) for n in nombres if datos[n]["Tipo"]!="Arquero"], key=lambda x:x[1], reverse=True)
            top = scores[:3]
            st.markdown(f"**{EMOJI[rol]} {rol}:** " + ", ".join([f"{n} ({s})" for n,s in top]))

        st.markdown("#### Mejor equipo 5-a-side")
        if len(nombres)>=5:
            best_score, best_team = -float('inf'), None
            for combo in combinations(nombres, 5):
                # Solo un arquero
                if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1:
                    continue
                # Suma todos los scores de muralla, orquestador, wildcard, gladiador, topadora
                equipo_score = (
                    score_muralla(proms[combo[0]]) +
                    score_orquestador(proms[combo[1]]) +
                    score_wildcard(proms[combo[2]]) +
                    score_gladiador(proms[combo[3]]) +
                    score_topadora(proms[combo[4]])
                )
                if equipo_score > best_score:
                    best_score, best_team = equipo_score, combo
            st.markdown(
                f"<div class='seccion'><b>Equipo óptimo:</b> {' | '.join([n for n in best_team])}</div>",
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main()
