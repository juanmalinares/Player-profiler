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
if 'page' not in st.session_state:
    st.session_state.page = "agregar"

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

def sidebar_convocados(datos):
    st.sidebar.markdown("## Menú")
    if st.sidebar.button("Editar o agregar jugador"):
        st.session_state.page = "agregar"
    if st.sidebar.button("Perfiles de jugadores"):
        st.session_state.page = "ver"
    if st.sidebar.button("Análisis"):
        st.session_state.page = "analizar"
    st.sidebar.markdown("---")
    st.sidebar.markdown("## Jugadores convocados")
    for nombre in datos:
        rol = rol_primario(nombre, datos)
        convocado = datos[nombre].get("Convocado", True)
        nuevo_valor = st.sidebar.checkbox(f"{EMOJI.get(rol,'')} {nombre}", value=convocado, key=f"convocado_{nombre}")
        datos[nombre]["Convocado"] = nuevo_valor
    guardar_datos(datos)
    st.sidebar.write("---")

def mejores_equipos_por_categoria(nombres, datos, proms, score_funcs, descripcion):
    equipos = []
    for combo in combinations(nombres, 5):
        if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1:
            continue
        team_score = sum([f(proms[p]) for f, p in zip(score_funcs, combo)])
        equipos.append((team_score, combo))
    equipos = sorted(equipos, reverse=True)[:3]
    cuadros = []
    for i, (score, eq) in enumerate(equipos):
        cuadros.append(f"**Equipo #{i+1}:** {' | '.join(eq)}  \nPuntaje: {score:.1f}  \n_{descripcion}_")
    return cuadros

