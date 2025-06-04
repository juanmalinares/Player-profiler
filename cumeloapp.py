import streamlit as st
import pandas as pd
import json
import os
from itertools import combinations
import numpy as np

ARCHIVO_DATOS = 'players.json'

# Inicializar estado de edición
if 'editing' not in st.session_state:
    st.session_state.editing = None

# ATRIBUTOS DE ROLES (según tus definiciones)
GLADIADOR_ATTRS = [
    "Resilience_When_Behind", "Composure", "Strength_in_Duels", "Stamina",
    "Recovery_Runs", "Pressing_Consistency", "Marking_Tightness"
]
ORQUESTADOR_ATTRS = [
    "First_Touch_Control", "Short_Passing_Accuracy", "Vision_Free_Player",
    "Ball_Retention", "Tactical_Awareness", "Balance", "Decision_Making_Speed",
    "Creativity", "Leadership_Presence", "Communication", "Spatial_Awareness"
]
WILDCARD_OFF = [
    "Acceleration", "Dribbling_Efficiency", "Power_Dribble_and_Score",
    "Finishing_Precision", "Attack_Transition"
]
WILDCARD_DEF = [
    "Pressing_Consistency", "Marking_Tightness", "Recovery_Runs", "Strength_in_Duels"
]
MURALLA_ATTRS = [
    "Strength_in_Duels", "Defense_Transition", "Leadership_Presence",
    "Recovery_Runs", "Pressing_Consistency", "Marking_Tightness", "Tactical_Awareness"
]
ARQUERO_ATTRS = [
    "GK_Reaction", "GK_Positioning", "GK_Foot_Play", "GK_Agility", "GK_Bravery", "GK_Distribution"
]

# FUNCIONES PARA CADA ROL
def score_gladiador(attrs):
    return sum(attrs.get(k, 0) for k in GLADIADOR_ATTRS)

def score_orquestador(attrs):
    return sum(attrs.get(k, 0) for k in ORQUESTADOR_ATTRS)

def score_wildcard(attrs):
    # Suma de ofensivos menos suma de defensivos (defensivos penalizan)
    off = sum(attrs.get(k, 0) for k in WILDCARD_OFF)
    # Para WILDCARD, menor defensa = mayor score
    # Se invierte la suma defensiva (5-puntaje, pues sliders de 0 a 5)
    defense = sum(5 - attrs.get(k, 0) for k in WILDCARD_DEF)
    return off + defense

def score_muralla(attrs):
    return sum(attrs.get(k, 0) for k in MURALLA_ATTRS)

def score_arquero(attrs):
    # GK_Reaction es clave, pero suma todo para ranking completo
    return sum(attrs.get(k, 0) for k in ARQUERO_ATTRS)

# Funciones para cargar y guardar datos
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, 'r') as f:
            return json.load(f)
    return {}

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, 'w') as f:
        json.dump(datos, f, indent=4)

# Definición de atributos de campo (25)
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

