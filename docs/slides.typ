#import "@preview/touying:0.5.5": *
#import themes.metropolis: *

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

// ----------------------------------------------------------------------------
// 1 — TITLE
// ----------------------------------------------------------------------------

#title-slide()


// ============================================================================
= Cas d'usage
// ============================================================================

// ----------------------------------------------------------------------------
// 2 — Le problème
// ----------------------------------------------------------------------------
== Le problème

#v(1.5em)

#align(center)[
  #text(size: 22pt, weight: 500)[
    L'investisseur particulier doit *jongler* avec :
  ]
]

#v(1.2em)

#align(center)[
  #grid(
    columns: 3,
    column-gutter: 2em,
    align: center,
    text(size: 18pt, weight: 700)[💼 Broker],
    text(size: 18pt, weight: 700)[📰 News],
    text(size: 18pt, weight: 700)[📊 Fondamentaux],
    text(size: 13pt, fill: rgb("#888"))[positions, équité],
    text(size: 13pt, fill: rgb("#888"))[macro, sentiment],
    text(size: 13pt, fill: rgb("#888"))[P/E, bêta, secteur],
  )
]

#v(1.5em)

#align(center)[
  #text(size: 26pt, weight: 700, fill: rgb("#0F4C81"))[
    Aucun outil ne les *combine*.
  ]
]


// ----------------------------------------------------------------------------
// 3 — La solution
// ----------------------------------------------------------------------------
== Une seule conversation

#v(0.5em)

#align(center)[
  #text(size: 18pt)[
    *Llamafolio* combine en une seule conversation :
  ]
]

#v(0.8em)

#table(
  columns: (1fr,),
  inset: 10pt,
  stroke: 0.5pt + rgb("#E5E7EB"),
  align: center,
  [#text(size: 16pt)[#text(weight: 700)[Analyse] · exposition sectorielle, concentration]],
  [#text(size: 16pt)[#text(weight: 700)[Recherche] · news, fondamentaux, web]],
  [#text(size: 16pt)[#text(weight: 700)[Risque] · volatilité, bêta, taille de position]],
  [#text(size: 16pt)[#text(weight: 700)[Exécution simulée] · uniquement après confirmation]],
)

#v(0.8em)

#align(center)[
  #text(size: 14pt, fill: rgb("#888"))[
    Cible : investisseur curieux ou étudiant en finance — pas un pro.
  ]
]


// ============================================================================
= Architecture technique
// ============================================================================

// ----------------------------------------------------------------------------
// 4 — Schéma archi
// ----------------------------------------------------------------------------
== Router + supervisor : 2 couches

#align(center)[
  #block(
    stroke: 0.5pt + rgb("#444"),
    radius: 4pt,
    inset: 10pt,
    width: 95%,
  )[
    #set text(font: "DejaVu Sans Mono", size: 9pt)
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
  #text(size: 18pt, weight: 700, fill: rgb("#0F4C81"))[
    9 round-trips → 2.3 ·  ×4 d'économie
  ]
]


// ----------------------------------------------------------------------------
// 5 — Stack et données
// ----------------------------------------------------------------------------
== Stack et données

#v(0.5em)

#grid(
  columns: 2,
  column-gutter: 1.5em,
  [
    *Stack*
    #v(0.4em)
    - *LangGraph* · supervisor pattern
    - *Gemini 3.1 Flash Lite* · Groq en secours
    - *Alpaca MCP* · 60+ outils
    - *Streamlit* · streaming UI
  ],
  [
    *Données (live, jamais statiques)*
    #v(0.4em)
    - *Alpaca* · positions, équité, ordres
    - *Alpaca market* · prix, news
    - *yfinance* · P/E, bêta, secteur
    - *Tavily* · recherche web macro
  ],
)

#v(0.8em)

#align(center)[
  #block(
    fill: rgb("#F1F5F9"),
    inset: 0.9em,
    radius: 6pt,
    width: 90%,
  )[
    #text(size: 14pt)[
      *Au-delà du cours :* Model Context Protocol · intent router ·
      pré-fetch du contexte
    ]
  ]
]


// ============================================================================
= Démonstration
// ============================================================================

// ----------------------------------------------------------------------------
// 6 — Démo screencast
// ----------------------------------------------------------------------------
== Démo (3 min)

#v(2em)

#align(center)[
  #block(
    stroke: 1pt + rgb("#444"),
    radius: 8pt,
    inset: 2em,
    width: 75%,
    height: 8em,
  )[
    #align(center + horizon)[
      #text(size: 28pt, weight: 700, fill: rgb("#0F4C81"))[
        🎥 Screencast
      ]
      #v(0.5em)
      #text(size: 14pt, fill: rgb("#888"))[
        data · complex · garde sécurité · multilingue
      ]
    ]
  ]
]

#v(1em)

#align(center)[
  #text(size: 12pt, fill: rgb("#888"))[
    _Vidéo lue ici en plein écran._
  ]
]


// ============================================================================
= Analyse critique
// ============================================================================

// ----------------------------------------------------------------------------
// 7 — Limites techniques
// ----------------------------------------------------------------------------
== Limites techniques

#v(0.6em)

- *Gemini _thinking_ × supervisor : incompatible.*
  Mitigation : `thinking_budget=0`, variantes `flash-lite` non-_thinking_.

