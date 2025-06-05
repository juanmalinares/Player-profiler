import streamlit as st
import pandas as pd
import json
import os
from itertools import combinations
import numpy as np

# --- Constants ---
ARCHIVO_DATOS = 'players.json'
KEY_TIPO = "Tipo"
KEY_VOTACIONES = "votaciones"
KEY_CONVOCADO = "convocado"
KEY_ATRIBUTOS_OLD = "Atributos"
DEFAULT_USER = "system_initial_data"
TIPO_CAMPO = "Campo"
TIPO_ARQUERO = "Arquero"

EMOJI = {
    "Arquero": "🧤", "Muralla": "🛡️", "Gladiador": "🦾",
    "Orquestador": "🎼", "Wildcard": "🎲", "Topadora": "🚜",
    "Versátil": "♟️" 
}

COMPARABLES = {
    "Arquero": ["Emiliano Martínez", "Iker Casillas"],
    "Gladiador": ["Arturo Vidal", "Gennaro Gattuso", "N'Golo Kanté"],
    "Orquestador": ["Toni Kroos", "Andrea Pirlo", "Xavi Hernández"],
    "Wildcard": ["Ángel Di María", "Vinícius Jr", "Eden Hazard"],
    "Muralla": ["Walter Samuel", "Kalidou Koulibaly", "Paolo Maldini"],
    "Topadora": ["Jude Bellingham", "Leon Goretzka", "Sergej Milinković-Savić"],
    "Versátil": ["Antoine Griezmann", "Bernardo Silva"] 
}

ATRIBUTOS_CAMPO_DEF = [ 
    ("First_Touch_Control", "Control del primer toque"),("Short_Passing_Accuracy","Precisión de pases cortos (<5 m)"),
    ("Vision_Free_Player", "Visión para encontrar compañeros libres"),("Finishing_Precision", "Precisión al definir ocasiones de gol"),
    ("Dribbling_Efficiency", "Eficiencia de regate en espacios reducidos"),("Power_Dribble_and_Score","Prob. de regatear a 3 y marcar"),
    ("Ball_Retention", "Retención de posesión bajo presión"),("Tactical_Awareness", "Comprensión táctica y posicionamiento"),
    ("Marking_Tightness", "Frecuencia con que pierde la marca sin balón"), 
    ("Pressing_Consistency", "Constancia en la presión sin posesión"),
    ("Recovery_Runs", "Efectividad al volver para defender"),("Acceleration", "Aceleración desde parado"),
    ("Agility", "Agilidad para cambiar de dirección"),("Stamina", "Resistencia para mantener esfuerzo intenso"),
    ("Strength_in_Duels", "Fuerza en duelos cuerpo a cuerpo"),("Balance", "Equilibrio al ser desafiado o regatear"),
    ("Composure", "Calma bajo presión"),("Decision_Making_Speed", "Rapidez para tomar buenas decisiones"),
    ("Creativity", "Creatividad para romper defensas"),("Leadership_Presence", "Liderazgo y motivación en cancha"),
    ("Communication", "Claridad y oportunidad en comunicación"),("Resilience_When_Behind","Resiliencia al ir perdiendo por ≥4 goles"),
    ("Attack_Transition", "Transición de defensa a ataque"),("Defense_Transition", "Transición de ataque a defensa"),
    ("Spatial_Awareness", "Conciencia del espacio libre alrededor"),
]
ATRIBUTOS_ARQUERO_DEF = [ 
    ("GK_Foot_Play", "Habilidad con los pies"), ("GK_Agility", "Agilidad para reaccionar"),
    ("GK_Reaction", "Rapidez de reacción en paradas"), ("GK_Bravery", "Valentía en duelos y disparos"),
    ("GK_Positioning", "Colocación y lectura de trayectorias"), ("GK_Distribution", "Precisión en distribución"),
]
ATTR_DISPLAY_NAMES = dict(ATRIBUTOS_CAMPO_DEF + ATRIBUTOS_ARQUERO_DEF)

TIPOS_JUGADOR = [TIPO_CAMPO, TIPO_ARQUERO]
ATR_GK_CAMPO = ["GK_Foot_Play", "GK_Agility", "GK_Bravery"]