def main():
    st.set_page_config(page_title="Perfilador 5v5", layout="wide")
    st.markdown(
        """
        <style>
            .stApp {background-color: #f5f6fa;}
            .titulo {font-size:1.5em; font-weight:700;}
            .seccion {border:2px solid #669bbc; border-radius:1em; background:#f1f1f8; padding:1em 2em; margin-bottom:2em;}
            .emoji {font-size:1.5em;}
        </style>
        """,
        unsafe_allow_html=True
    )

    datos = cargar_datos()
    sidebar_convocados(datos)  # Muestra sidebar SIEMPRE

    opcion = st.session_state.page

    # --- AGREGAR / EDITAR JUGADOR ---
    if opcion == "agregar":
        nombre_edit = st.session_state.editing
        es_edicion = nombre_edit is not None

        st.header("Agregar o editar jugador")
        if es_edicion:
            tipo = datos[nombre_edit]["Tipo"]
        else:
            tipo = st.radio("Tipo de jugador:", TIPOS_JUGADOR)

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
                datos[nombre] = {"Tipo": tipo, "Atributos": attrs, "Convocado": True}
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
        st.header("Perfiles de jugadores")
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
                fila["Convocado"] = info.get("Convocado", True)
                fila.update(info["Atributos"])
                filas.append(fila)
            df = pd.DataFrame(filas).set_index("Nombre")
            st.dataframe(df, use_container_width=True)

            st.subheader("Descripciones individuales")
            for jug in datos:
                rol = rol_primario(jug, datos)
                st.markdown(
                    f"<div class='seccion'><span class='emoji'>{EMOJI.get(rol,'')}</span> <b>{jug}</b>: {descripcion_jugador(jug, rol)}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No hay perfiles aún.")

    # --- ANÁLISIS DE EQUIPOS ---
    elif opcion == "analizar":
        st.header("Análisis de equipos y categorías")
        nombres = [n for n,info in datos.items() if info.get("Convocado", True)]
        proms = {p: datos[p]["Atributos"] for p in nombres}

        if len(nombres) < 5:
            st.warning("Convoca al menos 5 jugadores.")
            return

        # Mejor equipo 5v5
        equipos = []
        for combo in combinations(nombres, 5):
            if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1:
                continue
            score_team = (
                score_arquero(proms[combo[0]]) +
                score_muralla(proms[combo[1]]) +
                score_gladiador(proms[combo[2]]) +
                score_orquestador(proms[combo[3]]) +
                score_topadora(proms[combo[4]])
            )
            equipos.append((score_team, combo))
        equipos = sorted(equipos, reverse=True)[:3]
        st.markdown(f"<div class='seccion'><b>🏆 Top 3: Mejor equipo 5v5</b><br/>" + "<br/>".join([f"**Equipo #{i+1}:** {' | '.join(eq)} (Puntaje: {s:.1f})" for i,(s,eq) in enumerate(equipos)]) + "</div>", unsafe_allow_html=True)

        # Especiales
        # Catenaccio: Muralla, Gladiador y defensivos
        equipos_cat = []
        for combo in combinations(nombres, 5):
            if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1:
                continue
            score = sum([
                score_arquero(proms[combo[0]]),
                score_muralla(proms[combo[1]]),
                score_gladiador(proms[combo[2]]),
                score_muralla(proms[combo[3]]),
                score_gladiador(proms[combo[4]]),
            ])
            equipos_cat.append((score, combo))
        equipos_cat = sorted(equipos_cat, reverse=True)[:3]
        st.markdown(f"<div class='seccion'><b>🛡️ Top 3: Mejor Catenaccio (equipo defensivo)</b><br/>" + "<br/>".join([f"**Equipo #{i+1}:** {' | '.join(eq)} (Puntaje: {s:.1f})" for i,(s,eq) in enumerate(equipos_cat)]) + "</div>", unsafe_allow_html=True)

        # Contraataque: Wildcard, Topadora, Attack_Transition, Acceleration
        equipos_counter = []
        for combo in combinations(nombres, 5):
            if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1:
                continue
            score = (
                score_arquero(proms[combo[0]]) +
                score_topadora(proms[combo[1]]) +
                score_wildcard(proms[combo[2]]) +
                score_topadora(proms[combo[3]]) +
                score_wildcard(proms[combo[4]])
            )
            equipos_counter.append((score, combo))
        equipos_counter = sorted(equipos_counter, reverse=True)[:3]
        st.markdown(f"<div class='seccion'><b>🚀 Top 3: Mejor contraataque (rápidos y ofensivos)</b><br/>" + "<br/>".join([f"**Equipo #{i+1}:** {' | '.join(eq)} (Puntaje: {s:.1f})" for i,(s,eq) in enumerate(equipos_counter)]) + "</div>", unsafe_allow_html=True)

        # Tiki-Taka: Orquestador, Topadora, Creativity, Decision_Making, etc
        equipos_tiki = []
        for combo in combinations(nombres, 5):
            if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1:
                continue
            score = (
                score_arquero(proms[combo[0]]) +
                score_orquestador(proms[combo[1]]) +
                score_topadora(proms[combo[2]]) +
                score_orquestador(proms[combo[3]]) +
                score_topadora(proms[combo[4]])
            )
            equipos_tiki.append((score, combo))
        equipos_tiki = sorted(equipos_tiki, reverse=True)[:3]
        st.markdown(f"<div class='seccion'><b>🎼 Top 3: Mejor tiki-taka (posesión y control)</b><br/>" + "<br/>".join([f"**Equipo #{i+1}:** {' | '.join(eq)} (Puntaje: {s:.1f})" for i,(s,eq) in enumerate(equipos_tiki)]) + "</div>", unsafe_allow_html=True)

        # Ruleta rusa: equipos con más diferencia entre ataque y defensa
        equipos_ruleta = []
        for combo in combinations(nombres, 5):
            if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1:
                continue
            team = [proms[p] for p in combo]
            atk = sum([score_wildcard(p) for p in team])
            dfs = sum([score_gladiador(p) + score_muralla(p) for p in team])
            ruleta_score = abs(atk - dfs)
            equipos_ruleta.append((ruleta_score, combo))
        equipos_ruleta = sorted(equipos_ruleta, reverse=True)[:3]
        st.markdown(f"<div class='seccion'><b>🎲 Top 3: Mejor ruleta rusa (equipo más impredecible)</b><br/>" + "<br/>".join([f"**Equipo #{i+1}:** {' | '.join(eq)} (Puntaje: {s:.1f})" for i,(s,eq) in enumerate(equipos_ruleta)]) + "</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
