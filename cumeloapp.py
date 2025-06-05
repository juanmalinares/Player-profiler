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
    "Orquestador": "🎼", "Wildcard": "🎲", "Topadora": "🚜"
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
    ("First_Touch_Control", "Control del primer toque"),("Short_Passing_Accuracy","Precisión de pases cortos (<5 m)"),
    ("Vision_Free_Player", "Visión para encontrar compañeros libres"),("Finishing_Precision", "Precisión al definir ocasiones de gol"),
    ("Dribbling_Efficiency", "Eficiencia de regate en espacios reducidos"),("Power_Dribble_and_Score","Prob. de regatear a 3 y marcar"),
    ("Ball_Retention", "Retención de posesión bajo presión"),("Tactical_Awareness", "Comprensión táctica y posicionamiento"),
    ("Marking_Tightness", "Frecuencia con que pierde la marca sin balón"),("Pressing_Consistency", "Constancia en la presión sin posesión"),
    ("Recovery_Runs", "Efectividad al volver para defender"),("Acceleration", "Aceleración desde parado"),
    ("Agility", "Agilidad para cambiar de dirección"),("Stamina", "Resistencia para mantener esfuerzo intenso"),
    ("Strength_in_Duels", "Fuerza en duelos cuerpo a cuerpo"),("Balance", "Equilibrio al ser desafiado o regatear"),
    ("Composure", "Calma bajo presión"),("Decision_Making_Speed", "Rapidez para tomar buenas decisiones"),
    ("Creativity", "Creatividad para romper defensas"),("Leadership_Presence", "Liderazgo y motivación en cancha"),
    ("Communication", "Claridad y oportunidad en comunicación"),("Resilience_When_Behind","Resiliencia al ir perdiendo por ≥4 goles"),
    ("Attack_Transition", "Transición de defensa a ataque"),("Defense_Transition", "Transición de ataque a defensa"),
    ("Spatial_Awareness", "Conciencia del espacio libre alrededor"),
]