def aplicar_estilos_css():
    st.markdown("""
        <style>
        body, .stApp { background-color: #eeeeee; color: #333333; }
        .css-18e3th9, .st-emotion-cache-18e3th9 { background-color: #003049; } 
        .css-18e3th9 *, .st-emotion-cache-18e3th9 * { color: #e8e8e8; } 
        .css-18e3th9 .stRadio label, .st-emotion-cache-18e3th9 .stRadio label,
        .css-18e3th9 .stCheckbox label, .st-emotion-cache-18e3th9 .stCheckbox label {
             color: #e8e8e8 !important; 
        }
        /* Ajuste para botones en la sidebar */
        .css-18e3th9 .stButton>button, .st-emotion-cache-18e3th9 .stButton>button {
            border: 1px solid #e8e8e8; /* Borde claro para botones en sidebar oscura */
            color: #e8e8e8;
            background-color: transparent; /* Sin fondo para que se vea el de la sidebar */
            padding: 0.25em 0.5em; /* Hacerlos un poco más pequeños */
            font-size: 0.8em; /* Texto más pequeño */
            margin: 0 2px; /* Pequeño margen */
        }
        .css-18e3th9 .stButton>button:hover, .st-emotion-cache-18e3th9 .stButton>button:hover {
            border-color: #c1121f;
            color: #c1121f;
        }

        .stDataFrame { background-color: #003049; color: #fff;}
        h1, h2, h3, h4, h5 { color: #c1121f; font-size: 1.25em; margin-bottom: 0.25em;}
        .highlight {background: #669bbc22; border-radius: 10px; padding: 0.7em 1em; margin-bottom:1.2em; color: #333333; border: 1px solid #669bbc44;}
        .stRadio > label { font-size: 1.1em; color: #333333 !important; display: flex; align-items: center; margin-bottom: 0.5rem;}
        .stRadio > label > div > span { color: #333333 !important; }
        .stTextInput label, .stSlider label, .stSelectbox label, .stMultiselect label { color: #333333 !important; }
        .stButton>button {border-radius: 0.5rem; border: 1px solid #003049; color: #003049; padding: 0.5em 1em;} /* Botones principales */
        .stButton>button:hover {border-color: #c1121f; color: #c1121f;}
        .stButton>button:focus:not(:active) {border-color: #c1121f; color: #c1121f; box-shadow: 0 0 0 0.2rem rgba(193, 18, 31, 0.25);}
        .stCheckbox > label > div > span { color: #333333 !important; }
        </style>
    """, unsafe_allow_html=True)

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        try:
            with open(ARCHIVO_DATOS, 'r', encoding='utf-8') as f: raw_data = json.load(f)
        except json.JSONDecodeError: return {} 
    else: return {}
    migrated_data = {}
    for name, info in raw_data.items():
        if not isinstance(info, dict): continue 
        entry = {KEY_TIPO: info.get(KEY_TIPO, TIPO_CAMPO), KEY_CONVOCADO: info.get(KEY_CONVOCADO, True)}
        if KEY_VOTACIONES in info and isinstance(info[KEY_VOTACIONES], dict): entry[KEY_VOTACIONES] = info[KEY_VOTACIONES]
        elif KEY_ATRIBUTOS_OLD in info and isinstance(info[KEY_ATRIBUTOS_OLD], dict): entry[KEY_VOTACIONES] = {DEFAULT_USER: info[KEY_ATRIBUTOS_OLD]}
        else: entry[KEY_VOTACIONES] = {} 
        migrated_data[name] = entry
    return migrated_data

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, 'w', encoding='utf-8') as f: json.dump(datos, f, indent=4, ensure_ascii=False)

def obtener_usuario():
    if "usuario_valido" not in st.session_state: st.session_state.usuario_valido = False
    if not st.session_state.usuario_valido:
        st.sidebar.title("👋 ¡Bienvenido!")
        user_in = st.sidebar.text_input("🧑‍💻 Ingresa tu nombre de usuario:", key="user_login_input", help="Este nombre se usará para tus votos.")
        if st.sidebar.button("Acceder", key="login_button"):
            if user_in.strip():
                st.session_state["usuario"] = user_in.strip()
                st.session_state.usuario_valido = True
                st.rerun()
            else: st.sidebar.warning("Por favor, ingresa un nombre de usuario.")
        return None
    return st.session_state.get("usuario")

def promedio_atributos(votaciones):
    if not votaciones or not isinstance(votaciones, dict): return {}
    valid_votes = [v for v in votaciones.values() if isinstance(v, dict)]
    if not valid_votes: return {}
    df = pd.DataFrame(valid_votes)
    if df.empty: return {}
    num_df = df.select_dtypes(include=np.number)
    return num_df.mean(axis=0).to_dict() if not num_df.empty else {}

def obtener_rol(pr, tipo_jugador=TIPO_CAMPO):
    if not pr: return "Versátil", {"Versátil": 1.0} 
    if tipo_jugador == TIPO_ARQUERO: return "Arquero", {"Arquero": 1.0}

    UMBRAL_VISION = 6.0       
    UMBRAL_PASE_CORTO = 6.0   
    UMBRAL_CREATIVIDAD = 5.0  

    es_candidato_orquestador = (
        pr.get("Vision_Free_Player", 0) >= UMBRAL_VISION and
        pr.get("Short_Passing_Accuracy", 0) >= UMBRAL_PASE_CORTO and
        pr.get("Creativity", 0) >= UMBRAL_CREATIVIDAD
    )

    score_orquestador = 0 
    if es_candidato_orquestador:
        score_orquestador = (
            pr.get("Vision_Free_Player", 0) * 3.0       
            + pr.get("Short_Passing_Accuracy", 0) * 3.0  
            + pr.get("Creativity", 0) * 2.5             
            + pr.get("Decision_Making_Speed", 0) * 1.0  
            + pr.get("First_Touch_Control", 0) * 1.0    
            + pr.get("Spatial_Awareness", 0) * 1.0      
            + pr.get("Tactical_Awareness", 0) * 0.5     
            + pr.get("Composure", 0) * 0.5              
            + pr.get("Ball_Retention", 0) * 0.5         
        )

    scores = {
        "Wildcard": pr.get("Finishing_Precision",0)*1.5 + pr.get("Attack_Transition",0)*1.5 + pr.get("Dribbling_Efficiency",0)*1.5 + pr.get("Power_Dribble_and_Score",0)*1 + pr.get("Acceleration",0)*1.5 + pr.get("Creativity",0)*1 - pr.get("Pressing_Consistency",0)*0.5 - pr.get("Recovery_Runs",0)*0.5,
        "Muralla": pr.get("Strength_in_Duels",0)*2 + pr.get("Tactical_Awareness",0)*1.5 + pr.get("Marking_Tightness",0)*1.5 + pr.get("Defense_Transition",0)*1 + pr.get("Leadership_Presence",0)*1 + pr.get("Recovery_Runs",0)*1 + pr.get("Pressing_Consistency",0)*0.5,
        "Gladiador": pr.get("Stamina",0)*2 + pr.get("Pressing_Consistency",0)*1.5 + pr.get("Recovery_Runs",0)*1.5 + pr.get("Strength_in_Duels",0)*1 + pr.get("Resilience_When_Behind",0)*1 + pr.get("Composure",0)*0.5 + pr.get("Marking_Tightness",0)*0.5,
        "Orquestador": score_orquestador, 
        "Topadora": pr.get("Power_Dribble_and_Score",0)*2 + pr.get("Finishing_Precision",0)*1.5 + pr.get("Acceleration",0)*1.5 + pr.get("Strength_in_Duels",0)*1 + pr.get("Attack_Transition",0)*1 + pr.get("Ball_Retention",0)*0.5
    }
    valid_scores = {k: v for k, v in scores.items() if v is not None} 
    sum_pos = sum(max(0,s) for s in valid_scores.values())
    
    if not valid_scores or sum_pos == 0: 
        if not es_candidato_orquestador: 
             return "Versátil", {"Versátil": 1.0} 
        return "Orquestador", {"Orquestador": 1.0} 
    
    dist = {k: (max(0,v)/sum_pos if sum_pos > 0 else 0) for k,v in valid_scores.items()}
    
    rol_princ = max(dist, key=dist.get) if dist else "Versátil" 
    
    if rol_princ == "Orquestador" and not es_candidato_orquestador:
        dist_sin_orquestador_no_candidato = {k:v for k,v in dist.items() if k != "Orquestador"}
        if dist_sin_orquestador_no_candidato and any(v > 0 for v in dist_sin_orquestador_no_candidato.values()):
            rol_princ = max(dist_sin_orquestador_no_candidato, key=dist_sin_orquestador_no_candidato.get)
        else: 
            rol_princ = "Versátil" 
            dist = {"Versátil": 1.0} 

    return rol_princ, dist

