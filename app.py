import streamlit as st
import networkx as nx
import json
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# CONFIGURATION DE LA PAGE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Jeu de l'Inspecteur - Canvas Interactif",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# INITIALISATION DU SESSION STATE (GRAPHE INITIAL : UNIQUEMENT s ET t)
# -----------------------------------------------------------------------------
if "nodes" not in st.session_state:
    st.session_state.nodes = ["s", "t"]
if "positions" not in st.session_state:
    st.session_state.positions = {"s": {"x": -2.5, "y": 0.0}, "t": {"x": 2.5, "y": 0.0}}
if "edges" not in st.session_state:
    st.session_state.edges = []
if "source_node" not in st.session_state:
    st.session_state.source_node = "s"
if "target_node" not in st.session_state:
    st.session_state.target_node = "t"
if "show_grid" not in st.session_state:
    st.session_state.show_grid = True

# -----------------------------------------------------------------------------
# BARRE LATÉRALE - DÉPLACEMENT, COORDONNÉES ET SUPPRESSION
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Panneau de Contrôle")
    st.markdown("---")
    
    # 1. REPÈRE & GRILLE
    st.subheader("📐 Options d'Affichage")
    st.session_state.show_grid = st.checkbox("Afficher le repère cartésien", value=st.session_state.show_grid)
    
    st.markdown("---")
    
    # 2. AJOUT / MODIFICATION PAR COORDONNÉES (X, Y)
    st.subheader("➕ Ajouter / Deplacer un Sommet")
    node_name = st.text_input("Nom du sommet (ex: v1, s, t) :", value="v1").strip()
    col_x, col_y = st.columns(2)
    with col_x:
        pos_x = st.number_input("Coord. X :", value=0.0, step=0.5)
    with col_y:
        pos_y = st.number_input("Coord. Y :", value=0.0, step=0.5)
        
    if st.button("📍 Appliquer Coordonnées"):
        if node_name:
            if node_name not in st.session_state.nodes:
                st.session_state.nodes.append(node_name)
            st.session_state.positions[node_name] = {"x": pos_x, "y": pos_y}
            st.success(f"Sommet **{node_name}** positionné à ({pos_x}, {pos_y})")
            st.rerun()

    st.markdown("---")

    # 3. AJOUT D'UNE ARÊTE
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
                st.error("cₑ doit appartenir à [ℓₑ, uₑ] !")
            else:
                st.session_state.edges.append({
                    "source": src,
                    "target": dst,
                    "l_e": l_e,
                    "u_e": u_e,
                    "real_c": real_c
                })
                st.success(f"Connexion {src} ➔ {dst} créée !")
                st.rerun()

    st.markdown("---")
    
    # 4. SUPPRESSION INDIVIDUELLE
    st.subheader("🗑️ Suppression Individuelle")
    node_to_del = st.selectbox("Supprimer un sommet :", ["-- Aucun --"] + nodes_sorted)
    if st.button("❌ Supprimer le Sommet"):
        if node_to_del != "-- Aucun --":
            st.session_state.nodes.remove(node_to_del)
            st.session_state.positions.pop(node_to_del, None)
            st.session_state.edges = [e for e in st.session_state.edges if e["source"] != node_to_del and e["target"] != node_to_del]
            st.success(f"Sommet {node_to_del} supprimé.")
            st.rerun()

    edge_list_str = [f"{e['source']} ➔ {e['target']}" for e in st.session_state.edges]
    edge_to_del = st.selectbox("Supprimer une connexion :", ["-- Aucune --"] + edge_list_str)
    if st.button("❌ Supprimer la Connexion"):
        if edge_to_del != "-- Aucune --":
            idx_del = edge_list_str.index(edge_to_del) - 1
            del st.session_state.edges[idx_del]
            st.success("Connexion supprimée.")
            st.rerun()

    st.markdown("---")
    
    # 5. EXPORT & REINITIALISATION
    st.subheader("💾 Export & Reset")
    config_data = {
        "nodes": st.session_state.nodes,
        "positions": st.session_state.positions,
        "edges": st.session_state.edges,
        "source_node": st.session_state.source_node,
        "target_node": st.session_state.target_node
    }
    st.download_button(
        label="📥 Exporter la Configuration (JSON)",
        data=json.dumps(config_data, indent=4),
        file_name="graphe_inspecteur.json",
        mime="application/json"
    )
    
    if st.button("⚠️ Vider tout (Revenir à s et t)"):
        st.session_state.nodes = ["s", "t"]
        st.session_state.positions = {"s": {"x": -2.5, "y": 0.0}, "t": {"x": 2.5, "y": 0.0}}
        st.session_state.edges = []
        st.rerun()

