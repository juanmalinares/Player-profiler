import streamlit as st
import pandas as pd
import json
import os
from itertools import combinations, permutations
import numpy as np

ARCHIVO_DATOS = 'players.json'

EMOJI = {
    "Arquero": "🧤",
    "Gladiador": "🦾",
    "Orquestador": "🧠",
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

# SCORING Y ROLES
def score_arquero(attrs):
    return float(attrs.get("GK_Reaction", 0) or 0)

def score_gladiador(attrs):
    return sum([float(attrs.get(k,0) or 0) for k in [
        "Resilience_When_Behind","Composure","Strength_in_Duels","Stamina",
        "Recovery_Runs","Pressing_Consistency","Marking_Tightness"]])

def score_orquestador(attrs):
    return sum([float(attrs.get(k,0) or 0) for k in [
        "First_Touch_Control","Short_Passing_Accuracy","Vision_Free_Player","Ball_Retention",
        "Tactical_Awareness","Balance","Decision_Making_Speed","Creativity",
        "Leadership_Presence","Communication","Spatial_Awareness"]])

def score_wildcard(attrs):
    ataque = float(attrs.get("Acceleration",0) or 0) + float(attrs.get("Dribbling_Efficiency",0) or 0) + float(attrs.get("Power_Dribble_and_Score",0) or 0)
    ataque += float(attrs.get("Finishing_Precision",0) or 0) + float(attrs.get("Attack_Transition",0) or 0)
    defensa_baja = 15 - (float(attrs.get("Pressing_Consistency",0) or 0) + float(attrs.get("Marking_Tightness",0) or 0) + float(attrs.get("Recovery_Runs",0) or 0) + float(attrs.get("Strength_in_Duels",0) or 0))
    return ataque + defensa_baja

def score_muralla(attrs):
    return sum([float(attrs.get(k,0) or 0) for k in [
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
    ataque = sum([float(attrs.get(k,0) or 0) for k in [
        "Finishing_Precision","Attack_Transition","Dribbling_Efficiency","Power_Dribble_and_Score","Acceleration"]])
    defensa = sum([float(attrs.get(k,0) or 0) for k in [
        "Defense_Transition","Strength_in_Duels","Marking_Tightness","Recovery_Runs","Pressing_Consistency"]])
    mental = sum([float(attrs.get(k,0) or 0) for k in [
        "Composure","Decision_Making_Speed","Creativity"]])
    maxv = max(ataque,defensa,mental)
    minv = min(ataque,defensa,mental)
    return maxv-minv

def equipos_unicos_por_rol(jugadores, datos, roles_lista, arqueros):
    """Devuelve hasta 3 combinaciones distintas de equipos con un jugador por rol"""
    if not arqueros: return []
    equipos = []
    otros_roles = [r for r in roles_lista if r != "Arquero"]
    candidatos = {r: [j for j in jugadores if datos[j]["Tipo"]!="Arquero" and rol_primario(j, datos)==r] for r in otros_roles}
    for arq in arqueros[:3]:
        posibles = [candidatos[r] for r in otros_roles]
        for comb in permutations([j[0] if j else None for j in posibles], len(otros_roles)):
            if None in comb: continue
            equipo = [arq] + list(comb)
            if len(set(equipo))==5 and equipo not in equipos:
                equipos.append(equipo)
            if len(equipos)==3: break
        if len(equipos)==3: break
    return equipos

def rol_primario(n, datos):
    tipo = datos[n]["Tipo"]
    roles,_ = calcula_roles(datos[n]["Atributos"], tipo)
    if tipo=="Arquero":
        return "Arquero"
    else:
        return max(roles, key=roles.get)

def rol_secundario(n, datos):
    tipo = datos[n]["Tipo"]
    roles,_ = calcula_roles(datos[n]["Atributos"], tipo)
    if tipo=="Arquero":
        return None
    orden = sorted(roles.items(), key=lambda x: x[1], reverse=True)
    if len(orden)>1: return orden[1][0]
    return None

def pct_roles(n, datos):
    tipo = datos[n]["Tipo"]
    _, pct = calcula_roles(datos[n]["Atributos"], tipo)
    return pct

def main():
    st.set_page_config(page_title="Perfilador 5v5", layout="wide")
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

    # AGREGAR JUGADOR
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
            if st.button("Guardar Perfil"):
                datos[nombre] = {"Tipo": tipo, "Atributos": attrs, "descripcion": descripcion, "convocado": True}
                guardar_datos(datos)
                st.session_state.editing = None
                st.success("Perfil guardado")
                st.session_state.menu = "Ver Perfiles"
                return
        else:
            st.info("Ingresa un nombre para comenzar.")

    # VER PERFILES
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
                orden = sorted(roles.items(), key=lambda x: x[1], reverse=True)
                rol1, rol2 = orden[0][0], orden[1][0]
                pct1, pct2 = pct[rol1], pct[rol2]
            fila = {
                "Jugador": f"{EMOJI.get(rol1,'')} {nombre}",
                "Rol Principal": f"{rol1} ({pct1}%)",
                "Rol Secundario": f"{rol2 or '-'} ({pct2}%)",
                "Descripción": info.get("descripcion",""),
                "Comparables": ", ".join(COMPARABLES[rol1]),
            }
            for k in [a[0] for a in ATRIBUTOS_CAMPO] + [a[0] for a in ATRIBUTOS_ARQUERO]:
                fila[k] = attrs.get(k,"-")
            filas.append(fila)
        df = pd.DataFrame(filas)
        st.dataframe(df.style.set_properties(**{
            'background-color': '#fff',
            'border-radius': '6px',
            'font-size': '14px'
        }))

    # ANALIZAR EQUIPOS
    elif accion == "Analizar Equipos":
        st.header("Análisis de Equipos y Roles")
        nombres = [n for n in datos if datos[n].get("convocado",True)]
        if not nombres or len(nombres)<5:
            st.warning("Convoca al menos 5 jugadores.")
            return
        proms = {n: datos[n]["Atributos"] for n in nombres if isinstance(datos[n]["Atributos"], dict)}

        arqueros = [n for n in nombres if datos[n]["Tipo"]=="Arquero"]
        roles_lista = ["Arquero","Muralla","Gladiador","Orquestador","Wildcard"]
        # Equipos ideales por rol, hasta 3 variantes
        equipos = equipos_unicos_por_rol(nombres, datos, roles_lista, arqueros)
        for idx,equipo in enumerate(equipos):
            st.markdown('<div class="cuadro">', unsafe_allow_html=True)
            st.markdown(f"### 🏆 Mejor Equipo {idx+1}")
            st.caption("Incluye un jugador de cada rol, según máxima puntuación.")
            st.markdown("**Equipo:** " + ", ".join([f"{EMOJI.get(rol_primario(n, datos),'')} {n}" for n in equipo]))
            st.markdown('</div>', unsafe_allow_html=True)

        # Top 3 por rol
        for rol in ["Muralla","Gladiador","Orquestador","Wildcard"]:
            st.markdown('<div class="cuadro">', unsafe_allow_html=True)
            st.markdown(f"### {EMOJI[rol]} Top 3 {rol}")
            st.caption(f"Jugadores con mejor score de {rol}.")
            top3 = sorted([n for n in nombres if datos[n]["Tipo"]!="Arquero"],
                key=lambda n: calcula_roles(datos[n]["Atributos"],"Campo")[0][rol], reverse=True)[:3]
            st.markdown(", ".join([f"{EMOJI[rol]} {n}" for n in top3]) or "_Nadie evaluado en este rol_")
            st.markdown('</div>', unsafe_allow_html=True)

        # Equipos especiales (3 variantes c/u)
        def mejores_equipos_custom(func_score, nombre, emoji):
            equipos = []
            for i in range(3):
                resto = [n for n in nombres if datos[n]["Tipo"]!="Arquero"]
                arq = max([n for n in nombres if datos[n]["Tipo"]=="Arquero"], key=lambda x: score_arquero(datos[x]["Atributos"]), default=None)
                usados = set([arq]) if arq else set()
                candidatos = sorted(resto,key=lambda x: func_score(datos[x]["Atributos"]),reverse=True)
                equipo = [arq] + [n for n in candidatos if n not in usados][:4]
                equipos.append(equipo)
            return equipos

        # Catenaccio
        st.markdown('<div class="cuadro">', unsafe_allow_html=True)
        st.markdown("### 🛡️ Mejor Catenaccio")
        st.caption("Defensivos: Muralla y Gladiador sumados.")
        equipos_def = mejores_equipos_custom(lambda a: score_muralla(a)+score_gladiador(a), "Catenaccio", "🛡️")
        for i, equipo in enumerate(equipos_def):
            st.markdown(f"**Opción {i+1}:** " + ", ".join([f"{EMOJI.get(rol_primario(n, datos),'')} {n}" for n in equipo if n]))
        st.markdown('</div>', unsafe_allow_html=True)

        # Contraataque
        st.markdown('<div class="cuadro">', unsafe_allow_html=True)
        st.markdown("### ⚡ Mejor Contraataque")
        st.caption("Ofensivos, veloces y directos: Wildcard + Attack_Transition + Acceleration.")
        equipos_att = mejores_equipos_custom(
            lambda a: score_wildcard(a)+float(a.get("Acceleration",0))+float(a.get("Attack_Transition",0)),
            "Contraataque", "⚡")
        for i, equipo in enumerate(equipos_att):
            st.markdown(f"**Opción {i+1}:** " + ", ".join([f"{EMOJI.get(rol_primario(n, datos),'')} {n}" for n in equipo if n]))
        st.markdown('</div>', unsafe_allow_html=True)

        # Tiki-Taka
        st.markdown('<div class="cuadro">', unsafe_allow_html=True)
        st.markdown("### 🕹️ Mejor Tiki-Taka")
        st.caption("Técnicos y mentales: Orquestador + Creativity, Decision_Making_Speed, Composure.")
        equipos_tiki = mejores_equipos_custom(
            lambda a: score_orquestador(a)+float(a.get("Creativity",0))+float(a.get("Decision_Making_Speed",0))+float(a.get("Composure",0)),
            "Tiki-Taka", "🕹️")
        for i, equipo in enumerate(equipos_tiki):
            st.markdown(f"**Opción {i+1}:** " + ", ".join([f"{EMOJI.get(rol_primario(n, datos),'')} {n}" for n in equipo if n]))
        st.markdown('</div>', unsafe_allow_html=True)

        # Ruleta Rusa
        st.markdown('<div class="cuadro">', unsafe_allow_html=True)
        st.markdown("### 🎲 Mejor Ruleta Rusa")
        st.caption("Jugadores con mayor diferencial entre ataque, defensa y mental.")
        equipos_ruleta = mejores_equipos_custom(
            lambda a: ruleta_rusa_score(a),
            "Ruleta Rusa", "🎲")
        for i, equipo in enumerate(equipos_ruleta):
            st.markdown(f"**Opción {i+1}:** " + ", ".join([f"{EMOJI.get(rol_primario(n, datos),'')} {n}" for n in equipo if n]))
        st.markdown('</div>', unsafe_allow_html=True)

        # Balanceados
        st.markdown('<div class="cuadro">', unsafe_allow_html=True)
        st.markdown("### 🤝 Equipos Balanceados")
        st.caption("Balance de totales de puntuación, alternando opciones.")
        total = {p: sum([float(v) for v in proms[p].values() if isinstance(v,(int,float))]) for p in nombres if isinstance(proms[p],dict)}
        orden = sorted(total, key=total.get, reverse=True)
        for b in range(3):
            A, B = [], []
            for idx, p in enumerate(orden):
                (A if (idx+b)%2==0 else B).append(p)
            st.markdown(f"**Opción {b+1}:**\n- Equipo A: {', '.join([f'{EMOJI.get(rol_primario(n, datos),"")} {n}' for n in A[:5]])}\n- Equipo B: {', '.join([f'{EMOJI.get(rol_primario(n, datos),"")} {n}' for n in B[:5]])}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.sidebar.markdown(f"**Total de jugadores:** {len(datos)}")

if __name__ == "__main__":
    main()
