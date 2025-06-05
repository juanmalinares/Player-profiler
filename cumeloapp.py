import streamlit as st
import pandas as pd
import json
import os
from itertools import combinations
import numpy as np

# ======================= CONFIGURACIÓN DE TEMA =======================
st.set_page_config(page_title="Perfilador 5v5", page_icon="⚽", layout="wide")
st.markdown("""
    <style>
        body { background-color: #003049; color: #fff; }
        .stApp { background-color: #003049; }
        h1, h2, h3, h4 { color: #c1121f !important; font-size: 1.7rem !important; }
        .small-title { font-size: 1.15rem !important; color: #669bbc !important; }
        .emoji { font-size: 1.2rem !important; }
        .stDataFrame, .stTable { background-color: #003049 !important; }
    </style>
""", unsafe_allow_html=True)

# ============ EMOJIS de roles =============
EMOJI = {
    "Arquero": "🧤",
    "Muralla": "🛡️",
    "Gladiador": "🦾",
    "Orquestador": "🧠",
    "Wildcard": "🎲",
    "RuletaRusa": "💣",
    "TikiTaka": "🔄",
    "Catenaccio": "🧱",
    "Contraataque": "⚡"
}

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

ROLES = [
    ("Arquero", score_arquero, EMOJI["Arquero"]),
    ("Muralla", score_muralla, EMOJI["Muralla"]),
    ("Gladiador", score_gladiador, EMOJI["Gladiador"]),
    ("Orquestador", score_orquestador, EMOJI["Orquestador"]),
    ("Wildcard", score_wildcard, EMOJI["Wildcard"])
]

def calcular_roles(attrs, tipo):
    if tipo == "Arquero":
        roles = [("Arquero", score_arquero(attrs))]
    else:
        vals = [(rol, f(attrs)) for rol, f, _ in ROLES if rol != "Arquero"]
        vals = sorted(vals, key=lambda x: x[1], reverse=True)
        roles = vals
    total = sum(v for _, v in roles if v > 0)
    if total == 0: total = 1
    percent = [(r, v, int(100*v/total)) for r, v in roles]
    return percent

# ============= STREAMLIT APP ==============

