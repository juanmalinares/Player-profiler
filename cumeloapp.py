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
KEY_ATRIBUTOS_OLD = "Atributos"  # For migrating old data format
DEFAULT_USER = "system_initial_data"
TIPO_CAMPO = "Campo"
TIPO_ARQUERO = "Arquero"

# ---- Configuración visual y estilos ----
st.set_page_config(page_title="Perfilador 5v5", page_icon="⚽", layout="wide")
st.markdown("""
    <style>
    body, .stApp { background-color: #111; color: #e8e8e8;}
    .css-18e3th9 { background-color: #003049; } /* Streamlit <1.17 */
    .st-emotion-cache-18e3th9 { background-color: #003049; } /* Streamlit >=1.17 sidebar */
    .css-1d391kg { background-color: #003049; } /* Streamlit <1.17 */
    .st-emotion-cache-uf99v8 { background-color: #003049; } /* Streamlit >=1.17 main area with form */


    .st-bb { font-size: 1.1em; } /* Input widgets */
    .stDataFrame { background-color: #003049; color: #fff;}
    h1, h2, h3, h4, h5 { color: #c1121f; font-size: 1.25em; margin-bottom: 0.25em;}
    .highlight {background: #669bbc22; border-radius: 10px; padding: 0.7em 1em; margin-bottom:1.2em;}
    .stRadio label { font-size: 1.1em;}
    .emoji {font-size: 1.4em;}
    </style>
""", unsafe_allow_html=True)

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

# --- Definición de atributos ---
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

TIPOS_JUGADOR = [TIPO_CAMPO, TIPO_ARQUERO]
ATR_GK_CAMPO = ["GK_Foot_Play", "GK_Agility", "GK_Bravery"] # GK attributes also rateable for Field players

