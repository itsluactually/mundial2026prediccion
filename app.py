import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime
from itertools import combinations

# ──────────────────────────────────────────────────────────────
# 🔧 BASE DE DATOS & INICIALIZACIÓN
# ──────────────────────────────────────────────────────────────
DB_FILE = "mundial_2026_grupos.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS predicciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    groups JSON,
                    knockout JSON,
                    fecha TEXT)''')
    conn.commit()
    conn.close()

def save_prediction(nombre, groups_data, knockout_data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    ko_json = json.dumps(knockout_data) if knockout_data else "{}"
    c.execute("INSERT INTO predicciones (nombre, groups, knockout, fecha) VALUES (?, ?, ?, ?)",
              (nombre, json.dumps(groups_data), ko_json, fecha))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT nombre, groups, knockout, fecha FROM predicciones ORDER BY fecha DESC", conn)
    conn.close()
    if df.empty: return pd.DataFrame()
    # Muestra "⏳ Pendiente" mientras no se activen eliminatorias
    df["Campeón"] = df["knockout"].apply(lambda x: json.loads(x).get("Campeon", "⏳ Pendiente"))
    df["Subcampeón"] = df["knockout"].apply(lambda x: json.loads(x).get("Finalista", "⏳ Pendiente"))
    return df[["nombre", "Campeón", "Subcampeón", "fecha"]].rename(columns={"fecha": "📅 Enviado"})

init_db()

# ──────────────────────────────────────────────────────────────
# 🌍 CONFIGURACIÓN EDITABLE
# ──────────────────────────────────────────────────────────────
GROUPS = {
    "A": ["🇲🇽 México", "🇿🇦 Sudáfrica", "🇰🇷 Corea del Sur", "🇨🇿 Chequia"],
    "B": ["🇨🇦 Canadá", "🇧🇦 Bosnia y Herzegovina", "🇶🇦 Catar", "🇨🇭 Suiza"],
    "C": ["🇧🇷 Brasil", "🇲🇦 Marruecos", "🇭🇹 Haití", "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Escocia"],
    "D": ["🇺🇸 Estados Unidos", "🇵🇾 Paraguay", "🇦🇺 Australia", "🇹🇷 Turquía"],
    "E": ["🇩🇪 Alemania", "🇨🇼 Curazao", "\U0001F1E8\U0001F1EE Costa de Marfil", "🇪🇨 Ecuador"],
    "F": ["🇳🇱 Países Bajos", "🇯🇵 Japón", "🇸🇪 Suecia", "🇹🇳 Túnez"],
    "G": ["🇧🇪 Bélgica", "🇪🇬 Egipto", "🇮🇷 Irán", "🇳🇿 Nueva Zelanda"],
    "H": ["🇪🇸 España", "🇨🇻 Cabo Verde", "🇸🇦 Arabia Saudita", "🇺🇾 Uruguay"],
    "I": ["🇫🇷 Francia", "🇸🇳 Senegal", "🇮🇶 Irak", "🇳🇴 Noruega"],
    "J": ["🇦🇷 Argentina", "🇩🇿 Argelia", "🇦🇹 Austria", "🇯🇴 Jordania"],
    "K": ["🇵🇹 Portugal", "🇨🇴 Colombia", "🇺🇿 Uzbekistán", "🇨🇩 República Democrática del Congo"],
    "L": ["🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "🇭🇷 Croacia", "🇬🇭 Ghana", "🇵🇦 Panamá"]
}

GROUP_MATCHES = {grp: list(combinations(teams, 2)) for grp, teams in GROUPS.items()}

# ──────────────────────────────────────────────────────────────
# 📊 LÓGICA DE CLASIFICACIÓN Y TERCEROS
# ──────────────────────────────────────────────────────────────
def calc_standings(group, matches_scores):
    teams = GROUPS[group]
    standings = {t: {"PTS": 0, "GD": 0, "GF": 0, "GA": 0} for t in teams}
    
    for (t1, t2), (g1, g2) in matches_scores.items():
        if g1 is None or g2 is None: continue
        standings[t1]["GF"] += g1; standings[t1]["GA"] += g2
        standings[t2]["GF"] += g2; standings[t2]["GA"] += g1
        if g1 > g2: standings[t1]["PTS"] += 3
        elif g2 > g1: standings[t2]["PTS"] += 3
        else: standings[t1]["PTS"] += 1; standings[t2]["PTS"] += 1
        standings[t1]["GD"] = standings[t1]["GF"] - standings[t1]["GA"]
        standings[t2]["GD"] = standings[t2]["GF"] - standings[t2]["GA"]
        
    df = pd.DataFrame.from_dict(standings, orient="index").reset_index()
    df.rename(columns={"index": "Equipo"}, inplace=True)
    df.sort_values(["PTS", "GD", "GF"], ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.index += 1
    return df

def get_best_thirds(all_standings):
    thirds = []
    for grp, df in all_standings.items():
        if len(df) >= 3:
            t3 = df.iloc[2].copy()
            t3["Grupo"] = grp
            thirds.append(t3)
    tdf = pd.DataFrame(thirds)
    if tdf.empty: return []
    tdf.sort_values(["PTS", "GD", "GF"], ascending=False, inplace=True)
    return tdf.head(8)["Equipo"].tolist()

# ──────────────────────────────────────────────────────────────
# 🎨 ESTILO
# ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="🌎 Mundial 2026 - Predictor Pro", layout="wide")
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
    h1, h2, h3 { color: #fbbf24 !important; }
    .stExpander { background-color: #1e293b !important; border: 1px solid #334155 !important; border-radius: 10px !important; }
    .stNumberInput input { background-color: #334155 !important; color: #fff !important; border-radius: 8px !important; }
    .stButton button { background-color: #22c55e !important; color: #fff !important; border-radius: 8px !important; font-weight: bold; padding: 0.5rem 1rem; }
    .stProgress > div > div > div > div { background-color: #38bdf8 !important; }
    footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# 🖥️ INTERFAZ & ESTADO
# ──────────────────────────────────────────────────────────────
if "user" not in st.session_state: st.session_state.user = ""
if "step" not in st.session_state: st.session_state.step = "name"
if "scores" not in st.session_state: st.session_state.scores = {}

def reset_all():
    for k in ["user", "step", "scores"]: st.session_state.pop(k, None)
    st.rerun()

tab_pred, tab_board = st.tabs(["📝 Tu Predicción", "👀 Tablero Global"])

with tab_pred:
    st.title("🌎⚽ Predictor Mundial 2026")
    
    # PASO 1: NOMBRE
    if st.session_state.step == "name":
        st.markdown("### 👤 Identifícate")
        name = st.text_input("Nombre o apodo", key="name_input")
        if st.button("🚀 Empezar", type="primary", use_container_width=True):
            if name.strip():
                st.session_state.user = name.strip()
                st.session_state.step = "groups"
                st.rerun()
            else: st.error("Ingresa un nombre.")
    
    # PASO 2: FASE DE GRUPOS (ÚNICA ACTIVA POR AHORA)
    elif st.session_state.step == "groups":
        st.markdown("### 🏁 Fase de Grupos - Predice Marcadores")
        total_matches = sum(len(m) for m in GROUP_MATCHES.values())
        filled = sum(1 for v in st.session_state.scores.values() if v[0] is not None and v[1] is not None)
        st.progress(filled / total_matches, "📝 Progreso de predicciones")
        
        all_standings = {}
        
        for grp in GROUPS:
            with st.expander(f"📊 Grupo {grp}", expanded=False):
                matches = GROUP_MATCHES[grp]
                matches_scores = {}
                
                for t1, t2 in matches:
                    key = f"{grp}_{t1}_vs_{t2}"
                    col1, col_vs, col2 = st.columns([3, 1, 3])
                    with col1: st.markdown(f"**{t1}**")
                    g1 = st.number_input("", min_value=0, max_value=20, step=1, key=key+"g1", label_visibility="collapsed")
                    with col_vs: st.markdown("<div style='text-align:center;color:#94a3b8;font-weight:bold'>VS</div>", unsafe_allow_html=True)
                    g2 = st.number_input("", min_value=0, max_value=20, step=1, key=key+"g2", label_visibility="collapsed")
                    with col2: st.markdown(f"**{t2}**")
                    
                    matches_scores[(t1, t2)] = (g1, g2)
                    st.session_state.scores[key] = (g1, g2)
                
                std = calc_standings(grp, matches_scores)
                all_standings[grp] = std
                st.dataframe(std, use_container_width=True, hide_index=True, column_config={"Equipo": "🏳️", "PTS": "📊", "GD": "📈", "GF": "⚽", "GA": "🥅"})
        
        # Ranking de terceros
        st.markdown("---")
        st.subheader("🔄 Ranking de Terceros (clasifican 8)")
        thirds_df = pd.DataFrame([{"Equipo": df.iloc[2]["Equipo"], "Grupo": grp, "PTS": df.iloc[2]["PTS"], "GD": df.iloc[2]["GD"], "GF": df.iloc[2]["GF"]} 
                                  for grp, df in all_standings.items() if len(df)>=3])
        thirds_df.sort_values(["PTS", "GD", "GF"], ascending=False, inplace=True)
        thirds_df.index += 1
        st.dataframe(thirds_df.head(12), use_container_width=True, hide_index=True, column_config={"Equipo": "🏳️", "Grupo": "📍"})
        
        best_8 = get_best_thirds(all_standings)
        if best_8:
            st.success(f"✅ Clasifican como mejores terceros: `{', '.join(best_8)}`")
        
        st.markdown("---")
        st.info("🔒 **Fase Eliminatoria:** Se habilitará automáticamente cuando la FIFA confirme los cruces oficiales.")
        
        if st.button("💾 GUARDAR FASE DE GRUPOS", type="primary", use_container_width=True):
            groups_data = {k: list(v) for k, v in st.session_state.scores.items()}
            save_prediction(st.session_state.user, groups_data, None)
            st.success("✅ ¡Fase de Grupos guardada! Podrás completar eliminatorias más tarde.")
            st.button("🔄 Nueva Predicción", on_click=reset_all)

with tab_board:
    st.title("👀 Tablero Global de Amigos")
    df = get_leaderboard()
    if df.empty:
        st.info("📭 Aún no hay predicciones registradas.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption("💡 Las predicciones de eliminatorias se añadirán cuando se activen.")


