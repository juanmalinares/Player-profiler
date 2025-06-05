import streamlit as st
import pandas as pd
import json
import os
from itertools import combinations
import numpy as np

# Configuración visual
st.set_page_config(page_title="Perfilador 5v5", layout="wide")
st.markdown("""
    <style>
    body, .stApp, .css-18e3th9 { background-color: #F7F9FB; }
    .cuadro { background: #00304911; border-radius: 14px; padding: 1.3em 1em 1em 1em; margin-bottom: 1.5em; }
    .bigemoji { font-size: 1.7em !important; }
    th, .stDataFrame { font-size: 15px !important; }
    </style>
""", unsafe_allow_html=True)

ARCHIVO_DATOS = 'players.json'

EMOJI = {
    "Arquero":"🧤",
    "Muralla":"🛡️",
    "Gladiador":"🦾",
    "Orquestador":"🎼",
    "Wildcard":"🎲",
    "Topadora":"🚜"
}

# --- JUGADORES COMPARABLES POR ROL ---
COMPARABLES = {
    "Arquero": ["Emiliano Martínez", "Iker Casillas"],
    "Gladiador": ["Arturo Vidal", "Gennaro Gattuso", "N'Golo Kanté"],
    "Orquestador": ["Toni Kroos", "Juan Román Riquelme", "Andrea Pirlo"],
    "Wildcard": ["Ángel Di María", "Vinícius Jr", "Eden Hazard"],
    "Muralla": ["Walter Samuel", "Kalidou Koulibaly", "Paolo Maldini"],
    "Topadora":["Jude Bellingham", "Leon Goretzka", "Sergej Milinković-Savić"],
}

# --- FUNCIONES AUXILIARES DE DATOS ---
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

# --- SCORING DE ROLES ---
def score_muralla(a):
    keys = ["Strength_in_Duels","Defense_Transition","Leadership_Presence","Recovery_Runs","Pressing_Consistency","Marking_Tightness","Tactical_Awareness"]
    return sum([float(a.get(k,0)) for k in keys])
def score_gladiador(a):
    keys = ["Resilience_When_Behind","Composure","Strength_in_Duels","Stamina","Recovery_Runs","Pressing_Consistency","Marking_Tightness"]
    return sum([float(a.get(k,0)) for k in keys])
def score_orquestador(a):
    keys = ["First_Touch_Control","Short_Passing_Accuracy","Vision_Free_Player","Ball_Retention","Tactical_Awareness","Balance","Decision_Making_Speed","Creativity","Leadership_Presence","Communication","Spatial_Awareness"]
    return sum([float(a.get(k,0)) for k in keys])
def score_wildcard(a):
    off = sum([float(a.get(k,0)) for k in ["Acceleration","Dribbling_Efficiency","Power_Dribble_and_Score","Finishing_Precision","Attack_Transition"]])
    lowdef = 15 - sum([float(a.get(k,0)) for k in ["Pressing_Consistency","Marking_Tightness","Recovery_Runs","Strength_in_Duels"]])
    return off + lowdef
def score_topadora(a):
    keys = ["Finishing_Precision","Creativity","First_Touch_Control","Short_Passing_Accuracy","Vision_Free_Player","Ball_Retention","Power_Dribble_and_Score","Decision_Making_Speed","Composure","Attack_Transition","Spatial_Awareness"]
    return sum([float(a.get(k,0)) for k in keys])
def score_arquero(a):
    keys = ["GK_Reaction","GK_Positioning","GK_Foot_Play","GK_Agility","GK_Bravery","GK_Distribution"]
    return sum([float(a.get(k,0)) for k in keys])
ROLES = [
    ("Muralla",score_muralla),
    ("Gladiador",score_gladiador),
    ("Orquestador",score_orquestador),
    ("Wildcard",score_wildcard),
    ("Topadora",score_topadora),
]
def rol_primario(n, datos):
    if datos[n]["Tipo"]=="Arquero": return "Arquero"
    a = datos[n]["Atributos"]
    scores = {rol:sc(a) for rol,sc in ROLES}
    return max(scores,key=scores.get)