def descripcion_jugador(rol): return {
    "Muralla": "Defensa física e imponente.", "Gladiador": "Incansable y comprometido.",
    "Orquestador": "Organiza con visión, pase y creatividad. Toma decisiones clave en la creación.", 
    "Wildcard": "Desequilibrante e individualista.",
    "Topadora": "Potente y llegador.", "Arquero": "Especialista bajo palos.",
    "Versátil": "Jugador polivalente con un perfil equilibrado."
}.get(rol, "Indefinido.")

def calcular_score_equipo_general(equipo_nombres_lista, promedios_jugadores_dict):
    score_total = 0
    for jugador_nombre in equipo_nombres_lista:
        if jugador_nombre in promedios_jugadores_dict and isinstance(promedios_jugadores_dict[jugador_nombre], dict):
            score_total += sum(val for val in promedios_jugadores_dict[jugador_nombre].values() if isinstance(val, (int, float)))
    return score_total

def calcular_score_catenaccio(equipo, promedios_j, roles_e, aq_name=None):
    score, w_c, w_i, w_m, w_b = 0, 2.5, 1.5, 1.0, 0.5 
    bm, bg, bjrd = 30, 20, 10 
    nm, ng, hay_jrd = 0,0,False
    for jn in equipo:
        pr, rj = promedios_j.get(jn,{}), roles_e.get(jn,"")
        if not pr: continue
        ps = 0
        if jn == aq_name: 
            ps = pr.get("GK_Positioning",0)*w_c + pr.get("GK_Reaction",0)*w_c + pr.get("GK_Bravery",0)*w_i + pr.get("GK_Agility",0)*w_m + pr.get("GK_Distribution",0)*w_b + pr.get("Composure",0)*w_b
        else: 
            ps = pr.get("Marking_Tightness",0)*w_c + pr.get("Tactical_Awareness",0)*w_c + pr.get("Strength_in_Duels",0)*w_c + pr.get("Resilience_When_Behind",0)*w_i + pr.get("Composure",0)*w_i + pr.get("Defense_Transition",0)*w_m + pr.get("Recovery_Runs",0)*w_m + pr.get("Leadership_Presence",0)*w_m + pr.get("Pressing_Consistency",0)*w_b
            if datos_jugadores_global.get(jn, {}).get(KEY_TIPO) == TIPO_ARQUERO and jn != aq_name : 
                ps += pr.get("GK_Bravery",0) * w_b 
            if pr.get("Recovery_Runs",5.0)<4 and pr.get("Power_Dribble_and_Score",0)>6: ps-=10 
            if rj=="Muralla": nm+=1
            if rj=="Gladiador": ng+=1
            if rj not in ["Muralla","Gladiador"] and (pr.get("Acceleration",0)>=7 or pr.get("Dribbling_Efficiency",0)>=7): hay_jrd=True
        score += ps
    if nm>0: score += bm*nm
    if ng>0: score += bg*ng
    if hay_jrd: score += bjrd
    return score

def calcular_score_tikitaka(equipo, promedios_j, roles_e, aq_name=None):
    score, w_c, w_i, w_m, w_b = 0, 2.5, 1.5, 1.0, 0.5
    pusp, bo = -10, 30 
    no, ndcpm = 0,0
    for jn in equipo:
        pr, rj = promedios_j.get(jn,{}), roles_e.get(jn,"")
        if not pr: continue
        ps = 0
        if jn == aq_name: 
            ps = pr.get("GK_Foot_Play",0)*w_c + pr.get("GK_Agility",0)*w_i + pr.get("GK_Distribution",0)*w_m + pr.get("Composure",0)*w_b
        else:
            ps = pr.get("Short_Passing_Accuracy",0)*w_c + pr.get("First_Touch_Control",0)*w_c + pr.get("Vision_Free_Player",0)*w_i + pr.get("Ball_Retention",0)*w_i + pr.get("Spatial_Awareness",0)*w_i + pr.get("Tactical_Awareness",0)*w_m + pr.get("Composure",0)*w_m + pr.get("Decision_Making_Speed",0)*w_b + pr.get("Creativity",0)*w_b
            if datos_jugadores_global.get(jn, {}).get(KEY_TIPO) == TIPO_ARQUERO and jn != aq_name : 
                 ps += pr.get("GK_Foot_Play",0) * w_m 
            if pr.get("Acceleration",0)>6 and pr.get("Ball_Retention",0)<4: ps-=6
            if pr.get("Dribbling_Efficiency",0)>6 and pr.get("Short_Passing_Accuracy",0)<4: ps-=6
            if pr.get("Marking_Tightness",10)<=2 and pr.get("Strength_in_Duels",0)>=7 and pr.get("Short_Passing_Accuracy",0)<4: ps+=pusp
            if rj=="Orquestador": no+=1
            if rj in ["Muralla","Gladiador"] and pr.get("Short_Passing_Accuracy",0)>=4: ndcpm+=1 
        score += ps
    if no>0: score += bo*no
    if ndcpm>=1: score += 10 
    return score