# -----------------------------------------------------------------------------
# DESSIN DYNAMIQUE DU CANVAS HTML5 / JAVASCRIPT (DRAG&DROP, ZOOM, PLEIN ÉCRAN)
# -----------------------------------------------------------------------------
def build_interactive_canvas_html():
    nodes_json = json.dumps(st.session_state.nodes)
    positions_json = json.dumps(st.session_state.positions)
    edges_json = json.dumps(st.session_state.edges)
    show_grid_js = "true" if st.session_state.show_grid else "false"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; user-select: none; }}
            #canvas-container {{ position: relative; width: 100%; height: 500px; background-color: #FAFAFA; border: 1px solid #CBD5E1; border-radius: 8px; }}
            canvas {{ display: block; width: 100%; height: 100%; cursor: grab; }}
            canvas:active {{ cursor: grabbing; }}
            .controls {{ position: absolute; top: 12px; right: 12px; display: flex; gap: 8px; z-index: 10; }}
            .btn {{ background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px; font-weight: bold; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .btn:hover {{ background: #F1F5F9; }}
        </style>
    </head>
    <body>
        <div id="canvas-container">
            <div class="controls">
                <button class="btn" onclick="zoomIn()">➕ Zoom In</button>
                <button class="btn" onclick="zoomOut()">➖ Zoom Out</button>
                <button class="btn" onclick="resetView()">🔄 Réinitialiser la Vue</button>
                <button class="btn" onclick="toggleFullScreen()">🖥️ Plein Écran</button>
            </div>
            <canvas id="graphCanvas"></canvas>
        </div>

        <script>
            const canvas = document.getElementById('graphCanvas');
            const ctx = canvas.getContext('2d');
            const container = document.getElementById('canvas-container');

            let nodes = {nodes_json};
            let positions = {positions_json};
            let edges = {edges_json};
            let showGrid = {show_grid_js};

            let scale = 60; // Pixels par unité cartésienne
            let offsetX = 0;
            let offsetY = 0;

            let isDraggingNode = false;
            let draggedNode = null;
            let isPanning = false;
            let startX, startY;

            function resizeCanvas() {{
                canvas.width = container.clientWidth;
                canvas.height = container.clientHeight;
                if (offsetX === 0 && offsetY === 0) {{
                    offsetX = canvas.width / 2;
                    offsetY = canvas.height / 2;
                }
                draw();
            }}

            window.addEventListener('resize', resizeCanvas);

            function toScreenX(x) {{ return offsetX + x * scale; }}
            function toScreenY(y) {{ return offsetY - y * scale; }}
            function toMathX(px) {{ return (px - offsetX) / scale; }}
            function toMathY(py) {{ return (offsetY - py) / scale; }}

            function draw() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // 1. DESSINER LA GRILLE & LE REPÈRE
                if (showGrid) {{
                    ctx.strokeStyle = '#E2E8F0';
                    ctx.lineWidth = 1;
                    const startGridX = offsetX % scale;
                    for (let x = startGridX; x < canvas.width; x += scale) {{
                        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
                    }}
                    const startGridY = offsetY % scale;
                    for (let y = startGridY; y < canvas.height; y += scale) {{
                        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
                    }}

                    // Axes X et Y principaux
                    ctx.strokeStyle = '#94A3B8';
                    ctx.lineWidth = 2;
                    ctx.beginPath(); ctx.moveTo(offsetX, 0); ctx.lineTo(offsetX, canvas.height); ctx.stroke();
                    ctx.beginPath(); ctx.moveTo(0, offsetY); ctx.lineTo(canvas.width, offsetY); ctx.stroke();
                }}

                // 2. DESSINER LES ARÊTES
                edges.forEach(e => {{
                    if (positions[e.source] && positions[e.target]) {{
                        const x1 = toScreenX(positions[e.source].x);
                        const y1 = toScreenY(positions[e.source].y);
                        const x2 = toScreenX(positions[e.target].x);
                        const y2 = toScreenY(positions[e.target].y);

                        // Ligne
                        ctx.strokeStyle = '#64748B';
                        ctx.lineWidth = 2;
                        ctx.beginPath();
                        ctx.moveTo(x1, y1);
                        ctx.lineTo(x2, y2);
                        ctx.stroke();

                        // Flèche
                        const angle = Math.atan2(y2 - y1, x2 - x1);
                        const headlen = 12;
                        const targetRadius = 20;
                        const fx = x2 - targetRadius * Math.cos(angle);
                        const fy = y2 - targetRadius * Math.sin(angle);

                        ctx.fillStyle = '#64748B';
                        ctx.beginPath();
                        ctx.moveTo(fx, fy);
                        ctx.lineTo(fx - headlen * Math.cos(angle - Math.PI / 6), fy - headlen * Math.sin(angle - Math.PI / 6));
                        ctx.lineTo(fx - headlen * Math.cos(angle + Math.PI / 6), fy - headlen * Math.sin(angle + Math.PI / 6));
                        ctx.fill();

                        // Label
                        const mx = (x1 + x2) / 2;
                        const my = (y1 + y2) / 2;
                        const lbl = `[${{e.l_e}}, ${{e.u_e}}] | c=${{e.real_c}}`;
                        ctx.font = '11px sans-serif';
                        const textWidth = ctx.measureText(lbl).width;

                        ctx.fillStyle = '#FFFFFF';
                        ctx.fillRect(mx - textWidth / 2 - 4, my - 10, textWidth + 8, 16);
                        ctx.strokeStyle = '#CBD5E1';
                        ctx.lineWidth = 1;
                        ctx.strokeRect(mx - textWidth / 2 - 4, my - 10, textWidth + 8, 16);

                        ctx.fillStyle = '#334155';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(lbl, mx, my);
                    }}
                }});

                // 3. DESSINER LES SOMMETS (BOULES CLAIRES)
                nodes.forEach(n => {{
                    if (!positions[n]) positions[n] = {{ x: 0, y: 0 }};
                    const sx = toScreenX(positions[n].x);
                    const sy = toScreenY(positions[n].y);

                    let fillBg = '#F0F9FF', strokeColor = '#0284C7', textColor = '#0369A1';
                    if (n === 's') {{ fillBg = '#DCFCE7'; strokeColor = '#16A34A'; textColor = '#15803D'; }}
                    else if (n === 't') {{ fillBg = '#FEE2E2'; strokeColor = '#DC2626'; textColor = '#B91C1C'; }}

                    // Cercle principal (Boule claire)
                    ctx.fillStyle = fillBg;
                    ctx.strokeStyle = strokeColor;
                    ctx.lineWidth = 3;
                    ctx.beginPath();
                    ctx.arc(sx, sy, 20, 0, 2 * Math.PI);
                    ctx.fill();
                    ctx.stroke();

                    // Nom du Sommet
                    ctx.fillStyle = textColor;
                    ctx.font = 'bold 12px sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(n, sx, sy);

                    // Coordonnées
                    if (showGrid) {{
                        ctx.fillStyle = '#475569';
                        ctx.font = '10px sans-serif';
                        ctx.fillText(`(${{positions[n].x.toFixed(1)}}, ${{positions[n].y.toFixed(1)}})`, sx, sy + 28);
                    }}
                }});
            }}

            // INTERACTION À LA SOURIS (DRAG & DROP DE SOMMET ET PANNING)
            canvas.addEventListener('mousedown', (e) => {{
                const rect = canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;

                // Vérifier si un sommet est cliqué
                for (let n of nodes) {{
                    const sx = toScreenX(positions[n].x);
                    const sy = toScreenY(positions[n].y);
                    const dist = Math.hypot(mouseX - sx, mouseY - sy);
                    if (dist <= 20) {{
                        isDraggingNode = true;
                        draggedNode = n;
                        return;
                    }}
                }}

                // Sinon, déplacer la vue (Pan)
                isPanning = true;
                startX = mouseX - offsetX;
                startY = mouseY - offsetY;
            }});

            canvas.addEventListener('mousemove', (e) => {{
                const rect = canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;

                if (isDraggingNode && draggedNode) {{
                    positions[draggedNode].x = parseFloat(toMathX(mouseX).toFixed(1));
                    positions[draggedNode].y = parseFloat(toMathY(mouseY).toFixed(1));
                    draw();
                }} else if (isPanning) {{
                    offsetX = mouseX - startX;
                    offsetY = mouseY - startY;
                    draw();
                }}
            }});

            canvas.addEventListener('mouseup', () => {{ isDraggingNode = false; draggedNode = null; isPanning = false; }});

            // ZOOM AVEC MOLETTE
            canvas.addEventListener('wheel', (e) => {{
                e.preventDefault();
                const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
                scale *= zoomFactor;
                draw();
            }});

            // COMMANDES BOUTONS
            function zoomIn() {{ scale *= 1.2; draw(); }}
            function zoomOut() {{ scale *= 0.8; draw(); }}
            function resetView() {{
                scale = 60;
                offsetX = canvas.width / 2;
                offsetY = canvas.height / 2;
                draw();
            }}

            function toggleFullScreen() {{
                if (!document.fullscreenElement) {{
                    container.requestFullscreen().catch(err => alert("Erreur plein écran"));
                }} else {{
                    document.exitFullscreen();
                }}
            }}

            setTimeout(resizeCanvas, 100);
        </script>
    </body>
    </html>
    """
    return html_code

# -----------------------------------------------------------------------------
# INTERFACE PRINCIPALE DE L'APPLICATION
# -----------------------------------------------------------------------------
st.title("🔍 Le Jeu de l'Inspecteur - Graph Designer")
st.markdown("Glissez-déposez les sommets avec la souris ou ajustez leurs coordonnées précises dans le panneau latéral.")

col_main, col_info = st.columns([3, 2])

with col_main:
    st.subheader("🕸️ Vue Cannevas Dynamique")
    components.html(build_interactive_canvas_html(), height=520)

with col_info:
    st.subheader("📊 Coordonnées Cartésiennes")
    pos_table = []
    for n in st.session_state.nodes:
        pos = st.session_state.positions.get(n, {"x": 0.0, "y": 0.0})
        pos_table.append({"Sommet": n, "Coord. X": pos["x"], "Coord. Y": pos["y"]})
    st.dataframe(pos_table, use_container_width=True)

    st.subheader("🔗 Connexions & Intervalles")
    if st.session_state.edges:
        edge_table = []
        for e in st.session_state.edges:
            edge_table.append({
                "Arête": f"{e['source']} ➔ {e['target']}",
                "Intervalle [ℓₑ, uₑ]": f"[{e['l_e']}, {e['u_e']}]",
                "Coût Réel (cₑ)": e['real_c']
            })
        st.dataframe(edge_table, use_container_width=True)

        # Calcul des chemins
        G = nx.DiGraph()
        for e in st.session_state.edges:
            G.add_edge(e["source"], e["target"], weight=e["real_c"])

        src = st.session_state.source_node
        dst = st.session_state.target_node

        if nx.has_path(G, src, dst):
            all_paths = list(nx.all_simple_paths(G, src, dst))
            st.markdown(f"**Chemins simples de {src} à {dst} ({len(all_paths)}) :**")
            path_details = []
            for idx, p in enumerate(all_paths, 1):
                cost = sum(G[p[i]][p[i+1]]["weight"] for i in range(len(p)-1))
                path_details.append({"Chemin": " ➔ ".join(p), "Coût Total": cost})
            st.dataframe(path_details, use_container_width=True)
        else:
            st.info(f"Aucun chemin orienté entre {src} et {dst}.")
    else:
        st.write("Aucune connexion.")
