// ============================================================================
// PARTIE 2 — ARCHITECTURE TECHNIQUE (2 min)
// Schéma de l'architecture, choix de stack et justification, données utilisées.
// ============================================================================
#import "../theme.typ": *
#import "@preview/cetz:0.3.4"
#import "@preview/cetz-plot:0.1.1"

#section-slide("2", [Architecture technique])


#content-slide([Schéma général])[

  #align(center)[
    #image("../../assets/architecture-horizon.png", height: 72%)
  ]

  #v(0.4em)

  #align(center)[
    #text(size: 16pt, fill: LL_GREY)[
      Intent router en amont · 7 chemins · supervisor uniquement sur `complex`.
    ]
  ]
]


#content-slide([L'architecture comme levier de coût])[

  #grid(
    columns: (auto, auto),
    align: (center),
    column-gutter: 1em,
    inset: 1em,
    cetz.canvas({
      import cetz.draw: *
      cetz-plot.chart.barchart(
        mode: "basic",
        size: (12, 7.2),
        label-key: 0,
        value-key: 1,
        x-label: "LLM round-trips par tour (moyenne pondérée)",
        bar-style: (fill: LL_BLUE, stroke: none),
        x-tick-step: 5,
        (
          ("Multi-agent naïf", 18),
          ("avec pré-fetch", 12),
          ("avec parallel calls", 8),
          ("avec intent router", 2.3),
        ),
      )
    }),
    [
      #stat([×4], [d'économie sur le coût], color: LL_GREEN)
      #stat([×6], [d'économie sur la latence], color: LL_GREEN)
      #align(center)[
        #text(size: 14pt, fill: LL_GREY)[
          L'optimisation est #text(weight: 700, fill: LL_INK)[architecturale],\
          pas un changement de modèle.
        ]
      ]
    ],
  )
]


#content-slide([Stack et données])[

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 1.2em,
    [
      #text(size: 15pt, weight: 700, fill: LL_BLUE, tracking: 1pt)[STACK]
      #v(0.4em)
      #set text(size: 14pt)
      #table(
        columns: (auto, 1fr),
        inset: 5pt,
        stroke: 0.4pt + LL_BORDER,
        align: (left, left),
        fill: (col, row) => if calc.even(row) { LL_LIGHT } else { white },
        [#text(weight: 700)[LLM]],          [Gemini 3.1 Flash Lite · Groq · Ollama],
        [#text(weight: 700)[Orchestration]], [LangGraph + langgraph-supervisor],
        [#text(weight: 700)[Tools]],        [Alpaca MCP (60+ outils) · yfinance · Tavily],
        [#text(weight: 700)[UI]],           [Streamlit + Plotly · streaming natif],
        [#text(weight: 700)[Trace]],        [LangSmith (endpoint EU)],
        [#text(weight: 700)[Packaging]],    [uv · lockfile déterministe],
      )
    ],
    [
      #text(size: 15pt, weight: 700, fill: LL_BLUE, tracking: 1pt)[DONNÉES (live)]
      #v(0.4em)
      #set text(size: 14pt)
      #table(
        columns: (auto, 1fr),
        inset: 5pt,
        stroke: 0.4pt + LL_BORDER,
        align: (left, left),
        fill: (col, row) => if calc.even(row) { LL_LIGHT } else { white },
        [#text(weight: 700)[Alpaca]],         [comptes, positions, équité, ordres],
        [#text(weight: 700)[Alpaca market]],  [quotes, OHLCV, news (Benzinga)],
        [#text(weight: 700)[yfinance]],       [P/E, bêta, capitalisation, secteur],
        [#text(weight: 700)[Tavily]],         [recherche web macro / régulation],
      )
    ],
  )

  #v(0.8em)

  #align(center)[
    #card(fill: LL_AMBER, w: 96%, stroke: 0.4pt + rgb("#F59E0B"))[
      #align(center)[
        #text(size: 16pt)[
          #text(weight: 700)[Au-delà du cours :] Model Context Protocol · intent router · pré-fetch du contexte · dual provider Gemini / Groq / Ollama
        ]
      ]
    ]
  ]
]