def calcular_score_contraataque(equipo, promedios_j, roles_e, aq_name=None):
    score, w_c, w_i, w_m, w_b = 0, 2.5, 1.5, 1.0, 0.5
    pjl, bw, bt, bdtp, stfb = -10, 20, 20, 14, 7.0 
    nw, nt, jcbtd, ssc, njc = 0,0,0,0,0
    for jn in equipo:
        pr, rj = promedios_j.get(jn,{}), roles_e.get(jn,"")
        if not pr: continue
        ps = 0
        if jn == aq_name: 
            ps = pr.get("GK_Distribution",0)*w_c + pr.get("GK_Foot_Play",0)*w_i + pr.get("GK_Reaction",0)*w_m
        else:
            njc+=1
            ssc+=pr.get("Stamina",0)
            ps = pr.get("Attack_Transition",0)*w_c + pr.get("Acceleration",0)*w_c + pr.get("Finishing_Precision",0)*w_i + pr.get("Agility",0)*w_i + pr.get("Dribbling_Efficiency",0)*w_m + pr.get("Power_Dribble_and_Score",0)*w_m + pr.get("Decision_Making_Speed",0)*w_m + pr.get("Vision_Free_Player",0)*w_b
            if datos_jugadores_global.get(jn, {}).get(KEY_TIPO) == TIPO_ARQUERO and jn != aq_name: 
                ps += pr.get("GK_Distribution",0) * w_b 
            if pr.get("Ball_Retention",0)>6 and pr.get("Acceleration",0)<4: ps+=pjl
            if rj=="Wildcard": nw+=1
            if rj=="Topadora": nt+=1
            if pr.get("Defense_Transition",0)>=7: jcbtd+=1 
        score += ps
    if nw>0: score += bw*nw
    if nt>0: score += bt*nt
    if jcbtd>0: score += bdtp
    if njc>0 and (ssc/njc)>=stfb: score+=20 
    return score

# --- UI Rendering Functions ---
def render_sidebar(datos_jug, user_name):
    st.sidebar.title("⚽ Menú")
    st.sidebar.markdown(f"Usuario: **{user_name}**")
    st.sidebar.markdown("---")
    opts = ["Agregar o editar jugador", "Perfiles de jugadores", "Análisis"]
    current_selection_index = 0
    if 'menu_selection' in st.session_state and st.session_state.menu_selection in opts:
        current_selection_index = opts.index(st.session_state.menu_selection)
    else:
        st.session_state.menu_selection = opts[0] 

    menu = st.sidebar.radio("Selecciona opción:", opts, index=current_selection_index, key="main_menu_radio")
    st.session_state.menu_selection = menu
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Jugadores Convocados")
    
    # Estado para confirmación de borrado
    if 'confirm_delete_player' not in st.session_state:
        st.session_state.confirm_delete_player = None # Almacenará el nombre del jugador a borrar

    changed_convocatoria = False
    for name in sorted(datos_jug.keys()):
        info = datos_jug[name]
        proms = promedio_atributos(info.get(KEY_VOTACIONES, {}))
        rol, _ = obtener_rol(proms, info.get(KEY_TIPO, TIPO_CAMPO))
        conv = info.get(KEY_CONVOCADO, True)
        emoji = EMOJI.get(rol,"👤")

        # Layout para checkbox, nombre y botones
        col_check, col_edit, col_del = st.columns([0.7, 0.15, 0.15])

        with col_check:
            new_conv = st.checkbox(f"{emoji} {name}", value=conv, key=f"convoc_{name}_sidebar_v3")
            if conv != new_conv:
                datos_jug[name][KEY_CONVOCADO] = new_conv
                changed_convocatoria = True
        
        with col_edit:
            if st.button("✏️", key=f"edit_btn_{name}_sidebar", help=f"Editar {name}", use_container_width=True):
                st.session_state.nombre_jugador_input_ae_current = name
                st.session_state.menu_selection = "Agregar o editar jugador"
                # Limpiar selecciones de equipo manual para evitar conflictos
                if 'manual_team_selection' in st.session_state: st.session_state.manual_team_selection = []
                if 'nombre_equipo_manual_input_v3' in st.session_state: st.session_state.nombre_equipo_manual_input_v3 = ""
                st.rerun()
        
        with col_del:
            if st.button("🗑️", key=f"delete_btn_{name}_sidebar_ask", help=f"Eliminar {name}", use_container_width=True):
                st.session_state.confirm_delete_player = name # Marcar para confirmación
                st.rerun() # Rerun para mostrar la confirmación
    
    # Lógica de confirmación de borrado
    if st.session_state.confirm_delete_player:
        player_to_del = st.session_state.confirm_delete_player
        st.sidebar.markdown("---")
        st.sidebar.warning(f"¿Seguro que quieres eliminar a **{player_to_del}**?")
        col_confirm, col_cancel = st.sidebar.columns(2)
        if col_confirm.button("Sí, eliminar", key=f"confirm_del_{player_to_del}"):
            if player_to_del in datos_jug:
                del datos_jug[player_to_del]
                guardar_datos(datos_jug)
                st.success(f"Jugador '{player_to_del}' eliminado.")
                if st.session_state.get("nombre_jugador_input_ae_current") == player_to_del:
                    st.session_state.nombre_jugador_input_ae_current = ""
                st.session_state.confirm_delete_player = None # Resetear confirmación
                st.rerun()
        if col_cancel.button("Cancelar", key=f"cancel_del_{player_to_del}"):
            st.session_state.confirm_delete_player = None
            st.rerun()


    if changed_convocatoria:
        guardar_datos(datos_jug)
        st.rerun()
    return menu

