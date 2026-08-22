import streamlit as st
import networkx as nx
from streamlit_agraph import agraph, Node, Edge, Config

# Configuration de la page et style moderne
st.set_page_config(
    page_title="Jeu de l'Inspecteur - Graph Designer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour une interface moderne
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 24px 32px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    
    .main-header p {
        margin: 6px 0 0 0;
        color: #94A3B8;
        font-size: 0.95rem;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
        background-color: #2563EB;
        color: white;
        border: none;
        padding: 8px 16px;
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        background-color: #1D4ED8;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    
    .card-box {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation de l'état de la session (Session State)
if "nodes" not in st.session_state:
    st.session_state.nodes = set(["s", "t"])
if "edges" not in st.session_state:
    st.session_state.edges = []
if "source_node" not in st.session_state:
    st.session_state.source_node = "s"
if "target_node" not in st.session_state:
    st.session_state.target_node = "t"

# Barre Latérale de Contrôle
with st.sidebar:
    st.title("⚙️ Panneau de Contrôle")
    st.markdown("---")
    
    # 1. Sommets Source / Destination
    st.subheader("1. Configuration Globale")
    nodes_sorted = sorted(list(st.session_state.nodes))
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
    
    # 2. Ajout de Sommet (Node)
    st.subheader("2. Ajouter un Sommet")
    new_node = st.text_input("Nom du sommet (ex: v1, v2) :", key="node_input").strip()
    if st.button("➕ Ajouter Sommet"):
        if new_node:
            if new_node not in st.session_state.nodes:
                st.session_state.nodes.add(new_node)
                st.success(f"Sommet **{new_node}** ajouté !")
                st.rerun()
            else:
                st.warning("Ce sommet existe déjà.")
        else:
            st.error("Veuillez saisir un nom valide.")

    st.markdown("---")
    
    # 3. Ajout d'Arête (Edge) avec incertitudes et coût réel
    st.subheader("3. Ajouter une Arête Orientée")
    if len(st.session_state.nodes) >= 2:
        col_src, col_dst = st.columns(2)
        with col_src:
            src = st.selectbox("Origine :", nodes_sorted, key="edge_src")
        with col_dst:
            dst = st.selectbox("Destination :", nodes_sorted, key="edge_dst")
            
        col_l, col_u = st.columns(2)
        with col_l:
            l_e = st.number_input("Borne inf (ℓₑ) :", min_value=0.0, value=1.0, step=0.5)
        with col_u:
            u_e = st.number_input("Borne sup (uₑ) :", min_value=0.0, value=10.0, step=0.5)
            
        real_c = st.number_input("Coût Réel (cₑ) :", min_value=0.0, value=5.0, step=0.5)
        
        if st.button("🔗 Connecter les Sommets"):
            if src == dst:
                st.error("Impossible de créer une boucle sur le même sommet.")
            elif l_e > u_e:
                st.error("La borne inférieure ℓₑ doit être ≤ à la borne supérieure uₑ.")
            elif not (l_e <= real_c <= u_e):
                st.error("Le coût réel cₑ doit appartenir à l'intervalle [ℓₑ, uₑ] !")
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
        st.info("Ajoutez au moins deux sommets pour pouvoir créer des connexions.")

    st.markdown("---")
    if st.button("🗑️ Réinitialiser le Graphe"):
        st.session_state.nodes = set(["s", "t"])
        st.session_state.edges = []
        st.session_state.source_node = "s"
        st.session_state.target_node = "t"
        st.rerun()

# Entête Principale
st.markdown("""
<div class="main-header">
    <h1>🔍 Le Jeu de l'Inspecteur sur Graphes à Coûts Incertains</h1>
    <p>Concevez des topologies de graphes, configurez les incertitudes d'intervalles [ℓₑ, uₑ] et analysez la structure des chemins.</p>
</div>
""", unsafe_allow_html=True)

# Disposition principale en deux colonnes
col_graph, col_analysis = st.columns([3, 2])

with col_graph:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.subheader("🕸️ Visualisation Interactive du Graphe")
    
    agraph_nodes = []
    for n in st.session_state.nodes:
        if n == st.session_state.source_node:
            color = "#22C55E" # Vert pour la Source
        elif n == st.session_state.target_node:
            color = "#EF4444" # Rouge pour le Puits
        else:
            color = "#3B82F6" # Bleu pour les nœuds intermédiaires
        agraph_nodes.append(Node(id=n, label=n, size=24, color=color))
        
    agraph_edges = []
    for e in st.session_state.edges:
        lbl = f"[{e['l_e']}, {e['u_e']}] | c={e['real_c']}"
        agraph_edges.append(Edge(
            source=e["source"],
            target=e["target"],
            label=lbl,
            color="#64748B",
            fontsize=12
        ))
        
    config = Config(
        width=700,
        height=480,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#F59E0B"
    )
    
    if agraph_nodes:
        agraph(nodes=agraph_nodes, edges=agraph_edges, config=config)
    else:
        st.info("Le graphe est actuellement vide.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_analysis:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.subheader("📊 Tableau des Arêtes & Analyse")
    
    if st.session_state.edges:
        table_data = []
        for e in st.session_state.edges:
            table_data.append({
                "Arête": f"{e['source']} ➔ {e['target']}",
                "Intervalle [ℓₑ, uₑ]": f"[{e['l_e']}, {e['u_e']}]",
                "Coût Réel (cₑ)": e['real_c']
            })
        st.dataframe(table_data, use_container_width=True)
        
        st.markdown("### 🔀 Chemins Simples s ➔ t")
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
                path_details.append({"Chemin": f"P{idx}: {path_str}", "Coût Total Réel": cost})
            st.dataframe(path_details, use_container_width=True)
        else:
            st.info(f"Aucun chemin orienté n'existe entre **{src}** et **{dst}**.")
    else:
        st.write("Aucune arête n'a été ajoutée.")
    st.markdown('</div>', unsafe_allow_html=True)
