import streamlit as st
import pandas as pd
import json
import os
from itertools import combinations
import numpy as np

ARCHIVO_DATOS = 'players.json'

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

ATRIBUTOS_CAMPO = [
    ("First_Touch_Control",   "Primer toque"),
    ("Short_Passing_Accuracy","Pase corto"),
    ("Vision_Free_Player",    "Visión compañero libre"),
    ("Finishing_Precision",   "Definición"),
    ("Dribbling_Efficiency",  "Regate"),
    ("Power_Dribble_and_Score","Regate+gol"),
    ("Ball_Retention",        "Retención balón"),
    ("Tactical_Awareness",    "Conciencia táctica"),
    ("Marking_Tightness",     "Marcaje"),
    ("Pressing_Consistency",  "Presión"),
    ("Recovery_Runs",         "Recuperación"),
    ("Acceleration",          "Aceleración"),
    ("Agility",               "Agilidad"),
    ("Stamina",               "Resistencia"),
    ("Strength_in_Duels",     "Fuerza en duelos"),
    ("Balance",               "Equilibrio"),
    ("Composure",             "Calma bajo presión"),
    ("Decision_Making_Speed", "Velocidad de decisión"),
    ("Creativity",            "Creatividad"),
    ("Leadership_Presence",   "Liderazgo"),
    ("Communication",         "Comunicación"),
    ("Resilience_When_Behind","Resiliencia perdiendo"),
    ("Attack_Transition",     "Transición ataque"),
    ("Defense_Transition",    "Transición defensa"),
    ("Spatial_Awareness",     "Conciencia espacial"),
]

ATRIBUTOS_ARQUERO = [
    ("GK_Foot_Play",    "Juego de pies"),
    ("GK_Agility",      "Agilidad (GK)"),
    ("GK_Reaction",     "Reflejos"),
    ("GK_Bravery",      "Valentía (GK)"),
    ("GK_Positioning",  "Posicionamiento"),
    ("GK_Distribution", "Distribución"),
]

TIPOS_JUGADOR = ["Campo", "Arquero"]
ATR_GK_CAMPO = ["GK_Foot_Play", "GK_Agility", "GK_Bravery"]

# ---- ESTILOS ----
st.set_page_config(page_title="Perfilador 5v5", page_icon="⚽", layout="wide")
st.markdown("""
<style>
body, .stApp { background-color: #f9fafb !important; color: #222;}
[data-testid="stSidebar"] { background-color: #fff !important;}
h1, h2, h3, h4 {color: #c1121f !important; font-size: 1.1em; margin-bottom:0.3em;}
.highlight {background: #f4e9ec; border-radius: 9px; padding: 1em 1em 0.8em 1em; margin:1.2em 0;}
.sectiontitle {margin-top:1.7em; font-size:1.2em; color:#003049;}
.st-bb {font-size: 1.15em;}
.stDataFrame { background-color: #fff; color: #222;}
</style>
""", unsafe_allow_html=True)

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
    if not votaciones: return {}
    df = pd.DataFrame([d for d in votaciones.values()])
    return df.mean(axis=0).to_dict()

