"""
Genera diagramas de flujo vectoriales (SVG) y rasterizados (PNG) a partir
de un bloque JSON incrustado en el texto de la especificacion generada por LLM.

Formato esperado en la spec:
  ```json
  {
    "titulo": "...",
    "nodes": [
      {"id": "start", "label": "Inicio",      "type": "start"},
      {"id": "n1",    "label": "Paso",        "type": "process"},
      {"id": "n2",    "label": "¿Condicion?", "type": "decision"},
      {"id": "end",   "label": "Fin",         "type": "end"}
    ],
    "edges": [
      {"from": "start", "to": "n1"},
      {"from": "n1",    "to": "n2"},
      {"from": "n2",    "to": "end", "label": "Si"},
      {"from": "n2",    "to": "n1",  "label": "No"}
    ]
  }
  ```
"""
import io
import json
import re
import textwrap
from collections import defaultdict, deque

# ── palette ───────────────────────────────────────────────────────────────────
C_START_BG  = "#00c9b1"
C_END_BG    = "#1a3a6b"
C_PROC_BG   = "#ffffff"
C_PROC_BDR  = "#1a3a6b"
C_DEC_BG    = "#fef9c3"
C_DEC_BDR   = "#b45309"
C_ARROW     = "#1e6feb"
C_LBL_BG    = "#f0f4fa"
C_LBL_BDR   = "#c7d4eb"
C_TEXT_DK   = "#0d1b2a"
C_TEXT_LT   = "#ffffff"
C_CANVAS    = "#f8fafc"
C_BORDER    = "#e2e8f0"

# ── geometry ──────────────────────────────────────────────────────────────────
NW       = 160   # process rect width
NH       = 44    # process rect height
DH       = 52    # decision diamond half-diagonal
ERX      = 68    # start/end ellipse half-width
ERY      = 24    # start/end ellipse half-height
LAYER_H  = 130   # vertical distance between layer centres
H_GAP    = 52    # horizontal gap between siblings
PAD_X    = 90    # canvas horizontal padding
PAD_Y    = 70    # canvas vertical padding (below title)
TITLE_H  = 44    # space reserved for title at top


