import streamlit as st
import pandas as pd
import json
import os
from itertools import combinations
import numpy as np

ARCHIVO_DATOS = 'players.json'

if 'editing' not in st.session_state:
    st.session_state.editing = None

# ================== ATRIBUTOS ====================
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

# ================ UTILIDADES =====================

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, 'r') as f:
            return json.load(f)
    return {}

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, 'w') as f:
        json.dump(datos, f, indent=4)

def promedio_atributos(rankings_usuarios):
    rankings_usuarios = {k: v for k, v in rankings_usuarios.items() if isinstance(v, dict) and "Atributos" in v}
    if not rankings_usuarios: return {}
    claves = set()
    for rank in rankings_usuarios.values():
        claves |= set(rank["Atributos"].keys())
    promedios = {}
    for clave in claves:
        valores = [rank["Atributos"].get(clave, 0) for rank in rankings_usuarios.values()]
        promedios[clave] = round(sum(valores)/len(valores), 2)
    return promedios

# ========== FUNCIONES DE ROLES ===========

def score_arquero(attrs):
    return attrs.get("GK_Reaction", 0) + attrs.get("GK_Positioning", 0) + attrs.get("GK_Foot_Play", 0)

def score_muralla(attrs):
    return (attrs.get("Strength_in_Duels",0)*2 + attrs.get("Defense_Transition",0) + attrs.get("Leadership_Presence",0)
        + attrs.get("Recovery_Runs",0) + attrs.get("Pressing_Consistency",0) + attrs.get("Marking_Tightness",0)
        + attrs.get("Tactical_Awareness",0))

def score_wildcard(attrs):
    ataque = (
        attrs.get("Acceleration",0) + attrs.get("Dribbling_Efficiency",0) +
        attrs.get("Power_Dribble_and_Score",0) + attrs.get("Finishing_Precision",0) +
        attrs.get("Attack_Transition",0)
    )
    defensa_baja = (
        5 - attrs.get("Pressing_Consistency",0) + 5 - attrs.get("Marking_Tightness",0) +
        5 - attrs.get("Recovery_Runs",0) + 5 - attrs.get("Strength_in_Duels",0)
    )
    return ataque + defensa_baja

def score_orquestador(attrs):
    return (attrs.get("First_Touch_Control",0) + attrs.get("Short_Passing_Accuracy",0)
            + attrs.get("Vision_Free_Player",0) + attrs.get("Ball_Retention",0) + attrs.get("Tactical_Awareness",0)
            + attrs.get("Balance",0) + attrs.get("Decision_Making_Speed",0) + attrs.get("Creativity",0)
            + attrs.get("Leadership_Presence",0) + attrs.get("Communication",0) + attrs.get("Spatial_Awareness",0))

def score_gladiador(attrs):
    return (attrs.get("Resilience_When_Behind",0) + attrs.get("Composure",0) + attrs.get("Strength_in_Duels",0)
            + attrs.get("Stamina",0) + attrs.get("Recovery_Runs",0) + attrs.get("Pressing_Consistency",0)
            + attrs.get("Marking_Tightness",0))

def roles_scores(attrs):
    roles = {
        "Arquero": score_arquero(attrs),
        "Muralla": score_muralla(attrs),
        "Wildcard": score_wildcard(attrs),
        "Orquestador": score_orquestador(attrs),
        "Gladiador": score_gladiador(attrs),
    }
    total = sum(v for v in roles.values() if v > 0)
    porcentajes = {k: (v/total*100 if total > 0 else 0) for k, v in roles.items()}
    principal = max(roles, key=roles.get)
    secundarios = sorted([k for k in roles if k != principal], key=lambda k: roles[k], reverse=True)
    return principal, secundarios, porcentajes, roles

def score_ruletarusa(attrs):
    ataque = [
        "Acceleration","Attack_Transition","Finishing_Precision","Dribbling_Efficiency",
        "Power_Dribble_and_Score","First_Touch_Control","Short_Passing_Accuracy","Agility"
    ]
    defensa = [
        "Defense_Transition","Strength_in_Duels","Marking_Tightness","Pressing_Consistency",
        "Recovery_Runs","Stamina","Tactical_Awareness"
    ]
    mental = [
        "Composure","Decision_Making_Speed","Leadership_Presence","Communication",
        "Vision_Free_Player","Creativity","Spatial_Awareness","Ball_Retention"
    ]
    vals = lambda keys: np.mean([attrs.get(k,0) for k in keys])
    scores = [vals(ataque), vals(defensa), vals(mental)]
    diff = max(scores) - min(scores)
    return diff

