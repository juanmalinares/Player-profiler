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
# st.set_page_config se llama una sola vez y como primer comando de Streamlit
# Lo moveremos al inicio de la función main() o justo antes si es necesario globalmente,
# pero para el flujo de pedir usuario primero, es mejor controlarlo dentro de main.

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
    ("Marking_Tightness",     "¿Con qué frecuencia pierde al jugador que marca sin balón?"), # Interpretación varía
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
ATR_GK_CAMPO = ["GK_Foot_Play", "GK_Agility", "GK_Bravery"]

# ----------------- FUNCIONES DE DATOS -----------------

def aplicar_estilos_css():
    st.markdown("""
        <style>
        body, .stApp { 
            background-color: #eeeeee; /* MODIFICADO: Gris claro de fondo */
            color: #333333; /* MODIFICADO: Texto oscuro para contraste */
        }
        /* Estilos para la barra lateral y otros elementos pueden mantenerse oscuros o ajustarse */
        .css-18e3th9, .st-emotion-cache-18e3th9 { /* Sidebar Streamlit <1.17 y >=1.17 */
            background-color: #003049; 
        }
        /* Color de texto en la sidebar necesita ser claro si el fondo es oscuro */
        .css-18e3th9 *, .st-emotion-cache-18e3th9 * {
            color: #e8e8e8; /* Asegurar que el texto de la sidebar sea legible */
        }
        .css-18e3th9 .stRadio label, .st-emotion-cache-18e3th9 .stRadio label {
             color: #e8e8e8 !important; /* Forzar color en etiquetas de radio de sidebar */
        }
        .css-18e3th9 .stCheckbox label, .st-emotion-cache-18e3th9 .stCheckbox label {
             color: #e8e8e8 !important; /* Forzar color en etiquetas de checkbox de sidebar */
        }


        /* Si el área principal de formularios también usa estas clases y queremos que sea clara: */
        /* .css-1d391kg, .st-emotion-cache-uf99v8 { background-color: #ffffff; } */
        /* Por ahora, se deja que el fondo principal #eeeeee domine */

        .st-bb { /* Input widgets */
            font-size: 1.1em; 
        }
        .stDataFrame { /* DataFrame */
            background-color: #003049; 
            color: #fff;
        }
        /* Títulos con color distintivo */
        h1, h2, h3, h4, h5 { 
            color: #c1121f; 
            font-size: 1.25em; 
            margin-bottom: 0.25em;
        }
        .highlight { /* Cajas de resaltado */
            background: #669bbc22; 
            border-radius: 10px; 
            padding: 0.7em 1em; 
            margin-bottom:1.2em;
            /* Asegurar que el texto dentro del highlight sea legible sobre #eeeeee */
            color: #333333; 
            border: 1px solid #669bbc44; /* Borde sutil */
        }
        .stRadio label { /* Etiquetas de Radio Buttons en el área principal */
            font-size: 1.1em;
            color: #333333; /* Asegurar legibilidad en fondo claro */
        }
        .stTextInput label, .stSlider label { /* Etiquetas de Text Input y Slider */
             color: #333333 !important; /* Asegurar legibilidad */
        }
        .emoji {
            font-size: 1.4em;
        }
        </style>
    """, unsafe_allow_html=True)

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        try:
            with open(ARCHIVO_DATOS, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except json.JSONDecodeError:
            return {} 
    else:
        return {}

    migrated_data = {}
    for player_name, player_info in raw_data.items():
        if not isinstance(player_info, dict): continue 

        new_player_entry = {}
        new_player_entry[KEY_TIPO] = player_info.get(KEY_TIPO, TIPO_CAMPO) 
        new_player_entry[KEY_CONVOCADO] = player_info.get(KEY_CONVOCADO, True) 

        if KEY_VOTACIONES in player_info and isinstance(player_info[KEY_VOTACIONES], dict):
            new_player_entry[KEY_VOTACIONES] = player_info[KEY_VOTACIONES]
        elif KEY_ATRIBUTOS_OLD in player_info and isinstance(player_info[KEY_ATRIBUTOS_OLD], dict):
            new_player_entry[KEY_VOTACIONES] = {DEFAULT_USER: player_info[KEY_ATRIBUTOS_OLD]}
        else:
            new_player_entry[KEY_VOTACIONES] = {} 

        migrated_data[player_name] = new_player_entry
    return migrated_data


def guardar_datos(datos):
    with open(ARCHIVO_DATOS, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

def obtener_usuario():
    if "usuario_valido" not in st.session_state:
        st.session_state.usuario_valido = False # Flag para controlar si se ingresó un usuario

    if not st.session_state.usuario_valido:
        st.sidebar.title("👋 ¡Bienvenido!")
        usuario_input = st.sidebar.text_input("🧑‍💻 Ingresa tu nombre de usuario para comenzar:", 
                                              key="usuario_login_input",
                                              help="Este nombre se usará para registrar tus votos y ediciones.")
        if st.sidebar.button("Acceder", key="login_button"):
            if usuario_input.strip():
                st.session_state["usuario"] = usuario_input.strip()
                st.session_state.usuario_valido = True
                st.rerun() # Volver a ejecutar para mostrar el resto de la app
            else:
                st.sidebar.warning("Por favor, ingresa un nombre de usuario.")
        return None # Aún no hay usuario válido
    
    # Si el usuario ya es válido, simplemente retornarlo
    return st.session_state.get("usuario")


def promedio_atributos(votaciones):
    if not votaciones or not isinstance(votaciones, dict):
        return {}
    
    valid_votes = [vote_data for vote_data in votaciones.values() if isinstance(vote_data, dict)]
    if not valid_votes:
        return {}
        
    df = pd.DataFrame(valid_votes)
    if df.empty:
        return {}

    numeric_cols_df = df.select_dtypes(include=np.number)
    
    if numeric_cols_df.empty: 
        return {}
        
    return numeric_cols_df.mean(axis=0).to_dict()

def obtener_rol(promedio_attrs, tipo_jugador=TIPO_CAMPO):
    pr = promedio_attrs 
    if not pr: return "Orquestador", {"Orquestador": 1.0} 

    if tipo_jugador == TIPO_ARQUERO:
         return "Arquero", {"Arquero": 1.0}
    
    if pr.get("GK_Reaction", 0) >= 3 and tipo_jugador == TIPO_CAMPO : # Considerar rol de arquero para jugador de campo solo si GK_Reaction es alto
        # Esta lógica es más para display individual, para análisis de equipo se debe usar TIPO_ARQUERO
        # Podría ser útil si se permite que jugadores de campo jueguen de arquero esporádicamente.
        # Por ahora, esta condición de `tipo_jugador == TIPO_CAMPO` la hace redundante con la de arriba,
        # pero se mantiene para ser explícito.
        # Considerar si un jugador de campo con buena reacción de GK debería ser "Arquero" o un rol de campo.
        # Para la definición de roles principal, es mejor que sea un rol de campo.
        # Se podría tener un "rol secundario" o "apto para GK" si se desea.
        pass # No asignar rol de Arquero a un jugador de campo aquí, eso lo define su TIPO.


    score_wildcard = (
        pr.get("Finishing_Precision", 0) * 1.5 + pr.get("Attack_Transition", 0) * 1.5 + 
        pr.get("Dribbling_Efficiency", 0) * 1.5 + pr.get("Power_Dribble_and_Score", 0) * 1.0 +
        pr.get("Acceleration", 0) * 1.5 + pr.get("Creativity", 0) * 1.0
        - pr.get("Pressing_Consistency", 0) * 0.5 
        - pr.get("Recovery_Runs", 0) * 0.5 
    )
    score_muralla = (
        pr.get("Strength_in_Duels", 0) * 2.0 + 
        pr.get("Tactical_Awareness", 0) * 1.5 +
        pr.get("Marking_Tightness", 0) * 1.5 + # Asumiendo que un score alto es bueno para el rol
        pr.get("Defense_Transition", 0) * 1.0 +
        pr.get("Leadership_Presence", 0) * 1.0 + 
        pr.get("Recovery_Runs", 0) * 1.0 +
        pr.get("Pressing_Consistency", 0) * 0.5
    )
    score_gladiador = (
        pr.get("Stamina", 0) * 2.0 +
        pr.get("Pressing_Consistency", 0) * 1.5 +
        pr.get("Recovery_Runs", 0) * 1.5 +
        pr.get("Strength_in_Duels", 0) * 1.0 +
        pr.get("Resilience_When_Behind", 0) * 1.0 + 
        pr.get("Composure", 0) * 0.5 +
        pr.get("Marking_Tightness", 0) * 0.5 # Asumiendo que un score alto es bueno para el rol
    )
    # Lógica de Orquestador Refinada:
    score_orquestador = (
        pr.get("Vision_Free_Player", 0) * 2.5       
        + pr.get("Short_Passing_Accuracy", 0) * 2.5 
        + pr.get("Creativity", 0) * 2.0             
        + pr.get("Decision_Making_Speed", 0) * 1.5  
        + pr.get("First_Touch_Control", 0) * 1.5    
        + pr.get("Spatial_Awareness", 0) * 1.5      
        + pr.get("Tactical_Awareness", 0) * 1.0 # Para posicionarse y leer el juego   
        + pr.get("Composure", 0) * 1.0 # Para tomar decisiones bajo presión
        + pr.get("Ball_Retention", 0) * 0.5 # Para mantener posesión mientras se crea
    )
    score_topadora = (
        pr.get("Power_Dribble_and_Score", 0) * 2.0 +
        pr.get("Finishing_Precision", 0) * 1.5 + 
        pr.get("Acceleration", 0) * 1.5 +
        pr.get("Strength_in_Duels", 0) * 1.0 + # Para aguantar y definir
        pr.get("Attack_Transition", 0) * 1.0 +
        pr.get("Ball_Retention", 0) * 0.5 # Para proteger en avance
    )
    roles = {
        "Wildcard": score_wildcard, "Muralla": score_muralla, "Gladiador": score_gladiador,
        "Orquestador": score_orquestador, "Topadora": score_topadora
    }
    
    sum_positive_scores = sum(max(0,s) for s in roles.values() if s) # Considerar solo scores calculados
    if not roles or sum_positive_scores == 0: # Si no hay roles de campo o todos los scores son <=0
        # Fallback si ningún rol de campo tiene score positivo o el jugador es de un tipo no esperado
        # Si es un jugador de campo sin un perfil claro, podría ser "Versátil" o un default más genérico.
        # Pero como el default previo era Orquestador, lo mantenemos si no hay otro mejor.
        return "Orquestador", {"Orquestador": 1.0}


    dist = {k: (max(0, v) / sum_positive_scores if sum_positive_scores > 0 else 0) for k, v in roles.items() if v is not None}
    if not dist: # Si después de filtrar Nones, dist está vacío.
         return "Orquestador", {"Orquestador": 1.0} # Fallback final

    rol_princ = max(dist, key=dist.get)
        
    return rol_princ, dist

def descripcion_jugador(rol):
    descriptions = {
        "Muralla": "Imponente en defensa, fuerte físicamente, con buena recuperación y siempre dispuesto a frenar ataques rivales.",
        "Gladiador": "Incansable, comprometido en la presión y capaz de mantener el esfuerzo incluso cuando el equipo va perdiendo.",
        "Orquestador": "Organiza y da fluidez al juego con visión, pase y creatividad. Toma decisiones clave en la creación.",
        "Wildcard": "Impredecible y desequilibrante, puede cambiar un partido con su habilidad individual y vocación ofensiva.",
        "Topadora": "Potente en la llegada al área, combina fuerza, aceleración y definición para romper defensas.",
        "Arquero": "Especialista bajo los tres palos, seguro en reflejos, colocación y salida de balón."
    }
    return descriptions.get(rol, "Jugador versátil.")

# --- Style Specific Scoring Functions (Conceptual Logic) ---

def calcular_score_catenaccio(equipo, promedios_jugadores, roles_equipo, arquero_nombre_en_equipo):
    team_score = 0
    WEIGHT_CRUCIAL = 2.5
    WEIGHT_IMPORTANTE = 1.5
    WEIGHT_MODERADO = 1.0
    WEIGHT_BAJO = 0.5
    BONUS_MURALLA = 15
    BONUS_GLADIADOR = 10
    BONUS_JUGADOR_RAPIDO_DRIBLE = 5
    num_murallas = 0
    num_gladiadores = 0
    hay_jugador_rapido_drible = False

    for jugador_nombre in equipo:
        pr = promedios_jugadores.get(jugador_nombre, {})
        rol_jugador = roles_equipo.get(jugador_nombre, "")
        if not pr: continue

        player_score = 0
        if jugador_nombre == arquero_nombre_en_equipo: 
            player_score = (
                pr.get("GK_Positioning", 0) * WEIGHT_CRUCIAL +
                pr.get("GK_Reaction", 0) * WEIGHT_CRUCIAL +
                pr.get("GK_Bravery", 0) * WEIGHT_IMPORTANTE +
                pr.get("GK_Agility", 0) * WEIGHT_MODERADO +
                pr.get("GK_Distribution", 0) * WEIGHT_BAJO + 
                pr.get("Composure", 0) * WEIGHT_BAJO 
            )
        else: 
            # Marking_Tightness: Usuario indicó "Mayor puntaje siempre es mejor" para Catenaccio
            player_score = (
                pr.get("Marking_Tightness", 0) * WEIGHT_CRUCIAL + 
                pr.get("Tactical_Awareness", 0) * WEIGHT_CRUCIAL +
                pr.get("Strength_in_Duels", 0) * WEIGHT_CRUCIAL +
                pr.get("Resilience_When_Behind", 0) * WEIGHT_IMPORTANTE +
                pr.get("Composure", 0) * WEIGHT_IMPORTANTE +
                pr.get("Defense_Transition", 0) * WEIGHT_MODERADO +
                pr.get("Recovery_Runs", 0) * WEIGHT_MODERADO +
                pr.get("Leadership_Presence", 0) * WEIGHT_MODERADO +
                pr.get("Pressing_Consistency", 0) * WEIGHT_BAJO
            )
            if pr.get("Recovery_Runs", 2.5) < 2 and pr.get("Power_Dribble_and_Score", 0) > 3:
                player_score -= 5 
            
            if rol_jugador == "Muralla":
                num_murallas += 1
            if rol_jugador == "Gladiador":
                num_gladiadores += 1
            if rol_jugador not in ["Muralla", "Gladiador"] and \
               (pr.get("Acceleration", 0) >= 4 or pr.get("Dribbling_Efficiency", 0) >= 4):
                hay_jugador_rapido_drible = True
                
        team_score += player_score

    if num_murallas > 0:
        team_score += BONUS_MURALLA * num_murallas
    if num_gladiadores > 0:
        team_score += BONUS_GLADIADOR * num_gladiadores
    if hay_jugador_rapido_drible:
        team_score += BONUS_JUGADOR_RAPIDO_DRIBLE
        
    return team_score

def calcular_score_tikitaka(equipo, promedios_jugadores, roles_equipo, arquero_nombre_en_equipo):
    team_score = 0
    WEIGHT_CRUCIAL = 2.5
    WEIGHT_IMPORTANTE = 1.5
    WEIGHT_MODERADO = 1.0
    WEIGHT_BAJO = 0.5
    PENALTY_ULTRADEFENSIVO_SIN_PASE = -5 
    BONUS_ORQUESTADOR = 15
    num_orquestadores = 0
    num_defensores_con_pase_minimo = 0

    for jugador_nombre in equipo:
        pr = promedios_jugadores.get(jugador_nombre, {})
        rol_jugador = roles_equipo.get(jugador_nombre, "")
        if not pr: continue

        player_score = 0
        if jugador_nombre == arquero_nombre_en_equipo:
            player_score = (
                pr.get("GK_Foot_Play", 0) * WEIGHT_CRUCIAL +
                pr.get("GK_Agility", 0) * WEIGHT_IMPORTANTE + 
                pr.get("GK_Distribution", 0) * WEIGHT_MODERADO + 
                pr.get("Composure", 0) * WEIGHT_BAJO
            )
        else: 
            player_score = (
                pr.get("Short_Passing_Accuracy", 0) * WEIGHT_CRUCIAL +
                pr.get("First_Touch_Control", 0) * WEIGHT_CRUCIAL +
                pr.get("Vision_Free_Player", 0) * WEIGHT_IMPORTANTE +
                pr.get("Ball_Retention", 0) * WEIGHT_IMPORTANTE +
                pr.get("Spatial_Awareness", 0) * WEIGHT_IMPORTANTE +
                pr.get("Tactical_Awareness", 0) * WEIGHT_MODERADO + 
                pr.get("Composure", 0) * WEIGHT_MODERADO +
                pr.get("Decision_Making_Speed", 0) * WEIGHT_BAJO +
                pr.get("Creativity", 0) * WEIGHT_BAJO
            )
            if pr.get("Acceleration",0) > 3 and pr.get("Ball_Retention",0) < 2 : 
                 player_score -= 3
            if pr.get("Dribbling_Efficiency",0) > 3 and pr.get("Short_Passing_Accuracy",0) < 2: 
                 player_score -= 3
            
            is_ultradefensive = pr.get("Marking_Tightness", 5) <= 1 and pr.get("Strength_in_Duels",0) >=4 
            if is_ultradefensive and pr.get("Short_Passing_Accuracy",0) < 2:
                player_score += PENALTY_ULTRADEFENSIVO_SIN_PASE

            if rol_jugador == "Orquestador":
                num_orquestadores += 1
            
            if rol_jugador in ["Muralla", "Gladiador"] and pr.get("Short_Passing_Accuracy",0) >= 2:
                num_defensores_con_pase_minimo +=1

        team_score += player_score
    
    if num_orquestadores > 0:
        team_score += BONUS_ORQUESTADOR * num_orquestadores
    if num_defensores_con_pase_minimo >=1: 
        team_score += 5 

    return team_score

def calcular_score_contraataque(equipo, promedios_jugadores, roles_equipo, arquero_nombre_en_equipo):
    team_score = 0
    WEIGHT_CRUCIAL = 2.5
    WEIGHT_IMPORTANTE = 1.5
    WEIGHT_MODERADO = 1.0
    WEIGHT_BAJO = 0.5
    PENALTY_JUEGO_LENTO = -5
    BONUS_WILDCARD = 10
    BONUS_TOPADORA = 10
    BONUS_DEFENSE_TRANSITION_PLAYER = 7
    STAMINA_THRESHOLD_FOR_BONUS = 3.5
    num_wildcards = 0
    num_topadoras = 0
    jugadores_con_buena_trans_def = 0
    suma_stamina_campo = 0
    num_jugadores_campo = 0

    for jugador_nombre in equipo:
        pr = promedios_jugadores.get(jugador_nombre, {})
        rol_jugador = roles_equipo.get(jugador_nombre, "")
        if not pr: continue

        player_score = 0
        if jugador_nombre == arquero_nombre_en_equipo:
            player_score = (
                pr.get("GK_Distribution", 0) * WEIGHT_CRUCIAL + 
                pr.get("GK_Foot_Play", 0) * WEIGHT_IMPORTANTE + 
                pr.get("GK_Reaction", 0) * WEIGHT_MODERADO
            )
        else:
            num_jugadores_campo += 1
            suma_stamina_campo += pr.get("Stamina",0)

            player_score = (
                pr.get("Attack_Transition", 0) * WEIGHT_CRUCIAL +
                pr.get("Acceleration", 0) * WEIGHT_CRUCIAL +
                pr.get("Finishing_Precision", 0) * WEIGHT_IMPORTANTE +
                pr.get("Agility", 0) * WEIGHT_IMPORTANTE +
                pr.get("Dribbling_Efficiency", 0) * WEIGHT_MODERADO +
                pr.get("Power_Dribble_and_Score", 0) * WEIGHT_MODERADO +
                pr.get("Decision_Making_Speed", 0) * WEIGHT_MODERADO +
                pr.get("Vision_Free_Player", 0) * WEIGHT_BAJO 
            )
            if pr.get("Ball_Retention", 0) > 3 and pr.get("Acceleration",0) < 2:
                player_score += PENALTY_JUEGO_LENTO
            
            if rol_jugador == "Wildcard":
                num_wildcards += 1
            if rol_jugador == "Topadora":
                num_topadoras += 1
            if pr.get("Defense_Transition",0) >=4:
                jugadores_con_buena_trans_def +=1
                
        team_score += player_score

    if num_wildcards > 0:
        team_score += BONUS_WILDCARD * num_wildcards
    if num_topadoras > 0:
        team_score += BONUS_TOPADORA * num_topadoras
    if jugadores_con_buena_trans_def > 0: 
        team_score += BONUS_DEFENSE_TRANSITION_PLAYER 
    
    if num_jugadores_campo > 0 and (suma_stamina_campo / num_jugadores_campo) >= STAMINA_THRESHOLD_FOR_BONUS:
        team_score += 10 

    return team_score

# --- UI Rendering Functions ---

def render_sidebar(datos_jugadores_existentes, usuario_actual_nombre): # Cambiado nombre de param
    st.sidebar.title("⚽ Menú")
    
    # El nombre de usuario ya está validado, mostrarlo:
    st.sidebar.markdown(f"Usuario: **{usuario_actual_nombre}**")
    st.sidebar.markdown("---")

    menu_options = ["Agregar o editar jugador", "Perfiles de jugadores", "Análisis"]
    # No es necesario insertar "Agregar o editar jugador" basado en `usuario` aquí, ya que `usuario_actual_nombre` implica que ya existe.
    
    if 'menu_selection' not in st.session_state:
        st.session_state.menu_selection = menu_options[0] 

    if st.session_state.menu_selection not in menu_options:
         st.session_state.menu_selection = menu_options[0]

    menu = st.sidebar.radio("Selecciona opción:", menu_options, index=menu_options.index(st.session_state.menu_selection))
    st.session_state.menu_selection = menu

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Jugadores Convocados")
    
    convocados_changed = False
    sorted_player_names = sorted(datos_jugadores_existentes.keys())

    for nombre_jugador in sorted_player_names:
        info_jugador = datos_jugadores_existentes[nombre_jugador]
        proms = promedio_atributos(info_jugador.get(KEY_VOTACIONES, {}))
        rol, _ = obtener_rol(proms, info_jugador.get(KEY_TIPO, TIPO_CAMPO))
        es_convocado = info_jugador.get(KEY_CONVOCADO, True)
        emoji_rol = EMOJI.get(rol, "👤") 
        
        checkbox_label = f"{emoji_rol} {nombre_jugador}"
        # Usar un key único para el checkbox de convocatoria
        new_convocado_status = st.sidebar.checkbox(checkbox_label, value=es_convocado, key=f"convoc_{nombre_jugador}_sidebar")
        
        if datos_jugadores_existentes[nombre_jugador].get(KEY_CONVOCADO, True) != new_convocado_status: 
            datos_jugadores_existentes[nombre_jugador][KEY_CONVOCADO] = new_convocado_status
            convocados_changed = True
            
    if convocados_changed:
        guardar_datos(datos_jugadores_existentes)
        st.rerun() # Para reflejar cambios en la UI si es necesario
    return menu

def render_add_edit_player_page(datos, usuario):
    st.header("Editar o agregar jugador")
    # No es necesario chequear `usuario` aquí, ya que main() se encarga de eso.

    nombre_jugador_key = "nombre_jugador_input_add_edit" # Key única para el text_input
    nombre_jugador = st.text_input("Nombre del jugador", key=nombre_jugador_key).strip()
    
    default_tipo_index = 0 
    if nombre_jugador and nombre_jugador in datos:
        if datos[nombre_jugador].get(KEY_TIPO) == TIPO_ARQUERO:
            default_tipo_index = 1 
    
    tipo_jugador = st.radio("Tipo de Jugador", TIPOS_JUGADOR, horizontal=True, index=default_tipo_index, key="tipo_jugador_radio_add_edit")
    
    atributos_actuales = {}
    
    player_data = datos.get(nombre_jugador)
    existing_ratings_for_user = {}
    # Mostrar los ratings del usuario actual si existen, sino el promedio general
    if player_data and usuario in player_data.get(KEY_VOTACIONES, {}):
        existing_ratings_for_user = player_data[KEY_VOTACIONES][usuario]
        st.caption(f"Mostrando tus valoraciones previas para {nombre_jugador}.")
    elif player_data: 
        existing_ratings_for_user = promedio_atributos(player_data.get(KEY_VOTACIONES, {}))
        if existing_ratings_for_user:
            st.caption(f"Mostrando valoraciones promedio para {nombre_jugador} (aún no has votado por este jugador).")
        else:
            st.caption(f"{nombre_jugador} aún no tiene valoraciones. Establece las iniciales.")


    st.markdown("---")
    st.subheader("Atributos de Campo")
    for attr_key, attr_question in ATRIBUTOS_CAMPO:
        default_value = existing_ratings_for_user.get(attr_key, 2) 
        atributos_actuales[attr_key] = st.slider(attr_question, 0, 5, int(round(default_value)), key=f"{nombre_jugador_key}_{attr_key}_slider")

    st.markdown("---")
    if tipo_jugador == TIPO_CAMPO:
        st.subheader("Atributos Adicionales (Estilo Portero para Jugador de Campo)")
        dict_atributos_arquero = dict(ATRIBUTOS_ARQUERO)
        for attr_key in ATR_GK_CAMPO: 
            question = dict_atributos_arquero.get(attr_key, attr_key.replace("_", " "))
            default_value = existing_ratings_for_user.get(attr_key, 2)
            atributos_actuales[attr_key] = st.slider(question, 0, 5, int(round(default_value)), key=f"{nombre_jugador_key}_{attr_key}_gk_campo_slider")
    
    elif tipo_jugador == TIPO_ARQUERO:
        st.subheader("Atributos de Arquero")
        for attr_key, attr_question in ATRIBUTOS_ARQUERO:
            default_value = existing_ratings_for_user.get(attr_key, 2)
            atributos_actuales[attr_key] = st.slider(attr_question, 0, 5, int(round(default_value)), key=f"{nombre_jugador_key}_{attr_key}_arquero_slider")

    if st.button("💾 Guardar/Actualizar Jugador", key="save_player_button_add_edit"):
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
        if KEY_VOTACIONES not in datos[nombre_jugador] or not isinstance(datos[nombre_jugador][KEY_VOTACIONES], dict) :
             datos[nombre_jugador][KEY_VOTACIONES] = {} # Asegurar que votaciones es un dict

        datos[nombre_jugador][KEY_VOTACIONES][usuario] = atributos_actuales

        if KEY_CONVOCADO not in datos[nombre_jugador]:
            datos[nombre_jugador][KEY_CONVOCADO] = True

        guardar_datos(datos)
        st.success(f"¡Jugador '{nombre_jugador}' guardado/actualizado correctamente con tus valoraciones!")
        st.balloons()
        # Considerar limpiar el nombre del jugador para facilitar agregar otro, o dejarlo para re-editar.
        # st.session_state[nombre_jugador_key] = "" # Limpia el campo de nombre si se desea


def render_player_profiles_page(datos):
    st.header("Perfiles de jugadores")
    if not datos:
        st.info("Todavía no hay jugadores registrados. Agrega jugadores desde el menú lateral.")
        return

    perfiles_lista = []
    sorted_player_names = sorted(datos.keys())

    for nombre_jugador in sorted_player_names:
        info_jugador = datos[nombre_jugador]
        proms = promedio_atributos(info_jugador.get(KEY_VOTACIONES, {}))
        rol_principal, distribucion_roles = obtener_rol(proms, info_jugador.get(KEY_TIPO, TIPO_CAMPO))
        
        roles_ordenados = sorted(distribucion_roles.items(), key=lambda item: item[1], reverse=True)
        
        rol_secundario_str = "N/A"
        if len(roles_ordenados) > 1 and roles_ordenados[1][1] > 0.001: 
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
        
        displayed_attributes = {}
        # Para el DataFrame, queremos mostrar todos los atributos posibles, por si alguno tiene valor
        todos_atributos_keys = [k for k,_ in ATRIBUTOS_CAMPO] + [k for k,_ in ATRIBUTOS_ARQUERO]
        
        for attr_key in todos_atributos_keys:
             displayed_attributes[attr_key] = round(proms.get(attr_key, 0), 1)
       
        perfil_data.update(displayed_attributes)
        perfiles_lista.append(perfil_data)

    if perfiles_lista:
        df_perfiles = pd.DataFrame(perfiles_lista).fillna(0)
        
        column_order_display = ["Nombre", "Rol principal", "Rol secundario", "Descripción", "Comparables"]
        
        # Ordenar las columnas de atributos alfabéticamente para consistencia después de las columnas principales
        attribute_cols_from_data = sorted([col for col in df_perfiles.columns if col not in column_order_display])
        
        final_column_order_df = column_order_display + attribute_cols_from_data
        
        # Asegurar que todas las columnas en el orden final existan en el df, por si acaso
        for col in final_column_order_df:
            if col not in df_perfiles.columns:
                df_perfiles[col] = 0.0 

        # Presentar solo las columnas que tienen algún valor distinto de cero en alguna fila (para atributos)
        # O mantener todas si se prefiere ver el set completo de atributos.
        # Por ahora, mantenemos todas las columnas de atributos definidas.
        st.dataframe(df_perfiles[final_column_order_df].astype(str).replace(r'\.0$', '', regex=True), use_container_width=True) 
        
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
    
    roles_todos_jugadores = {
        nombre: obtener_rol(promedios_convocados[nombre], datos[nombre].get(KEY_TIPO, TIPO_CAMPO))[0] 
        for nombre in convocados if nombre in promedios_convocados
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

    def calcular_score_equipo_general(equipo_nombres_lista, promedios_jugadores_dict):
        score_total = 0
        for jugador_nombre in equipo_nombres_lista:
            if jugador_nombre in promedios_jugadores_dict and isinstance(promedios_jugadores_dict[jugador_nombre], dict):
                score_total += sum(val for val in promedios_jugadores_dict[jugador_nombre].values() if isinstance(val, (int, float)))
        return score_total

    st.markdown("#### 🏆 Mejores Equipos 5v5 (Equilibrio General)")
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
        st.info("No se pudieron generar equipos con balance general.")
    st.caption("Lógica Puntuación General: Suma de todos los atributos promediados.")
    st.markdown("---")

    estilos_tacticos = [
        {"nombre": "Catenaccio", "funcion_score": calcular_score_catenaccio, "emoji": "🛡️", 
         "caption": "Prioriza: Defensa sólida (Marcaje, Táctica, Fuerza), Atributos Mentales. Roles: Murallas, Gladiadores. Arquero: Clásico."},
        {"nombre": "Tiki-Taka", "funcion_score": calcular_score_tikitaka, "emoji": "🎼",
         "caption": "Prioriza: Pase, Control, Visión, Retención. Roles: Orquestadores. Arquero: Con buen juego de pies."},
        {"nombre": "Contraataque", "funcion_score": calcular_score_contraataque, "emoji": "⚡",
         "caption": "Prioriza: Velocidad, Dribbling, Transición Ofensiva, Definición. Roles: Wildcards, Topadoras. Arquero: Buen distribuidor."}
    ]

    for estilo in estilos_tacticos:
        st.markdown(f"#### {estilo['emoji']} Equipos Estilo {estilo['nombre']}")
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
            st.info(f"No se pudieron generar equipos estilo {estilo['nombre']}.")
        st.caption(estilo["caption"])
        st.markdown("---")

# --- Lógica Principal ---
def main():
    # Configuración de página como primer comando Streamlit
    st.set_page_config(page_title="Perfilador 5v5 Cumelo", page_icon="⚽", layout="wide")
    aplicar_estilos_css() # Aplicar CSS después de set_page_config

    usuario_actual = obtener_usuario()

    if not usuario_actual:
        # Mensaje en el área principal si el usuario aún no ha accedido.
        # La función obtener_usuario ya muestra el input en la sidebar.
        st.info("👈 Por favor, ingresa un nombre de usuario en la barra lateral y presiona 'Acceder' para usar la aplicación.")
        st.stop() # Detiene la ejecución del script aquí si no hay usuario.

    # Si llegamos aquí, el usuario es válido.
    datos_jugadores = cargar_datos()
    
    menu_seleccionado = render_sidebar(datos_jugadores, usuario_actual) # Pasar nombre del usuario

    if menu_seleccionado == "Agregar o editar jugador":
        render_add_edit_player_page(datos_jugadores, usuario_actual)
    elif menu_seleccionado == "Perfiles de jugadores":
        render_player_profiles_page(datos_jugadores)
    elif menu_seleccionado == "Análisis":
        render_team_analysis_page(datos_jugadores)

if __name__ == "__main__":
    main()
```

**Resumen de los cambios clave aplicados:**

1.  **Flujo de Inicio con Nombre de Usuario:**
    * La función `main()` ahora llama a `obtener_usuario()` como primer paso real después de la configuración de la página y CSS.
    * `obtener_usuario()` ha sido modificada para usar `st.session_state.usuario_valido`. Inicialmente es `False`. Muestra un `st.text_input` y un `st.button("Acceder")` en la barra lateral.
    * Solo cuando se presiona "Acceder" con un nombre válido, `st.session_state.usuario_valido` se vuelve `True`, se guarda el nombre en `st.session_state.usuario` y se ejecuta `st.rerun()` para recargar la app.
    * Si `st.session_state.usuario_valido` es `False`, `main()` muestra un mensaje de "Por favor, ingresa un nombre..." y se detiene con `st.stop()`.
    * Una vez que el usuario accede, `render_sidebar` muestra el nombre del usuario y el menú normal.

2.  **Color de Fondo y CSS:**
    * `st.set_page_config()` se llama al inicio de `main()`.
    * Una nueva función `aplicar_estilos_css()` se llama inmediatamente después para aplicar el CSS.
    * El CSS para `body, .stApp` se ha cambiado a `background-color: #eeeeee; color: #333333;`.
    * Se han añadido reglas CSS para asegurar que el texto en la barra lateral (que sigue siendo oscura) sea claro y legible (ej: `color: #e8e8e8 !important;` para etiquetas de radio y checkbox en la sidebar).
    * Se ha intentado hacer las etiquetas de los inputs del área principal más legibles sobre el fondo claro.

3.  **Lógica de Rol "Orquestador" Refinada:**
    * En la función `obtener_rol`, el cálculo de `score_orquestador` ahora es:
        ```python
        score_orquestador = (
            pr.get("Vision_Free_Player", 0) * 2.5       
            + pr.get("Short_Passing_Accuracy", 0) * 2.5 
            + pr.get("Creativity", 0) * 2.0             
            + pr.get("Decision_Making_Speed", 0) * 1.5  
            + pr.get("First_Touch_Control", 0) * 1.5    
            + pr.get("Spatial_Awareness", 0) * 1.5      
            + pr.get("Tactical_Awareness", 0) * 1.0    
            + pr.get("Composure", 0) * 1.0 
            + pr.get("Ball_Retention", 0) * 0.5 
        )
        ```
    * También he ajustado ligeramente las ponderaciones de otros roles para mantener un cierto equilibrio y diferenciación.

4.  **Responsividad:**
    * La estructura principal de Streamlit con `layout="wide"` y el uso de componentes estándar de Streamlit ya proporcionan una base responsiva.
    * Los cambios de CSS se han realizado con unidades relativas (`em`) o son cambios de color que no deberían afectar negativamente la responsividad. No se han introducido anchos fijos que puedan romper el layout en móviles.

**Consideraciones Adicionales en el Código:**

* He añadido `st.rerun()` después de que el usuario accede con éxito para asegurar que la interfaz se actualice inmediatamente.
* He añadido `key` únicas a varios widgets de Streamlit para evitar posibles conflictos de estado, especialmente con el nuevo flujo de login.
* En `render_add_edit_player_page`, se muestra un caption indicando si se están viendo las valoraciones previas del usuario actual o el promedio general.
* Pequeños ajustes en la lógica de `obtener_rol` para el manejo de jugadores tipo `TIPO_ARQUERO` y cómo se considera el atributo `GK_Reaction` para jugadores de campo (principalmente para visualización individual, no para la conformación del equipo donde el `TIPO_ARQUERO` es prioritario).

Espero que estos cambios se ajusten a tus necesidades. ¡Pruébalo y dime qué tal funcio