# Definición de atributos de arquero
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

        # Encabezado y tipo
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

        # Nombre
        default_name = nombre_edit if es_edicion else ""
        nombre = st.text_input("Nombre del Jugador", value=default_name, key="player_name")

        if nombre:
            st.markdown("### Evalúa cada atributo (0–5)")
            attrs = {}

            # Atributos campo
            for clave, preg in ATRIBUTOS_CAMPO:
                default = datos[nombre_edit]["Atributos"].get(clave, 2) if es_edicion else 2
                attrs[clave] = st.slider(preg, 0, 5, default, key=clave)

            # Atributos GK opcionales si es campo
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

            # Guardar perfil
            if st.button("Guardar Perfil"):
                datos[nombre] = {"Tipo": tipo, "Atributos": attrs}
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
                fila = {"Nombre": jug, "Tipo": info["Tipo"]}
                fila.update(info["Atributos"])
                fila["Gladiador"] = score_gladiador(info["Atributos"])
                fila["Orquestador"] = score_orquestador(info["Atributos"])
                fila["Wildcard"] = score_wildcard(info["Atributos"])
                fila["Muralla"] = score_muralla(info["Atributos"])
                fila["Arquero"] = score_arquero(info["Atributos"])
                filas.append(fila)
            df = pd.DataFrame(filas).set_index("Nombre")
            st.dataframe(df)

            # Botones de editar y borrar
            st.write("---")
            for jug in list(datos.keys()):
                c1, c2, c3 = st.columns([6, 1, 1])
                c1.write(jug)
                if c2.button("✏️", key=f"edt_{jug}"):
                    st.session_state.editing = jug
                    return
                if c3.button("✖️", key=f"del_{jug}"):
                    datos.pop(jug)
                    guardar_datos(datos)
                    return
        else:
            st.info("No hay perfiles aún. Añade un jugador primero.")

    # --- ANALIZAR EQUIPOS ---
    elif accion == "Analizar Equipos":
        st.header("Compatibilidad y Construcción de Equipos")
        nombres = list(datos.keys())

        # Distancias
        if len(nombres) < 2:
            st.warning("Se necesitan al menos 2 jugadores.")
        else:
            mat = []
            for p in nombres:
                v = [datos[p]["Atributos"].get(k, 0) for k, _ in ATRIBUTOS_CAMPO]
                v += [datos[p]["Atributos"].get(k, 0) for k in ATR_GK_CAMPO]
                v += [datos[p]["Atributos"].get(k, 0) for k, _ in ATRIBUTOS_ARQUERO]
                mat.append(v)
            arr = np.array(mat)
            dist_list = []
            for i, j in combinations(range(len(nombres)), 2):
                d = np.linalg.norm(arr[i] - arr[j])
                dist_list.append({"A": nombres[i], "B": nombres[j], "Dist": round(d, 2)})
            df_dist = pd.DataFrame(dist_list).sort_values("Dist", ascending=False)
            st.subheader("Distancias por Pareja")
            st.dataframe(df_dist)
            mejor, peor = df_dist.iloc[0], df_dist.iloc[-1]
            st.markdown(f"**Más complementarios:** {mejor['A']} & {mejor['B']} (Dist {mejor['Dist']})")
            st.markdown(f"**Más similares:** {peor['A']} & {peor['B']} (Dist {peor['Dist']})")

            # Mejor por rol
            st.info(f"🥾 Mejor Gladiador: {max(nombres, key=lambda p: score_gladiador(datos[p]['Atributos']))}")
            st.info(f"🎩 Mejor Orquestador: {max(nombres, key=lambda p: score_orquestador(datos[p]['Atributos']))}")
            st.info(f"🔥 Mejor Wildcard: {max(nombres, key=lambda p: score_wildcard(datos[p]['Atributos']))}")
            st.info(f"💪 Mejor Muralla: {max(nombres, key=lambda p: score_muralla(datos[p]['Atributos']))}")
            st.info(f"🧤 Mejor Arquero: {max(nombres, key=lambda p: score_arquero(datos[p]['Atributos']))}")

        # Mejor equipo 5-a-side
        if len(nombres) >= 5:
            best_score, best_combo = -1, None
            for combo in combinations(nombres, 5):
                if sum(1 for p in combo if datos[p]['Tipo'] == 'Arquero') != 1:
                    continue
                speeds = [datos[p]['Atributos'].get('Acceleration', 0) for p in combo]
                strengths = [datos[p]['Atributos'].get('Strength_in_Duels', 0) for p in combo]
                leaders = [datos[p]['Atributos'].get('Leadership_Presence', 0) for p in combo]
                score = min(speeds) + min(strengths) + min(leaders)
                if score > best_score:
                    best_score, best_combo = score, combo
            if best_combo:
                st.subheader("🏆 Mejor Equipo 5-a-side")
                st.write(", ".join(best_combo))
                roles = {}
                used = set()
                asigns = [
                    ('Arquero', 'GK_Reaction'),
                    ('Extremo', 'Acceleration'),
                    ('Defensor', 'Strength_in_Duels'),
                    ('Capitán', 'Leadership_Presence'),
                    ('Creador', 'Creativity'),
                ]
                for rol, atr in asigns:
                    pick = max(
                        (p for p in best_combo if p not in used),
                        key=lambda p: datos[p]['Atributos'].get(atr, 0)
                    )
                    roles[pick] = rol
                    used.add(pick)
                st.table(pd.DataFrame.from_dict(roles, orient='index', columns=['Rol']))

        # Dos equipos balanceados
        if len(nombres) >= 10:
            st.subheader("🤝 Dos Equipos Balanceados")
            total = {
                p: sum(v for v in datos[p]['Atributos'].values() if isinstance(v, (int, float)))
                for p in nombres
            }
            orden = sorted(total, key=total.get, reverse=True)
            A, B = [], []
            for idx, p in enumerate(orden):
                (A if idx % 2 == 0 else B).append(p)
            st.write("**Equipo A:**", ", ".join(A[:5]))
            st.write("**Equipo B:**", ", ".join(B[:5]))

    barra.write(f"**Jugadores:** {len(datos)}")

if __name__ == "__main__":
    main()