def main():
    st.title("Perfilador de Jugadores 5v5 de Fútbol")
    barra = st.sidebar
    barra.header("Menú")
    accion = barra.selectbox("Elige acción:", ["Agregar Jugador", "Ver Perfiles", "Analizar Equipos"])
    if st.session_state.editing is not None:
        accion = "Agregar Jugador"
    datos = cargar_datos()

    # --- AGREGAR / EDITAR JUGADOR ---
    if accion == "Agregar Jugador":
        nombre_edit = st.session_state.editing
        es_edicion = nombre_edit is not None

        if es_edicion:
            st.header(f"Editando perfil de {nombre_edit}")
            tipo = datos[nombre_edit]["Tipo"]
        else:
            st.header("Agregar nuevo jugador")
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

            convocado = datos.get(nombre, {}).get("convocado", True)
            convocado = st.checkbox("Convocado (habilitado para selección de equipos)", value=convocado)
            if st.button("Guardar Perfil"):
                datos[nombre] = {"Tipo": tipo, "Atributos": attrs, "convocado": convocado}
                if tipo == "Arquero":
                    datos[nombre]["GK_Rotacion"] = rot
                guardar_datos(datos)
                st.session_state.editing = None
                st.success("Perfil guardado")
                return
        else:
            st.info("Ingresa un nombre para comenzar.")

    # --- VER PERFILES ---
    elif accion == "Ver Perfiles":
        st.header("Perfiles de Jugadores Guardados")
        st.markdown(f"**Total de jugadores evaluados:** {len(datos)}")

        if datos:
            filas = []
            for jug, info in datos.items():
                fila = {"Nombre": jug, "Tipo": info["Tipo"], "Convocado": info.get("convocado", True)}
                proms = info["Atributos"]
                roles = calcular_roles(proms, info["Tipo"])
                fila["Rol principal"] = f"{roles[0][2]} {roles[0][0]} {roles[0][1]}"
                if len(roles) > 1:
                    fila["Rol secundario"] = f"{roles[1][2]} {roles[1][0]} {roles[1][1]}"
                else:
                    fila["Rol secundario"] = ""
                fila["%Roles"] = ", ".join([f"{r} {v}%" for r, _, v in roles])
                filas.append(fila)
            df = pd.DataFrame(filas).set_index("Nombre")
            st.dataframe(df)

            st.write("---")
            for jug in list(datos.keys()):
                c1, c2, c3, c4 = st.columns([5, 1, 1, 1])
                c1.write(jug)
                if c2.button("✏️", key=f"edt_{jug}"):
                    st.session_state.editing = jug
                    return
                if c3.button("✖️", key=f"del_{jug}"):
                    datos.pop(jug)
                    guardar_datos(datos)
                    return
                if c4.button("✅" if datos[jug].get("convocado", True) else "⬜️", key=f"conv_{jug}"):
                    datos[jug]["convocado"] = not datos[jug].get("convocado", True)
                    guardar_datos(datos)
                    return
        else:
            st.info("No hay perfiles aún. Añade un jugador primero.")

    # --- ANALIZAR EQUIPOS ---
    elif accion == "Analizar Equipos":
        st.header("Compatibilidad y Construcción de Equipos")
        nombres = [p for p, info in cargar_datos().items() if info.get("convocado", True)]
        datos = cargar_datos()

        # Roles pre-calculados por jugador
        proms = {p: datos[p]["Atributos"] for p in nombres}
        tipos = {p: datos[p]["Tipo"] for p in nombres}

        # --- Utilidades ---
        def mejores_equipo(score_func, min_arqs=1, size=5):
            arqs = [p for p in nombres if tipos[p] == "Arquero"]
            campos = [p for p in nombres if tipos[p] == "Campo"]
            equipos = []
            for combo in combinations(nombres, size):
                if sum([tipos[p]=="Arquero" for p in combo]) < min_arqs:
                    continue
                score = sum(score_func(proms[p]) for p in combo)
                equipos.append((combo, score))
            equipos = sorted(equipos, key=lambda x: x[1], reverse=True)
            return equipos[:3] if equipos else []

        # ---------- MEJOR EQUIPO 5-A-SIDE (Con roles nuevos) ---------
        st.markdown(f"<span class='small-title'><b>🏆 Mejor Equipo 5-a-side (Top 3):</b></span>", unsafe_allow_html=True)
        equipo5s = mejores_equipo(lambda attrs: sum([score_muralla(attrs), score_wildcard(attrs), score_orquestador(attrs), score_gladiador(attrs)]), 1)
        for eq, score in equipo5s:
            roles = []
            usados = set()
            for rol, f, emoji in ROLES:
                if rol=="Arquero":
                    pick = [p for p in eq if tipos[p]=="Arquero"]
                else:
                    pick = [p for p in eq if tipos[p]=="Campo" and p not in usados]
                    if pick: pick = [max(pick, key=lambda p: f(proms[p]))]
                if pick:
                    usados |= set(pick)
                    roles += [f"{emoji} {pick[0]}"]
            st.markdown(f"{', '.join(roles)} | <span class='emoji'>⭐</span> Puntaje: <b>{score:.1f}</b>", unsafe_allow_html=True)

        # ---------- TOP 3 DE CADA ROL POR EQUIPO 5-A-SIDE ----------
        for rol, f, emoji in ROLES:
            if rol=="Arquero":
                top3 = sorted([p for p in nombres if tipos[p]=="Arquero"], key=lambda p: f(proms[p]), reverse=True)[:3]
            else:
                top3 = sorted([p for p in nombres if tipos[p]=="Campo"], key=lambda p: f(proms[p]), reverse=True)[:3]
            if top3:
                st.markdown(f"{emoji} <b>Top 3 {rol}:</b> " + ", ".join(top3), unsafe_allow_html=True)

        # -------- EQUIPOS TEMÁTICOS ----------
        def score_cat(attrs): # Catenaccio
            return score_muralla(attrs) + attrs.get("Composure",0) + attrs.get("Decision_Making_Speed",0)
        def score_tiki(attrs): # TikiTaka
            return score_orquestador(attrs) + attrs.get("Creativity",0) + attrs.get("Composure",0)
        def score_counter(attrs): # Contraataque
            return score_wildcard(attrs) + attrs.get("Acceleration",0) + attrs.get("Attack_Transition",0) + attrs.get("First_Touch_Control",0) + attrs.get("Finishing_Precision",0)
        def score_ruleta(attrs): # Ruleta rusa: máximo diferencial entre ataque y defensa
            ataq = score_wildcard(attrs)
            defn = score_muralla(attrs)
            ment = score_orquestador(attrs)
            diffs = [abs(ataq-defn), abs(ataq-ment), abs(defn-ment)]
            return max(diffs)

        for titulo, score_func, emoji in [
            ("Mejor Catenaccio", score_cat, EMOJI["Catenaccio"]),
            ("Mejor Tiki Taka", score_tiki, EMOJI["TikiTaka"]),
            ("Mejor Contraataque", score_counter, EMOJI["Contraataque"]),
            ("Mejor Ruleta Rusa", score_ruleta, EMOJI["RuletaRusa"]),
        ]:
            st.markdown(f"<span class='small-title'>{emoji} <b>{titulo} (Top 3):</b></span>", unsafe_allow_html=True)
            equipos = mejores_equipo(score_func, 1)
            for eq, score in equipos:
                st.markdown(f"{', '.join(eq)} | <span class='emoji'>⭐</span> Puntaje: <b>{score:.1f}</b>", unsafe_allow_html=True)

        # ------------ EQUIPOS BALANCEADOS ------------
        st.markdown("<span class='small-title'><b>🤝 Equipos Balanceados (Top 3):</b></span>", unsafe_allow_html=True)
        if len(nombres)>=10:
            total = {p: sum(proms[p].values()) for p in nombres}
            orden = sorted(total, key=total.get, reverse=True)
            A, B = [], []
            for idx, p in enumerate(orden):
                (A if idx % 2 == 0 else B).append(p)
            for i in range(3):
                st.write(f"**Equipo A:** {', '.join(A[i::3][:5])} | **Equipo B:** {', '.join(B[i::3][:5])}")

    barra.write(f"**Jugadores:** {len(datos)}")

if __name__ == "__main__":
    main()
