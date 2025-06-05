import streamlit as st
import pandas as pd
import json
import os
from itertools import combinations
import numpy as np

ARCHIVO_DATOS = 'players.json'

# Emojis por rol
EMOJI = {
    "Arquero": "🧤",
    "Gladiador": "🦾",
    "Orquestador": "🎻",
    "Wildcard": "🎲",
    "Muralla": "🧱",
}

COMPARABLES = {
    "Arquero": ["Emiliano Martínez", "Iker Casillas"],
    "Gladiador": ["Arturo Vidal", "Gennaro Gattuso", "N'Golo Kanté"],
    "Orquestador": ["Toni Kroos", "Juan Román Riquelme", "Andrea Pirlo"],
    "Wildcard": ["Ángel Di María", "Vinícius Jr", "Eden Hazard"],
    "Muralla": ["Walter Samuel", "Kalidou Koulibaly", "Paolo Maldini"]
}
DESCRIPCION = {
    "Arquero": "Especialista bajo palos, seguro y rápido de reflejos, domina el mano a mano",
    "Gladiador": "Luchador, intenso, gran recuperador,incansable.",
    "Orquestador": "El cerebro del equipo, organiza y da sentido al juego.",
    "Wildcard": "Inesperado, ciclotímico, desequilibra para bien o para mal.",
    "Muralla": "Muro defensivo, impasable y muy físico."
}

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

# --------------- SCORING Y ROLES -----------------

def score_arquero(attrs):
    return attrs.get("GK_Reaction", 0)

def score_gladiador(attrs):
    return sum([attrs.get(k,0) for k in [
        "Resilience_When_Behind","Composure","Strength_in_Duels","Stamina",
        "Recovery_Runs","Pressing_Consistency","Marking_Tightness"]])

def score_orquestador(attrs):
    return sum([attrs.get(k,0) for k in [
        "First_Touch_Control","Short_Passing_Accuracy","Vision_Free_Player","Ball_Retention",
        "Tactical_Awareness","Balance","Decision_Making_Speed","Creativity",
        "Leadership_Presence","Communication","Spatial_Awareness"]])

def score_wildcard(attrs):
    ataque = attrs.get("Acceleration",0) + attrs.get("Dribbling_Efficiency",0) + attrs.get("Power_Dribble_and_Score",0)
    ataque += attrs.get("Finishing_Precision",0) + attrs.get("Attack_Transition",0)
    defensa_baja = 15 - (attrs.get("Pressing_Consistency",0) + attrs.get("Marking_Tightness",0) + attrs.get("Recovery_Runs",0) + attrs.get("Strength_in_Duels",0))
    return ataque + defensa_baja

def score_muralla(attrs):
    return sum([attrs.get(k,0) for k in [
        "Strength_in_Duels","Defense_Transition","Leadership_Presence",
        "Recovery_Runs","Pressing_Consistency","Marking_Tightness","Tactical_Awareness"]])

def calcula_roles(attrs, tipo):
    roles = {}
    if tipo=="Arquero":
        roles["Arquero"]=score_arquero(attrs)
    else:
        roles["Gladiador"]=score_gladiador(attrs)
        roles["Orquestador"]=score_orquestador(attrs)
        roles["Wildcard"]=score_wildcard(attrs)
        roles["Muralla"]=score_muralla(attrs)
    total = sum(roles.values())
    if total>0:
        pct = {k: int(round(100*v/total)) for k,v in roles.items()}
    else:
        pct = {k:0 for k in roles}
    return roles, pct

def ruleta_rusa_score(attrs):
    """Diferencial máximo entre grupo de atributos ofensivos, defensivos, mentales"""
    ataque = sum([attrs.get(k,0) for k in [
        "Finishing_Precision","Attack_Transition","Dribbling_Efficiency","Power_Dribble_and_Score","Acceleration"]])
    defensa = sum([attrs.get(k,0) for k in [
        "Defense_Transition","Strength_in_Duels","Marking_Tightness","Recovery_Runs","Pressing_Consistency"]])
    mental = sum([attrs.get(k,0) for k in [
        "Composure","Decision_Making_Speed","Creativity"]])
    maxv = max(ataque,defensa,mental)
    minv = min(ataque,defensa,mental)
    return maxv-minv