def rol_secundario(n, datos):
    if datos[n]["Tipo"]=="Arquero": return ""
    a = datos[n]["Atributos"]
    scores = {rol:sc(a) for rol,sc in ROLES}
    prim = max(scores,key=scores.get)
    sec = sorted(scores.items(), key=lambda x: x[1], reverse=True)[1]
    primv = scores[prim]
    total = sum(scores.values())
    if total == 0: return ""
    return f"{sec[0]} ({int(100*sec[1]/total)}%)"
def get_percent_rol(n, datos):
    if datos[n]["Tipo"]=="Arquero": return "Arquero (100%)"
    a = datos[n]["Atributos"]
    scores = {rol:sc(a) for rol,sc in ROLES}
    prim = max(scores,key=scores.get)
    total = sum(scores.values())
    if total == 0: return ""
    return f"{prim} ({int(100*scores[prim]/total)}%)"
def get_percent_roles(n, datos):
    if datos[n]["Tipo"]=="Arquero": return "Arquero (100%)"
    a = datos[n]["Atributos"]
    scores = {rol:sc(a) for rol,sc in ROLES}
    prim, sec = sorted(scores, key=scores.get, reverse=True)[:2]
    total = sum(scores.values())
    if total == 0: return ""
    return f"{prim} ({int(100*scores[prim]/total)}%), {sec} ({int(100*scores[sec]/total)}%)"

# --- DESCRIPCIÓN DE JUGADOR ---
def descripcion_jugador(nombre, datos):
    d = datos[nombre]
    tipo = d["Tipo"]
    a = d["Atributos"]
    if tipo == "Arquero":
        return (f"{nombre} es un arquero con reflejos {rango(a['GK_Reaction'])}, habilidad con los pies {rango(a['GK_Foot_Play'])} y "
                f"posicionamiento {rango(a['GK_Positioning'])}. Destaca por su valentía ({rango(a['GK_Bravery'])}) y "
                f"reparto de juego {rango(a['GK_Distribution'])}.")
    # Campo:
    rol = rol_primario(nombre, datos)
    sec = rol_secundario(nombre, datos)
    score_rol = get_percent_roles(nombre, datos)
    base = f"{nombre} es principalmente un {rol.lower()} ({score_rol}). "
    # Características según rol
    if rol == "Muralla":
        return base + "Imponente en defensa, fuerte físicamente, con buena recuperación y siempre dispuesto a frenar ataques rivales."
    elif rol == "Gladiador":
        return base + "Incansable, comprometido en la presión y capaz de mantener el esfuerzo incluso cuando el equipo va perdiendo."
    elif rol == "Orquestador":
        return base + "Es quien organiza y da fluidez al juego, destacando en visión, control y creatividad en la circulación."
    elif rol == "Wildcard":
        return base + "Impredecible y desequilibrante, puede cambiar un partido en una jugada para bien o para mal."
    elif rol == "Topadora":
        return base + "Potente llegada al área, combina pase y definición, mentalidad ofensiva y llegada. "
    else:
        return base + "Jugador de perfil equilibrado, versátil."
def rango(val):
    val = float(val)
    if val >= 4: return "excelente"
    if val >= 3: return "bueno"
    if val >= 2: return "aceptable"
    if val >= 1: return "limitado"
    return "muy bajo"

# --- INICIALIZACIÓN STREAMLIT ---
if 'editing' not in st.session_state: st.session_state.editing = None

