import streamlit as st
import networkx as nx
import json
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# CONFIGURATION DE LA PAGE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Jeu de l'Inspecteur - Graph Designer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
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
# INITIALISATION (GRAPHE VIDE DÉPART : UNIQUEMENT s ET t)
# -----------------------------------------------------------------------------
if "nodes" not in st.session_state:
    st.session_state.nodes = ["s", "t"]
if "positions" not in st.session_state:
    st.session_state.positions = {"s": (-3.0, 0.0), "t": (3.0, 0.0)}
if "edges" not in st.session_state:
    st.session_state.edges = []
if "source_node" not in st.session_state:
    st.session_state.source_node = "s"
if "target_node" not in st.session_state:
    st.session_state.target_node = "t"
if "show_grid" not in st.session_state:
    st.session_state.show_grid = True

# -----------------------------------------------------------------------------
# BARRE LATÉRALE
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Panneau de Contrôle")
    st.markdown("---")
    
    # 1. Option Repère
    st.subheader("📐 Repère Cartésien")
    st.session_state.show_grid = st.checkbox("Afficher le repère & coordonnées", value=st.session_state.show_grid)
    
    st.markdown("---")
    
    # 2. Ajouter un Sommet avec Coordonnées (X, Y)
    st.subheader("➕ Ajouter un Sommet")
    new_node = st.text_input("Nom du sommet (ex: v1) :", key="node_input").strip()
    col_x, col_y = st.columns(2)
    with col_x:
        pos_x = st.number_input("Coord. X :", value=0.0, step=0.5, key="new_x")
    with col_y:
        pos_y = st.number_input("Coord. Y :", value=0.0, step=0.5, key="new_y")
        
    if st.button("Ajouter Sommet"):
        if new_node:
            if new_node not in st.session_state.nodes:
                st.session_state.nodes.append(new_node)
                st.session_state.positions[new_node] = (pos_x, pos_y)
                st.success(f"Sommet {new_node} ajouté !")
                st.rerun()
            else:
                st.warning("Ce sommet existe déjà.")
        else:
            st.error("Nom invalide.")

    st.markdown("---")

    # 3. Ajouter une Arête Orientée
    st.subheader("🔗 Ajouter une Connexion")
    nodes_sorted = sorted(list(set(st.session_state.nodes)))
    if len(nodes_sorted) >= 2:
        c_src, c_dst = st.columns(2)
        with c_src:
            src = st.selectbox("Origine :", nodes_sorted, key="edge_src")
        with c_dst:
            dst = st.selectbox("Destination :", nodes_sorted, key="edge_dst")
            
        c_l, c_u = st.columns(2)
        with c_l:
            l_e = st.number_input("Borne inf (ℓₑ) :", min_value=0.0, value=1.0, step=0.5)
        with c_u:
            u_e = st.number_input("Borne sup (uₑ) :", min_value=0.0, value=5.0, step=0.5)
            
        real_c = st.number_input("Coût Réel (cₑ) :", min_value=0.0, value=2.0, step=0.5)
        
        if st.button("Connecter"):
            if src == dst:
                st.error("Impossible de créer une boucle.")
            elif l_e > u_e:
                st.error("ℓₑ doit être ≤ uₑ.")
            elif not (l_e <= real_c <= u_e):
                st.error("cₑ doit être dans [ℓₑ, uₑ] !")
            else:
                st.session_state.edges.append({
                    "source": src,
                    "target": dst,
                    "l_e": l_e,
                    "u_e": u_e,
                    "real_c": real_c
                })
                st.success(f"Connexion {src} ➔ {dst} ajoutée !")
                st.rerun()

    st.markdown("---")
    
    # 4. Suppressions Individuelles
    st.subheader("🗑️ Supprimer un Élément")
    
    # Supprimer un Sommet
    node_to_del = st.selectbox("Supprimer un sommet :", ["-- Aucun --"] + nodes_sorted)
    if st.button("❌ Supprimer Sommet"):
        if node_to_del != "-- Aucun --":
            st.session_state.nodes.remove(node_to_del)
            st.session_state.positions.pop(node_to_del, None)
            st.session_state.edges = [e for e in st.session_state.edges if e["source"] != node_to_del and e["target"] != node_to_del]
            st.success(f"Sommet {node_to_del} supprimé.")
            st.rerun()

    # Supprimer une Arête
    edge_list_str = [f"{e['source']} ➔ {e['target']}" for e in st.session_state.edges]
    edge_to_del = st.selectbox("Supprimer une connexion :", ["-- Aucune --"] + edge_list_str)
    if st.button("❌ Supprimer Connexion"):
        if edge_to_del != "-- Aucune --":
            idx_del = edge_list_str.index(edge_to_del) - 1
            del st.session_state.edges[idx_del]
            st.success("Connexion supprimée.")
            st.rerun()

    st.markdown("---")
    
    # 5. Export JSON & Reset
    st.subheader("💾 Export & Vider")
    config_data = {
        "nodes": st.session_state.nodes,
        "positions": st.session_state.positions,
        "edges": st.session_state.edges,
        "source_node": st.session_state.source_node,
        "target_node": st.session_state.target_node
    }
    st.download_button(
        label="📥 Exporter Setup (JSON)",
        data=json.dumps(config_data, indent=4),
        file_name="graphe_setup.json",
        mime="application/json"
    )
    
    if st.button("⚠️ Revenir à s et t vides"):
        st.session_state.nodes = ["s", "t"]
        st.session_state.positions = {"s": (-3.0, 0.0), "t": (3.0, 0.0)}
        st.session_state.edges = []
        st.rerun()

