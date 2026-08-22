import streamlit as st
import networkx as nx
import json
import streamlit.components.v1 as components
from pyvis.network import Network

# -----------------------------------------------------------------------------
# CONFIGURATION DE LA PAGE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Jeu de l'Inspecteur - Graph Designer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS épuré et moderne
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 20px 28px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    
    .main-header p {
        margin: 4px 0 0 0;
        color: #94A3B8;
        font-size: 0.9rem;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
        background-color: #2563EB;
        color: white;
        border: none;
        padding: 8px 16px;
    }
    
    .stButton>button:hover {
        background-color: #1D4ED8;
    }
    
    .card-box {
        background-color: #FFFFFF;
        padding: 18px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# INITIALISATION DE LA SESSION
# -----------------------------------------------------------------------------
if "nodes" not in st.session_state:
    st.session_state.nodes = ["s", "t", "v1", "v2"]
if "edges" not in st.session_state:
    st.session_state.edges = [
        {"source": "s", "target": "v1", "l_e": 1.0, "u_e": 5.0, "real_c": 2.5},
        {"source": "v1", "target": "t", "l_e": 2.0, "u_e": 8.0, "real_c": 4.0},
        {"source": "s", "target": "v2", "l_e": 1.0, "u_e": 10.0, "real_c": 3.0},
        {"source": "v2", "target": "t", "l_e": 0.5, "u_e": 4.0, "real_c": 1.0}
    ]
if "source_node" not in st.session_state:
    st.session_state.source_node = "s"
if "target_node" not in st.session_state:
    st.session_state.target_node = "t"
if "layout_mode" not in st.session_state:
    st.session_state.layout_mode = "Règle & Grille Alignée"

# Convertir la liste de sommets en ensemble trié pour affichage
nodes_sorted = sorted(list(set(st.session_state.nodes)))

# -----------------------------------------------------------------------------
# BARRE LATÉRALE (SIDEBAR)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Panneau de Contrôle")
    st.markdown("---")
    
    # --- SECTION SAUVEGARDE ET CHARGEMENT ---
    st.subheader("💾 Sauvegarde & Chargement")
    
    # 1. Export JSON
    config_data = {
        "nodes": list(st.session_state.nodes),
        "edges": st.session_state.edges,
        "source_node": st.session_state.source_node,
        "target_node": st.session_state.target_node
    }
    json_str = json.dumps(config_data, indent=4)
    
    st.download_button(
        label="📥 Exporter la Configuration (JSON)",
        data=json_str,
        file_name="graphe_setup.json",
        mime="application/json"
    )
    
    # 2. Import JSON
    uploaded_file = st.file_uploader("📂 Importer un fichier de configuration", type=["json"])
    if uploaded_file is not None:
        try:
            imported_data = json.load(uploaded_file)
            st.session_state.nodes = list(imported_data.get("nodes", ["s", "t"]))
            st.session_state.edges = imported_data.get("edges", [])
            st.session_state.source_node = imported_data.get("source_node", "s")
            st.session_state.target_node = imported_data.get("target_node", "t")
            st.success("Configuration chargée avec succès !")
            st.rerun()
        except Exception as e:
            st.error("Erreur lors de la lecture du fichier JSON.")

    st.markdown("---")
    
    # --- DISPOSITION / ALIGNEMENT (STYLE RÈGLE) ---
    st.subheader("📐 Disposition du Graphe")
    layout_choice = st.radio(
        "Mode d'alignement :",
        ["Règle & Grille Alignée", "Dynamique (Libre)"],
        index=0 if st.session_state.layout_mode == "Règle & Grille Alignée" else 1
    )
    st.session_state.layout_mode = layout_choice

    st.markdown("---")

    # 1. Configuration des Sommets
    st.subheader("1. Configuration des Sommets")
    st.session_state.source_node = st.selectbox(
        "Sommet Source (s) :", 
        nodes_sorted, 
        index=nodes_sorted.index(st.session_state.source_node) if st.session_state.source_node in nodes_sorted else 0
    )
    st.session_state.target_node = st.selectbox(
        "Sommet Puits (t) :", 
        nodes_sorted, 
        index=nodes_sorted.index(st.session_state.target_node) if st.session_state.target_node in nodes_sorted else min(1, len(nodes_sorted)-1)
    )
    
    st.markdown("---")
    
    # 2. Ajout de Sommet
    st.subheader("2. Ajouter un Sommet")
    new_node = st.text_input("Nom du sommet (ex: v3) :", key="node_input").strip()
    if st.button("➕ Ajouter Sommet"):
        if new_node:
            if new_node not in st.session_state.nodes:
                st.session_state.nodes.append(new_node)
                st.success(f"Sommet **{new_node}** ajouté !")
                st.rerun()
            else:
                st.warning("Ce sommet existe déjà.")
        else:
            st.error("Nom invalide.")

    st.markdown("---")
    
    # 3. Ajout d'Arête Orientée
    st.subheader("3. Ajouter une Arête Orientée")
    if len(nodes_sorted) >= 2:
        col_src, col_dst = st.columns(2)
        with col_src:
            src = st.selectbox("Origine :", nodes_sorted, key="edge_src")
        with col_dst:
            dst = st.selectbox("Destination :", nodes_sorted, key="edge_dst")
            
        col_l, col_u = st.columns(2)
        with col_l:
            l_e = st.number_input("Borne inf (ℓₑ) :", min_value=0.0, value=1.0, step=0.5)
        with col_u:
            u_e = st.number_input("Borne sup (uₑ) :", min_value=0.0, value=5.0, step=0.5)
            
        real_c = st.number_input("Coût Réel (cₑ) :", min_value=0.0, value=2.0, step=0.5)
        
        if st.button("🔗 Connecter les Sommets"):
            if src == dst:
                st.error("Impossible de créer une boucle sur le même sommet.")
            elif l_e > u_e:
                st.error("La borne ℓₑ doit être ≤ uₑ.")
            elif not (l_e <= real_c <= u_e):
                st.error("Le coût réel cₑ doit appartenir à [ℓₑ, uₑ] !")
            else:
                st.session_state.edges.append({
                    "source": src,
                    "target": dst,
                    "l_e": l_e,
                    "u_e": u_e,
                    "real_c": real_c
                })
                st.success(f"Arête **{src} ➔ {dst}** ajoutée !")
                st.rerun()
    else:
        st.info("Ajoutez au moins deux sommets.")

    st.markdown("---")
    if st.button("🗑️ Réinitialiser le Graphe"):
        st.session_state.nodes = ["s", "t", "v1", "v2"]
        st.session_state.edges = []
        st.session_state.source_node = "s"
        st.session_state.target_node = "t"
        st.rerun()

# -----------------------------------------------------------------------------
# PAGE PRINCIPALE
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🔍 Le Jeu de l'Inspecteur sur Graphes à Coûts Incertains</h1>
    <p>Conception, alignement strict et analyse de graphes orientés avec incertitudes d'intervalles [ℓₑ, uₑ].</p>
</div>
""", unsafe_allow_html=True)

col_graph, col_analysis = st.columns([3, 2])

# -----------------------------------------------------------------------------
# VISUALISATION (Mode Alignement Règle & Grille / Mode Libres)
# -----------------------------------------------------------------------------
with col_graph:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.subheader(f"🕸️ Visualisation du Graphe ({st.session_state.layout_mode})")
    
    net = Network(height="460px", width="100%", directed=True, bgcolor="#FFFFFF", font_color="#000000")
    
    # Détermination des coordonnées géométriques (Alignement à la Règle)
    if st.session_state.layout_mode == "Règle & Grille Alignée":
        net.toggle_physics(False)  # Désactiver la physique pour figer l'alignement rectiligne
        
        # Algorithme de placement sur grille géométrique
        other_nodes = [n for n in nodes_sorted if n not in [st.session_state.source_node, st.session_state.target_node]]
        
        # Placer la source à gauche (x = -300)
        net.add_node(
            st.session_state.source_node, 
            label=f"s ({st.session_state.source_node})", 
            color="#22C55E", shape="circle", size=25, x=-350, y=0,
            font={"size": 18, "color": "#FFFFFF", "bold": True}
        )
        
        # Placer le puits à droite (x = +300)
        net.add_node(
            st.session_state.target_node, 
            label=f"t ({st.session_state.target_node})", 
            color="#EF4444", shape="circle", size=25, x=350, y=0,
            font={"size": 18, "color": "#FFFFFF", "bold": True}
        )
        
        # Placer les sommets intermédiaires alignés en colonnes rectilignes
        n_inter = len(other_nodes)
        if n_inter > 0:
            step_y = 120
            start_y = -((n_inter - 1) * step_y) / 2
            for idx, n in enumerate(other_nodes):
                # Disposition en double colonne si le nombre de sommets est grand
                x_pos = -120 if idx % 2 == 0 else 120
                y_pos = start_y + (idx // 2) * step_y if n_inter > 2 else start_y + idx * step_y
                net.add_node(
                    n, label=str(n), color="#3B82F6", shape="circle", size=22, x=x_pos, y=y_pos,
                    font={"size": 16, "color": "#FFFFFF"}
                )
    else:
        # Mode Dynamique
        net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=120, spring_strength=0.08)
        for n in nodes_sorted:
            if n == st.session_state.source_node:
                net.add_node(n, label=f"s ({n})", color="#22C55E", shape="circle", size=25, font={"size": 18, "color": "#FFFFFF", "bold": True})
            elif n == st.session_state.target_node:
                net.add_node(n, label=f"t ({n})", color="#EF4444", shape="circle", size=25, font={"size": 18, "color": "#FFFFFF", "bold": True})
            else:
                net.add_node(n, label=str(n), color="#3B82F6", shape="circle", size=20, font={"size": 16, "color": "#FFFFFF"})

    # Ajout des Arêtes avec étiquettes d'intervalles [ℓe, ue] et coût réel c_e
    for e in st.session_state.edges:
        label_text = f" [{e['l_e']}, {e['u_e']}] \n c={e['real_c']} "
        net.add_edge(
            e["source"], 
            e["target"], 
            label=label_text, 
            color="#475569", 
            arrows="to", 
            font={"size": 12, "align": "top", "background": "#F1F5F9"}
        )

    # Rendu HTML rapide
    net.save_graph("graph.html")
    with open("graph.html", "r", encoding="utf-8") as f:
        html_code = f.read()
    components.html(html_code, height=480)
    
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TABLEAU ET ANALYSE ALGORITHMIQUE
# -----------------------------------------------------------------------------
with col_analysis:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.subheader("📊 Liste des Arêtes & Intervalles")
    
    if st.session_state.edges:
        table_data = []
        for e in st.session_state.edges:
            table_data.append({
                "Arête": f"{e['source']} ➔ {e['target']}",
                "Intervalle ]ℓₑ, uₑ[": f"]{e['l_e']}, {e['u_e']}[",
                "Coût Réel (cₑ)": e['real_c']
            })
        st.dataframe(table_data, use_container_width=True)
        
        st.markdown("### 🔀 Chemins Simples de s à t")
        G = nx.DiGraph()
        for e in st.session_state.edges:
            G.add_edge(e["source"], e["target"], weight=e["real_c"])
            
        src = st.session_state.source_node
        dst = st.session_state.target_node
        
        if nx.has_path(G, src, dst):
            all_paths = list(nx.all_simple_paths(G, src, dst))
            st.write(f"Nombre total de chemins simples : **{len(all_paths)}**")
            
            path_details = []
            for idx, p in enumerate(all_paths, 1):
                cost = 0
                for i in range(len(p)-1):
                    cost += G[p[i]][p[i+1]]["weight"]
                path_str = " ➔ ".join(p)
                path_details.append({"Chemin": f"P{idx}: {path_str}", "Coût Total": cost})
            st.dataframe(path_details, use_container_width=True)
        else:
            st.info(f"Aucun chemin orienté n'existe entre **{src}** et **{dst}**.")
    else:
        st.write("Aucune arête n'a été ajoutée.")
    st.markdown('</div>', unsafe_allow_html=True)
