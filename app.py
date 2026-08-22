import streamlit as st
import networkx as nx
import json
import math
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

# -----------------------------------------------------------------------------
# INITIALISATION DU SESSION STATE
# -----------------------------------------------------------------------------
if "nodes" not in st.session_state:
    st.session_state.nodes = ["s", "t"]
if "positions" not in st.session_state:
    st.session_state.positions = {"s": {"x": -2.5, "y": 0.0}, "t": {"x": 2.5, "y": 0.0}}
if "edges" not in st.session_state:
    st.session_state.edges = []
if "selected_node" not in st.session_state:
    st.session_state.selected_node = None
if "selected_edge" not in st.session_state:
    st.session_state.selected_edge = None
if "show_grid" not in st.session_state:
    st.session_state.show_grid = True

# Sync positions & sélections via les query_params
query_params = st.query_params
if "canvas_data" in query_params:
    try:
        updated_positions = json.loads(query_params["canvas_data"])
        for node, pos in updated_positions.items():
            if node in st.session_state.positions:
                st.session_state.positions[node] = pos
    except Exception:
        pass

if "selected_node" in query_params:
    st.session_state.selected_node = query_params["selected_node"] if query_params["selected_node"] != "" else None

if "selected_edge" in query_params:
    try:
        st.session_state.selected_edge = json.loads(query_params["selected_edge"]) if query_params["selected_edge"] != "" else None
    except Exception:
        st.session_state.selected_edge = None

