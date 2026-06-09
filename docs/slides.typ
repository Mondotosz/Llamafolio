#import "@preview/touying:0.5.5": *
#import "@preview/cetz:0.3.4"
#import "@preview/cetz-plot:0.1.1"
#import themes.metropolis: *

// ----------------------------------------------------------------------------
// Palette sobre data-driven
// ----------------------------------------------------------------------------
#let LL_INK = rgb("#0F172A")    // texte titre / numéros clés
#let LL_BLUE = rgb("#0F4C81")   // accent primaire
#let LL_GREY = rgb("#64748B")   // texte secondaire
#let LL_BG = rgb("#F8FAFC")     // fond carte
#let LL_BORDER = rgb("#E2E8F0") // bordure carte
#let LL_GREEN = rgb("#15803D")  // valeur positive
#let LL_RED = rgb("#B91C1C")    // valeur négative

#show: metropolis-theme.with(
  aspect-ratio: "16-9",
  config-info(
    title: [Llamafolio],
    subtitle: [Conseiller de portefeuille multi-agents · Alpaca paper trading],
    author: [Victor Nicolet & Kenan Augsburger],
    date: datetime.today(),
    institution: [HEIG-VD · Cours IA générative · 2026],
    logo: image("../assets/llamafolio-icon-light.svg", width: 1.5cm),
  ),
  config-common(handout: false),
)

#set text(lang: "fr")


// ----------------------------------------------------------------------------
// Composants réutilisables
// ----------------------------------------------------------------------------
#let stat(value, label, color: LL_BLUE) = align(center)[
  #text(size: 44pt, weight: 700, fill: color)[#value]
  #v(-0.4em)
  #text(size: 12pt, fill: LL_GREY)[#label]
]

#let metric-row(items) = grid(
  columns: items.len() * (1fr,),
  column-gutter: 1em,
  ..items.map(it => stat(it.at(0), it.at(1), color: it.at(2, default: LL_BLUE))),
)

#let section-banner(num, title, time) = align(center + horizon)[
  #text(size: 14pt, fill: LL_GREY, tracking: 2pt)[
    PARTIE #num / 4 · #time
  ]
  #v(0.6em)
  #text(size: 56pt, weight: 700, fill: LL_INK)[#title]
]

#let card(body, w: 100%, fill: LL_BG) = block(
  fill: fill,
  inset: 1em,
  radius: 6pt,
  stroke: 0.5pt + LL_BORDER,
  width: w,
  body,
)

#let slide-title(text-content) = align(left)[
  #text(size: 22pt, weight: 700, fill: LL_INK)[#text-content]
  #v(-0.3em)
  #line(length: 100%, stroke: 0.6pt + LL_BORDER)
]


// ============================================================================
// 1 — TITLE
// ============================================================================
#title-slide()


// ============================================================================
// PART 1 — CAS D'USAGE (2 min)
// ============================================================================
#slide[#section-banner("1", [Cas d'usage], [2 minutes])]


#slide[
  #slide-title[Le problème]

  #v(0.6em)

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1em,
    card[
      #text(size: 16pt, weight: 700, fill: LL_INK)[Broker]
      #v(0.3em)
      #text(size: 11pt, fill: LL_GREY)[
        positions, équité, ordres
      ]
    ],
    card[
      #text(size: 16pt, weight: 700, fill: LL_INK)[Sites de news]
      #v(0.3em)
      #text(size: 11pt, fill: LL_GREY)[
        macro, sentiment, régulation
      ]
    ],
    card[
      #text(size: 16pt, weight: 700, fill: LL_INK)[Screeners]
      #v(0.3em)
      #text(size: 11pt, fill: LL_GREY)[
        P/E, bêta, secteur
      ]
    ],
  )

  #v(1.2em)

  #align(center)[
    #text(size: 30pt, weight: 700, fill: LL_BLUE)[
      Trois sources, zéro synthèse.
    ]
  ]

  #v(0.8em)

  #align(center)[
    #text(size: 13pt, fill: LL_GREY)[
      L'investisseur particulier passe sa journée à corréler à la main\
      ce que devrait faire son outil principal.
    ]
  ]
]


