#import "@preview/touying:0.5.5": *
#import themes.metropolis: *

#let LL_BLUE = rgb("#0F4C81")
#let LL_RED = rgb("#DC2626")
#let LL_GREEN = rgb("#16A34A")
#let LL_GREY = rgb("#64748B")
#let LL_BG = rgb("#F1F5F9")
#let LL_AMBER = rgb("#FEF3C7")

#show: metropolis-theme.with(
  aspect-ratio: "16-9",
  config-info(
    title: [Llamafolio],
    subtitle: [Conseiller de portefeuille multi-agents · Alpaca paper trading],
    author: [Victor & Kenan],
    date: datetime.today(),
    institution: [HEIG-VD · Cours IA générative],
    logo: image("../assets/llamafolio-icon-light.svg", width: 1.5cm),
  ),
  config-common(handout: false),
)

#set text(lang: "fr")

#let big-card(body, fill: LL_BG, w: 90%) = block(
  fill: fill,
  inset: 1.1em,
  radius: 8pt,
  width: w,
  body,
)

#let section-banner(num, title, time) = align(center + horizon)[
  #v(-1em)
  #text(size: 18pt, fill: LL_GREY)[Partie #num / 4]
  #v(0.4em)
  #text(size: 48pt, weight: 700, fill: LL_BLUE)[#title]
  #v(0.3em)
  #text(size: 16pt, fill: LL_GREY)[#time]
]


// ----------------------------------------------------------------------------
// 1 — TITLE
// ----------------------------------------------------------------------------
#title-slide()


// ----------------------------------------------------------------------------
// SECTION 1 — Cas d'usage (2 min)
// ----------------------------------------------------------------------------
#slide[
  #section-banner("1", [Cas d'usage], [2 minutes])
]


#slide[
  #set align(horizon)

  #align(center)[
    #text(size: 28pt, weight: 500)[
      L'investisseur particulier doit *jongler* avec :
    ]
  ]

  #v(1.5em)

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1.2em,
    big-card(w: 100%, fill: LL_BG)[
      #align(center)[
        #text(size: 22pt, weight: 700)[Broker]
        #v(0.3em)
        #text(size: 14pt, fill: LL_GREY)[positions, équité]
      ]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #align(center)[
        #text(size: 22pt, weight: 700)[News]
        #v(0.3em)
        #text(size: 14pt, fill: LL_GREY)[macro, sentiment]
      ]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #align(center)[
        #text(size: 22pt, weight: 700)[Fondamentaux]
        #v(0.3em)
        #text(size: 14pt, fill: LL_GREY)[P/E, bêta, secteur]
      ]
    ],
  )

  #v(1.8em)

  #align(center)[
    #text(size: 36pt, weight: 700, fill: LL_BLUE)[
      Aucun outil ne les combine.
    ]
  ]
]


#slide[
  #set align(horizon)

  #align(center)[
    #text(size: 22pt, weight: 500)[
      #text(weight: 700, fill: LL_BLUE)[Llamafolio] combine en *une seule conversation* :
    ]
  ]

  #v(1.2em)

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 1em,
    row-gutter: 0.8em,
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 18pt, weight: 700)[Analyse]\
      #text(size: 13pt, fill: LL_GREY)[exposition sectorielle, concentration]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 18pt, weight: 700)[Recherche]\
      #text(size: 13pt, fill: LL_GREY)[news, fondamentaux, web]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 18pt, weight: 700)[Risque]\
      #text(size: 13pt, fill: LL_GREY)[volatilité, bêta, taille de position]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 18pt, weight: 700)[Exécution simulée]\
      #text(size: 13pt, fill: LL_GREY)[uniquement après confirmation]
    ],
  )

  #v(1.2em)

  #align(center)[
    #text(size: 14pt, fill: LL_GREY)[
      Cible : investisseur curieux ou étudiant en finance — pas un professionnel.
    ]
  ]
]


// ----------------------------------------------------------------------------
// SECTION 2 — Architecture (2 min)
// ----------------------------------------------------------------------------
#slide[
  #section-banner("2", [Architecture technique], [2 minutes])
]