# ============ CSS DARK THEME & COLORES ============
def dark_css():
    st.markdown("""
        <style>
        html, body, [class*="css"]  {
            background-color: #003049 !important;
        }
        h1, h2, h3 {
            color: #c1121f !important;
            font-size: 1.5rem !important;
            margin-top: 0.6em !important;
            margin-bottom: 0.2em !important;
        }
        .stMarkdown, .stText, .stDataFrame, .stTable, .st-bw, .st-c8, .stSelectbox label, .stRadio label {
            color: #f7f7ff !important;
        }
        .stButton>button {
            background-color: #c1121f;
            color: #fff;
            font-weight: bold;
            border-radius: 6px;
        }
        .st-bw, .st-c8 {color: #669bbc !important;}
        .stCheckbox, .stRadio {color: #c1121f !important;}
        .css-10trblm {color: #669bbc !important;}
        .st-emotion-cache-ocqkz7 {background-color: #003049 !important;}
        .sidebar .sidebar-content {background-color: #212939 !important;}
        </style>
        """, unsafe_allow_html=True)

# ================ MAIN STREAMLIT ================
def main():
    dark_css()
    st.title("Perfilador de Jugadores 5v5 – Colaborativo, Roles y Equipos Especiales")

    usuario = st.sidebar.text_input("Tu nombre (anónimo en la interfaz)", value=st.session_state.get("usuario", ""))
    if usuario:
        st.session_state["usuario"] = usuario
    if not usuario:
        st.warning("Por favor ingresa tu nombre de usuario (anónimo) en la barra lateral para continuar.")
        st.stop()

    barra = st.sidebar
    barra.header("Menú")
    accion = barra.selectbox("Elige acción:", [
        "Agregar/Rankear Jugador", 
        "Ver Perfiles Promediados", 
        "Analizar Equipos"
    ])
    if st.session_state.editing is not None:
        accion = "Agregar/Rankear Jugador"
    datos = cargar_datos()

    # ---- Convocatoria (sidebar)
    st.sidebar.markdown("## Convocatoria")
    convocados = {}
    for nombre in datos:
        convocados[nombre] = st.sidebar.checkbox(f"{nombre}", value=datos[nombre].get("convocado", True))
    for nombre in datos:
        datos[nombre]["convocado"] = convocados[nombre]
    guardar_datos(datos)

    # --- AGREGAR / RANQUEAR JUGADOR ---
    if accion == "Agregar/Rankear Jugador":
        jugadores = list(datos.keys())
        nombre = st.selectbox("Jugador a rankear", ["Nuevo..."] + jugadores)
        if nombre == "Nuevo...":
            nombre_nuevo = st.text_input("Nombre del nuevo jugador", "")
            if nombre_nuevo:
                nombre = nombre_nuevo
        if nombre:
            tipo = st.radio("Tipo de jugador:", TIPOS_JUGADOR, key=f"tipo_{nombre}")
            st.markdown("### Evalúa cada atributo (0–5)")
            attrs = {}
            for clave, preg in ATRIBUTOS_CAMPO:
                valor = datos.get(nombre, {}).get(usuario, {}).get("Atributos", {}).get(clave, 2)
                attrs[clave] = st.slider(preg, 0, 5, valor, key=f"{clave}_{nombre}")
            if tipo == "Campo":
                for clave in ATR_GK_CAMPO:
                    preg = dict(ATRIBUTOS_ARQUERO)[clave]
                    valor = datos.get(nombre, {}).get(usuario, {}).get("Atributos", {}).get(clave, 2)
                    attrs[clave] = st.slider(preg, 0, 5, valor, key=f"{clave}_{nombre}")
            else:
                for clave, preg in ATRIBUTOS_ARQUERO:
                    valor = datos.get(nombre, {}).get(usuario, {}).get("Atributos", {}).get(clave, 2)
                    attrs[clave] = st.slider(preg, 0, 5, valor, key=f"{clave}_{nombre}")
            if st.button("Guardar Ranking"):
                if nombre not in datos:
                    datos[nombre] = {}
                datos[nombre][usuario] = {"Atributos": attrs, "Tipo": tipo}
                if "convocado" not in datos[nombre]:
                    datos[nombre]["convocado"] = True
                guardar_datos(datos)
                st.success("Ranking guardado correctamente.")

    # --- VER PERFILES PROMEDIADOS ---
    elif accion == "Ver Perfiles Promediados":
        st.header("Perfiles de Jugadores (Promedio de rankings)")
        if datos:
            filas = []
            for jug, rankings in datos.items():
                if not rankings.get("convocado", True):
                    continue
                rankings_usuarios = {k: v for k, v in rankings.items() if isinstance(v, dict) and "Atributos" in v}
                attrs_avg = promedio_atributos(rankings_usuarios)
                tipos = [rank.get("Tipo") for rank in rankings_usuarios.values() if "Tipo" in rank]
                tipo = max(set(tipos), key=tipos.count) if tipos else ""
                principal, secundarios, porcentajes, roles = roles_scores(attrs_avg)
                sec = secundarios[0] if secundarios else ""
                fila = {
                    "Nombre": jug,
                    "Tipo": tipo,
                    "Rol principal": f"{principal} ({porcentajes[principal]:.0f}%)",
                    "Rol secundario": f"{sec} ({porcentajes[sec]:.0f}%)" if sec else "",
                    **attrs_avg
                }
                filas.append(fila)
            df = pd.DataFrame(filas).set_index("Nombre")
            st.dataframe(df)
        else:
            st.info("No hay rankings aún.")

    # --- ANALIZAR EQUIPOS ---
    elif accion == "Analizar Equipos":
        st.header("Análisis de equipos")
        nombres = [n for n in datos.keys() if datos[n].get("convocado", True)]
        if len(nombres) < 5:
            st.warning("Se necesitan al menos 5 jugadores convocados.")
        else:
            proms = {p: promedio_atributos({
                k: v for k, v in datos[p].items() if isinstance(v, dict) and "Atributos" in v
            }) for p in nombres}

            # TOP 3 de cada rol
            for rol, fun in [
                ("Gladiador", score_gladiador),
                ("Orquestador", score_orquestador),
                ("Wildcard", score_wildcard),
                ("Muralla", score_muralla),
                ("Arquero", score_arquero),
                ("Ruleta Rusa", score_ruletarusa),
            ]:
                top3 = sorted(nombres, key=lambda p: fun(proms[p]), reverse=True)[:3]
                st.markdown(f"<span style='color:#669bbc; font-size:1.1rem;'><b>Top 3 {rol}:</b> {' | '.join(top3)}</span>", unsafe_allow_html=True)

            # MEJOR EQUIPO (uno por rol)
            equipo = []
            rol_funcs = [
                ("Arquero", score_arquero),
                ("Muralla", score_muralla),
                ("Wildcard", score_wildcard),
                ("Orquestador", score_orquestador),
                ("Gladiador", score_gladiador),
            ]
            usados = set()
            for rol, fun in rol_funcs:
                disponibles = [p for p in nombres if p not in usados]
                pick = max(disponibles, key=lambda p: fun(proms[p]))
                equipo.append(f"{pick} ({rol})")
                usados.add(pick)
            st.markdown(f"<span style='color:#c1121f; font-size:1.2rem;'><b>Mejor Equipo 5-a-side (Roles nuevos):</b> {', '.join(equipo)}</span>", unsafe_allow_html=True)

            # Mejor Catenaccio (más defensivos, mucha muralla+gladiador+mental)
            def score_cat(p):
                return (
                    score_muralla(proms[p]) + score_gladiador(proms[p]) +
                    proms[p].get("Composure",0) + proms[p].get("Tactical_Awareness",0) +
                    proms[p].get("Leadership_Presence",0) + proms[p].get("Communication",0) +
                    proms[p].get("Stamina",0) + proms[p].get("Recovery_Runs",0)
                )
            # Mejor Contraataque (wildcard, ataque y velocidad)
            def score_contra(p):
                ofens = score_wildcard(proms[p]) + proms[p].get("Acceleration",0) + proms[p].get("Attack_Transition",0)
                skill = proms[p].get("First_Touch_Control",0)+proms[p].get("Short_Passing_Accuracy",0)+proms[p].get("Finishing_Precision",0)
                skill += proms[p].get("Dribbling_Efficiency",0)+proms[p].get("Power_Dribble_and_Score",0)+proms[p].get("Agility",0)
                skill += proms[p].get("Stamina",0)+proms[p].get("Decision_Making_Speed",0)
                return ofens + skill
            # Mejor Tiki-Taka (control, pase, mental)
            def score_tikitaka(p):
                return (
                    proms[p].get("First_Touch_Control",0) +