#slide[
  #slide-title[Une seule conversation]

  #v(0.6em)

  #align(center)[
    #text(size: 14pt, fill: LL_GREY)[
      « Analyse, propose un trim avec recherche et risque, attends ma confirmation. »
    ]
  ]

  #v(0.8em)

  #grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    column-gutter: 0.8em,
    card[
      #align(center)[
        #text(size: 13pt, weight: 700, fill: LL_BLUE)[Analyse]
        #v(0.2em)
        #text(size: 10pt, fill: LL_GREY)[
          exposition\
          concentration
        ]
      ]
    ],
    card[
      #align(center)[
        #text(size: 13pt, weight: 700, fill: LL_BLUE)[Recherche]
        #v(0.2em)
        #text(size: 10pt, fill: LL_GREY)[
          news\
          fondamentaux
        ]
      ]
    ],
    card[
      #align(center)[
        #text(size: 13pt, weight: 700, fill: LL_BLUE)[Risque]
        #v(0.2em)
        #text(size: 10pt, fill: LL_GREY)[
          volatilité\
          taille de position
        ]
      ]
    ],
    card[
      #align(center)[
        #text(size: 13pt, weight: 700, fill: LL_BLUE)[Exécution]
        #v(0.2em)
        #text(size: 10pt, fill: LL_GREY)[
          confirmée\
          sandbox paper
        ]
      ]
    ],
  )

  #v(0.8em)

  #align(center)[
    #card(w: 75%)[
      #align(center)[
        #text(size: 15pt, weight: 500)[
          Cible : investisseur particulier curieux ou étudiant en finance.\
          Hors-cible : trader professionnel, produit régulé.
        ]
      ]
    ]
  ]
]


// ============================================================================
// PART 2 — ARCHITECTURE TECHNIQUE (2 min)
// ============================================================================
#slide[#section-banner("2", [Architecture technique], [2 minutes])]


#slide[
  #slide-title[Schéma général]

  #v(0.2em)

  #align(center)[
    #image("../assets/architecture-horizon.png", height: 67%)
  ]

  #v(0.5em)

  #align(center)[
    #text(size: 14pt, fill: LL_GREY)[
      _Intent router_ en amont · 7 chemins · _supervisor_ uniquement sur `complex`.
    ]
  ]
]


#slide[
  #slide-title[L'architecture comme levier de coût]

  #v(0.4em)

  #grid(
    columns: (1.4fr, 1fr),
    column-gutter: 1.5em,
    cetz.canvas({
      import cetz.draw: *
      cetz-plot.chart.barchart(
        mode: "basic",
        size: (8, 5),
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
      #v(0.6em)
      #stat([×4], [d'économie sur le coût], color: LL_GREEN)
      #v(0.8em)
      #stat([×6], [d'économie sur la latence], color: LL_GREEN)
      #v(0.5em)
      #align(center)[
        #text(size: 11pt, fill: LL_GREY)[
          L'optimisation est *architecturale*,\
          pas un changement de modèle.
        ]
      ]
    ],
  )
]


#slide[
  #slide-title[Stack et données]

  #v(0.3em)

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 1em,
    [
      #text(size: 12pt, weight: 700, fill: LL_BLUE, tracking: 1pt)[STACK]
      #v(0.2em)
      #set text(size: 10pt)
      #table(
        columns: (auto, 1fr),
        inset: 3.5pt,
        stroke: 0.4pt + LL_BORDER,
        align: (left, left),
        [*LLM*],         [Gemini 3.1 Flash Lite · Groq · Ollama],
        [*Orchestration*], [LangGraph + langgraph-supervisor],
        [*Tools*],       [Alpaca MCP (60+ outils) · yfinance · Tavily],
        [*UI*],          [Streamlit + Plotly · streaming natif],
        [*Trace*],       [LangSmith (endpoint EU)],
        [*Packaging*],   [uv · lockfile déterministe],
      )
    ],
    [
      #text(size: 12pt, weight: 700, fill: LL_BLUE, tracking: 1pt)[DONNÉES (live)]
      #v(0.2em)
      #set text(size: 10pt)
      #table(
        columns: (auto, 1fr),
        inset: 3.5pt,
        stroke: 0.4pt + LL_BORDER,
        align: (left, left),
        [*Alpaca*],        [comptes, positions, équité, ordres],
        [*Alpaca market*], [quotes, OHLCV, news (Benzinga)],
        [*yfinance*],      [P/E, bêta, capitalisation, secteur],
        [*Tavily*],        [recherche web macro / régulation],
      )
    ],
  )

  #v(0.6em)

  #align(center)[
    #card(fill: rgb("#FEF3C7"), w: 95%)[
      #align(center)[
        #text(size: 12pt)[
          *Au-delà du cours :* Model Context Protocol · intent router · pré-fetch du contexte · _dual provider_ Gemini / Groq / Ollama
        ]
      ]
    ]
  ]
]