# -----------------------------------------------------------------------------
# BARRE LATÉRALE - CONTRÔLES
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Panneau de Contrôle")
    st.markdown("---")
    
    st.subheader("📐 Options d'Affichage")
    st.session_state.show_grid = st.checkbox("Afficher le repère cartésien", value=st.session_state.show_grid)
    st.markdown("---")

    # AFFICHAGE DE LA SÉLECTION COURANTE
    if st.session_state.selected_node:
        st.info(f"📍 Sommet Sélectionné : **{st.session_state.selected_node}**")
    if st.session_state.selected_edge:
        st.info(f"🔗 Connexion Sélectionnée : **{st.session_state.selected_edge['source']} ➔ {st.session_state.selected_edge['target']}**")
    
    # 1. AJOUT / MODIFICATION DE SOMMET
    st.subheader("➕ Ajouter / Déplacer un Sommet")
    default_node = st.session_state.selected_node if st.session_state.selected_node else "v1"
    node_name = st.text_input("Nom du sommet :", value=default_node).strip()
    
    curr_x = st.session_state.positions.get(node_name, {}).get("x", 0.0)
    curr_y = st.session_state.positions.get(node_name, {}).get("y", 0.0)
    
    col_x, col_y = st.columns(2)
    with col_x:
        pos_x = st.number_input("Coord. X :", value=float(curr_x), step=0.5)
    with col_y:
        pos_y = st.number_input("Coord. Y :", value=float(curr_y), step=0.5)
        
    if st.button("📍 Positionner / Modifier le Sommet"):
        if node_name:
            if node_name not in st.session_state.nodes:
                st.session_state.nodes.append(node_name)
            st.session_state.positions[node_name] = {"x": pos_x, "y": pos_y}
            st.success(f"Sommet **{node_name}** mis à jour.")
            st.rerun()

    st.markdown("---")

    # 2. AJOUT D'UNE ARÊTE ET INTERVALLE DE COÛTS
    st.subheader("🔗 Ajouter une Connexion (Orientée)")
    nodes_sorted = sorted(list(set(st.session_state.nodes)))
    if len(nodes_sorted) >= 2:
        c_src, c_dst = st.columns(2)
        with c_src:
            src = st.selectbox("Origine :", nodes_sorted, key="edge_src")
        with c_dst:
            dst = st.selectbox("Destination :", nodes_sorted, key="edge_dst")
            
        interval_type = st.radio("Intervalle de Coût :", ["Infini ]0, +∞[", "Borné [ℓₑ, uₑ]"], key="interval_type")
        
        if interval_type == "Borné [ℓₑ, uₑ]":
            c_l, c_u = st.columns(2)
            with c_l:
                l_e = st.number_input("Borne inf (ℓₑ) :", min_value=0.0, value=1.0, step=0.5)
            with c_u:
                u_e = st.number_input("Borne sup (uₑ) :", min_value=0.0, value=5.0, step=0.5)
            real_c = st.number_input("Coût Réel (cₑ) :", min_value=0.0, value=2.0, step=0.5)
        else:
            l_e = 0.0
            u_e = float("inf")
            real_c = st.number_input("Coût Réel (cₑ) :", min_value=0.1, value=1.0, step=0.5)
            
        if st.button("Connecter"):
            if src == dst:
                st.error("Les boucles sur le même nœud sont interdites.")
            else:
                st.session_state.edges.append({
                    "source": src,
                    "target": dst,
                    "l_e": l_e,
                    "u_e": u_e,
                    "real_c": real_c
                })
                st.success(f"Arête {src} ➔ {dst} ajoutée !")
                st.rerun()

    st.markdown("---")
    
    # 3. SUPPRESSION PRÉCISE VIA CLIC OU SÉLECTION
    st.subheader("🗑️ Supprimer un Élément")

    # Supprimer l'élément sélectionné par le clic
    if st.session_state.selected_node:
        if st.button(f"❌ Supprimer le sommet '{st.session_state.selected_node}' par clic"):
            if st.session_state.selected_node in ["s", "t"]:
                st.error("Les nœuds 's' et 't' ne peuvent pas être supprimés.")
            else:
                target_node = st.session_state.selected_node
                st.session_state.nodes.remove(target_node)
                st.session_state.positions.pop(target_node, None)
                st.session_state.edges = [e for e in st.session_state.edges if e["source"] != target_node and e["target"] != target_node]
                st.session_state.selected_node = None
                st.rerun()

    if st.session_state.selected_edge:
        e_sel = st.session_state.selected_edge
        if st.button(f"❌ Supprimer l'arête '{e_sel['source']} ➔ {e_sel['target']}' par clic"):
            st.session_state.edges = [e for e in st.session_state.edges if not (e["source"] == e_sel["source"] and e["target"] == e_sel["target"])]
            st.session_state.selected_edge = None
            st.rerun()

    # Supprimer via la liste déroulante classique
    node_to_del = st.selectbox("Ou supprimer un sommet de la liste :", ["-- Aucun --"] + nodes_sorted)
    if st.button("❌ Supprimer Sommet Sélectionné (Liste)"):
        if node_to_del not in ["-- Aucun --", "s", "t"]:
            st.session_state.nodes.remove(node_to_del)
            st.session_state.positions.pop(node_to_del, None)
            st.session_state.edges = [e for e in st.session_state.edges if e["source"] != node_to_del and e["target"] != node_to_del]
            st.session_state.selected_node = None
            st.rerun()
        elif node_to_del in ["s", "t"]:
            st.error("Les nœuds s et t ne peuvent pas être supprimés.")

    edge_list_str = [f"{e['source']} ➔ {e['target']}" for e in st.session_state.edges]
    edge_to_del = st.selectbox("Ou supprimer une connexion de la liste :", ["-- Aucune --"] + edge_list_str)
    if st.button("❌ Supprimer Connexion Sélectionnée (Liste)"):
        if edge_to_del != "-- Aucune --":
            idx_del = edge_list_str.index(edge_to_del) - 1
            del st.session_state.edges[idx_del]
            st.session_state.selected_edge = None
            st.rerun()

    st.markdown("---")
    if st.button("⚠️ Vider tout (Garder s et t)"):
        st.session_state.nodes = ["s", "t"]
        st.session_state.positions = {"s": {"x": -2.5, "y": 0.0}, "t": {"x": 2.5, "y": 0.0}}
        st.session_state.edges = []
        st.session_state.selected_node = None
        st.session_state.selected_edge = None
        st.rerun()