# ─────────────────────────────────────────────────────────────────────────────
#  JSON extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_flow_json(spec_text: str) -> dict | None:
    """Return parsed flow dict from the first ```json block in spec_text."""
    match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", spec_text, re.IGNORECASE)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
        if "nodes" not in data or "edges" not in data:
            return None
        return data
    except (json.JSONDecodeError, ValueError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  Layout
# ─────────────────────────────────────────────────────────────────────────────

def _layout(nodes_list: list, edges_list: list) -> tuple[dict, float, float]:
    """BFS-layered layout → {node_id: (cx, cy)}, canvas_w, canvas_h."""
    ids = {n["id"] for n in nodes_list}
    adj: dict[str, list] = defaultdict(list)
    for e in edges_list:
        if e.get("from") in ids and e.get("to") in ids:
            adj[e["from"]].append(e["to"])

    # Root detection
    roots = [n["id"] for n in nodes_list if n.get("type") == "start"]
    if not roots:
        in_deg: dict[str, int] = defaultdict(int)
        for e in edges_list:
            if e.get("from") in ids and e.get("to") in ids:
                in_deg[e["to"]] += 1
        roots = [n["id"] for n in nodes_list if in_deg[n["id"]] == 0]
    if not roots:
        roots = [nodes_list[0]["id"]]

    # BFS rank assignment
    rank: dict[str, int] = {}
    q: deque = deque()
    for r in roots:
        rank[r] = 0
        q.append(r)
    visited = set(roots)
    while q:
        nid = q.popleft()
        for nb in adj[nid]:
            if nb not in visited:
                rank[nb] = rank[nid] + 1
                visited.add(nb)
                q.append(nb)
    max_rank = max(rank.values(), default=0)
    for n in nodes_list:
        if n["id"] not in rank:
            max_rank += 1
            rank[n["id"]] = max_rank

    # Group by rank
    by_rank: dict[int, list] = defaultdict(list)
    for n in nodes_list:
        by_rank[rank[n["id"]]].append(n["id"])

    max_cols = max(len(v) for v in by_rank.values())
    canvas_w = max(max_cols * (NW + H_GAP) - H_GAP + 2 * PAD_X, 420.0)
    canvas_h = (max_rank + 1) * LAYER_H + 2 * PAD_Y

    positions: dict[str, tuple[float, float]] = {}
    for row, nids in by_rank.items():
        n = len(nids)
        total_w = n * NW + (n - 1) * H_GAP
        x0 = (canvas_w - total_w) / 2
        cy = PAD_Y + row * LAYER_H + LAYER_H / 2
        for col, nid in enumerate(nids):
            positions[nid] = (x0 + col * (NW + H_GAP) + NW / 2, cy)

    return positions, canvas_w, canvas_h


def _bounds(node: dict, cx: float, cy: float) -> dict[str, tuple[float, float]]:
    t = node.get("type", "process")
    if t in ("start", "end"):
        return {"top": (cx, cy - ERY), "bottom": (cx, cy + ERY),
                "left": (cx - ERX, cy), "right": (cx + ERX, cy)}
    if t == "decision":
        return {"top": (cx, cy - DH), "bottom": (cx, cy + DH),
                "left": (cx - DH, cy), "right": (cx + DH, cy)}
    return {"top": (cx, cy - NH / 2), "bottom": (cx, cy + NH / 2),
            "left": (cx - NW / 2, cy), "right": (cx + NW / 2, cy)}


# ─────────────────────────────────────────────────────────────────────────────
#  SVG generation (pure Python, zero dependencies)
# ─────────────────────────────────────────────────────────────────────────────

def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def _svg_node(node: dict, cx: float, cy: float) -> str:
    nid   = node["id"]
    label = node.get("label", nid)
    t     = node.get("type", "process")
    lines = textwrap.wrap(label, 20) or [""]
    lh    = 14.0
    spans = "".join(
        f'<tspan x="{cx:.1f}" dy="{((i - (len(lines)-1)/2) * lh):.1f}">{_esc(ln)}</tspan>'
        for i, ln in enumerate(lines)
    )

    if t == "start":
        shape = (f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{ERX}" ry="{ERY}" '
                 f'fill="{C_START_BG}" stroke="{C_PROC_BDR}" stroke-width="2"/>')
        tc = C_TEXT_DK
    elif t == "end":
        shape = (f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{ERX}" ry="{ERY}" '
                 f'fill="{C_END_BG}" stroke="{C_PROC_BDR}" stroke-width="2"/>')
        tc = C_TEXT_LT
    elif t == "decision":
        pts = (f"{cx:.1f},{cy - DH:.1f} {cx + DH:.1f},{cy:.1f} "
               f"{cx:.1f},{cy + DH:.1f} {cx - DH:.1f},{cy:.1f}")
        shape = (f'<polygon points="{pts}" fill="{C_DEC_BG}" '
                 f'stroke="{C_DEC_BDR}" stroke-width="2"/>')
        tc = C_TEXT_DK
    else:
        shape = (f'<rect x="{cx - NW/2:.1f}" y="{cy - NH/2:.1f}" '
                 f'width="{NW}" height="{NH}" rx="6" '
                 f'fill="{C_PROC_BG}" stroke="{C_PROC_BDR}" stroke-width="1.5" '
                 f'filter="url(#sh)"/>')
        tc = C_TEXT_DK

    text = (f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" '
            f'dominant-baseline="central" font-size="11" '
            f'font-family="Arial,Helvetica,sans-serif" fill="{tc}" '
            f'font-weight="500">{spans}</text>')
    return shape + text


def _svg_edge(x1: float, y1: float, x2: float, y2: float,
              label: str = "", back: bool = False) -> str:
    if back:
        ox = min(x1, x2) - 55
        d  = (f"M {x1:.1f} {y1:.1f} C {ox:.1f} {y1:.1f} "
              f"{ox:.1f} {y2:.1f} {x2:.1f} {y2:.1f}")
    elif abs(y2 - y1) < 8:
        d = f"M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}"
    else:
        my = (y1 + y2) / 2
        d  = (f"M {x1:.1f} {y1:.1f} C {x1:.1f} {my:.1f} "
              f"{x2:.1f} {my:.1f} {x2:.1f} {y2:.1f}")

    path = (f'<path d="{d}" fill="none" stroke="{C_ARROW}" stroke-width="1.8" '
            f'marker-end="url(#arr)"/>')

    lbl_svg = ""
    if label:
        lx = (x1 + x2) / 2 + (14 if not back else -22)
        ly = (y1 + y2) / 2
        lbl_svg = (
            f'<rect x="{lx-13:.1f}" y="{ly-9:.1f}" width="26" height="16" '
            f'rx="3" fill="{C_LBL_BG}" stroke="{C_LBL_BDR}"/>'
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
            f'dominant-baseline="central" font-size="9" '
            f'font-family="Arial,Helvetica,sans-serif" fill="{C_TEXT_DK}" '
            f'font-weight="700">{_esc(label)}</text>'
        )
    return path + lbl_svg


def generate_svg(spec_text: str) -> str:
    data = extract_flow_json(spec_text)
    if not data:
        return _empty_svg()

    nodes_list: list = data.get("nodes", [])
    edges_list: list = data.get("edges", [])
    title: str       = data.get("titulo", "Diagrama de Flujo")
    if not nodes_list:
        return _empty_svg()

    nodes_map = {n["id"]: n for n in nodes_list}
    positions, W, H = _layout(nodes_list, edges_list)
    total_h = H + TITLE_H

    # rank for back-edge detection
    ranks = {
        nid: round((cy - PAD_Y - LAYER_H / 2) / LAYER_H)
        for nid, (_, cy) in positions.items()
    }

    out: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {W:.0f} {total_h:.0f}" '
        f'width="{W:.0f}" height="{total_h:.0f}">',
        f'<defs>'
        f'<marker id="arr" markerWidth="9" markerHeight="9" '
        f'refX="8" refY="4.5" orient="auto" markerUnits="strokeWidth">'
        f'<path d="M0,0 L0,9 L9,4.5 Z" fill="{C_ARROW}"/></marker>'
        f'<filter id="sh" x="-8%" y="-8%" width="116%" height="116%">'
        f'<feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.12"/>'
        f'</filter>'
        f'</defs>',
        f'<rect width="{W:.0f}" height="{total_h:.0f}" '
        f'fill="{C_CANVAS}" rx="12" stroke="{C_BORDER}" stroke-width="1"/>',
        # title
        f'<text x="{W/2:.1f}" y="{TITLE_H/2 + 4:.1f}" text-anchor="middle" '
        f'dominant-baseline="central" font-size="13" font-weight="700" '
        f'fill="{C_END_BG}" font-family="Arial,Helvetica,sans-serif">'
        f'{_esc(title)}</text>',
        f'<g transform="translate(0,{TITLE_H})">',
    ]

    # Edges first (drawn behind nodes)
    for e in edges_list:
        fid, tid = e.get("from"), e.get("to")
        if fid not in positions or tid not in positions:
            continue
        fx, fy = positions[fid]
        tx, ty = positions[tid]
        sb = _bounds(nodes_map[fid], fx, fy)
        tb = _bounds(nodes_map[tid], tx, ty)
        back = ranks.get(tid, 0) <= ranks.get(fid, 0)

        if back:
            x1, y1 = sb["left"]
            x2, y2 = tb["left"]
        elif abs(ty - fy) < 8:
            if tx >= fx:
                x1, y1 = sb["right"]; x2, y2 = tb["left"]
            else:
                x1, y1 = sb["left"];  x2, y2 = tb["right"]
        else:
            x1, y1 = sb["bottom"]
            x2, y2 = tb["top"]

        out.append(_svg_edge(x1, y1, x2, y2, e.get("label", ""), back))

    # Nodes
    for n in nodes_list:
        if n["id"] in positions:
            cx, cy = positions[n["id"]]
            out.append(_svg_node(n, cx, cy))

    out.append("</g></svg>")
    return "\n".join(out)