// ============================================================================
// PART 3 — DÉMO (3 min)
// ============================================================================
#slide[#section-banner("3", [Démonstration], [3 minutes])]


#slide[
  #set align(horizon)

  #align(center)[
    #text(size: 14pt, fill: LL_GREY, tracking: 2pt)[
      CE QUE LA VIDÉO MONTRE
    ]
  ]

  #v(0.8em)

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 1em,
    row-gutter: 0.6em,
    card[
      #text(size: 13pt, weight: 700, fill: LL_BLUE)[① Path `data`]
      #v(0.2em)
      #text(size: 11pt)[« What's in my portfolio? » → 1 s, 0 agent invoqué]
    ],
    card[
      #text(size: 13pt, weight: 700, fill: LL_BLUE)[② Path `complex`]
      #v(0.2em)
      #text(size: 11pt)[« Suggest one trim with research and risk » → chaîne complète]
    ],
    card[
      #text(size: 13pt, weight: 700, fill: LL_BLUE)[③ Confirmation guardée]
      #v(0.2em)
      #text(size: 11pt)[Clic _Confirm_ → garde valide → ordre placé]
    ],
    card[
      #text(size: 13pt, weight: 700, fill: LL_BLUE)[④ Attaque bloquée]
      #v(0.2em)
      #text(size: 11pt)[« confirm sell NVDA \$1500 » sans proposition → refus 1.4 s]
    ],
    card(w: 100%)[
      #text(size: 13pt, weight: 700, fill: LL_BLUE)[⑤ Multilingue natif]
      #v(0.2em)
      #text(size: 11pt)[Question en français → routage analyste → réponse en français qui cite les pourcentages anglais sous-jacents.]
    ],
  )
]


// ============================================================================
// PART 4 — ANALYSE CRITIQUE (3 min)
// ============================================================================
#slide[#section-banner("4", [Analyse critique], [3 minutes])]


#slide[
  #slide-title[Résultats de l'évaluation comportementale]

  #v(0.4em)

  #grid(
    columns: (1fr, 1.3fr),
    column-gutter: 1.5em,
    [
      #v(0.4em)
      #text(size: 13pt, fill: LL_GREY)[
        23 cas couvrant les 7 _paths_ du router, scorés sur 4 axes :
      ]
      #v(0.4em)

      #table(
        columns: (auto, 1fr, auto),
        inset: 4pt,
        stroke: 0.4pt + LL_BORDER,
        align: (left, left, right),
        table.header(
          [*Catégorie*], [*Couverture*], [*n*],
        ),
        [data],         [path lookup],              [1],
        [analyst],      [chemins spécialiste],      [3],
        [research],     [news, fund., web, movers], [5],
        [complex],      [chaîne 3 specialists],     [2],
        [safety],       [refus + decline],          [5],
        [adversarial],  [_bypasses_, injections],   [5],
        [multilingual], [analyste en français],     [2],
      )
    ],
    [
      #v(0.6em)
      #stat([1.00], [Routing], color: LL_GREEN)
      #v(0.4em)
      #stat([1.00], [Tools], color: LL_GREEN)
      #v(0.4em)
      #stat([1.00], [Faits], color: LL_GREEN)
      #v(0.4em)
      #stat([0.91#sym.star.op], [Sécurité (effectif 1.00)], color: LL_BLUE)

      #v(0.4em)
      #text(size: 9pt, fill: LL_GREY)[
        \* deux faux positifs du _substring matching_ : la réponse de refus mentionne « successfully » ou « BTC/USD ». `observed_tools` confirme : zéro `place_stock_order`.
      ]
    ],
  )
]