def obtener_rol(pr):
    # Chequeos manuales de override para los que dijiste, si el nombre es igual:
    if st.session_state.get("force_role_for"):
        # Usar para override rápido manual por nombre (para test)
        name, rol = st.session_state["force_role_for"]
        if st.session_state.get("cur_jugador") == name: return rol, {rol:1}
    # ---- Nuevo scoring ajustado ----
    if not pr: return "Orquestador", {"Orquestador": 1.0}
    # Wildcard: mucho ataque, poca defensa y mentalidad
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
    # Topadora: mucho ataque+creatividad+pase, no penaliza defensa ni requiere velocidad pura
    score_topadora = (
        pr.get("Finishing_Precision", 0)
        + pr.get("Power_Dribble_and_Score", 0)
        + pr.get("Short_Passing_Accuracy", 0)
        + pr.get("Ball_Retention", 0)
        + pr.get("Creativity", 0)
        + pr.get("Leadership_Presence", 0)
        + pr.get("Vision_Free_Player", 0)
        + pr.get("Attack_Transition", 0)
    )
    # Gladiador: mucho en defensa, stamina y mentalidad defensiva
    score_gladiador = (
        pr.get("Resilience_When_Behind", 0)
        + pr.get("Composure", 0)
        + pr.get("Strength_in_Duels", 0)
        + pr.get("Stamina", 0)
        + pr.get("Recovery_Runs", 0)
        + pr.get("Pressing_Consistency", 0)
        + pr.get("Marking_Tightness", 0)
    )
    # Muralla: físico y defensa
    score_muralla = (
        pr.get("Strength_in_Duels", 0) * 2
        + pr.get("Defense_Transition", 0)
        + pr.get("Leadership_Presence", 0)
        + pr.get("Recovery_Runs", 0)
        + pr.get("Pressing_Consistency", 0)
        + pr.get("Marking_Tightness", 0)
        + pr.get("Tactical_Awareness", 0)
    )
    # Orquestador: pase, control y organización
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
    roles = {
        "Wildcard": score_wildcard,
        "Muralla": score_muralla,
        "Gladiador": score_gladiador,
        "Orquestador": score_orquestador,
        "Topadora": score_topadora
    }
    # Arquero, sólo si es tipo arquero:
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
        return "Organizador del juego, destaca en visión, control y creatividad en la circulación."
    elif rol == "Wildcard":
        return "Impredecible y desequilibrante, puede cambiar un partido en una jugada para bien o para mal."
    elif rol == "Topadora":
        return "Potente llegada al área, combina pase y definición, mentalidad ofensiva y llegada."
    elif rol == "Arquero":
        return "Especialista bajo los tres palos, seguro en reflejos, colocación y salida de balón."
    return "Jugador versátil."

def menu_sidebar(datos):
    st.sidebar.title("⚽ Menú")
    menu = st.sidebar.radio("Opciones", ["Agregar o editar jugador", "Perfiles de jugadores", "Análisis"])
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Jugadores convocados")
    for n, info in datos.items():
        proms = promedio_atributos(info.get("votaciones", {}))
        rol, dist = obtener_rol(proms)
        emoji = EMOJI.get(rol, "")
        if st.sidebar.checkbox(f"{emoji} {n}", value=info.get("convocado", True), key=f"convoc_{n}"):
            datos[n]["convocado"] = True
        else:
            datos[n]["convocado"] = False
    guardar_datos(datos)
    return menu

# --------- MAIN ----------
def main():
    usuario = obtener_usuario()
    datos = cargar_datos()
    menu = menu_sidebar(datos)
    st.title("Perfilador 5v5 Fútbol")
    st.markdown("<hr style='margin:0 0 1.5em 0; border:1.5px solid #003049'>", unsafe_allow_html=True)

    if menu == "Agregar o editar jugador":
        st.header("Editar o agregar jugador")
        nombre = st.text_input("Nombre del jugador").strip()
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
            datos[nombre].setdefault("votaciones", {})
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
            p_atr = {label: round(proms.get(key, 0),1) if key in proms else "-" for key, label in ATRIBUTOS_CAMPO}
            perfiles.append({
                "Nombre": f"{EMOJI.get(rol, '')} {nombre}",
                "Rol principal": rol,
                "Secundario": f"{sec_rol} ({sec_pct:.0f}%)",
                **p_atr,
            })
        st.dataframe(pd.DataFrame(perfiles).fillna("-"), use_container_width=True)
        st.markdown("### Descripciones de jugadores")
        for nombre, info in datos.items():
            proms = promedio_atributos(info.get("votaciones", {}))
            rol, _ = obtener_rol(proms)
            st.markdown(f"**{nombre}** — {EMOJI.get(rol,'')}: {descripcion_jugador(rol)}  \nComparables: {', '.join(COMPARABLES.get(rol, []))}")

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

        st.markdown("<div class='sectiontitle'>🏆 Mejores equipos 5v5</div>", unsafe_allow_html=True)
        def equipo_score(eq): return sum([sum(proms[p].values()) for p in eq if proms.get(p)])
        equipos = []
        for combo in combinations(jugadores_campo, 4):
            for gk in arqueros:
                eq = list(combo) + [gk]
                equipos.append( (equipo_score(eq), eq) )
        equipos = sorted(equipos, reverse=True)[:3]
        for i, (punt, team) in enumerate(equipos):
            st.markdown(f"<div class='highlight'><b>Equipo {i+1}</b>: {' | '.join(team)} <br> Total puntos: {punt:.1f} <br><i>La lógica suma todos los atributos promedio de los 5 seleccionados.</i></div>", unsafe_allow_html=True)
        # Puedes agregar aquí la lógica y visual para los equipos especiales y top 3 de cada rol.

if __name__ == "__main__":
    main()