#slide[
  #set align(horizon)

  #align(center)[
    #text(size: 22pt, weight: 700)[Router + supervisor : 2 couches]
  ]

  #v(0.6em)

  #align(center)[
    #block(
      stroke: 1pt + LL_BLUE,
      radius: 6pt,
      inset: 14pt,
      width: 96%,
    )[
      #set text(font: "DejaVu Sans Mono", size: 10pt)
      #align(left)[
```
                       ┌──────────────────┐
   user ──────────────►│  intent router   │   1 LLM call
                       └─┬────────────────┘
                         │
     ┌──────────┬────────┼────────┬────────────┬──────────┐
     ▼          ▼        ▼        ▼            ▼          ▼
    data    analyst  research   risk      executor*   complex
   0 LLM    2 LLM    2 LLM    2 LLM       2 LLM     6–12 LLM
                                                       ▼
                                                 supervisor chain

   * garde structurel programmatique
```
      ]
    ]
  ]

  #v(0.8em)

  #align(center)[
    #big-card(w: 80%, fill: LL_BG)[
      #align(center)[
        #text(size: 28pt, weight: 700, fill: LL_BLUE)[
          9 round-trips  →  2.3
        ]
        #v(0.2em)
        #text(size: 16pt, fill: LL_GREY)[
          ×4 d'économie sans changer de modèle
        ]
      ]
    ]
  ]
]


#slide[
  #set align(horizon)

  #align(center)[
    #text(size: 22pt, weight: 700)[Stack et données]
  ]

  #v(0.8em)

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 1.5em,
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 18pt, weight: 700, fill: LL_BLUE)[Stack]
      #v(0.4em)
      #text(size: 13pt)[
        *LangGraph* · supervisor pattern\
        *Gemini 3.1 Flash Lite* · Groq en secours\
        *Alpaca MCP* · 60+ outils\
        *Streamlit* · streaming UI
      ]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 18pt, weight: 700, fill: LL_BLUE)[Données (live)]
      #v(0.4em)
      #text(size: 13pt)[
        *Alpaca* · positions, équité, ordres\
        *Alpaca market* · prix, news\
        *yfinance* · P/E, bêta, secteur\
        *Tavily* · recherche web macro
      ]
    ],
  )

  #v(1em)

  #align(center)[
    #big-card(w: 92%, fill: LL_AMBER)[
      #align(center)[
        #text(size: 15pt)[
          *Au-delà du cours :* Model Context Protocol · intent router · pré-fetch du contexte
        ]
      ]
    ]
  ]
]


// ----------------------------------------------------------------------------
// SECTION 3 — Démo (3 min)
// ----------------------------------------------------------------------------
#slide[
  #section-banner("3", [Démonstration], [3 minutes])
]


#slide[
  #set align(horizon)

  #align(center)[
    #block(
      stroke: 2pt + LL_BLUE,
      radius: 10pt,
      inset: 3em,
      width: 80%,
    )[
      #align(center)[
        #text(size: 56pt, weight: 700, fill: LL_BLUE)[Screencast]
        #v(0.6em)
        #text(size: 18pt, fill: LL_GREY)[
          data · complex · garde sécurité · multilingue
        ]
      ]
    ]
  ]

  #v(1em)

  #align(center)[
    #text(size: 12pt, fill: LL_GREY)[
      _Vidéo lue ici en plein écran._
    ]
  ]
]


// ----------------------------------------------------------------------------
// SECTION 4 — Analyse critique (3 min)
// ----------------------------------------------------------------------------
#slide[
  #section-banner("4", [Analyse critique], [3 minutes])
]


#slide[
  #set align(horizon)

  #align(center)[
    #text(size: 22pt, weight: 700)[Limites techniques]
  ]

  #v(0.6em)

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 1em,
    row-gutter: 0.8em,
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 15pt, weight: 700)[Gemini _thinking_ × supervisor]
      #v(0.3em)
      #text(size: 12pt, fill: LL_GREY)[
        Incompatible : `thought_signature` manquante.
        Fix : `thinking_budget=0`.
      ]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 15pt, weight: 700)[Rate limits gratuits]
      #v(0.3em)
      #text(size: 12pt, fill: LL_GREY)[
        Gemini 15 RPM / 500 RPD.
        Notre archi (~2 round-trips) reste viable.
      ]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 15pt, weight: 700)[Substring matching]
      #v(0.3em)
      #text(size: 12pt, fill: LL_GREY)[
        Détecte les régressions structurelles.
        LLM-as-judge compléterait sur la qualité.
      ]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 15pt, weight: 700)[Couverture eval minimale]
      #v(0.3em)
      #text(size: 12pt, fill: LL_GREY)[
        18 cas — suffisants pour trouver la faille
        executor. Insuffisants en production.
      ]
    ],
  )
]