def _empty_svg(msg: str = "Diagrama no disponible") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 80" width="440" height="80">'
        f'<rect width="440" height="80" rx="8" fill="{C_CANVAS}" stroke="{C_BORDER}"/>'
        f'<text x="220" y="40" text-anchor="middle" dominant-baseline="central" '
        f'font-size="13" font-family="Arial,Helvetica,sans-serif" fill="#5a6a85">{_esc(msg)}</text>'
        f'</svg>'
    )


# ─────────────────────────────────────────────────────────────────────────────
#  PNG generation (Pillow, for DOCX embedding)
# ─────────────────────────────────────────────────────────────────────────────

def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def generate_png_bytes(spec_text: str, scale: int = 2) -> bytes:
    """Return PNG bytes of the flow diagram at `scale`x resolution."""
    from PIL import Image, ImageDraw, ImageFont

    data = extract_flow_json(spec_text)
    if not data:
        return _empty_png()

    nodes_list: list = data.get("nodes", [])
    edges_list: list = data.get("edges", [])
    if not nodes_list:
        return _empty_png()

    nodes_map = {n["id"]: n for n in nodes_list}
    positions, W, H = _layout(nodes_list, edges_list)
    total_h = H + TITLE_H

    iw = int(W * scale)
    ih = int(total_h * scale)
    img = Image.new("RGB", (iw, ih), _hex(C_CANVAS))
    draw = ImageDraw.Draw(img)

    def s(v: float) -> int:
        return int(round(v * scale))

    # Fonts
    font_md = font_sm = ImageFont.load_default()
    try:
        font_md = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", s(11))
        font_sm = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", s(9))
    except Exception:
        try:
            font_md = ImageFont.load_default(size=s(11))
            font_sm = ImageFont.load_default(size=s(9))
        except TypeError:
            pass

    def text_wh(txt: str, fnt) -> tuple[int, int]:
        bb = draw.textbbox((0, 0), txt, font=fnt)
        return bb[2] - bb[0], bb[3] - bb[1]

    def draw_text_c(txt: str, cx: float, cy: float, fnt, fill):
        tw, th = text_wh(txt, fnt)
        draw.text((s(cx) - tw // 2, s(cy) - th // 2), txt, font=fnt, fill=fill)

    def draw_rrect(x0, y0, x1, y1, r, fill, outline):
        """Rounded rectangle fallback (works across Pillow versions)."""
        r = min(r, (x1 - x0) // 2, (y1 - y0) // 2)
        try:
            draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill, outline=outline, width=2)
        except AttributeError:
            draw.rectangle([x0, y0, x1, y1], fill=fill, outline=outline)

    def draw_arrow_line(x1: float, y1: float, x2: float, y2: float, back: bool = False):
        color = _hex(C_ARROW)
        lw = max(2, scale)
        if back:
            ox = s(min(x1, x2) - 55)
            pts = [(s(x1), s(y1)), (ox, s(y1)), (ox, s(y2)), (s(x2), s(y2))]
            draw.line(pts, fill=color, width=lw)
        elif abs(y2 - y1) < 8:
            draw.line([(s(x1), s(y1)), (s(x2), s(y2))], fill=color, width=lw)
        else:
            draw.line([(s(x1), s(y1)), (s(x2), s(y2))], fill=color, width=lw)
        # Arrowhead
        import math
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length < 1:
            return
        ux, uy = dx / length, dy / length
        hs = 8
        ax = s(x2 - ux * hs - uy * hs * 0.5)
        ay = s(y2 - uy * hs + ux * hs * 0.5)
        bx = s(x2 - ux * hs + uy * hs * 0.5)
        by_ = s(y2 - uy * hs - ux * hs * 0.5)
        draw.polygon([(s(x2), s(y2)), (ax, ay), (bx, by_)], fill=color)

    # Title bar
    title_txt = data.get("titulo", "Diagrama de Flujo")
    draw_text_c(title_txt, W / 2, TITLE_H / 2, font_md, _hex(C_END_BG))

    # rank map
    ranks = {
        nid: round((cy - PAD_Y - LAYER_H / 2) / LAYER_H)
        for nid, (_, cy) in positions.items()
    }

    # Edges
    for e in edges_list:
        fid, tid = e.get("from"), e.get("to")
        if fid not in positions or tid not in positions:
            continue
        fx, fy = positions[fid]
        tx, ty = positions[tid]
        sb = _bounds(nodes_map[fid], fx, fy)
        tb = _bounds(nodes_map[tid], tx, ty)
        back = ranks.get(tid, 0) <= ranks.get(fid, 0)

        if back:
            x1, y1 = sb["left"];  x2, y2 = tb["left"]
        elif abs(ty - fy) < 8:
            if tx >= fx:
                x1, y1 = sb["right"]; x2, y2 = tb["left"]
            else:
                x1, y1 = sb["left"];  x2, y2 = tb["right"]
        else:
            x1, y1 = sb["bottom"]; x2, y2 = tb["top"]

        # Adjust target y offset by TITLE_H
        draw_arrow_line(x1, y1 + TITLE_H, x2, y2 + TITLE_H, back)

        lbl = e.get("label", "")
        if lbl:
            lx = (x1 + x2) / 2 + (12 if not back else -22)
            ly = (y1 + y2) / 2 + TITLE_H
            draw_text_c(lbl, lx, ly, font_sm, _hex(C_TEXT_DK))

    # Nodes
    for n in nodes_list:
        if n["id"] not in positions:
            continue
        cx, cy = positions[n["id"]]
        cy += TITLE_H  # offset below title
        t     = n.get("type", "process")
        label = n.get("label", n["id"])
        lines = textwrap.wrap(label, 20) or [label]

        if t == "start":
            draw.ellipse([s(cx - ERX), s(cy - ERY), s(cx + ERX), s(cy + ERY)],
                         fill=_hex(C_START_BG), outline=_hex(C_PROC_BDR))
            draw_text_c(label[:22], cx, cy, font_md, _hex(C_TEXT_DK))
        elif t == "end":
            draw.ellipse([s(cx - ERX), s(cy - ERY), s(cx + ERX), s(cy + ERY)],
                         fill=_hex(C_END_BG), outline=_hex(C_PROC_BDR))
            draw_text_c(label[:22], cx, cy, font_md, _hex(C_TEXT_LT))
        elif t == "decision":
            pts = [(s(cx), s(cy - DH)), (s(cx + DH), s(cy)),
                   (s(cx), s(cy + DH)), (s(cx - DH), s(cy))]
            draw.polygon(pts, fill=_hex(C_DEC_BG), outline=_hex(C_DEC_BDR))
            for i, ln in enumerate(lines[:2]):
                dy_off = (i - (min(len(lines), 2) - 1) / 2) * s(13)
                draw_text_c(ln, cx, cy + dy_off / scale, font_md, _hex(C_TEXT_DK))
        else:
            draw_rrect(s(cx - NW/2), s(cy - NH/2), s(cx + NW/2), s(cy + NH/2),
                       s(6), _hex(C_PROC_BG), _hex(C_PROC_BDR))
            for i, ln in enumerate(lines[:2]):
                dy_off = (i - (min(len(lines), 2) - 1) / 2) * s(13)
                draw_text_c(ln, cx, cy + dy_off / scale, font_md, _hex(C_TEXT_DK))

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()


def _empty_png() -> bytes:
    from PIL import Image, ImageDraw
    img  = Image.new("RGB", (440, 80), _hex(C_CANVAS))
    draw = ImageDraw.Draw(img)
    draw.text((220, 40), "Diagrama no disponible", fill=_hex("#5a6a85"))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf.read()