# ------------- INTERFAZ STREAMLIT ---------------

def main():
    st.set_page_config(page_title="Perfilador 5v5", layout="wide")
    # Estilos CSS
    st.markdown("""
        <style>
        body {background-color: #eaf1fa;}
        .main {background-color: #eaf1fa;}
        .small-title {font-size:18px !important; font-weight:700;}
        .emoji {font-size:26px;}
        .jugador-nombre {font-size:18px;}
        .jug-table td {padding: 3px 8px;}
        .cuadro {background: #fff; border-radius: 12px; border: 2px solid #669bbc; box-shadow:0 2px 6px #00304910; padding:20px 18px 10px 18px; margin-bottom:14px;}
        .menu-top {display:flex; gap:20px; margin-bottom:14px;}
        .menu-top .stButton > button {background:#c1121f; color:#fff; border-radius:6px; font-weight:700;}
        .stDataFrame {background-color: #fff;}
        </style>
    """, unsafe_allow_html=True)

    if 'editing' not in st.session_state:
        st.session_state.editing = None
    if 'menu' not in st.session_state:
        st.session_state.menu = "Agregar Jugador"

    datos = cargar_datos()

    # ------ MENÚ ARRIBA ------
    st.markdown('<div class="menu-top">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("Agregar Jugador"):
            st.session_state.menu = "Agregar Jugador"
    with col2:
        if st.button("Ver Perfiles"):
            st.session_state.menu = "Ver Perfiles"
    with col3:
        if st.button("Analizar Equipos"):
            st.session_state.menu = "Analizar Equipos"
    st.markdown('</div>', unsafe_allow_html=True)
    accion = st.session_state.menu

    # ------ SIDEBAR: JUGADORES ------
    st.sidebar.title("Jugadores")
    for nombre, info in datos.items():
        roles, pct = calcula_roles(info["Atributos"], info["Tipo"])
        if info["Tipo"]=="Arquero":
            rol = "Arquero"
        else:
            rol = max(roles, key=roles.get)
        em = EMOJI.get(rol, "⚽")
        convocado = info.get("convocado", True)
        check = st.sidebar.checkbox(f"{em} {nombre}", value=convocado, key=f"cb_{nombre}")
        if check != convocado:
            datos[nombre]["convocado"] = check
            guardar_datos(datos)

    # ------ AGREGAR / EDITAR JUGADOR ------
    if accion == "Agregar Jugador":
        nombre_edit = st.session_state.editing
        es_edicion = nombre_edit is not None
        st.header("Agregar / Editar jugador")
        if es_edicion:
            tipo = datos[nombre_edit]["Tipo"]
        else:
            tipo = st.radio("Tipo de jugador:", TIPOS_JUGADOR)
        if tipo == "Arquero":
            rot = st.selectbox("Arquero:", ["Titular", "Rotativo"])
        else:
            rot = None
        default_name = nombre_edit if es_edicion else ""
        nombre = st.text_input("Nombre del Jugador", value=default_name, key="player_name")
        descripcion = st.text_input("Descripción breve", value=datos[nombre_edit].get("descripcion","") if es_edicion else "")
        if nombre:
            st.markdown("### Evalúa cada atributo (0–5)")
            attrs = {}
            for clave, preg in ATRIBUTOS_CAMPO:
                default = datos[nombre_edit]["Atributos"].get(clave, 2) if es_edicion else 2
                attrs[clave] = st.slider(preg, 0, 5, default, key=clave)
            if tipo=="Campo":
                for clave in ATR_GK_CAMPO:
                    preg = dict(ATRIBUTOS_ARQUERO)[clave]
                    default = datos[nombre_edit]["Atributos"].get(clave,2) if es_edicion else 2
                    attrs[clave] = st.slider(preg,0,5,default,key=clave)
            else:
                for clave, preg in ATRIBUTOS_ARQUERO:
                    default = datos[nombre_edit]["Atributos"].get(clave,2) if es_edicion else 2
                    attrs[clave] = st.slider(preg,0,5,default,key=clave)
            # Guardar
            if st.button("Guardar Perfil"):
                datos[nombre] = {"Tipo": tipo, "Atributos": attrs, "descripcion": descripcion, "convocado": True}
                guardar_datos(datos)
                st.session_state.editing = None
                st.success("Perfil guardado")
                st.session_state.menu = "Ver Perfiles"
                return
        else:
            st.info("Ingresa un nombre para comenzar.")

    # ------ VER PERFILES ------
    elif accion == "Ver Perfiles":
        st.header("Perfiles Guardados")
        filas = []
        for nombre, info in datos.items():
            attrs = info["Atributos"]
            roles, pct = calcula_roles(attrs, info["Tipo"])
            if info["Tipo"]=="Arquero":
                rol1, rol2 = "Arquero", None
                pct1, pct2 = 100, 0
            else:
                orden = sorted(roles, key=roles.get, reverse=True)
                rol1, rol2 = orden[0], orden[1]
                pct1, pct2 = pct[rol1], pct[rol2]
            fila = {
                "Jugador": f"{EMOJI.get(rol1,'')} {nombre}",
                "Rol Principal": f"{rol1} ({pct1}%)",
                "Rol Secundario": f"{rol2 or '-'} ({pct2}%)",
                "Descripción": info.get("descripcion",""),
                "Comparables": ", ".join(COMPARABLES[rol1]),
            }
            # Suma todos los atributos:
            for k in [a[0] for a in ATRIBUTOS_CAMPO] + [a[0] for a in ATRIBUTOS_ARQUERO]:
                fila[k] = attrs.get(k,"-")
            filas.append(fila)
        df = pd.DataFrame(filas)
        st.dataframe(df.style.set_properties(**{
            'background-color': '#fff',
            'border-radius': '6px',
            'font-size': '14px'
        }))

    # ------ ANALIZAR EQUIPOS ------
    elif accion == "Analizar Equipos":
        st.header("Análisis de Equipos y Roles")
        # Solo jugadores convocados
        nombres = [n for n in datos if datos[n].get("convocado",True)]
        if not nombres or len(nombres)<5:
            st.warning("Convoca al menos 5 jugadores.")
            return

        # Pre-cálculo de promedios
        proms = {n: datos[n]["Atributos"] for n in nombres if isinstance(datos[n]["Atributos"], dict)}

        def rol_primario(n):
            tipo = datos[n]["Tipo"]
            roles,_ = calcula_roles(datos[n]["Atributos"], tipo)
            if tipo=="Arquero":
                return "Arquero"
            else:
                return max(roles, key=roles.get)

        # ---- Equipo ideal 5v5 ----
        st.markdown('<div class="cuadro">', unsafe_allow_html=True)
        st.markdown("### 🏆 Mejor Equipo 5v5")
        st.caption("El mejor equipo maximiza la suma ponderada de roles críticos: 1 Arquero, 1 Muralla, 1 Gladiador, 1 Orquestador y 1 Wildcard, buscando máxima diversidad de roles y atributos.")
        mejores_jugadores = []
        for rol in ["Arquero","Muralla","Gladiador","Orquestador","Wildcard"]:
            if rol=="Arquero":
                candidatos = [n for n in nombres if datos[n]["Tipo"]=="Arquero"]
            else:
                candidatos = [n for n in nombres if datos[n]["Tipo"]!="Arquero" and rol_primario(n)==rol]
            if candidatos:
                mejor = max(candidatos, key=lambda x: calcula_roles(datos[x]["Atributos"], datos[x]["Tipo"])[0][rol])
                mejores_jugadores.append(mejor)
        st.markdown("**Equipo ideal:** " + ", ".join([f"{EMOJI[rol_primario(n)]} {n}" for n in mejores_jugadores]))
        st.markdown('</div>', unsafe_allow_html=True)

        # ---- Top 3 por rol ----
        for rol in ["Arquero","Muralla","Gladiador","Orquestador","Wildcard"]:
            st.markdown('<div class="cuadro">', unsafe_allow_html=True)
            st.markdown(f"#### {EMOJI[rol]} Top 3 {rol}")
            st.caption(f"Se listan los 3 jugadores con más puntuación en {rol}.")
            if rol=="Arquero":
                candidatos = [n for n in nombres if datos[n]["Tipo"]=="Arquero"]
            else:
                candidatos = [n for n in nombres if datos[n]["Tipo"]!="Arquero" and rol_primario(n)==rol]
            top3 = sorted(candidatos, key=lambda x: calcula_roles(datos[x]["Atributos"], datos[x]["Tipo"])[0][rol], reverse=True)[:3]
            st.markdown(", ".join([f"{EMOJI[rol]} {n}" for n in top3]) or "_Nadie evaluado en este rol_")
            st.markdown('</div>', unsafe_allow_html=True)

        # ---- Equipo "Catenaccio" ----
        st.markdown('<div class="cuadro">', unsafe_allow_html=True)
        st.markdown("### 🛡️ Mejor Catenaccio")
        st.caption("El equipo con mejores atributos defensivos y mentales: Muralla y Gladiador.")
        equipo_def = []
        arq = max([n for n in nombres if datos[n]["Tipo"]=="Arquero"], key=lambda x: score_arquero(datos[x]["Atributos"]), default=None)
        equipo_def.append(arq)
        resto = [n for n in nombres if n!=arq and datos[n]["Tipo"]!="Arquero"]
        # Gladiador + Muralla x2 + Orquestador
        eq_roles = [
            ("Muralla",2),("Gladiador",1),("Orquestador",1)
        ]
        usados = set()
        for rol, cant in eq_roles:
            candidates = [n for n in resto if rol_primario(n)==rol and n not in usados]
            best = sorted(candidates,key=lambda x:calcula_roles(datos[x]["Atributos"],"Campo")[0][rol],reverse=True)[:cant]
            equipo_def.extend(best)
            usados.update(best)
        st.markdown("**Equipo Catenaccio:** " + ", ".join([f"{EMOJI.get(rol_primario(n),'')} {n}" for n in equipo_def if n]))
        st.markdown('</div>', unsafe_allow_html=True)

        # ---- Equipo "Contraataque" ----
        st.markdown('<div class="cuadro">', unsafe_allow_html=True)
        st.markdown("### ⚡ Mejor Contraataque")
        st.caption("Los 5 más rápidos, ofensivos y directos (Wildcard, Attack_Transition, Acceleration, etc).")
        arq = max([n for n in nombres if datos[n]["Tipo"]=="Arquero"], key=lambda x: score_arquero(datos[x]["Atributos"]), default=None)
        resto = [n for n in nombres if n!=arq and datos[n]["Tipo"]!="Arquero"]
        candidatos = sorted(resto,key=lambda x: (
            score_wildcard(datos[x]["Atributos"])
            + datos[x]["Atributos"].get("Acceleration",0)
            + datos[x]["Atributos"].get("Attack_Transition",0)
            + datos[x]["Atributos"].get("Finishing_Precision",0)
            + datos[x]["Atributos"].get("Dribbling_Efficiency",0)
            + datos[x]["Atributos"].get("Power_Dribble_and_Score",0)
            + datos[x]["Atributos"].get("Agility",0)
            + datos[x]["Atributos"].get("Stamina",0)
            + datos[x]["Atributos"].get("Decision_Making_Speed",0)
        ), reverse=True)[:4]
        equipo_att = [arq]+candidatos
        st.markdown("**Equipo Contraataque:** " + ", ".join([f"{EMOJI.get(rol_primario(n),'')} {n}" for n in equipo_att if n]))
        st.markdown('</div>', unsafe_allow_html=True)

        # ---- Equipo "Tiki Taka" ----
        st.markdown('<div class="cuadro">', unsafe_allow_html=True)
        st.markdown("### 🕹️ Mejor Tiki-Taka")
        st.caption("Los 5 más técnicos, mentales y de control: Orquestador + atributos mentales (Creativity, Decision_Making_Speed, Composure, etc.)")
        arq = max([n for n in nombres if datos[n]["Tipo"]=="Arquero"], key=lambda x: score_arquero(datos[x]["Atributos"]), default=None)
        resto = [n for n in nombres if n!=arq and datos[n]["Tipo"]!="Arquero"]
        candidatos = sorted(resto,key=lambda x: (
            score_orquestador(datos[x]["Atributos"])
            + datos[x]["Atributos"].get("Creativity",0)
            + datos[x]["Atributos"].get("Decision_Making_Speed",0)
            + datos[x]["Atributos"].get("Composure",0)
            + datos[x]["Atributos"].get("First_Touch_Control",0)
            + datos[x]["Atributos"].get("Short_Passing_Accuracy",0)
            + datos[x]["Atributos"].get("Ball_Retention",0)
        ), reverse=True)[:4]
        equipo_tiki = [arq]+candidatos
        st.markdown("**Equipo Tiki-Taka:** " + ", ".join([f"{EMOJI.get(rol_primario(n),'')} {n}" for n in equipo_tiki if n]))
        st.markdown('</div>', unsafe_allow_html=True)

        # ---- Equipo "Ruleta Rusa" ----
        st.markdown('<div class="cuadro">', unsafe_allow_html=True)
        st.markdown("### 🎲 Mejor Ruleta Rusa")
        st.caption("Equipo con jugadores más desbalanceados: brillan mucho en ataque o defensa, pero son flojos en otra dimensión.")
        arq = max([n for n in nombres if datos[n]["Tipo"]=="Arquero"], key=lambda x: score_arquero(datos[x]["Atributos"]), default=None)
        resto = [n for n in nombres if n!=arq and datos[n]["Tipo"]!="Arquero"]
        candidatos = sorted(resto,key=lambda x: ruleta_rusa_score(datos[x]["Atributos"]), reverse=True)[:4]
        equipo_ruleta = [arq]+candidatos
        st.markdown("**Equipo Ruleta Rusa:** " + ", ".join([f"{EMOJI.get(rol_primario(n),'')} {n}" for n in equipo_ruleta if n]))
        st.markdown('</div>', unsafe_allow_html=True)

        # ---- Equipos balanceados (3 opciones) ----
        st.markdown('<div class="cuadro">', unsafe_allow_html=True)
        st.markdown("### 🤝 Equipos Balanceados")
        st.caption("Se arman 3 combinaciones distintas alternando los más y menos valorados.")
        total = {p: sum(proms[p].values()) for p in nombres if isinstance(proms[p],dict)}
        orden = sorted(total, key=total.get, reverse=True)
        for b in range(3):
            A, B = [], []
            for idx, p in enumerate(orden):
                (A if (idx+b)%2==0 else B).append(p)
            st.markdown(f"**Opción {b+1}:**\n- Equipo A: {', '.join([f'{EMOJI.get(rol_primario(n),'')} {n}' for n in A[:5]])}\n- Equipo B: {', '.join([f'{EMOJI.get(rol_primario(n),'')} {n}' for n in B[:5]])}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Pie de página
    st.sidebar.markdown(f"**Total de jugadores:** {len(datos)}")

if __name__ == "__main__":
    main()
