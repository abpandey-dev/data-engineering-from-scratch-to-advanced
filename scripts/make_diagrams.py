"""Draw docs/how-it-works.svg and docs/what-we-get.svg."""
from pathlib import Path
DOCS = Path(__file__).resolve().parent.parent / "docs"
INK, MUTED, LINE = "#14213A", "#586980", "#D3DCE5"
FONT = "font-family='Segoe UI, Helvetica, Arial, sans-serif'"


def card(body, w, h):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}' {FONT}>"
            f"<rect x='1' y='1' width='{w - 2}' height='{h - 2}' rx='16' fill='#FFFFFF' stroke='{LINE}'/>{body}</svg>")


def text(x, y, s, size=14, weight="400", fill=INK, anchor="start"):
    s = s.replace("&", "&amp;")
    return f"<text x='{x}' y='{y}' font-size='{size}' font-weight='{weight}' fill='{fill}' text-anchor='{anchor}'>{s}</text>"


LANES = [
    ("1  Foundations", "#0F766E", ["How Data Flows", "Python", "SQL", "Advanced SQL"]),
    ("2  How systems work", "#2563EB", ["Databases", "Data Modelling", "Files & Storage", "Toolbox"]),
    ("3  Building pipelines", "#7C3AED", ["Pipeline Patterns", "Distributed Systems", "Spark", "Spark Tuning", "Airflow"]),
    ("4  Real time & modern stack", "#C2410C", ["Kafka", "Streaming", "Data Quality", "Lakehouse", "Warehouses & dbt"]),
    ("5  Senior skills", "#BE123C", ["Cloud & Security", "System Design", "Data for AI"]),
]


def how_it_works():
    out = [text(32, 44, "How the course works: 21 topics, in order", 22, "700"),
           text(32, 70, "Each topic: theory → lessons with worked numbers → 20 questions → scenario questions", 14, fill=MUTED)]
    y = 92
    for name, colour, topics in LANES:
        out.append(f"<rect x='24' y='{y}' width='912' height='62' rx='10' fill='{colour}' fill-opacity='0.08' stroke='{colour}' stroke-opacity='0.35'/>")
        out.append(text(40, y + 36, name, 14, "700", colour))
        x = 262
        width = (660 - 8 * (len(topics) - 1)) / len(topics)
        for t in topics:
            out.append(f"<rect x='{x:.0f}' y='{y + 12}' width='{width:.0f}' height='38' rx='7' fill='#FFFFFF' stroke='{colour}' stroke-opacity='0.5'/>")
            out.append(text(f"{x + width / 2:.0f}", y + 36, t, 12, "600", INK, "middle"))
            x += width + 8
        y += 72
    return card("".join(out), 960, y + 14)


OUTCOMES = [
    ("420", "tested questions", "A step-by-step and an efficient answer for each, which you can watch run", "#0F766E"),
    ("91", "lessons", "Worked by hand with real numbers, explaining why things work", "#2563EB"),
    ("22", "teacher notebooks", "Open in Colab, with self-checking practice and hidden hints", "#7C3AED"),
    ("2", "hands-on labs", "A complete pipeline, and real PySpark, plus 5 projects to build", "#C2410C"),
]


def what_we_get():
    out = [text(32, 44, "What you get", 22, "700")]
    for i, (num, label, desc, colour) in enumerate(OUTCOMES):
        x = 24 + i * 231
        out.append(f"<rect x='{x}' y='64' width='219' height='176' rx='12' fill='{colour}' fill-opacity='0.07' stroke='{colour}' stroke-opacity='0.35'/>")
        out.append(text(x + 16, 112, num, 38, "800", colour))
        out.append(text(x + 16, 138, label, 14, "700"))
        words, line, yy = desc.split(), "", 164
        for w in words:
            if len(line) + len(w) > 29:
                out.append(text(x + 16, yy, line, 12, fill=MUTED))
                line, yy = "", yy + 17
            line = (line + " " + w).strip()
        out.append(text(x + 16, yy, line, 12, fill=MUTED))
    return card("".join(out), 960, 258)


DOCS.mkdir(exist_ok=True)
(DOCS / "how-it-works.svg").write_text(how_it_works())
(DOCS / "what-we-get.svg").write_text(what_we_get())
print("diagrams written")