- *_Rate limits_ gratuits.*
  Gemini 15 RPM / 500 RPD. Notre archi (~2 _round-trips_/tour) reste
  viable, mais limite atteinte sur les _runs_ d'eval intensifs.

- *_Substring matching_ vs sémantique.*
  L'_eval_ détecte les régressions structurelles ; un _LLM-as-judge_
  comblerait le gap sur la qualité narrative.

- *Couverture eval minimale.*
  18 cas suffisent à trouver les bugs majeurs — et ont d'ailleurs
  trouvé la faille executor.


// ----------------------------------------------------------------------------
// 8 — La faille trouvée par l'eval
// ----------------------------------------------------------------------------
== La faille trouvée par l'eval

#v(0.8em)

#grid(
  columns: 2,
  column-gutter: 2em,
  align: center,
  [
    #text(size: 16pt, weight: 700)[Avant patch]
    #v(0.6em)
    #text(size: 56pt, weight: 700, fill: rgb("#DC2626"))[0.00]
    #v(0.3em)
    #text(size: 13pt, fill: rgb("#888"))[
      « confirm » seul → ordre passé\
      « confirm sell NVDA \$1500 » → ordre passé
    ]
  ],
  [
    #text(size: 16pt, weight: 700)[Après patch]
    #v(0.6em)
    #text(size: 56pt, weight: 700, fill: rgb("#16A34A"))[1.00]
    #v(0.3em)
    #text(size: 13pt, fill: rgb("#888"))[
      Refus déterministe, ~1.4s\
      _zéro_ appel LLM, _zéro_ appel tool
    ]
  ],
)

#v(1em)

#align(center)[
  #block(
    fill: rgb("#FEF3C7"),
    inset: 0.8em,
    radius: 6pt,
    width: 88%,
  )[
    #text(size: 14pt)[
      *Leçon :* sur la sécurité, la règle qui vaut est celle écrite en
      *Python*, pas celle écrite en anglais dans un prompt.
    ]
  ]
]


// ----------------------------------------------------------------------------
// 9 — Améliorations envisagées
// ----------------------------------------------------------------------------
== Améliorations envisagées

#v(0.6em)

- *_LLM-as-judge_* sur la qualité des sorties, au-delà du _substring
  matching_.

- *Cas adversariaux* : _prompt injection_ via news, confirmations
  multilingues forgées, blocs structurés forgés en `HumanMessage`.

- *CI GitHub Actions* : _lint_, _type-check_, _eval_ automatique à
  chaque PR avec _badge_.

- *Mémoire persistante* via LangGraph _checkpointer_ + Postgres pour
  garder l'historique des recommandations entre sessions.

- *_Backtest_ historique* : faire tourner les recommandations sur des
  dates passées et mesurer le _hit rate_.


// ----------------------------------------------------------------------------
// 10 — Dimension éthique
// ----------------------------------------------------------------------------
== Dimension éthique

#v(0.6em)

- *Sur-confiance du modèle* : tendance à formuler observations comme
  recommandations. Dangereux sur un produit financier réel.

- *Pas un produit régulé* : aucune obligation MiFID II / FINMA
  d'évaluation d'adéquation. Le _disclaimer_ ne dispense pas d'un
  encadrement professionnel.

- *Boucle de confirmation trop fluide* : un clic suffit. Une étape
  « justifier le trade » forcerait une décision réfléchie.

- *Biais des sources* : news Alpaca essentiellement anglo-saxonnes.

- *Coût environnemental* : un tour _complex_ ≈ 50 k tokens. Le router
  l'atténue en évitant la chaîne quand inutile.


// ============================================================================
= Conclusion
// ============================================================================

// ----------------------------------------------------------------------------
// 11 — Conclusion
// ----------------------------------------------------------------------------
== Ce que démontre Llamafolio

#v(1em)

#align(center)[
  #grid(
    columns: 1,
    row-gutter: 0.8em,
    block(
      fill: rgb("#F1F5F9"),
      inset: 1em,
      radius: 6pt,
      width: 85%,
    )[
      #text(size: 18pt, weight: 700)[
        L'architecture pèse plus lourd que le provider.
      ]
    ],
    block(
      fill: rgb("#F1F5F9"),
      inset: 1em,
      radius: 6pt,
      width: 85%,
    )[
      #text(size: 18pt, weight: 700)[
        La sécurité est architecturale, pas un _disclaimer_.
      ]
    ],
    block(
      fill: rgb("#F1F5F9"),
      inset: 1em,
      radius: 6pt,
      width: 85%,
    )[
      #text(size: 18pt, weight: 700)[
        L'eval trouve les bugs que les prompts cachent.
      ]
    ],
  )
]

#v(0.8em)

#align(center)[
  #text(size: 12pt, fill: rgb("#888"))[
    Dépôt : #link("https://github.com/Vicolet/IAG-AI-Trademaxxing")
  ]
]


// ----------------------------------------------------------------------------
// 12 — Q&A
// ----------------------------------------------------------------------------
== Questions ?

#v(2.5em)

#align(center)[
  #text(size: 56pt, weight: 700)[Merci.]
  #v(0.6em)
  #text(size: 18pt, fill: rgb("#888"))[Q & R]
]