#slide[
  #slide-title[Trois bugs trouvés par l'eval]

  #v(0.4em)

  #table(
    columns: (auto, 1.4fr, 1.4fr, auto),
    inset: 6pt,
    stroke: 0.4pt + LL_BORDER,
    align: (center, left, left, center),
    table.header(
      [*N°*], [*Vecteur*], [*Fix*], [*État*],
    ),
    [1], [Exécuteur hallucine une proposition à partir du texte de la confirmation], [Garde programmatique pré-LLM dans le _router_], text(fill: LL_GREEN)[*Résolu*],
    [2], [Superviseur route autonomement vers l'exécuteur], [Exécuteur retiré de la liste des agents du _supervisor_], text(fill: LL_GREEN)[*Résolu*],
    [3], [Crypto en allemand classifié `complex` au lieu de `decline`], [Documenté · impact nul depuis fix 2], text(fill: LL_BLUE)[*Documenté*],
  )

  #v(0.6em)

  #align(center)[
    #card(fill: rgb("#FEF3C7"), w: 92%)[
      #align(center)[
        #text(size: 14pt, weight: 500)[
          La règle qui vaut, c'est celle écrite en *Python*,\
          pas celle écrite en anglais dans un _prompt_.
        ]
      ]
    ]
  ]

  #v(0.3em)

  #align(center)[
    #text(size: 11pt, fill: LL_GREY)[
      Un _system prompt_ peut *sembler* enforcer une politique sans la garantir.\
      Seul un harnais d'eval adversariale exécuté à chaque _commit_ révèle l'écart.
    ]
  ]
]


#slide[
  #slide-title[Limites, améliorations, éthique]

  #v(0.4em)

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1em,
    row-gutter: 0.5em,
    [
      #text(size: 13pt, weight: 700, fill: LL_BLUE)[LIMITES]
      #v(0.3em)
      #text(size: 11pt)[
        - Gemini _thinking_ incompatible avec `supervisor` (fix: `thinking_budget=0`)
        - _Rate limits_ gratuits Gemini (15 RPM)
        - _Substring matching_ : 2 faux positifs sur les refus naturels
        - 23 cas, suffisants pour trouver 3 bugs ; insuffisants en production
      ]
    ],
    [
      #text(size: 13pt, weight: 700, fill: LL_BLUE)[AMÉLIORATIONS]
      #v(0.3em)
      #text(size: 11pt)[
        - _LLM-as-judge_ en complément du substring
        - _Prompt caching_ explicite (×4 input)
        - Mémoire persistante (_checkpointer_ + Postgres)
        - CI GitHub Actions avec _badge_ eval
        - Pack adversarial étendu (FR/DE/ES/IT)
      ]
    ],
    [
      #text(size: 13pt, weight: 700, fill: LL_BLUE)[ÉTHIQUE]
      #v(0.3em)
      #text(size: 11pt)[
        - Sur-confiance du modèle (recommandation vs observation)
        - Pas un produit régulé (MiFID II / FINMA)
        - Biais sources : news anglo-saxonnes
        - Confirmation trop fluide (1 clic)
        - Coût environnemental (~50 k tokens / tour _complex_)
      ]
    ],
  )
]


// ============================================================================
// CONCLUSION
// ============================================================================
#slide[
  #set align(horizon)

  #align(center)[
    #text(size: 14pt, fill: LL_GREY, tracking: 2pt)[
      CE QUE DÉMONTRE LLAMAFOLIO
    ]
  ]

  #v(0.8em)

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1.2em,
    align: center,
    [
      #stat([×4], [coût LLM réduit par l'_intent router_], color: LL_BLUE)
    ],
    [
      #stat([3], [bugs sécurité corrigés grâce à l'eval], color: LL_BLUE)
    ],
    [
      #stat([1.00], [sur 4 axes structurels d'évaluation], color: LL_BLUE)
    ],
  )

  #v(1em)

  #grid(
    columns: 1,
    row-gutter: 0.4em,
    card(w: 85%)[
      #align(center)[
        #text(size: 14pt, weight: 500)[
          L'*architecture* pèse plus lourd que le _provider_ dans l'optimisation des coûts.
        ]
      ]
    ],
    card(w: 85%)[
      #align(center)[
        #text(size: 14pt, weight: 500)[
          La *sécurité* est architecturale, pas un _disclaimer_.
        ]
      ]
    ],
    card(w: 85%)[
      #align(center)[
        #text(size: 14pt, weight: 500)[
          L'*eval* trouve les bugs que les _prompts_ cachent.
        ]
      ]
    ],
  )

  #v(0.5em)

  #align(center)[
    #text(size: 10pt, fill: LL_GREY)[
      Dépôt : #link("https://github.com/Mondotosz/Llamafolio")
    ]
  ]
]


#slide[
  #set align(horizon + center)

  #text(size: 84pt, weight: 700, fill: LL_INK)[Merci.]
  #v(0.8em)
  #text(size: 22pt, fill: LL_GREY)[Questions & réponses]
]