# ----------------- FUNCIONES DE DATOS -----------------

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        try:
            with open(ARCHIVO_DATOS, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except json.JSONDecodeError:
            return {} # Return empty if JSON is corrupted
    else:
        return {}

    migrated_data = {}
    for player_name, player_info in raw_data.items():
        if not isinstance(player_info, dict): continue # Skip malformed entries

        new_player_entry = {}
        new_player_entry[KEY_TIPO] = player_info.get(KEY_TIPO, TIPO_CAMPO) # Default to Campo if missing
        new_player_entry[KEY_CONVOCADO] = player_info.get(KEY_CONVOCADO, True) # Default to True

        if KEY_VOTACIONES in player_info and isinstance(player_info[KEY_VOTACIONES], dict):
            new_player_entry[KEY_VOTACIONES] = player_info[KEY_VOTACIONES]
        elif KEY_ATRIBUTOS_OLD in player_info and isinstance(player_info[KEY_ATRIBUTOS_OLD], dict):
            # Migrate from old "Atributos" structure to new "votaciones" structure
            new_player_entry[KEY_VOTACIONES] = {DEFAULT_USER: player_info[KEY_ATRIBUTOS_OLD]}
        else:
            new_player_entry[KEY_VOTACIONES] = {} # Initialize if no rating data found

        migrated_data[player_name] = new_player_entry
    return migrated_data


def guardar_datos(datos):
    with open(ARCHIVO_DATOS, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

def obtener_usuario():
    if "usuario" not in st.session_state:
        st.session_state["usuario"] = ""
    
    usuario_placeholder = "Anónimo (visible solo para ti)" if not st.session_state["usuario"] else st.session_state["usuario"]
    usuario_input = st.sidebar.text_input("🧑‍💻 Tu nombre de usuario (para votar):", 
                                          value=st.session_state["usuario"],
                                          placeholder=usuario_placeholder)
    
    st.session_state["usuario"] = usuario_input.strip()
    
    if not st.session_state["usuario"]:
        st.sidebar.warning("Debes ingresar un nombre de usuario para votar o editar jugadores.")
        # Allow viewing profiles and analysis even without username
        return None # Return None if no user, so other functions can check
    return st.session_state["usuario"]


def promedio_atributos(votaciones):
    if not votaciones or not isinstance(votaciones, dict):
        return {}
    
    valid_votes = [vote_data for vote_data in votaciones.values() if isinstance(vote_data, dict)]
    if not valid_votes:
        return {}
        
    df = pd.DataFrame(valid_votes)
    if df.empty:
        return {}

    # Select only columns with numeric data types before calculating the mean
    numeric_cols_df = df.select_dtypes(include=np.number)
    
    if numeric_cols_df.empty: # No numeric columns found or left
        return {}
        
    return numeric_cols_df.mean(axis=0).to_dict()

def obtener_rol(promedio_attrs):
    pr = promedio_attrs # shorthand
    if not pr: return "Orquestador", {"Orquestador": 1.0} # Default if no attributes

    # Check for Arquero type based on GK_Reaction first
    if pr.get("GK_Reaction", 0) >= 3:
        return "Arquero", {"Arquero": 1.0}

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
    score_muralla = (
        pr.get("Strength_in_Duels", 0) * 2
        + pr.get("Defense_Transition", 0)
        + pr.get("Leadership_Presence", 0)
        + pr.get("Recovery_Runs", 0)
        + pr.get("Pressing_Consistency", 0)
        + pr.get("Marking_Tightness", 0)
        + pr.get("Tactical_Awareness", 0)
    )
    score_gladiador = (
        pr.get("Resilience_When_Behind", 0)
        + pr.get("Composure", 0)
        + pr.get("Strength_in_Duels", 0)
        + pr.get("Stamina", 0)
        + pr.get("Recovery_Runs", 0)
        + pr.get("Pressing_Consistency", 0)
        + pr.get("Marking_Tightness", 0)
    )
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
    score_topadora = (
        pr.get("Finishing_Precision", 0)
        + pr.get("Power_Dribble_and_Score", 0)
        + pr.get("Short_Passing_Accuracy", 0)
        + pr.get("Ball_Retention", 0)
        + pr.get("Creativity", 0)
        + pr.get("Leadership_Presence", 0)
        + pr.get("Vision_Free_Player", 0)
    )
    roles = {
        "Wildcard": score_wildcard,
        "Muralla": score_muralla,
        "Gladiador": score_gladiador,
        "Orquestador": score_orquestador,
        "Topadora": score_topadora
    }
    
    sum_positive_scores = sum(max(0,s) for s in roles.values())

    if sum_positive_scores == 0: 
        rol_princ = "Orquestador" 
        dist = {role: (1.0 if role == rol_princ else 0.0) for role in roles}
    else:
        dist = {k: (max(0, v) / sum_positive_scores) for k, v in roles.items()}
        rol_princ = max(dist, key=dist.get)
        
    return rol_princ, dist

def descripcion_jugador(rol):
    descriptions = {
        "Muralla": "Imponente en defensa, fuerte físicamente, con buena recuperación y siempre dispuesto a frenar ataques rivales.",
        "Gladiador": "Incansable, comprometido en la presión y capaz de mantener el esfuerzo incluso cuando el equipo va perdiendo.",
        "Orquestador": "Es quien organiza y da fluidez al juego, destacando en visión, control y creatividad en la circulación.",
        "Wildcard": "Impredecible y desequilibrante, puede cambiar un partido en una jugada para bien o para mal.",
        "Topadora": "Potente llegada al área, combina pase y definición, mentalidad ofensiva y llegada.",
        "Arquero": "Especialista bajo los tres palos, seguro en reflejos, colocación y salida de balón."
    }
    return descriptions.get(rol, "Jugador versátil.")

# --- UI Rendering Functions ---

def render_sidebar(datos, usuario):
    st.sidebar.title("⚽ Menú")
    
    menu_options = ["Perfiles de jugadores", "Análisis"]
    if usuario: 
        menu_options.insert(0, "Agregar o editar jugador")

    if 'menu_selection' not in st.session_state:
        st.session_state.menu_selection = menu_options[0] if menu_options else "Perfiles de jugadores"

    if st.session_state.menu_selection not in menu_options:
         st.session_state.menu_selection = menu_options[0] if menu_options else "Perfiles de jugadores"

    menu = st.sidebar.radio("Selecciona opción", menu_options, index=menu_options.index(st.session_state.menu_selection))
    st.session_state.menu_selection = menu

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Jugadores Convocados")
    
    convocados_changed = False
    for nombre_jugador, info_jugador in datos.items():
        proms = promedio_atributos(info_jugador.get(KEY_VOTACIONES, {}))
        rol, _ = obtener_rol(proms)
        es_convocado = info_jugador.get(KEY_CONVOCADO, True)
        emoji_rol = EMOJI.get(rol, "👤") 
        
        checkbox_label = f"{emoji_rol} {nombre_jugador}"
        new_convocado_status = st.sidebar.checkbox(checkbox_label, value=es_convocado, key=f"convoc_{nombre_jugador}")
        
        if datos[nombre_jugador].get(KEY_CONVOCADO, True) != new_convocado_status: # Check before assignment
            datos[nombre_jugador][KEY_CONVOCADO] = new_convocado_status
            convocados_changed = True
            
    if convocados_changed:
        guardar_datos(datos)
    return menu

def render_add_edit_player_page(datos, usuario):
    st.header("Editar o agregar jugador")
    if not usuario:
        st.warning("Por favor, ingresa un nombre de usuario en la barra lateral para agregar o editar jugadores.")
        return

    nombre_jugador = st.text_input("Nombre del jugador").strip()
    tipo_jugador = st.radio("Tipo de Jugador", TIPOS_JUGADOR, horizontal=True, index=0)
    
    atributos_actuales = {}
    
    player_data = datos.get(nombre_jugador)
    existing_ratings_for_user = {}
    if player_data and usuario in player_data.get(KEY_VOTACIONES, {}):
        existing_ratings_for_user = player_data[KEY_VOTACIONES][usuario]
    elif player_data: 
        existing_ratings_for_user = promedio_atributos(player_data.get(KEY_VOTACIONES, {}))


    st.markdown("---")
    st.subheader("Atributos de Campo")
    for attr_key, attr_question in ATRIBUTOS_CAMPO:
        default_value = existing_ratings_for_user.get(attr_key, 2)
        atributos_actuales[attr_key] = st.slider(attr_question, 0, 5, int(default_value), key=f"{nombre_jugador}_{attr_key}")

    st.markdown("---")
    if tipo_jugador == TIPO_CAMPO:
        st.subheader("Atributos Adicionales (Estilo Portero para Jugador de Campo)")
        dict_atributos_arquero = dict(ATRIBUTOS_ARQUERO)
        for attr_key in ATR_GK_CAMPO: 
            question = dict_atributos_arquero.get(attr_key, attr_key.replace("_", " "))
            default_value = existing_ratings_for_user.get(attr_key, 2)
            atributos_actuales[attr_key] = st.slider(question, 0, 5, int(default_value), key=f"{nombre_jugador}_{attr_key}_gk_campo")
    
    elif tipo_jugador == TIPO_ARQUERO:
        st.subheader("Atributos de Arquero")
        for attr_key, attr_question in ATRIBUTOS_ARQUERO:
            default_value = existing_ratings_for_user.get(attr_key, 2)
            atributos_actuales[attr_key] = st.slider(attr_question, 0, 5, int(default_value), key=f"{nombre_jugador}_{attr_key}_arquero")

    if st.button("💾 Guardar/Actualizar Jugador"):
        if not nombre_jugador:
            st.error("El nombre del jugador no puede estar vacío.")
            return

        if nombre_jugador not in datos:
            datos[nombre_jugador] = {
                KEY_TIPO: tipo_jugador,
                KEY_VOTACIONES: {},
                KEY_CONVOCADO: True 
            }
        
        datos[nombre_jugador][KEY_TIPO] = tipo_jugador 
        datos[nombre_jugador][KEY_VOTACIONES][usuario] = atributos_actuales
        if KEY_CONVOCADO not in datos[nombre_jugador]:
            datos[nombre_jugador][KEY_CONVOCADO] = True

        guardar_datos(datos)
        st.success(f"¡Jugador '{nombre_jugador}' guardado/actualizado correctamente!")
        st.balloons()


def render_player_profiles_page(datos):
    st.header("Perfiles de jugadores")
    if not datos:
        st.info("Todavía no hay jugadores registrados. Agrega jugadores desde el menú lateral.")
        return

    perfiles_lista = []
    for nombre_jugador, info_jugador in datos.items():
        proms = promedio_atributos(info_jugador.get(KEY_VOTACIONES, {}))
        rol_principal, distribucion_roles = obtener_rol(proms)
        
        roles_ordenados = sorted(distribucion_roles.items(), key=lambda item: item[1], reverse=True)
        
        rol_secundario_str = "N/A"
        if len(roles_ordenados) > 1 and roles_ordenados[1][1] > 0.001: # check for meaningful secondary role
            rol_sec = roles_ordenados[1][0]
            pct_sec = roles_ordenados[1][1] * 100
            rol_secundario_str = f"{rol_sec} ({pct_sec:.0f}%)"

        perfil_data = {
            "Nombre": f"{EMOJI.get(rol_principal, '👤')} {nombre_jugador}",
            "Rol principal": rol_principal,
            "Rol secundario": rol_secundario_str,
            "Descripción": descripcion_jugador(rol_principal),
            "Comparables": ", ".join(COMPARABLES.get(rol_principal, ["N/A"]))
        }
        
        # Determine which attribute set to display based on primary role or player type
        # For simplicity, show all defined field attributes, and GK if player is GK type or GK role
        
        displayed_attributes = {}
        for attr_key, _ in ATRIBUTOS_CAMPO:
            displayed_attributes[attr_key] = round(proms.get(attr_key, 0), 1)
        
        # If player's designated type is Arquero or their role is Arquero, show GK attributes
        if info_jugador.get(KEY_TIPO) == TIPO_ARQUERO or rol_principal == TIPO_ARQUERO:
            for attr_key, _ in ATRIBUTOS_ARQUERO:
                 displayed_attributes[attr_key] = round(proms.get(attr_key, 0), 1)
        elif info_jugador.get(KEY_TIPO) == TIPO_CAMPO: # For field players, also show their rated GK_CAMPO attributes
            for attr_key in ATR_GK_CAMPO:
                 displayed_attributes[attr_key] = round(proms.get(attr_key, 0), 1)


        perfil_data.update(displayed_attributes)
        perfiles_lista.append(perfil_data)

    if perfiles_lista:
        df_perfiles = pd.DataFrame(perfiles_lista).fillna(0)
        
        column_order = ["Nombre", "Rol principal", "Rol secundario", "Descripción", "Comparables"]
        
        # Get all unique attribute keys present in the generated profiles
        all_attribute_keys_in_data = set()
        for p in perfiles_lista:
            for k in p.keys():
                if k not in column_order:
                    all_attribute_keys_in_data.add(k)
        
        # Order these attributes: first ATRIBUTOS_CAMPO keys, then ATRIBUTOS_ARQUERO keys
        # This ensures a somewhat logical order if both types of attributes are present.
        
        sorted_attribute_cols = []
        # Add field attributes that are in the data
        for attr_key, _ in ATRIBUTOS_CAMPO:
            if attr_key in all_attribute_keys_in_data:
                sorted_attribute_cols.append(attr_key)
        # Add GK attributes that are in the data and not already added (e.g. from ATR_GK_CAMPO)
        for attr_key, _ in ATRIBUTOS_ARQUERO:
            if attr_key in all_attribute_keys_in_data and attr_key not in sorted_attribute_cols:
                sorted_attribute_cols.append(attr_key)
        # Add any remaining attributes from ATR_GK_CAMPO if not covered (should be by above)
        for attr_key in ATR_GK_CAMPO:
             if attr_key in all_attribute_keys_in_data and attr_key not in sorted_attribute_cols:
                sorted_attribute_cols.append(attr_key)


        final_column_order = column_order + sorted_attribute_cols
        
        # Ensure all columns in final_column_order actually exist in df_perfiles, or add them with 0
        for col in final_column_order:
            if col not in df_perfiles.columns:
                df_perfiles[col] = 0

        st.dataframe(df_perfiles[final_column_order], use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Descripciones Detalladas y Comparables")
        for p_info in perfiles_lista:
            st.markdown(f"**{p_info['Nombre']} ({p_info['Rol principal']})**: {p_info['Descripción']}")
            st.markdown(f"*Similar a: {p_info['Comparables']}*")
            st.markdown("---")
    else:
        st.info("No hay perfiles para mostrar.")


def render_team_analysis_page(datos):
    st.header("Análisis de equipos y compatibilidades")
    
    convocados = [nombre for nombre, info in datos.items() if info.get(KEY_CONVOCADO, False)]
    if not convocados:
        st.info("No hay jugadores convocados. Selecciona jugadores en la barra lateral.")
        return

    promedios_convocados = {
        nombre: promedio_atributos(datos[nombre].get(KEY_VOTACIONES, {})) for nombre in convocados
    }
    
    jugadores_campo_convocados = [
        nombre for nombre in convocados if datos[nombre].get(KEY_TIPO) == TIPO_CAMPO
    ]
    arqueros_convocados = [
        nombre for nombre in convocados if datos[nombre].get(KEY_TIPO) == TIPO_ARQUERO
    ]

    if len(jugadores_campo_convocados) < 4 or not arqueros_convocados:
        st.info("Se necesitan al menos 4 jugadores de campo y 1 arquero convocados para el análisis de equipos 5v5.")
        return

    def calcular_score_equipo_general(equipo, promedios_jugadores):
        score_total = 0
        for jugador_nombre in equipo:
            if jugador_nombre in promedios_jugadores:
                score_total += sum(val for val in promedios_jugadores[jugador_nombre].values() if isinstance(val, (int, float)))
        return score_total

    posibles_equipos_5v5 = []
    if len(jugadores_campo_convocados) >=4 and arqueros_convocados: # Ensure we can form a team
        for combo_campo in combinations(jugadores_campo_convocados, 4):
            for arquero in arqueros_convocados:
                equipo_actual = list(combo_campo) + [arquero]
                score = calcular_score_equipo_general(equipo_actual, promedios_convocados)
                posibles_equipos_5v5.append((score, equipo_actual))
    
    mejores_equipos_5v5 = sorted(posibles_equipos_5v5, key=lambda x: x[0], reverse=True)[:3]

    st.markdown("#### 🏆 Mejores Equipos 5v5 (Basado en Suma General de Atributos)")
    if mejores_equipos_5v5:
        for i, (puntaje, equipo) in enumerate(mejores_equipos_5v5):
            nombres_equipo_str = " | ".join(equipo)
            for gk in arqueros_convocados: # Highlight GKs in the list
                if gk in nombres_equipo_str: # Simple check
                    nombres_equipo_str = nombres_equipo_str.replace(gk, f"🧤{EMOJI.get('Arquero','')}{gk}")


            st.markdown(f"<div class='highlight'><b>Equipo {i+1}</b>: {nombres_equipo_str} <br> Puntuación Total: {puntaje:.1f}</div>", unsafe_allow_html=True)
    else:
        st.info("No se pudieron generar equipos. Verifica las convocatorias y tipos de jugadores.")
    
    st.caption("Lógica de Puntuación: Suma de todos los atributos promediados de los jugadores convocados en el equipo.")
    st.markdown("---")
    st.markdown("💡 **Próximamente**: Análisis más detallados como 'Catenaccio', 'Tiki-Taka', 'Contraataque', usando fórmulas de puntuación específicas para cada estilo de juego.")


# --- Lógica Principal ---
def main():
    datos_jugadores = cargar_datos()
    usuario_actual = obtener_usuario() 

    menu_seleccionado = render_sidebar(datos_jugadores, usuario_actual)

    if menu_seleccionado == "Agregar o editar jugador":
        render_add_edit_player_page(datos_jugadores, usuario_actual)
    elif menu_seleccionado == "Perfiles de jugadores":
        render_player_profiles_page(datos_jugadores)
    elif menu_seleccionado == "Análisis":
        render_team_analysis_page(datos_jugadores)

if __name__ == "__main__":
    main()