def render_add_edit_player_page(datos, usuario):
    st.header("Editar o agregar jugador")
    nombre_key_session = "nombre_jugador_input_ae_current" 
    if nombre_key_session not in st.session_state:
        st.session_state[nombre_key_session] = ""

    # El nombre del jugador se toma de session_state si se vino de "editar"
    # o es el valor que el usuario está escribiendo.
    nombre_jugador_actual_input = st.text_input(
        "Nombre del jugador", 
        value=st.session_state[nombre_key_session], 
        key=nombre_key_session + "_widget_input_v2" # Nueva key para asegurar refresco
    )
    # Importante: Actualizar session_state con lo que se escribe para que los sliders usen el nombre correcto en sus keys
    st.session_state[nombre_key_session] = nombre_jugador_actual_input 
    nombre_jugador_para_sliders = nombre_jugador_actual_input.strip() # Usar el nombre actual para las keys de los sliders
    
    tipo_idx = 0
    # Usar nombre_jugador_para_sliders para cargar datos existentes
    if nombre_jugador_para_sliders and nombre_jugador_para_sliders in datos and datos[nombre_jugador_para_sliders].get(KEY_TIPO) == TIPO_ARQUERO: 
        tipo_idx = 1
    tipo_jugador = st.radio("Tipo de Jugador", TIPOS_JUGADOR, horizontal=True, index=tipo_idx, key="tipo_jugador_radio_ae_v2")
    
    attrs_actuales = {}
    player_data = datos.get(nombre_jugador_para_sliders) # Usar el nombre actual para buscar datos
    ratings = {}
    caption_text = f"{nombre_jugador_para_sliders if nombre_jugador_para_sliders else 'Nuevo Jugador'} aún no tiene valoraciones (o no existe)."
    if player_data:
        if usuario in player_data.get(KEY_VOTACIONES, {}):
            ratings = player_data[KEY_VOTACIONES][usuario]
            caption_text = f"Mostrando tus valoraciones previas para {nombre_jugador_para_sliders}."
        else:
            ratings = promedio_atributos(player_data.get(KEY_VOTACIONES, {}))
            if ratings: caption_text = f"Mostrando valoraciones promedio para {nombre_jugador_para_sliders} (aún no has votado)."
            else: caption_text = f"{nombre_jugador_para_sliders} no tiene valoraciones promedio. Establece las iniciales."
    elif nombre_jugador_para_sliders: 
        caption_text = f"Agregando nuevo jugador: {nombre_jugador_para_sliders}. Establece sus atributos."

    st.caption(caption_text)

    default_slider_val = 5 
    st.markdown("---"); st.subheader("Atributos de Campo")
    for k,q in ATRIBUTOS_CAMPO_DEF: 
        # Usar nombre_jugador_para_sliders en la key del slider para que se actualice si el nombre cambia
        attrs_actuales[k] = st.slider(q,0,10,int(round(ratings.get(k, default_slider_val))),key=f"slider_{nombre_jugador_para_sliders}_{k}_v2")
    st.markdown("---")
    if tipo_jugador == TIPO_CAMPO:
        st.subheader("Atributos Adicionales (Portero para Jugador de Campo)")
        d_aq_atr = dict(ATRIBUTOS_ARQUERO_DEF)
        for k in ATR_GK_CAMPO: 
            attrs_actuales[k] = st.slider(d_aq_atr.get(k,k.replace("_"," ")),0,10,int(round(ratings.get(k,default_slider_val))),key=f"slider_{nombre_jugador_para_sliders}_{k}_gkc_v2")
    elif tipo_jugador == TIPO_ARQUERO:
        st.subheader("Atributos de Arquero")
        for k,q in ATRIBUTOS_ARQUERO_DEF: 
            attrs_actuales[k] = st.slider(q,0,10,int(round(ratings.get(k,default_slider_val))),key=f"slider_{nombre_jugador_para_sliders}_{k}_aq_v2")

    if st.button("💾 Guardar/Actualizar Jugador", key="save_player_btn_ae_v2"):
        nombre_a_guardar = st.session_state[nombre_key_session].strip() # Confirmar el nombre desde session_state al momento del click
        if not nombre_a_guardar: 
            st.error("El nombre del jugador no puede estar vacío.")
            return
        
        if nombre_a_guardar not in datos: 
            datos[nombre_a_guardar] = {KEY_TIPO: tipo_jugador, KEY_VOTACIONES:{}, KEY_CONVOCADO:True}
        
        # Si el nombre cambió (ej. se editó un jugador y se cambió su nombre),
        # hay que borrar la entrada antigua si se quiere renombrar.
        # Por ahora, si el nombre en el input es diferente al original (si venimos de editar),
        # se creará uno nuevo o sobreescribirá si ya existe con ese nuevo nombre.
        # Si se quisiera una lógica de "renombrar" real, sería más complejo.
        
        datos[nombre_a_guardar][KEY_TIPO] = tipo_jugador 
        if KEY_VOTACIONES not in datos[nombre_a_guardar] or not isinstance(datos[nombre_a_guardar].get(KEY_VOTACIONES),dict): 
            datos[nombre_a_guardar][KEY_VOTACIONES]={} 
        datos[nombre_a_guardar][KEY_VOTACIONES][usuario] = attrs_actuales 
        if KEY_CONVOCADO not in datos[nombre_a_guardar]: 
            datos[nombre_a_guardar][KEY_CONVOCADO] = True 
        
        guardar_datos(datos)
        st.success(f"¡Jugador '{nombre_a_guardar}' guardado/actualizado con tus valoraciones!")
        st.balloons()
        
        st.session_state[nombre_key_session] = "" # Limpiar el campo del nombre del jugador
        st.rerun()