#slide[
  #set align(horizon)

  #align(center)[
    #text(size: 22pt, weight: 700)[La faille trouvée par l'eval]
  ]

  #v(0.8em)

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 2em,
    align: center,
    [
      #text(size: 18pt, weight: 700)[Avant patch]
      #v(0.6em)
      #text(size: 76pt, weight: 700, fill: LL_RED)[0.00]
      #v(0.4em)
      #text(size: 13pt, fill: LL_GREY)[
        « confirm » seul → ordre passé\
        « confirm sell NVDA \$1500 » → ordre passé
      ]
    ],
    [
      #text(size: 18pt, weight: 700)[Après patch]
      #v(0.6em)
      #text(size: 76pt, weight: 700, fill: LL_GREEN)[1.00]
      #v(0.4em)
      #text(size: 13pt, fill: LL_GREY)[
        Refus déterministe, \~1.4 s\
        zéro LLM, zéro tool call
      ]
    ],
  )

  #v(1em)

  #align(center)[
    #big-card(w: 90%, fill: LL_AMBER)[
      #align(center)[
        #text(size: 16pt)[
          *Leçon :* sur la sécurité, la règle qui vaut est celle écrite\
          en *Python*, pas celle écrite en anglais dans un _prompt_.
        ]
      ]
    ]
  ]
]


#slide[
  #set align(horizon)

  #align(center)[
    #text(size: 22pt, weight: 700)[Améliorations envisagées]
  ]

  #v(0.6em)

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 1em,
    row-gutter: 0.7em,
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 14pt, weight: 700, fill: LL_BLUE)[ML]
      #v(0.2em)
      #text(size: 12pt)[
        LLM-as-judge sur la qualité narrative\
        Backtest historique des recommandations
      ]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 14pt, weight: 700, fill: LL_BLUE)[Sécurité]
      #v(0.2em)
      #text(size: 12pt)[
        Cas adversariaux étendus\
        Sanitization des news (anti _prompt injection_)
      ]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 14pt, weight: 700, fill: LL_BLUE)[MLOps]
      #v(0.2em)
      #text(size: 12pt)[
        GitHub Actions CI avec badge eval\
        Prompt caching explicite
      ]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 14pt, weight: 700, fill: LL_BLUE)[Produit]
      #v(0.2em)
      #text(size: 12pt)[
        Mémoire persistante (LangGraph + Postgres)\
        Streamlit Cloud pour démo publique
      ]
    ],
  )
]


#slide[
  #set align(horizon)

  #align(center)[
    #text(size: 22pt, weight: 700)[Dimension éthique]
  ]

  #v(0.8em)

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 1em,
    row-gutter: 0.7em,
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 14pt, weight: 700)[Sur-confiance du modèle]
      #v(0.3em)
      #text(size: 12pt, fill: LL_GREY)[
        Tendance à formuler des observations comme
        des recommandations.
      ]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 14pt, weight: 700)[Produit non régulé]
      #v(0.3em)
      #text(size: 12pt, fill: LL_GREY)[
        Pas d'obligation MiFID II / FINMA.
        Disclaimer ne suffit pas.
      ]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 14pt, weight: 700)[Confirmation trop fluide]
      #v(0.3em)
      #text(size: 12pt, fill: LL_GREY)[
        Un clic suffit. Une étape « justifier »
        forcerait une réflexion.
      ]
    ],
    big-card(w: 100%, fill: LL_BG)[
      #text(size: 14pt, weight: 700)[Biais des sources]
      #v(0.3em)
      #text(size: 12pt, fill: LL_GREY)[
        News Alpaca essentiellement anglo-saxonnes.
      ]
    ],
  )
]


// ----------------------------------------------------------------------------
// CONCLUSION
// ----------------------------------------------------------------------------
#slide[
  #set align(horizon)

  #align(center)[
    #text(size: 26pt, weight: 700)[Ce que démontre Llamafolio]
  ]

  #v(1em)

  #align(center)[
    #grid(
      columns: 1,
      row-gutter: 0.7em,
      big-card(w: 80%, fill: LL_BG)[
        #align(center)[
          #text(size: 20pt, weight: 700, fill: LL_BLUE)[
            L'architecture pèse plus lourd que le provider.
          ]
        ]
      ],
      big-card(w: 80%, fill: LL_BG)[
        #align(center)[
          #text(size: 20pt, weight: 700, fill: LL_BLUE)[
            La sécurité est architecturale, pas un disclaimer.
          ]
        ]
      ],
      big-card(w: 80%, fill: LL_BG)[
        #align(center)[
          #text(size: 20pt, weight: 700, fill: LL_BLUE)[
            L'eval trouve les bugs que les _prompts_ cachent.
          ]
        ]
      ],
    )
  ]

  #v(1em)

  #align(center)[
    #text(size: 11pt, fill: LL_GREY)[
      #link("https://github.com/Mondotosz/Llamafolio")
    ]
  ]
]


#slide[
  #set align(horizon + center)

  #text(size: 84pt, weight: 700)[Merci.]

  #v(1em)

  #text(size: 22pt, fill: LL_GREY)[Questions & réponses]
]