# -----------------------------------------------------------------------------
# ZONE PRINCIPALE
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🔍 Le Jeu de l'Inspecteur sur Graphes à Coûts Incertains</h1>
    <p>Visualisation interactive : boules claires, repère cartésien et suppression unitaire.</p>
</div>
""", unsafe_allow_html=True)

col_graph, col_data = st.columns([3, 2])

# -----------------------------------------------------------------------------
# RENDU CANVAS SVG (SANS AUCUNE DÉPENDANCE NÉCESSAIRE)
# -----------------------------------------------------------------------------
def render_svg_graph():
    # Définition de la grille cartésienne SVG (Largeur: 600, Hauteur: 400)
    width, height = 600, 400
    cx, cy = width / 2, height / 2
    scale = 60  # Échelle pixels par unité cartésienne

    svg_content = f'<svg width="{width}" height="{height}" style="background-color: #FAFAFA; border: 1px solid #E2E8F0; border-radius: 8px;">'
    
    # Dessin du Repère Grille (Axes X et Y)
    if st.session_state.show_grid:
        for x in range(0, width, int(scale)):
            svg_content += f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="#E2E8F0" stroke-width="1"/>'
        for y in range(0, height, int(scale)):
            svg_content += f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#E2E8F0" stroke-width="1"/>'
        # Axes principaux (0,0)
        svg_content += f'<line x1="{cx}" y1="0" x2="{cx}" y2="{height}" stroke="#CBD5E1" stroke-width="2"/>'
        svg_content += f'<line x1="0" y1="{cy}" x2="{width}" y2="{cy}" stroke="#CBD5E1" stroke-width="2"/>'

    # Calcul des Coordonnées
    node_coords = {}
    for n in st.session_state.nodes:
        px, py = st.session_state.positions.get(n, (0.0, 0.0))
        svg_x = cx + (px * scale)
        svg_y = cy - (py * scale)  # Inversion de l'axe Y pour la représentation cartésienne
        node_coords[n] = (svg_x, svg_y)

    # Marker Flèche SVG pour les arêtes
    svg_content += """
    <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748B"/>
        </marker>
    </defs>
    """

    # Dessin des Arêtes Orientées
    for e in st.session_state.edges:
        if e['source'] in node_coords and e['target'] in node_coords:
            x1, y1 = node_coords[e['source']]
            x2, y2 = node_coords[e['target']]
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            
            lbl = f"[{e['l_e']}, {e['u_e']}] | c={e['real_c']}"
            svg_content += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#64748B" stroke-width="2" marker-end="url(#arrow)"/>'
            svg_content += f'<rect x="{mid_x - 35}" y="{mid_y - 12}" width="70" height="18" fill="#FFFFFF" rx="4" stroke="#CBD5E1" stroke-width="1"/>'
            svg_content += f'<text x="{mid_x}" y="{mid_y + 1}" font-size="10" fill="#334155" text-anchor="middle" font-family="Inter">{lbl}</text>'

    # Dessin des Sommets (Boules Claires)
    for n in st.session_state.nodes:
        x, y = node_coords[n]
        if n == st.session_state.source_node:
            fill_bg, stroke_col, txt_col = "#DCFCE7", "#16A34A", "#15803D"
        elif n == st.session_state.target_node:
            fill_bg, stroke_col, txt_col = "#FEE2E2", "#DC2626", "#B91C1C"
        else:
            fill_bg, stroke_col, txt_col = "#F0F9FF", "#0284C7", "#0369A1"

        px, py = st.session_state.positions.get(n, (0.0, 0.0))
        label_text = f"{n} ({px},{py})" if st.session_state.show_grid else f"{n}"

        svg_content += f'<circle cx="{x}" cy="{y}" r="18" fill="{fill_bg}" stroke="{stroke_col}" stroke-width="2.5"/>'
        svg_content += f'<text x="{x}" y="{y + 4}" font-size="11" font-weight="bold" fill="{txt_col}" text-anchor="middle" font-family="Inter">{label_text}</text>'

    svg_content += '</svg>'
    return svg_content

with col_graph:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.subheader("🕸️ Vue du Graphe sur le Repère")
    components.html(render_svg_graph(), height=420)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TABLEAUX DE DONNÉES
# -----------------------------------------------------------------------------
with col_data:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.subheader("📌 Coordonnées des Sommets")
    
    pos_table = []
    for n in st.session_state.nodes:
        x, y = st.session_state.positions.get(n, (0.0, 0.0))
        pos_table.append({"Sommet": n, "X": x, "Y": y})
    st.dataframe(pos_table, use_container_width=True)

    st.markdown("### 📊 Connexions & Intervalles")
    if st.session_state.edges:
        edge_table = []
        for e in st.session_state.edges:
            edge_table.append({
                "Arête": f"{e['source']} ➔ {e['target']}",
                "Intervalle [ℓₑ, uₑ]": f"[{e['l_e']}, {e['u_e']}]",
                "Coût (cₑ)": e['real_c']
            })
        st.dataframe(edge_table, use_container_width=True)
        
        # Calculation de chemin simple avec NetworkX
        st.markdown("### 🔀 Chemins de s à t")
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
                cost = sum(G[p[i]][p[i+1]]["weight"] for i in range(len(p)-1))
                path_details.append({"Chemin": " ➔ ".join(p), "Coût Total": cost})
            st.dataframe(path_details, use_container_width=True)
        else:
            st.info(f"Aucun chemin orienté entre **{src}** et **{dst}**.")
    else:
        st.write("Aucune connexion.")
    st.markdown('</div>', unsafe_allow_html=True)