def render_player_profiles_page(datos):
    st.header("Perfiles de jugadores")
    if not datos: st.info("No hay jugadores registrados."); return
    perfiles = []
    for name in sorted(datos.keys()):
        info_jugador = datos[name]
        proms = promedio_atributos(info_jugador.get(KEY_VOTACIONES,{})) 
        rol, dist = obtener_rol(proms, info_jugador.get(KEY_TIPO, TIPO_CAMPO))
        roles_ord = sorted(dist.items(), key=lambda item:item[1], reverse=True)
        rol_sec_str = "N/A"
        if len(roles_ord) > 1 and roles_ord[0][0] != roles_ord[1][0] and roles_ord[1][1] > 0.1: 
             rol_sec_str = f"{roles_ord[1][0]} ({roles_ord[1][1]*100:.0f}%)"
        elif len(roles_ord) == 1 and roles_ord[0][0] != rol : 
             pass 

        perfil = {"Nombre":f"{EMOJI.get(rol,'👤')} {name}", "Rol principal":rol, "Rol secundario":rol_sec_str, 
                  "Descripción":descripcion_jugador(rol), "Comparables":", ".join(COMPARABLES.get(rol,["N/A"]))}
        
        all_attr_keys = [k for k,_ in ATRIBUTOS_CAMPO_DEF] + [k for k,_ in ATRIBUTOS_ARQUERO_DEF] 
        for attr_k in all_attr_keys: perfil[attr_k] = round(proms.get(attr_k,0),1) 
        perfiles.append(perfil)

    if perfiles:
        df_p = pd.DataFrame(perfiles).fillna(0)
        cols_disp = ["Nombre","Rol principal","Rol secundario","Descripción","Comparables"]
        attr_cols = sorted([c for c in df_p.columns if c not in cols_disp])
        final_cols = cols_disp + attr_cols
        for c in final_cols: 
            if c not in df_p.columns: df_p[c]=0.0
        df_display = df_p[final_cols].copy()
        for col in attr_cols: 
            df_display[col] = df_display[col].apply(lambda x: '-' if x == 0 else f"{x:.1f}".replace('.0',''))

        st.dataframe(df_display, use_container_width=True)
        st.markdown("---"); st.markdown("### Descripciones Detalladas y Comparables")
        for p_info in perfiles:
            st.markdown(f"**{p_info['Nombre']} ({p_info['Rol principal']})**: {p_info['Descripción']}")
            st.markdown(f"*Similar a: {p_info['Comparables']}*"); st.markdown("---")
    else: st.info("No hay perfiles para mostrar.")

def calcular_promedios_globales(datos_jugadores):
    todos_proms_ind = []
    for _, info in datos_jugadores.items():
        if info.get(KEY_VOTACIONES):
            proms_j = promedio_atributos(info.get(KEY_VOTACIONES, {}))
            if proms_j: todos_proms_ind.append(proms_j)
    if not todos_proms_ind: return {}
    df_g = pd.DataFrame(todos_proms_ind)
    if df_g.empty: return {}
    num_df_g = df_g.select_dtypes(include=np.number)
    return num_df_g.mean(axis=0).to_dict() if not num_df_g.empty else {}

def generar_analisis_texto(nombre_equipo_seleccionado, equipo_seleccionado_nombres, promedios_equipo_sel, roles_equipo_sel, promedios_globales_todos_jugadores, datos_completos_todos_jugadores):
    if not promedios_equipo_sel: return "No se pudieron calcular los promedios para el equipo seleccionado."
    
    team_avg_attrs_list = [promedios_equipo_sel.get(player_name, {}) for player_name in equipo_seleccionado_nombres]
    valid_player_attrs_list = [attrs for attrs in team_avg_attrs_list if attrs]
    if not valid_player_attrs_list: return "No hay suficientes datos de atributos para analizar este equipo."
    df_team_attrs = pd.DataFrame(valid_player_attrs_list)
    if df_team_attrs.empty: return "No se pudieron obtener atributos para el equipo seleccionado."
    numeric_df_team_attrs = df_team_attrs.select_dtypes(include=np.number)
    if numeric_df_team_attrs.empty: return "Los atributos del equipo seleccionado no son numéricos para el análisis."
    team_avg_attrs = numeric_df_team_attrs.mean().to_dict()

    sobreindexa_items = []
    for attr, team_val in team_avg_attrs.items():
        global_val = promedios_globales_todos_jugadores.get(attr, 0)
        attr_nombre_display = ATTR_DISPLAY_NAMES.get(attr, attr.replace("_"," "))
        if global_val > 1.0 and team_val > global_val * 1.15: 
            sobreindexa_items.append(f"{attr_nombre_display} ({team_val:.1f} vs prom. global {global_val:.1f})")
        elif team_val > 8.0 and global_val < 7.0 :
             sobreindexa_items.append(f"{attr_nombre_display} ({team_val:.1f}, destacado globalmente)")
    
    sobreindexa_text = "\n".join([f"* {item}" for item in sobreindexa_items]) if sobreindexa_items else "* El equipo muestra un perfil equilibrado sin una sobreindexación clara en atributos específicos comparado al promedio general."

    arquero_sel = None
    for nombre_jugador in equipo_seleccionado_nombres: 
        if datos_completos_todos_jugadores.get(nombre_jugador, {}).get(KEY_TIPO) == TIPO_ARQUERO:
            arquero_sel = nombre_jugador
            break
    
    scores_tacticos = {
        "Catenaccio": calcular_score_catenaccio(equipo_seleccionado_nombres, promedios_equipo_sel, roles_equipo_sel, arquero_sel),
        "Tiki-Taka": calcular_score_tikitaka(equipo_seleccionado_nombres, promedios_equipo_sel, roles_equipo_sel, arquero_sel),
        "Contraataque": calcular_score_contraataque(equipo_seleccionado_nombres, promedios_equipo_sel, roles_equipo_sel, arquero_sel),
    }
    mejor_estilo_tactico_nombre = "Ninguno destacado"
    if scores_tacticos : # Asegurarse que no está vacío
        mejor_estilo_tactico_nombre = max(scores_tacticos, key=scores_tacticos.get)

    score_equilibrio_general = calcular_score_equipo_general(equipo_seleccionado_nombres, promedios_equipo_sel)

    mejor_estilo_text = (
        f"El **mejor estilo táctico** para '{nombre_equipo_seleccionado}' parece ser: **{mejor_estilo_tactico_nombre}** "
        f"(Puntaje Táctico: {scores_tacticos.get(mejor_estilo_tactico_nombre, 0):.1f}).\n"
        f"* Puntaje de Equilibrio General del equipo: {score_equilibrio_general:.1f}."
    )

    sorted_team_attrs = sorted(team_avg_attrs.items(), key=lambda item: item[1], reverse=True)
    puntos_fuertes_items = [f"{ATTR_DISPLAY_NAMES.get(clave, clave)} ({v:.1f})" for clave,v in sorted_team_attrs[:3] if v > 6.0] 
    if not puntos_fuertes_items: puntos_fuertes_items.append("No se identifican puntos fuertes dominantes basados en atributos individuales muy altos.")
    roles_presentes_str = ", ".join(set(r for r in roles_equipo_sel.values() if r != "Arquero")) 
    if arquero_sel: 
        puntos_fuertes_items.append(f"Presencia de Arquero: {arquero_sel}.")
    if roles_presentes_str:
        puntos_fuertes_items.append(f"Combinación de roles de campo: {roles_presentes_str}.")
    else:
        if not arquero_sel: 
             puntos_fuertes_items.append("El equipo se compone de jugadores sin un rol claramente definido.")
        elif len(equipo_seleccionado_nombres) > 1: 
            puntos_fuertes_items.append("Los jugadores de campo tienen perfiles versátiles sin un rol especializado dominante.")

    puntos_fuertes_text = "\n".join([f"* {item}" for item in puntos_fuertes_items])

    puntos_debiles_items = [f"{ATTR_DISPLAY_NAMES.get(clave, clave)} ({v:.1f})" for clave,v in sorted_team_attrs[-3:] if v < 5.0] 
    if not puntos_debiles_items: puntos_debiles_items.append("El equipo no muestra debilidades críticas obvias en atributos individuales.")
    puntos_debiles_text = "\n".join([f"* {item}" for item in puntos_debiles_items])

    return f"""### Análisis del Equipo: {nombre_equipo_seleccionado}
**Sobreindexación y Perfil General:**
{sobreindexa_text}

**Estilo de Juego Sugerido:**
{mejor_estilo_text}

**Puntos Fuertes:**
{puntos_fuertes_text}

**Puntos Débiles Potenciales:**
{puntos_debiles_text}"""