# -----------------------------------------------------------------------------
# CANVAS INTERACTIF HTML5 AVEC DÉTECTION DE CLIC
# -----------------------------------------------------------------------------
def build_interactive_canvas_html():
    nodes_json = json.dumps(st.session_state.nodes)
    positions_json = json.dumps(st.session_state.positions)
    selected_node_json = json.dumps(st.session_state.selected_node)
    selected_edge_json = json.dumps(st.session_state.selected_edge)
    
    edges_copy = []
    for e in st.session_state.edges:
        e_c = dict(e)
        if math.isinf(e_c["u_e"]):
            e_c["u_e"] = "Infinity"
        edges_copy.append(e_c)
    edges_json = json.dumps(edges_copy)
    show_grid_js = "true" if st.session_state.show_grid else "false"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; font-family: sans-serif; user-select: none; }}
            #canvas-container {{ position: relative; width: 100%; height: 500px; background-color: #FAFAFA; border: 1px solid #CBD5E1; border-radius: 8px; }}
            canvas {{ display: block; width: 100%; height: 100%; cursor: grab; }}
            canvas:active {{ cursor: grabbing; }}
            .controls {{ position: absolute; top: 12px; right: 12px; display: flex; gap: 8px; z-index: 10; }}
            .btn {{ background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 12px; font-weight: bold; cursor: pointer; }}
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
            let selectedNode = {selected_node_json};
            let selectedEdge = {selected_edge_json};
            let showGrid = {show_grid_js};

            let scale = 60;
            let offsetX = 0, offsetY = 0;
            let isDraggingNode = false, draggedNode = null, isPanning = false, startX, startY;
            let mouseDownTime = 0;

            function resizeCanvas() {{
                canvas.width = container.clientWidth;
                canvas.height = container.clientHeight;
                if (offsetX === 0 && offsetY === 0) {{
                    offsetX = canvas.width / 2;
                    offsetY = canvas.height / 2;
                }}
                draw();
            }}

            window.addEventListener('resize', resizeCanvas);

            function toScreenX(x) {{ return offsetX + x * scale; }}
            function toScreenY(y) {{ return offsetY - y * scale; }}
            function toMathX(px) {{ return (px - offsetX) / scale; }}
            function toMathY(py) {{ return (offsetY - py) / scale; }}

            function saveStateToStreamlit() {{
                const url = new URL(window.parent.location.href);
                url.searchParams.set('canvas_data', JSON.stringify(positions));
                
                if (selectedNode) {{
                    url.searchParams.set('selected_node', selectedNode);
                }} else {{
                    url.searchParams.set('selected_node', '');
                }}

                if (selectedEdge) {{
                    url.searchParams.set('selected_edge', JSON.stringify(selectedEdge));
                }} else {{
                    url.searchParams.set('selected_edge', '');
                }}

                window.parent.history.replaceState({{}}, '', url.toString());
            }}

            function distanceToSegment(px, py, x1, y1, x2, y2) {{
                const l2 = (x2 - x1) ** 2 + (y2 - y1) ** 2;
                if (l2 === 0) return Math.hypot(px - x1, py - y1);
                let t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2;
                t = Math.max(0, Math.min(1, t));
                return Math.hypot(px - (x1 + t * (x2 - x1)), py - (y1 + t * (y2 - y1)));
            }}

            function draw() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                if (showGrid) {{
                    ctx.strokeStyle = '#E2E8F0'; ctx.lineWidth = 1;
                    for (let x = offsetX % scale; x < canvas.width; x += scale) {{
                        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
                    }}
                    for (let y = offsetY % scale; y < canvas.height; y += scale) {{
                        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
                    }}

                    ctx.strokeStyle = '#94A3B8'; ctx.lineWidth = 2;
                    ctx.beginPath(); ctx.moveTo(offsetX, 0); ctx.lineTo(offsetX, canvas.height); ctx.stroke();
                    ctx.beginPath(); ctx.moveTo(0, offsetY); ctx.lineTo(canvas.width, offsetY); ctx.stroke();
                }}

                // Dessin des arêtes
                edges.forEach(e => {{
                    if (positions[e.source] && positions[e.target]) {{
                        const x1 = toScreenX(positions[e.source].x);
                        const y1 = toScreenY(positions[e.source].y);
                        const x2 = toScreenX(positions[e.target].x);
                        const y2 = toScreenY(positions[e.target].y);

                        const isSelected = selectedEdge && selectedEdge.source === e.source && selectedEdge.target === e.target;
                        ctx.strokeStyle = isSelected ? '#EAB308' : '#64748B';
                        ctx.lineWidth = isSelected ? 4 : 2;

                        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();

                        const angle = Math.atan2(y2 - y1, x2 - x1);
                        const fx = x2 - 20 * Math.cos(angle);
                        const fy = y2 - 20 * Math.sin(angle);

                        ctx.fillStyle = isSelected ? '#EAB308' : '#64748B';
                        ctx.beginPath();
                        ctx.moveTo(fx, fy);
                        ctx.lineTo(fx - 12 * Math.cos(angle - Math.PI / 6), fy - 12 * Math.sin(angle - Math.PI / 6));
                        ctx.lineTo(fx - 12 * Math.cos(angle + Math.PI / 6), fy - 12 * Math.sin(angle + Math.PI / 6));
                        ctx.fill();

                        const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
                        const upperStr = e.u_e === "Infinity" ? "∞" : e.u_e;
                        const lbl = `]${{e.l_e}}, ${{upperStr}}[ | c=${{e.real_c}}`;
                        ctx.font = '11px sans-serif';
                        const textWidth = ctx.measureText(lbl).width;

                        ctx.fillStyle = isSelected ? '#FEF08A' : '#FFFFFF';
                        ctx.fillRect(mx - textWidth / 2 - 4, my - 10, textWidth + 8, 16);
                        ctx.strokeStyle = isSelected ? '#CA8A04' : '#CBD5E1';
                        ctx.strokeRect(mx - textWidth / 2 - 4, my - 10, textWidth + 8, 16);

                        ctx.fillStyle = '#334155'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                        ctx.fillText(lbl, mx, my);
                    }}
                }});

                // Dessin des nœuds
                nodes.forEach(n => {{
                    if (!positions[n]) positions[n] = {{ x: 0, y: 0 }};
                    const sx = toScreenX(positions[n].x);
                    const sy = toScreenY(positions[n].y);

                    let fillBg = '#F0F9FF', strokeColor = '#0284C7', textColor = '#0369A1';
                    if (n === 's') {{ fillBg = '#DCFCE7'; strokeColor = '#16A34A'; textColor = '#15803D'; }}
                    else if (n === 't') {{ fillBg = '#FEE2E2'; strokeColor = '#DC2626'; textColor = '#B91C1C'; }}

                    if (n === selectedNode) {{
                        ctx.fillStyle = 'rgba(234, 179, 8, 0.3)';
                        ctx.beginPath(); ctx.arc(sx, sy, 28, 0, 2 * Math.PI); ctx.fill();
                        strokeColor = '#CA8A04';
                    }}

                    ctx.fillStyle = fillBg; ctx.strokeStyle = strokeColor; ctx.lineWidth = 3;
                    ctx.beginPath(); ctx.arc(sx, sy, 20, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();

                    ctx.fillStyle = textColor; ctx.font = 'bold 12px sans-serif';
                    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                    ctx.fillText(n, sx, sy);

                    if (showGrid) {{
                        ctx.fillStyle = '#475569'; ctx.font = '10px sans-serif';
                        ctx.fillText(`(${{positions[n].x.toFixed(1)}}, ${{positions[n].y.toFixed(1)}})`, sx, sy + 28);
                    }}
                }});
            }}

            canvas.addEventListener('mousedown', (e) => {{
                mouseDownTime = Date.now();
                const rect = canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left, mouseY = e.clientY - rect.top;

                for (let n of nodes) {{
                    const sx = toScreenX(positions[n].x), sy = toScreenY(positions[n].y);
                    if (Math.hypot(mouseX - sx, mouseY - sy) <= 20) {{
                        isDraggingNode = true; draggedNode = n; return;
                    }}
                }}
                isPanning = true; startX = mouseX - offsetX; startY = mouseY - offsetY;
            }});

            canvas.addEventListener('mousemove', (e) => {{
                const rect = canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left, mouseY = e.clientY - rect.top;

                if (isDraggingNode && draggedNode) {{
                    positions[draggedNode].x = parseFloat(toMathX(mouseX).toFixed(1));
                    positions[draggedNode].y = parseFloat(toMathY(mouseY).toFixed(1));
                    draw();
                }} else if (isPanning) {{
                    offsetX = mouseX - startX; offsetY = mouseY - startY; draw();
                }}
            }});

            canvas.addEventListener('mouseup', (e) => {{
                const clickDuration = Date.now() - mouseDownTime;
                const rect = canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left, mouseY = e.clientY - rect.top;

                if (clickDuration < 200) {{
                    let foundNode = null;
                    let foundEdge = null;

                    // Vérifier si un nœud a été cliqué
                    for (let n of nodes) {{
                        const sx = toScreenX(positions[n].x), sy = toScreenY(positions[n].y);
                        if (Math.hypot(mouseX - sx, mouseY - sy) <= 20) {{
                            foundNode = n;
                            break;
                        }}
                    }}

                    // Si aucun nœud n'a été cliqué, vérifier si une arête a été cliquée
                    if (!foundNode) {{
                        for (let e_item of edges) {{
                            if (positions[e_item.source] && positions[e_item.target]) {{
                                const x1 = toScreenX(positions[e_item.source].x);
                                const y1 = toScreenY(positions[e_item.source].y);
                                const x2 = toScreenX(positions[e_item.target].x);
                                const y2 = toScreenY(positions[e_item.target].y);

                                const dist = distanceToSegment(mouseX, mouseY, x1, y1, x2, y2);
                                if (dist <= 8) {{
                                    foundEdge = {{ source: e_item.source, target: e_item.target }};
                                    break;
                                }}
                            }}
                        }}
                    }}

                    selectedNode = foundNode;
                    selectedEdge = foundEdge;
                    saveStateToStreamlit();
                }} else if (isDraggingNode) {{
                    saveStateToStreamlit();
                }}

                isDraggingNode = false; draggedNode = null; isPanning = false; 
                draw();
            }});

            canvas.addEventListener('wheel', (e) => {{
                e.preventDefault(); scale *= e.deltaY < 0 ? 1.1 : 0.9; draw();
            }});

            function zoomIn() {{ scale *= 1.2; draw(); }}
            function zoomOut() {{ scale *= 0.8; draw(); }}
            function resetView() {{ scale = 60; offsetX = canvas.width / 2; offsetY = canvas.height / 2; draw(); }}
            function toggleFullScreen() {{
                if (!document.fullscreenElement) container.requestFullscreen();
                else document.exitFullscreen();
            }}

            setTimeout(resizeCanvas, 100);
        </script>
    </body>
    </html>
    """
    return html_code

# -----------------------------------------------------------------------------
# INTERFACE PRINCIPALE
# -----------------------------------------------------------------------------
st.title("🔍 Le Jeu de l'Inspecteur - Graph Designer")

col_main, col_info = st.columns([3, 2])

with col_main:
    st.subheader("🕸️ Représentation du Graphe (Cliquez sur un sommet ou une connexion pour la sélectionner)")
    components.html(build_interactive_canvas_html(), height=520)

with col_info:
    st.subheader("⚡ Résolution du Chemin Optimal de s à t")
    
    if st.button("🚀 Calculer le Chemin Optimal & f(G, s, t, C)"):
        G = nx.DiGraph()
        for e in st.session_state.edges:
            G.add_edge(e["source"], e["target"], l_e=e["l_e"], u_e=e["u_e"], weight=e["real_c"])

        src, dst = "s", "t"

        if not nx.has_path(G, src, dst):
            st.error(f"Aucun chemin orienté valide ne relie la source '{src}' au puit '{dst}'.")
        else:
            shortest_path = nx.shortest_path(G, src, dst, weight="weight")
            shortest_cost = nx.shortest_path_length(G, src, dst, weight="weight")
            
            st.success(f"**Chemin Optimal de s à t :** {' ➔ '.join(shortest_path)}")
            st.info(f"**Coût Total Réel (cₑ) :** {shortest_cost}")

            paths = list(nx.all_simple_paths(G, src, dst))
            edges_in_paths = set()
            edge_counts = {}
            for p in paths:
                for i in range(len(p) - 1):
                    e = (p[i], p[i+1])
                    edges_in_paths.add(e)
                    edge_counts[e] = edge_counts.get(e, 0) + 1

            total_paths = len(paths)
            bridges = [e for e, count in edge_counts.items() if count == total_paths]
            D_0 = [e for e in edges_in_paths if e not in bridges]
            f_val = len(D_0)

            st.metric(label="Valeur f(G, s, t, C)", value=f_val)
            st.markdown(f"* **Nombre total de chemins simples de s à t :** {total_paths}")
            st.markdown(f"* **Ponts obligatoires exclus (|B|) :** {len(bridges)}")
            st.markdown(f"* **Taille de l'ensemble minimal D₀ :** {f_val}")

    st.markdown("---")
    st.subheader("📊 Sommets & Coordonnées")
    pos_table = [{"Sommet": n, "X": st.session_state.positions.get(n, {}).get("x", 0.0), "Y": st.session_state.positions.get(n, {}).get("y", 0.0)} for n in st.session_state.nodes]
    st.dataframe(pos_table, use_container_width=True)

    st.subheader("🔗 Arêtes de s à t")
    if st.session_state.edges:
        edge_table = []
        for e in st.session_state.edges:
            u_str = "∞" if math.isinf(e['u_e']) else str(e['u_e'])
            edge_table.append({
                "Arête": f"{e['source']} ➔ {e['target']}",
                "Intervalle ]ℓₑ, uₑ[": f"]{e['l_e']}, {u_str}[",
                "Coût Réel (cₑ)": e['real_c']
            })
        st.dataframe(edge_table, use_container_width=True)