# --- INTERFAZ ---
def main():
    st.title("⚽ Perfilador 5v5 de Fútbol")
    menu = st.columns([1,1,1])
    opt = menu[0].button("Editar o agregar jugador")
    opt2 = menu[1].button("Perfiles de jugadores")
    opt3 = menu[2].button("Análisis")
    # Manejo simple del menú
    if not "seccion" in st.session_state:
        st.session_state.seccion = "Editar o agregar jugador"
    if opt: st.session_state.seccion = "Editar o agregar jugador"
    if opt2: st.session_state.seccion = "Perfiles de jugadores"
    if opt3: st.session_state.seccion = "Análisis"

    datos = cargar_datos()
    barra = st.sidebar
    barra.header("Jugadores")
    for n in datos:
        em = EMOJI.get(rol_primario(n, datos), "❓")
        cb = barra.checkbox(f"{em} {n}", value=datos[n].get("convocado", True), key=f"convocado_{n}")
        datos[n]["convocado"] = cb
    guardar_datos(datos)

    if st.session_state.seccion == "Editar o agregar jugador":
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
                datos[nombre] = {"Tipo": tipo, "Atributos": attrs, "convocado": True}
                if tipo == "Arquero":
                    datos[nombre]["GK_Rotacion"] = rot
                guardar_datos(datos)
                st.session_state.editing = None
                st.success("Perfil guardado")
                st.experimental_rerun()
        else:
            st.info("Ingresa un nombre para comenzar.")
    elif st.session_state.seccion == "Perfiles de jugadores":
        st.header("Perfiles de Jugadores Guardados")
        datos = cargar_datos()
        convocados = [n for n in datos if datos[n].get("convocado", True)]
        if datos:
            filas = []
            for jug, info in datos.items():
                fila = {"Nombre": jug, "Tipo": info["Tipo"]}
                fila["Rol principal"] = rol_primario(jug, datos)
                fila["Porcentajes"] = get_percent_roles(jug, datos)
                fila.update(info["Atributos"])
                filas.append(fila)
            df = pd.DataFrame(filas).set_index("Nombre")
            st.dataframe(df)
            # Sección perfiles personalizados
            st.markdown("### Perfiles de Jugador")
            for n in datos:
                st.markdown(f"**{n}**: {descripcion_jugador(n, datos)}")
                if datos[n]["Tipo"] != "Arquero":
                    comparables = COMPARABLES[rol_primario(n, datos)]
                    st.caption(f"Jugadores comparables: {', '.join(comparables)}")
                else:
                    st.caption(f"Jugadores comparables: {', '.join(COMPARABLES['Arquero'])}")
            st.write("---")
            for jug in list(datos.keys()):
                c1, c2, c3 = st.columns([6, 1, 1])
                c1.write(jug)
                if c2.button("✏️", key=f"edt_{jug}"):
                    st.session_state.editing = jug
                    st.session_state.seccion = "Editar o agregar jugador"
                    st.experimental_rerun()
                if c3.button("✖️", key=f"del_{jug}"):
                    datos.pop(jug)
                    guardar_datos(datos)
                    st.experimental_rerun()
        else:
            st.info("No hay perfiles aún. Añade un jugador primero.")
    elif st.session_state.seccion == "Análisis":
        st.header("Análisis de Equipos y Roles")
        datos = cargar_datos()
        convocados = [n for n in datos if datos[n].get("convocado", True)]
        arqueros = [n for n in convocados if datos[n]["Tipo"]=="Arquero"]
        nombres = [n for n in convocados if datos[n]["Tipo"]!="Arquero"]
        proms = {p: datos[p]["Atributos"] for p in convocados}
        # Top 3 por rol
        st.subheader("🏅 Top 3 por Rol")
        for rol, sc in ROLES + [("Topadora",score_topadora)]:
            mejores = sorted([n for n in nombres if datos[n]["Tipo"]!="Arquero"], key=lambda n: sc(datos[n]["Atributos"]), reverse=True)[:3]
            em = EMOJI.get(rol,"")
            st.markdown(f"**{em} {rol}:** " + ", ".join(mejores))
        # Mejor equipo 5-a-side: lógica igual que antes, solo roles nuevos
        st.markdown("### 🏆 Mejor Equipo 5-a-side (Equilibrado)")
        equipos = []
        for combo in combinations(convocados, 5):
            if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1:
                continue
            # Penalizar si hay más de un arquero
            campo = [p for p in combo if datos[p]["Tipo"]!="Arquero"]
            rolsc = [rol_primario(p, datos) for p in campo]
            punt = (
                score_muralla(datos[campo[0]]["Atributos"]) +
                score_gladiador(datos[campo[1]]["Atributos"]) +
                score_orquestador(datos[campo[2]]["Atributos"]) +
                score_topadora(datos[campo[3]]["Atributos"]) +
                score_wildcard(datos[campo[4]]["Atributos"])
            )
            equipos.append((punt,combo))
        equipos = sorted(equipos, reverse=True)[:3]
        for ix, (punt, combo) in enumerate(equipos,1):
            st.markdown(f"<div class='cuadro'><b>Opción {ix}:</b> {' ,'.join(combo)}<br>Lógica: Un jugador por rol clave, maximiza equilibrio.</div>",unsafe_allow_html=True)
        # Mejor equipo "Catenaccio"
        st.markdown("### 🛡️ Mejor Catenaccio (Defensivo)")
        equipos = []
        for combo in combinations(convocados, 5):
            if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1:
                continue
            campo = [p for p in combo if datos[p]["Tipo"]!="Arquero"]
            punt = sum([score_muralla(datos[p]["Atributos"])+score_gladiador(datos[p]["Atributos"]) for p in campo])
            equipos.append((punt,combo))
        equipos = sorted(equipos, reverse=True)[:3]
        for ix, (punt, combo) in enumerate(equipos,1):
            st.markdown(f"<div class='cuadro'><b>Opción {ix}:</b> {' ,'.join(combo)}<br>Lógica: Jugadores más defensivos, máxima seguridad.</div>",unsafe_allow_html=True)
        # Mejor equipo "Tiki Taka"
        st.markdown("### 🎼 Mejor Tiki Taka (Control y posesión)")
        equipos = []
        for combo in combinations(convocados, 5):
            if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1:
                continue
            campo = [p for p in combo if datos[p]["Tipo"]!="Arquero"]
            punt = sum([score_orquestador(datos[p]["Atributos"]) for p in campo])
            equipos.append((punt,combo))
        equipos = sorted(equipos, reverse=True)[:3]
        for ix, (punt, combo) in enumerate(equipos,1):
            st.markdown(f"<div class='cuadro'><b>Opción {ix}:</b> {' ,'.join(combo)}<br>Lógica: Mejor manejo de balón y control mental.</div>",unsafe_allow_html=True)
        # Mejor equipo "Contraataque"
        st.markdown("### 🚀 Mejor Contraataque (Rápidos y ofensivos)")
        equipos = []
        for combo in combinations(convocados, 5):
            if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1:
                continue
            campo = [p for p in combo if datos[p]["Tipo"]!="Arquero"]
            punt = sum([score_wildcard(datos[p]["Atributos"])+score_topadora(datos[p]["Atributos"]) for p in campo])
            equipos.append((punt,combo))
        equipos = sorted(equipos, reverse=True)[:3]
        for ix, (punt, combo) in enumerate(equipos,1):
            st.markdown(f"<div class='cuadro'><b>Opción {ix}:</b> {' ,'.join(combo)}<br>Lógica: Maximiza potencial ofensivo, velocidad y verticalidad.</div>",unsafe_allow_html=True)
        # Mejor equipo "Ruleta Rusa"
        st.markdown("### 🎲 Mejor Ruleta Rusa (Mayor diferencia entre ataque/defensa/mental)")
        equipos = []
        def ruleta_score(p):
            a = datos[p]["Atributos"]
            ofens = sum([float(a.get(k,0)) for k in ["Finishing_Precision","Creativity","First_Touch_Control","Power_Dribble_and_Score"]])
            defens = sum([float(a.get(k,0)) for k in ["Pressing_Consistency","Strength_in_Duels","Defense_Transition","Marking_Tightness"]])
            ment = sum([float(a.get(k,0)) for k in ["Composure","Decision_Making_Speed"]])
            return max(abs(ofens-defens), abs(ofens-ment), abs(ment-defens))
        for combo in combinations(convocados, 5):
            if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1: continue
            campo = [p for p in combo if datos[p]["Tipo"]!="Arquero"]
            punt = sum([ruleta_score(p) for p in campo])
            equipos.append((punt,combo))
        equipos = sorted(equipos, reverse=True)[:3]
        for ix, (punt, combo) in enumerate(equipos,1):
            st.markdown(f"<div class='cuadro'><b>Opción {ix}:</b> {' ,'.join(combo)}<br>Lógica: Más extremos/descompensados, potencial de genialidad y caos.</div>",unsafe_allow_html=True)

if __name__ == "__main__":
    main()