def render_team_analysis_page(datos_jugadores_todos):
    st.header("Análisis de equipos y compatibilidades")
    st.markdown("---")
    st.subheader("🔬 Análisis de Equipo Manual")

    convocados_para_seleccion = {n: i for n, i in datos_jugadores_todos.items() if i.get(KEY_CONVOCADO, False)}
    if not convocados_para_seleccion:
        st.info("No hay jugadores convocados para seleccionar. Marca jugadores como convocados en la barra lateral.")
    else: 
        opciones_todos_jugadores_convocados = {
            n: f"{EMOJI.get(obtener_rol(promedio_atributos(i.get(KEY_VOTACIONES, {})), i.get(KEY_TIPO, TIPO_CAMPO))[0], '👤')} {n} ({i.get(KEY_TIPO, TIPO_CAMPO)})" 
            for n,i in convocados_para_seleccion.items()
        }
        lista_nombres_todos_convocados = list(opciones_todos_jugadores_convocados.keys())

        if 'manual_team_selection' not in st.session_state:
            st.session_state.manual_team_selection = []
        
        st.session_state.manual_team_selection = [
            p for p in st.session_state.manual_team_selection if p in lista_nombres_todos_convocados
        ]
        if len(st.session_state.manual_team_selection) > 5:
            st.session_state.manual_team_selection = st.session_state.manual_team_selection[:5]

        st.session_state.manual_team_selection = st.multiselect(
            "Selecciona 5 jugadores en total (pueden ser todos de campo o incluir un arquero):", 
            options=lista_nombres_todos_convocados,
            default=st.session_state.manual_team_selection,
            format_func=lambda x: opciones_todos_jugadores_convocados.get(x,x),
            key="multiselect_custom_team_selection", 
            max_selections=5 
        )
        
        # Usar una key diferente para el widget de text_input para asegurar que se refresca correctamente
        # si el valor en session_state cambia por otra vía (aunque aquí no es el caso principal, es buena práctica)
        nombre_equipo_manual_key_widget = "text_input_nombre_equipo_manual_widget_v4"
        nombre_equipo_manual_key_session = "nombre_equipo_manual_input_v4"

        if nombre_equipo_manual_key_session not in st.session_state:
            st.session_state[nombre_equipo_manual_key_session] = ""

        nombre_equipo_manual = st.text_input("Nombre para tu equipo (opcional):", 
                                             value=st.session_state[nombre_equipo_manual_key_session], 
                                             key=nombre_equipo_manual_key_widget).strip()
        st.session_state[nombre_equipo_manual_key_session] = nombre_equipo_manual # Actualizar session_state con el input
        
        nombre_equipo_manual_display = nombre_equipo_manual if nombre_equipo_manual else "Equipo Seleccionado"


        if st.button("⚡ Analizar Equipo Seleccionado", key="analizar_equipo_manual_btn_v3"): # Nueva key para el botón
            if len(st.session_state.manual_team_selection) == 5: 
                equipo_nombres = st.session_state.manual_team_selection
                
                arquero_en_seleccion = None
                for nombre_j in equipo_nombres:
                    if datos_jugadores_todos.get(nombre_j, {}).get(KEY_TIPO) == TIPO_ARQUERO:
                        arquero_en_seleccion = nombre_j
                        break 
                
                proms_eq_sel = {n: promedio_atributos(datos_jugadores_todos[n].get(KEY_VOTACIONES,{})) for n in equipo_nombres if n in datos_jugadores_todos}
                roles_eq_sel = {n: obtener_rol(proms_eq_sel.get(n,{}), datos_jugadores_todos[n].get(KEY_TIPO, TIPO_CAMPO))[0] for n in equipo_nombres} 
                proms_globales = calcular_promedios_globales(datos_jugadores_todos)

                if not proms_globales: st.error("No se calcularon promedios globales para comparación.")
                else: 
                    analisis_txt = generar_analisis_texto(nombre_equipo_manual_display, equipo_nombres, proms_eq_sel, roles_eq_sel, proms_globales, datos_jugadores_todos)
                    st.markdown(analisis_txt)
            else: st.warning("Por favor, selecciona exactamente 5 jugadores para analizar.") 
    
    st.markdown("---")
    
    st.subheader("🌟 Mejores Combinaciones de Equipos (Automático - 5v5: 1 Arquero + 4 de Campo)")
    convocados_auto = [n for n, i in datos_jugadores_todos.items() if i.get(KEY_CONVOCADO, False)]
    if not convocados_auto:
        st.info("No hay jugadores convocados para el análisis automático.")
    else:
        proms_conv_auto = {n: promedio_atributos(datos_jugadores_todos[n].get(KEY_VOTACIONES,{})) for n in convocados_auto}
        roles_conv_auto = {n: obtener_rol(proms_conv_auto.get(n,{}), datos_jugadores_todos[n].get(KEY_TIPO, TIPO_CAMPO))[0] for n in convocados_auto} 
        campo_conv_auto = [n for n in convocados_auto if datos_jugadores_todos[n].get(KEY_TIPO) == TIPO_CAMPO]
        aq_conv_auto = [n for n in convocados_auto if datos_jugadores_todos[n].get(KEY_TIPO) == TIPO_ARQUERO]

        if len(campo_conv_auto) < 4 or not aq_conv_auto: 
            st.info("Se necesitan al menos 4 jugadores de campo y 1 arquero convocados para el análisis automático de mejores combinaciones 5v5.")
        else:
            st.markdown("#### 🏆 Equilibrio General (5v5)")
            posibles_eq_gen = []
            for combo_c in combinations(campo_conv_auto, 4): 
                for aq_n in aq_conv_auto:
                    eq_nombres = list(combo_c) + [aq_n]
                    score = calcular_score_equipo_general(eq_nombres, proms_conv_auto)
                    posibles_eq_gen.append((score, eq_nombres, aq_n))
            
            mejores_eq_gen = sorted(posibles_eq_gen, key=lambda x: x[0], reverse=True)[:3]
            if mejores_eq_gen:
                for i, (punt, eq, gk) in enumerate(mejores_eq_gen):
                    n_eq_str = " | ".join(p if p!=gk else f"🧤{EMOJI.get('Arquero','')}{p}" for p in eq)
                    st.markdown(f"<div class='highlight'><b>Equipo {i+1}</b>: {n_eq_str} <br> Puntuación: {punt:.1f}</div>", unsafe_allow_html=True)
            else: st.info("No se generaron equipos generales (automático).")
            st.caption("Lógica: Suma de atributos promediados.")
            st.markdown("---")

            estilos = [
                {"n": "Catenaccio", "f": calcular_score_catenaccio, "e": "🛡️", "c": "Prioriza: Defensa, Mentalidad. Roles: Murallas, Gladiadores."},
                {"n": "Tiki-Taka", "f": calcular_score_tikitaka, "e": "🎼", "c": "Prioriza: Pase, Control, Visión. Roles: Orquestadores."},
                {"n": "Contraataque", "f": calcular_score_contraataque, "e": "⚡", "c": "Prioriza: Velocidad, Dribbling, Transición. Roles: Wildcards, Topadoras."}
            ]
            for est in estilos:
                st.markdown(f"#### {est['e']} {est['n']} (5v5)")
                posibles_eq_est = []
                for combo_c in combinations(campo_conv_auto, 4): 
                    for aq_n in aq_conv_auto:
                        eq_nombres = list(combo_c) + [aq_n]
                        roles_eq_act = {n_j: roles_conv_auto.get(n_j, "Desconocido") for n_j in eq_nombres}
                        score = est["f"](eq_nombres, proms_conv_auto, roles_eq_act, aq_n)
                        posibles_eq_est.append((score, eq_nombres, aq_n))
                mejores_eq_est = sorted(posibles_eq_est, key=lambda x:x[0], reverse=True)[:3]
                if mejores_eq_est:
                    for i, (punt, eq, gk) in enumerate(mejores_eq_est):
                        n_eq_str = " | ".join(p if p!=gk else f"🧤{EMOJI.get('Arquero','')}{p}" for p in eq)
                        st.markdown(f"<div class='highlight'><b>Equipo {i+1}</b>: {n_eq_str} <br> Puntuación {est['n']}: {punt:.1f}</div>", unsafe_allow_html=True)
                else: st.info(f"No se generaron equipos estilo {est['n']} (automático).")
                st.caption(est["c"]); st.markdown("---")

datos_jugadores_global = {}

def main():
    global datos_jugadores_global 
    st.set_page_config(page_title="Perfilador 5v5 Cumelo", page_icon="⚽", layout="wide")
    aplicar_estilos_css()
    usuario_actual = obtener_usuario()
    if not usuario_actual:
        st.info("👈 Por favor, ingresa un nombre de usuario en la barra lateral y presiona 'Acceder' para usar la aplicación.")
        st.stop()
    
    if 'manual_team_selection' not in st.session_state: st.session_state.manual_team_selection = []
    if 'nombre_equipo_manual_input_v3' not in st.session_state: st.session_state.nombre_equipo_manual_input_v3 = "" 


    datos_jugadores_global = cargar_datos() 
    
    menu_seleccionado = render_sidebar(datos_jugadores_global, usuario_actual) 
    if menu_seleccionado == "Agregar o editar jugador": render_add_edit_player_page(datos_jugadores_global, usuario_actual)
    elif menu_seleccionado == "Perfiles de jugadores": render_player_profiles_page(datos_jugadores_global)
    elif menu_seleccionado == "Análisis": render_team_analysis_page(datos_jugadores_global)

if __name__ == "__main__":
    main()