ATRIBUTOS_ARQUERO = [
    ("GK_Foot_Play", "Habilidad con los pies"), ("GK_Agility", "Agilidad para reaccionar"),
    ("GK_Reaction", "Rapidez de reacción en paradas"), ("GK_Bravery", "Valentía en duelos y disparos"),
    ("GK_Positioning", "Colocación y lectura de trayectorias"), ("GK_Distribution", "Precisión en distribución"),
]

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
        .stDataFrame { background-color: #003049; color: #fff;}
        h1, h2, h3, h4, h5 { color: #c1121f; font-size: 1.25em; margin-bottom: 0.25em;}
        .highlight {background: #669bbc22; border-radius: 10px; padding: 0.7em 1em; margin-bottom:1.2em; color: #333333; border: 1px solid #669bbc44;}
        .stRadio > label { font-size: 1.1em; color: #333333 !important; /* Ensure main area radio labels are dark */ display: flex; align-items: center; margin-bottom: 0.5rem;}
        .stRadio > label > div > span { color: #333333 !important; } /* Text part of radio */
        .stTextInput label, .stSlider label, .stSelectbox label, .stMultiselect label { color: #333333 !important; }
        .stButton>button {border-radius: 0.5rem; border: 1px solid #003049; color: #003049; padding: 0.5em 1em;}
        .stButton>button:hover {border-color: #c1121f; color: #c1121f;}
        .stButton>button:focus:not(:active) {border-color: #c1121f; color: #c1121f; box-shadow: 0 0 0 0.2rem rgba(193, 18, 31, 0.25);}
        .stCheckbox > label > div > span { color: #333333 !important; /* For main area checkbox labels */}
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
    if not pr: return "Orquestador", {"Orquestador": 1.0} 
    if tipo_jugador == TIPO_ARQUERO: return "Arquero", {"Arquero": 1.0}

    scores = {
        "Wildcard": pr.get("Finishing_Precision",0)*1.5 + pr.get("Attack_Transition",0)*1.5 + pr.get("Dribbling_Efficiency",0)*1.5 + pr.get("Power_Dribble_and_Score",0)*1 + pr.get("Acceleration",0)*1.5 + pr.get("Creativity",0)*1 - pr.get("Pressing_Consistency",0)*0.5 - pr.get("Recovery_Runs",0)*0.5,
        "Muralla": pr.get("Strength_in_Duels",0)*2 + pr.get("Tactical_Awareness",0)*1.5 + pr.get("Marking_Tightness",0)*1.5 + pr.get("Defense_Transition",0)*1 + pr.get("Leadership_Presence",0)*1 + pr.get("Recovery_Runs",0)*1 + pr.get("Pressing_Consistency",0)*0.5,
        "Gladiador": pr.get("Stamina",0)*2 + pr.get("Pressing_Consistency",0)*1.5 + pr.get("Recovery_Runs",0)*1.5 + pr.get("Strength_in_Duels",0)*1 + pr.get("Resilience_When_Behind",0)*1 + pr.get("Composure",0)*0.5 + pr.get("Marking_Tightness",0)*0.5,
        "Orquestador": pr.get("Vision_Free_Player",0)*2.5 + pr.get("Short_Passing_Accuracy",0)*2.5 + pr.get("Creativity",0)*2 + pr.get("Decision_Making_Speed",0)*1.5 + pr.get("First_Touch_Control",0)*1.5 + pr.get("Spatial_Awareness",0)*1.5 + pr.get("Tactical_Awareness",0)*1 + pr.get("Composure",0)*1 + pr.get("Ball_Retention",0)*0.5,
        "Topadora": pr.get("Power_Dribble_and_Score",0)*2 + pr.get("Finishing_Precision",0)*1.5 + pr.get("Acceleration",0)*1.5 + pr.get("Strength_in_Duels",0)*1 + pr.get("Attack_Transition",0)*1 + pr.get("Ball_Retention",0)*0.5
    }
    sum_pos = sum(max(0,s) for s in scores.values() if s)
    if not scores or sum_pos == 0: return "Orquestador", {"Orquestador": 1.0}
    dist = {k: (max(0,v)/sum_pos if sum_pos > 0 else 0) for k,v in scores.items() if v is not None}
    return max(dist, key=dist.get) if dist else ("Orquestador", {"Orquestador": 1.0}), dist

def descripcion_jugador(rol): return {
    "Muralla": "Defensa física e imponente.", "Gladiador": "Incansable y comprometido.",
    "Orquestador": "Organiza con visión y pase.", "Wildcard": "Desequilibrante e individualista.",
    "Topadora": "Potente y llegador.", "Arquero": "Especialista bajo palos."
}.get(rol, "Versátil.")

# --- Style Specific Scoring Functions ---
def calcular_score_catenaccio(equipo, promedios_j, roles_e, aq_name):
    score, w_c, w_i, w_m, w_b = 0, 2.5, 1.5, 1.0, 0.5
    bm, bg, bjrd = 15, 10, 5
    nm, ng, hay_jrd = 0,0,False
    for jn in equipo:
        pr, rj = promedios_j.get(jn,{}), roles_e.get(jn,"")
        if not pr: continue
        ps = 0
        if jn == aq_name: ps = pr.get("GK_Positioning",0)*w_c + pr.get("GK_Reaction",0)*w_c + pr.get("GK_Bravery",0)*w_i + pr.get("GK_Agility",0)*w_m + pr.get("GK_Distribution",0)*w_b + pr.get("Composure",0)*w_b
        else:
            ps = pr.get("Marking_Tightness",0)*w_c + pr.get("Tactical_Awareness",0)*w_c + pr.get("Strength_in_Duels",0)*w_c + pr.get("Resilience_When_Behind",0)*w_i + pr.get("Composure",0)*w_i + pr.get("Defense_Transition",0)*w_m + pr.get("Recovery_Runs",0)*w_m + pr.get("Leadership_Presence",0)*w_m + pr.get("Pressing_Consistency",0)*w_b
            if pr.get("Recovery_Runs",2.5)<2 and pr.get("Power_Dribble_and_Score",0)>3: ps-=5
            if rj=="Muralla": nm+=1
            if rj=="Gladiador": ng+=1
            if rj not in ["Muralla","Gladiador"] and (pr.get("Acceleration",0)>=4 or pr.get("Dribbling_Efficiency",0)>=4): hay_jrd=True
        score += ps
    if nm>0: score += bm*nm
    if ng>0: score += bg*ng
    if hay_jrd: score += bjrd
    return score

def calcular_score_tikitaka(equipo, promedios_j, roles_e, aq_name):
    score, w_c, w_i, w_m, w_b = 0, 2.5, 1.5, 1.0, 0.5
    pusp, bo = -5, 15
    no, ndcpm = 0,0
    for jn in equipo:
        pr, rj = promedios_j.get(jn,{}), roles_e.get(jn,"")
        if not pr: continue
        ps = 0
        if jn == aq_name: ps = pr.get("GK_Foot_Play",0)*w_c + pr.get("GK_Agility",0)*w_i + pr.get("GK_Distribution",0)*w_m + pr.get("Composure",0)*w_b
        else:
            ps = pr.get("Short_Passing_Accuracy",0)*w_c + pr.get("First_Touch_Control",0)*w_c + pr.get("Vision_Free_Player",0)*w_i + pr.get("Ball_Retention",0)*w_i + pr.get("Spatial_Awareness",0)*w_i + pr.get("Tactical_Awareness",0)*w_m + pr.get("Composure",0)*w_m + pr.get("Decision_Making_Speed",0)*w_b + pr.get("Creativity",0)*w_b
            if pr.get("Acceleration",0)>3 and pr.get("Ball_Retention",0)<2: ps-=3
            if pr.get("Dribbling_Efficiency",0)>3 and pr.get("Short_Passing_Accuracy",0)<2: ps-=3
            if pr.get("Marking_Tightness",5)<=1 and pr.get("Strength_in_Duels",0)>=4 and pr.get("Short_Passing_Accuracy",0)<2: ps+=pusp
            if rj=="Orquestador": no+=1
            if rj in ["Muralla","Gladiador"] and pr.get("Short_Passing_Accuracy",0)>=2: ndcpm+=1
        score += ps
    if no>0: score += bo*no
    if ndcpm>=1: score += 5
    return score

def calcular_score_contraataque(equipo, promedios_j, roles_e, aq_name):
    score, w_c, w_i, w_m, w_b = 0, 2.5, 1.5, 1.0, 0.5
    pjl, bw, bt, bdtp, stfb = -5, 10, 10, 7, 3.5
    nw, nt, jcbtd, ssc, njc = 0,0,0,0,0
    for jn in equipo:
        pr, rj = promedios_j.get(jn,{}), roles_e.get(jn,"")
        if not pr: continue
        ps = 0
        if jn == aq_name: ps = pr.get("GK_Distribution",0)*w_c + pr.get("GK_Foot_Play",0)*w_i + pr.get("GK_Reaction",0)*w_m
        else:
            njc+=1
            ssc+=pr.get("Stamina",0)
            ps = pr.get("Attack_Transition",0)*w_c + pr.get("Acceleration",0)*w_c + pr.get("Finishing_Precision",0)*w_i + pr.get("Agility",0)*w_i + pr.get("Dribbling_Efficiency",0)*w_m + pr.get("Power_Dribble_and_Score",0)*w_m + pr.get("Decision_Making_Speed",0)*w_m + pr.get("Vision_Free_Player",0)*w_b
            if pr.get("Ball_Retention",0)>3 and pr.get("Acceleration",0)<2: ps+=pjl
            if rj=="Wildcard": nw+=1
            if rj=="Topadora": nt+=1
            if pr.get("Defense_Transition",0)>=4: jcbtd+=1
        score += ps
    if nw>0: score += bw*nw
    if nt>0: score += bt*nt
    if jcbtd>0: score += bdtp
    if njc>0 and (ssc/njc)>=stfb: score+=10
    return score

# --- UI Rendering Functions ---
def render_sidebar(datos_jug, user_name):
    st.sidebar.title("⚽ Menú")
    st.sidebar.markdown(f"Usuario: **{user_name}**")
    st.sidebar.markdown("---")
    opts = ["Agregar o editar jugador", "Perfiles de jugadores", "Análisis"]
    if 'menu_selection' not in st.session_state: st.session_state.menu_selection = opts[0]
    if st.session_state.menu_selection not in opts: st.session_state.menu_selection = opts[0]
    menu = st.sidebar.radio("Selecciona opción:", opts, index=opts.index(st.session_state.menu_selection), key="main_menu_radio")
    st.session_state.menu_selection = menu
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Jugadores Convocados")
    changed = False
    for name in sorted(datos_jug.keys()):
        info = datos_jug[name]
        proms = promedio_atributos(info.get(KEY_VOTACIONES,{}))
        rol,_ = obtener_rol(proms, info.get(KEY_TIPO, TIPO_CAMPO))
        conv = info.get(KEY_CONVOCADO, True)
        emoji = EMOJI.get(rol,"👤")
        new_conv = st.sidebar.checkbox(f"{emoji} {name}", value=conv, key=f"convoc_{name}_sidebar")
        if datos_jug[name].get(KEY_CONVOCADO,True) != new_conv:
            datos_jug[name][KEY_CONVOCADO] = new_conv
            changed = True
    if changed:
        guardar_datos(datos_jug)
        st.rerun()
    return menu

def render_add_edit_player_page(datos, usuario):
    st.header("Editar o agregar jugador")
    nombre_key = "nombre_jugador_input_ae"
    nombre_jugador = st.text_input("Nombre del jugador", key=nombre_key, value=st.session_state.get(nombre_key,"")).strip()
    
    tipo_idx = 0
    if nombre_jugador and nombre_jugador in datos and datos[nombre_jugador].get(KEY_TIPO) == TIPO_ARQUERO: tipo_idx = 1
    tipo_jugador = st.radio("Tipo de Jugador", TIPOS_JUGADOR, horizontal=True, index=tipo_idx, key="tipo_jugador_radio_ae")
    
    attrs_actuales = {}
    player_data = datos.get(nombre_jugador)
    ratings = {}
    caption_text = f"{nombre_jugador} aún no tiene valoraciones."
    if player_data:
        if usuario in player_data.get(KEY_VOTACIONES, {}):
            ratings = player_data[KEY_VOTACIONES][usuario]
            caption_text = f"Mostrando tus valoraciones previas para {nombre_jugador}."
        else:
            ratings = promedio_atributos(player_data.get(KEY_VOTACIONES, {}))
            if ratings: caption_text = f"Mostrando valoraciones promedio para {nombre_jugador} (aún no has votado)."
    st.caption(caption_text)

    st.markdown("---"); st.subheader("Atributos de Campo")
    for k,q in ATRIBUTOS_CAMPO: attrs_actuales[k] = st.slider(q,0,5,int(round(ratings.get(k,2))),key=f"{nombre_key}_{k}_s")
    st.markdown("---")
    if tipo_jugador == TIPO_CAMPO:
        st.subheader("Atributos Adicionales (Portero para Jugador de Campo)")
        d_aq_atr = dict(ATRIBUTOS_ARQUERO)
        for k in ATR_GK_CAMPO: attrs_actuales[k] = st.slider(d_aq_atr.get(k,k.replace("_"," ")),0,5,int(round(ratings.get(k,2))),key=f"{nombre_key}_{k}_gkc_s")
    elif tipo_jugador == TIPO_ARQUERO:
        st.subheader("Atributos de Arquero")
        for k,q in ATRIBUTOS_ARQUERO: attrs_actuales[k] = st.slider(q,0,5,int(round(ratings.get(k,2))),key=f"{nombre_key}_{k}_aq_s")

    if st.button("💾 Guardar/Actualizar Jugador", key="save_player_btn_ae"):
        if not nombre_jugador: st.error("El nombre del jugador no puede estar vacío."); return
        if nombre_jugador not in datos: datos[nombre_jugador] = {KEY_TIPO: tipo_jugador, KEY_VOTACIONES:{}, KEY_CONVOCADO:True}
        datos[nombre_jugador][KEY_TIPO] = tipo_jugador
        if KEY_VOTACIONES not in datos[nombre_jugador] or not isinstance(datos[nombre_jugador][KEY_VOTACIONES],dict): datos[nombre_jugador][KEY_VOTACIONES]={}
        datos[nombre_jugador][KEY_VOTACIONES][usuario] = attrs_actuales
        if KEY_CONVOCADO not in datos[nombre_jugador]: datos[nombre_jugador][KEY_CONVOCADO] = True
        guardar_datos(datos)
        st.success(f"¡Jugador '{nombre_jugador}' guardado/actualizado con tus valoraciones!")
        st.balloons()
        st.session_state[nombre_key] = "" # Limpiar para agregar nuevo

def render_player_profiles_page(datos):
    st.header("Perfiles de jugadores")
    if not datos: st.info("No hay jugadores registrados."); return
    perfiles = []
    for name in sorted(datos.keys()):
        info, proms = datos[name], promedio_atributos(info.get(KEY_VOTACIONES,{}))
        rol, dist = obtener_rol(proms, info.get(KEY_TIPO, TIPO_CAMPO))
        roles_ord = sorted(dist.items(), key=lambda item:item[1], reverse=True)
        rol_sec_str = "N/A"
        if len(roles_ord)>1 and roles_ord[1][1]>0.001: rol_sec_str = f"{roles_ord[1][0]} ({roles_ord[1][1]*100:.0f}%)"
        
        perfil = {"Nombre":f"{EMOJI.get(rol,'👤')} {name}", "Rol principal":rol, "Rol secundario":rol_sec_str, 
                  "Descripción":descripcion_jugador(rol), "Comparables":", ".join(COMPARABLES.get(rol,["N/A"]))}
        
        all_attr_keys = [k for k,_ in ATRIBUTOS_CAMPO] + [k for k,_ in ATRIBUTOS_ARQUERO]
        for attr_k in all_attr_keys: perfil[attr_k] = round(proms.get(attr_k,0),1)
        perfiles.append(perfil)

    if perfiles:
        df_p = pd.DataFrame(perfiles).fillna(0)
        cols_disp = ["Nombre","Rol principal","Rol secundario","Descripción","Comparables"]
        attr_cols = sorted([c for c in df_p.columns if c not in cols_disp])
        final_cols = cols_disp + attr_cols
        for c in final_cols: 
            if c not in df_p.columns: df_p[c]=0.0
        st.dataframe(df_p[final_cols].astype(str).replace(r'\.0$','',regex=True), use_container_width=True)
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

def generar_analisis_texto(nombre_equipo_seleccionado, equipo_seleccionado_nombres, promedios_equipo_sel, roles_equipo_sel, promedios_globales_todos_jugadores):
    if not promedios_equipo_sel: return "No se pudieron calcular los promedios para el equipo seleccionado."

    # 1. Calcular promedios de atributos para el equipo seleccionado
    team_avg_attrs = {}
    # Primero, unimos todos los atributos individuales de los jugadores del equipo
    all_team_player_attrs_list = [promedios_equipo_sel.get(player_name, {}) for player_name in equipo_seleccionado_nombres]
    # Filtramos diccionarios vacíos que podrían surgir si un jugador no tiene promedios
    valid_player_attrs_list = [attrs for attrs in all_team_player_attrs_list if attrs]

    if not valid_player_attrs_list:
        return "No hay suficientes datos de atributos para analizar este equipo."

    df_team_attrs = pd.DataFrame(valid_player_attrs_list)
    if df_team_attrs.empty:
        return "No se pudieron obtener atributos para el equipo seleccionado."
    
    numeric_df_team_attrs = df_team_attrs.select_dtypes(include=np.number)
    if numeric_df_team_attrs.empty:
        return "Los atributos del equipo seleccionado no son numéricos para el análisis."
    
    team_avg_attrs = numeric_df_team_attrs.mean().to_dict()

    # 2. Determinar en qué sobreindexa
    sobreindexa_text = "Este equipo sobreindexa en: "
    highlights = []
    for attr, team_val in team_avg_attrs.items():
        global_val = promedios_globales_todos_jugadores.get(attr, 0)
        # Considerar sobreindexación si es al menos un 10-15% mejor que el promedio y el valor global no es trivial
        if global_val > 0.5 and team_val > global_val * 1.15: 
            highlights.append(f"{attr.replace('_',' ')} ({team_val:.1f} vs prom. global {global_val:.1f})")
        elif team_val > 4.0 and global_val < 3.5 : # Alto en absoluto y significativamente mejor
             highlights.append(f"{attr.replace('_',' ')} ({team_val:.1f}, destacado)")
    
    if highlights: sobreindexa_text += ", ".join(highlights) + "."
    else: sobreindexa_text = "El equipo muestra un perfil equilibrado sin una sobreindexación clara en atributos específicos comparado al promedio general."

    # 3. Determinar mejor estilo
    # (Asumimos que las funciones calcular_score_* toman los nombres del equipo, los promedios de ese equipo y los roles de ese equipo)
    # Necesitamos el nombre del arquero del equipo seleccionado
    arquero_sel = None
    datos_completos = cargar_datos() # Cargar datos para obtener tipo
    for nombre_jugador in equipo_seleccionado_nombres:
        if datos_completos.get(nombre_jugador, {}).get(KEY_TIPO) == TIPO_ARQUERO:
            arquero_sel = nombre_jugador
            break
    
    if not arquero_sel: # Esto no debería pasar si la selección es 1 GK + 4 Field
        return "Error: No se encontró un arquero en el equipo seleccionado para el análisis de estilo."

    scores_estilos = {
        "Equilibrio General": calcular_score_equipo_general(equipo_seleccionado_nombres, promedios_equipo_sel),
        "Catenaccio": calcular_score_catenaccio(equipo_seleccionado_nombres, promedios_equipo_sel, roles_equipo_sel, arquero_sel),
        "Tiki-Taka": calcular_score_tikitaka(equipo_seleccionado_nombres, promedios_equipo_sel, roles_equipo_sel, arquero_sel),
        "Contraataque": calcular_score_contraataque(equipo_seleccionado_nombres, promedios_equipo_sel, roles_equipo_sel, arquero_sel),
    }
    mejor_estilo_nombre = max(scores_estilos, key=scores_estilos.get)
    mejor_estilo_text = f"El mejor estilo de juego para '{nombre_equipo_seleccionado}' parece ser: **{mejor_estilo_nombre}** (Puntaje: {scores_estilos[mejor_estilo_nombre]:.1f})."

    # 4. Puntos Fuertes y Débiles (simplificado)
    # Ordenar atributos del equipo por valor
    sorted_team_attrs = sorted(team_avg_attrs.items(), key=lambda item: item[1], reverse=True)
    
    puntos_fuertes_text = "Puntos Fuertes Destacados: "
    top_attrs = [f"{k.replace('_',' ')} ({v:.1f})" for k,v in sorted_team_attrs[:3] if v > 3.0] # Top 3 si son > 3.0
    if top_attrs: puntos_fuertes_text += ", ".join(top_attrs) + "."
    else: puntos_fuertes_text += "No se identifican puntos fuertes dominantes basados en atributos individuales muy altos."
    
    # Añadir roles clave presentes como punto fuerte
    roles_presentes_str = ", ".join(set(roles_equipo_sel.values()))
    puntos_fuertes_text += f" La combinación de roles ({roles_presentes_str}) puede ser una ventaja."


    puntos_debiles_text = "Áreas de Posible Mejora: "
    bottom_attrs = [f"{k.replace('_',' ')} ({v:.1f})" for k,v in sorted_team_attrs[-3:] if v < 2.5] # Bottom 3 si son < 2.5
    if bottom_attrs: puntos_debiles_text += ", ".join(bottom_attrs) + "."
    else: puntos_debiles_text += "El equipo no muestra debilidades críticas obvias en atributos individuales."

    return f"""### Análisis del Equipo: {nombre_equipo_seleccionado}

**Sobreindexación y Perfil General:**
{sobreindexa_text}

**Estilo de Juego Sugerido:**
{mejor_estilo_text}

**Puntos Fuertes:**
{puntos_fuertes_text}

**Puntos Débiles Potenciales:**
{puntos_debiles_text}
"""

def render_team_analysis_page(datos_jugadores_todos): # Cambiado nombre del parámetro
    st.header("Análisis de equipos y compatibilidades")
    
    # --- Sección de Análisis de Equipo Manual ---
    st.markdown("---")
    st.subheader("🔬 Análisis de Equipo Manual")

    convocados_para_seleccion = {
        nombre: info for nombre, info in datos_jugadores_todos.items() if info.get(KEY_CONVOCADO, False)
    }
    if not convocados_para_seleccion:
        st.info("No hay jugadores convocados para seleccionar. Marca jugadores como convocados en la barra lateral.")
        st.stop()

    arqueros_opciones = {n:f"{EMOJI.get(obtener_rol(promedio_atributos(i.get(KEY_VOTACIONES, {})), TIPO_ARQUERO)[0], '👤')} {n}" for n,i in convocados_para_seleccion.items() if i.get(KEY_TIPO)==TIPO_ARQUERO}
    campo_opciones = {n:f"{EMOJI.get(obtener_rol(promedio_atributos(i.get(KEY_VOTACIONES, {})), TIPO_CAMPO)[0], '👤')} {n}" for n,i in convocados_para_seleccion.items() if i.get(KEY_TIPO)==TIPO_CAMPO}

    # Usar st.session_state para mantener selecciones
    if 'custom_gk_select' not in st.session_state: st.session_state.custom_gk_select = None
    if 'custom_field_select' not in st.session_state: st.session_state.custom_field_select = []
    
    # Crear selectbox para el arquero
    # La lista de opciones para el selectbox necesita ser solo los nombres (keys del dict)
    # pero el format_func usará el dict para mostrar emoji + nombre.
    lista_nombres_arqueros = list(arqueros_opciones.keys())
    
    # Si el arquero seleccionado ya no está en las opciones (ej. fue desconvocado), resetearlo
    if st.session_state.custom_gk_select and st.session_state.custom_gk_select not in lista_nombres_arqueros:
        st.session_state.custom_gk_select = None

    st.session_state.custom_gk_select = st.selectbox(
        "Selecciona 1 Arquero:", 
        options=[None] + lista_nombres_arqueros, # Añadir None para opción "no seleccionado"
        format_func=lambda x: "---" if x is None else arqueros_opciones.get(x, x),
        key="selectbox_custom_gk" # key diferente para el widget
    )

    # Crear multiselect para jugadores de campo
    lista_nombres_campo = list(campo_opciones.keys())
    
    # Filtrar jugadores de campo seleccionados que ya no estén disponibles
    st.session_state.custom_field_select = [
        p for p in st.session_state.custom_field_select if p in lista_nombres_campo
    ]

    st.session_state.custom_field_select = st.multiselect(
        "Selecciona 4 Jugadores de Campo:",
        options=lista_nombres_campo,
        default=st.session_state.custom_field_select,
        format_func=lambda x: campo_opciones.get(x,x),
        key="multiselect_custom_field",
        max_selections=4
    )
    
    nombre_equipo_manual = st.text_input("Nombre para tu equipo (opcional):", key="nombre_equipo_manual_input").strip()
    if not nombre_equipo_manual:
        nombre_equipo_manual = "Equipo Seleccionado"


    if st.button("⚡ Analizar Equipo Seleccionado", key="analizar_equipo_manual_btn"):
        if st.session_state.custom_gk_select and len(st.session_state.custom_field_select) == 4:
            equipo_seleccionado_nombres = [st.session_state.custom_gk_select] + st.session_state.custom_field_select
            
            promedios_equipo_sel = {
                nombre: promedio_atributos(datos_jugadores_todos[nombre].get(KEY_VOTACIONES, {}))
                for nombre in equipo_seleccionado_nombres if nombre in datos_jugadores_todos
            }
            roles_equipo_sel = {
                nombre: obtener_rol(promedios_equipo_sel[nombre], datos_jugadores_todos[nombre].get(KEY_TIPO, TIPO_CAMPO))[0]
                for nombre in equipo_seleccionado_nombres if nombre in promedios_equipo_sel
            }
            
            # Calcular promedios globales de todos los jugadores en el archivo de datos
            promedios_globales_todos_jugadores = calcular_promedios_globales(datos_jugadores_todos)

            if not promedios_globales_todos_jugadores:
                st.error("No se pudieron calcular los promedios globales de atributos para la comparación.")
            else:
                analisis_texto = generar_analisis_texto(nombre_equipo_manual, equipo_seleccionado_nombres, promedios_equipo_sel, roles_equipo_sel, promedios_globales_todos_jugadores)
                st.markdown(analisis_texto)
        else:
            st.warning("Por favor, selecciona 1 arquero y 4 jugadores de campo para analizar.")
    
    st.markdown("---") # Separador antes de la sección de análisis automático existente
    
    # --- Sección de Análisis Automático Existente ---
    # (El código de esta sección se mantiene como estaba antes)
    convocados = [nombre for nombre, info in datos_jugadores_todos.items() if info.get(KEY_CONVOCADO, False)] # Usar datos_jugadores_todos
    if not convocados: # Re-chequear aquí por si el filtro anterior de "convocados_para_seleccion" fue demasiado restrictivo para esta parte
        st.info("No hay jugadores convocados para el análisis automático de equipos.")
        # st.stop() # No detener toda la página si esta sección no puede correr pero la manual sí.
        return # Salir de esta función si no hay convocados para el análisis automático.


    promedios_convocados = {
        nombre: promedio_atributos(datos_jugadores_todos[nombre].get(KEY_VOTACIONES, {})) for nombre in convocados
    }
    roles_todos_jugadores = {
        nombre: obtener_rol(promedios_convocados[nombre], datos_jugadores_todos[nombre].get(KEY_TIPO, TIPO_CAMPO))[0] 
        for nombre in convocados if nombre in promedios_convocados
    }
    jugadores_campo_convocados = [
        nombre for nombre in convocados if datos_jugadores_todos[nombre].get(KEY_TIPO) == TIPO_CAMPO
    ]
    arqueros_convocados = [
        nombre for nombre in convocados if datos_jugadores_todos[nombre].get(KEY_TIPO) == TIPO_ARQUERO
    ]

    if len(jugadores_campo_convocados) < 4 or not arqueros_convocados:
        st.info("Se necesitan al menos 4 jugadores de campo y 1 arquero convocados para el análisis automático de mejores combinaciones.")
        # return # No salir si la sección manual sí pudo funcionar
    else: # Solo ejecutar si hay suficientes jugadores para combinaciones
        st.markdown("#### 🏆 Mejores Equipos 5v5 (Equilibrio General - Automático)")
        posibles_equipos_general = []
        if len(jugadores_campo_convocados) >=4 and arqueros_convocados:
            for combo_campo in combinations(jugadores_campo_convocados, 4):
                for arquero_nombre in arqueros_convocados:
                    equipo_actual_nombres = list(combo_campo) + [arquero_nombre]
                    score = calcular_score_equipo_general(equipo_actual_nombres, promedios_convocados)
                    posibles_equipos_general.append((score, equipo_actual_nombres, arquero_nombre)) 
        
        mejores_equipos_general = sorted(posibles_equipos_general, key=lambda x: x[0], reverse=True)[:3]

        if mejores_equipos_general:
            for i, (puntaje, equipo, gk_name) in enumerate(mejores_equipos_general):
                nombres_equipo_str = " | ".join(p if p != gk_name else f"🧤{EMOJI.get('Arquero','')}{p}" for p in equipo)
                st.markdown(f"<div class='highlight'><b>Equipo {i+1}</b>: {nombres_equipo_str} <br> Puntuación General: {puntaje:.1f}</div>", unsafe_allow_html=True)
        else:
            st.info("No se pudieron generar equipos con balance general (automático).")
        st.caption("Lógica Puntuación General: Suma de todos los atributos promediados.")
        st.markdown("---")

        estilos_tacticos = [
            {"nombre": "Catenaccio", "funcion_score": calcular_score_catenaccio, "emoji": "🛡️", 
            "caption": "Prioriza: Defensa sólida, Atributos Mentales. Roles: Murallas, Gladiadores. Arquero: Clásico."},
            {"nombre": "Tiki-Taka", "funcion_score": calcular_score_tikitaka, "emoji": "🎼",
            "caption": "Prioriza: Pase, Control, Visión, Retención. Roles: Orquestadores. Arquero: Con buen juego de pies."},
            {"nombre": "Contraataque", "funcion_score": calcular_score_contraataque, "emoji": "⚡",
            "caption": "Prioriza: Velocidad, Dribbling, Transición Ofensiva, Definición. Roles: Wildcards, Topadoras. Arquero: Buen distribuidor."}
        ]

        for estilo in estilos_tacticos:
            st.markdown(f"#### {estilo['emoji']} Mejores Equipos Estilo {estilo['nombre']} (Automático)")
            posibles_equipos_estilo = []
            if len(jugadores_campo_convocados) >= 4 and arqueros_convocados:
                for combo_campo in combinations(jugadores_campo_convocados, 4):
                    for arquero_nombre in arqueros_convocados:
                        equipo_actual_nombres = list(combo_campo) + [arquero_nombre]
                        roles_equipo_actual = {
                            nombre_jugador: roles_todos_jugadores.get(nombre_jugador, "Desconocido")
                            for nombre_jugador in equipo_actual_nombres
                        }
                        score = estilo["funcion_score"](equipo_actual_nombres, promedios_convocados, roles_equipo_actual, arquero_nombre)
                        posibles_equipos_estilo.append((score, equipo_actual_nombres, arquero_nombre))

            mejores_equipos_estilo = sorted(posibles_equipos_estilo, key=lambda x: x[0], reverse=True)[:3]

            if mejores_equipos_estilo:
                for i, (puntaje, equipo, gk_name) in enumerate(mejores_equipos_estilo):
                    nombres_equipo_str = " | ".join(p if p != gk_name else f"🧤{EMOJI.get('Arquero','')}{p}" for p in equipo)
                    st.markdown(f"<div class='highlight'><b>Equipo {i+1}</b>: {nombres_equipo_str} <br> Puntuación {estilo['nombre']}: {puntaje:.1f}</div>", unsafe_allow_html=True)
            else:
                st.info(f"No se pudieron generar equipos estilo {estilo['nombre']} (automático).")
            st.caption(estilo["caption"])
            st.markdown("---")

def main():
    st.set_page_config(page_title="Perfilador 5v5 Cumelo", page_icon="⚽", layout="wide")
    aplicar_estilos_css()
    usuario_actual = obtener_usuario()
    if not usuario_actual:
        st.info("👈 Por favor, ingresa un nombre de usuario en la barra lateral y presiona 'Acceder' para usar la aplicación.")
        st.stop()
    
    # Inicializar estado de selección para análisis manual si no existe
    if 'custom_gk_select' not in st.session_state: st.session_state.custom_gk_select = None
    if 'custom_field_select' not in st.session_state: st.session_state.custom_field_select = []
    if 'nombre_equipo_manual_input' not in st.session_state: st.session_state.nombre_equipo_manual_input = "Equipo Elegido"


    datos_jugadores = cargar_datos()
    menu_seleccionado = render_sidebar(datos_jugadores, usuario_actual)
    if menu_seleccionado == "Agregar o editar jugador": render_add_edit_player_page(datos_jugadores, usuario_actual)
    elif menu_seleccionado == "Perfiles de jugadores": render_player_profiles_page(datos_jugadores)
    elif menu_seleccionado == "Análisis": render_team_analysis_page(datos_jugadores)

if __name__ == "__main__":
    main()
