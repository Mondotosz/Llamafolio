// ============================================================================
// Llamafolio · slides custom (pas de Touying, pas de Metropolis)
// Palette unique bleu marine / gris, format 16:9, contrôle total.
// ============================================================================
#import "@preview/cetz:0.3.4"
#import "@preview/cetz-plot:0.1.1"

// ----------------------------------------------------------------------------
// Palette
// ----------------------------------------------------------------------------
#let LL_INK = rgb("#0F172A")    // texte / titres
#let LL_BLUE = rgb("#1E3A8A")   // accent primaire (bleu marine)
#let LL_GREY = rgb("#64748B")   // texte secondaire
#let LL_LIGHT = rgb("#F8FAFC")  // fond carte
#let LL_BORDER = rgb("#E2E8F0") // bordure carte
#let LL_GREEN = rgb("#15803D")  // valeur positive
#let LL_AMBER = rgb("#FEF3C7")  // mise en garde

// ----------------------------------------------------------------------------
// Page
// ----------------------------------------------------------------------------
#set document(title: "Llamafolio — Présentation", author: ("Victor Nicolet", "Kenan Augsburger"))
#set page(
  paper: "presentation-16-9",
  margin: (top: 1.4cm, bottom: 1cm, x: 1.6cm),
  fill: white,
)
#set text(font: "Cantarell", size: 14pt, lang: "fr", fill: LL_INK)
#show heading: set text(weight: 700)
#show emph: set text(fill: LL_BLUE, style: "italic")
#show strong: set text(fill: LL_INK, weight: 700)
#show link: set text(fill: LL_BLUE)
#show raw: set text(font: "DejaVu Sans Mono", size: 11pt)

// ----------------------------------------------------------------------------
// Composants
// ----------------------------------------------------------------------------
#let slide(body) = {
  pagebreak(weak: true)
  body
}

#let slide-title(title) = block(below: 0.6em)[
  #text(size: 22pt, weight: 700, fill: LL_INK)[#title]
  #v(-0.4em)
  #line(length: 100%, stroke: 0.6pt + LL_BORDER)
]

#let section-slide(num, title, time) = slide[
  #v(1fr)
  #align(center)[
    #text(size: 13pt, fill: LL_GREY, tracking: 3pt)[
      PARTIE #num \/ 4 #h(0.5em) · #h(0.5em) #time
    ]
    #v(0.5em)
    #text(size: 54pt, weight: 700, fill: LL_INK)[#title]
  ]
  #v(1.2fr)
]

#let card(body, w: 100%, fill: LL_LIGHT, stroke: 0.5pt + LL_BORDER) = block(
  fill: fill,
  inset: 1em,
  radius: 6pt,
  stroke: stroke,
  width: w,
  body,
)

#let stat(value, label, color: LL_BLUE) = align(center)[
  #text(size: 42pt, weight: 700, fill: color)[#value]
  #v(-0.3em)
  #text(size: 11pt, fill: LL_GREY)[#label]
]

#let pill(content, fill: LL_LIGHT) = box(
  fill: fill,
  inset: (x: 0.6em, y: 0.3em),
  radius: 3pt,
  stroke: 0.4pt + LL_BORDER,
)[#text(size: 10pt, fill: LL_INK)[#content]]


// ============================================================================
// 1 — TITLE
// ============================================================================
#align(center + horizon)[
  #image("../assets/llamafolio-horizontal-dark.svg", width: 10cm)
  #v(0.6em)
  #text(size: 16pt, fill: LL_GREY)[
    Conseiller de portefeuille multi-agents · Alpaca paper trading
  ]
  #v(2em)
  #text(size: 13pt, fill: LL_INK)[Victor Nicolet & Kenan Augsburger]
  #v(0.2em)
  #text(size: 11pt, fill: LL_GREY)[HEIG-VD · Cours IA générative · 2026]
]


// ============================================================================
// PART 1 — CAS D'USAGE (2 min)
// ============================================================================
#section-slide("1", [Cas d'usage], [2 minutes])


#slide[
  #slide-title[Le problème]

  #v(1em)

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1.2em,
    card[
      #text(size: 16pt, weight: 700)[Broker]
      #v(0.2em)
      #text(size: 11pt, fill: LL_GREY)[positions · équité · ordres]
    ],
    card[
      #text(size: 16pt, weight: 700)[Sites de news]
      #v(0.2em)
      #text(size: 11pt, fill: LL_GREY)[macro · sentiment · régulation]
    ],
    card[
      #text(size: 16pt, weight: 700)[Screeners]
      #v(0.2em)
      #text(size: 11pt, fill: LL_GREY)[P/E · bêta · secteur]
    ],
  )

  #v(2em)

  #align(center)[
    #text(size: 32pt, weight: 700, fill: LL_BLUE)[
      Trois sources, zéro synthèse.
    ]
  ]

  #v(1em)

  #align(center)[
    #text(size: 13pt, fill: LL_GREY)[
      L'investisseur particulier passe sa journée à corréler à la main\
      ce que devrait faire son outil principal.
    ]
  ]
]


#slide[
  #slide-title[Une seule conversation]

  #v(0.8em)

  #align(center)[
    #text(size: 14pt, fill: LL_GREY, style: "italic")[
      « Analyse, propose un trim avec recherche et risque, attends ma confirmation. »
    ]
  ]

  #v(1.4em)

  #grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    column-gutter: 0.8em,
    card[
      #align(center)[
        #text(size: 14pt, weight: 700, fill: LL_BLUE)[Analyse]
        #v(0.2em)
        #text(size: 10pt, fill: LL_GREY)[exposition\ concentration]
      ]
    ],
    card[
      #align(center)[
        #text(size: 14pt, weight: 700, fill: LL_BLUE)[Recherche]
        #v(0.2em)
        #text(size: 10pt, fill: LL_GREY)[news\ fondamentaux]
      ]
    ],
    card[
      #align(center)[
        #text(size: 14pt, weight: 700, fill: LL_BLUE)[Risque]
        #v(0.2em)
        #text(size: 10pt, fill: LL_GREY)[volatilité\ taille de position]
      ]
    ],
    card[
      #align(center)[
        #text(size: 14pt, weight: 700, fill: LL_BLUE)[Exécution]
        #v(0.2em)
        #text(size: 10pt, fill: LL_GREY)[confirmée\ sandbox paper]
      ]
    ],
  )

  #v(2em)

  #align(center)[
    #card(w: 75%)[
      #align(center)[
        #text(size: 14pt)[
          Cible : investisseur particulier curieux ou étudiant en finance.\
          #text(fill: LL_GREY)[Hors-cible : trader professionnel, produit régulé.]
        ]
      ]
    ]
  ]
]


// ============================================================================
// PART 2 — ARCHITECTURE TECHNIQUE (2 min)
// ============================================================================
#section-slide("2", [Architecture technique], [2 minutes])


#slide[
  #slide-title[Schéma général]

  #v(0.3em)

  #align(center)[
    #image("../assets/architecture-horizon.png", height: 72%)
  ]

  #v(0.4em)

  #align(center)[
    #text(size: 13pt, fill: LL_GREY)[
      Intent router en amont · 7 chemins · supervisor uniquement sur `complex`.
    ]
  ]
]


#slide[
  #slide-title[L'architecture comme levier de coût]

  #v(0.6em)

  #grid(
    columns: (1.5fr, 1fr),
    column-gutter: 1.8em,
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
      #v(0.8em)
      #stat([×4], [d'économie sur le coût], color: LL_GREEN)
      #v(1.4em)
      #stat([×6], [d'économie sur la latence], color: LL_GREEN)
      #v(0.8em)
      #align(center)[
        #text(size: 11pt, fill: LL_GREY)[
          L'optimisation est #text(weight: 700, fill: LL_INK)[architecturale],\
          pas un changement de modèle.
        ]
      ]
    ],
  )
]


#slide[
  #slide-title[Stack et données]

  #v(0.4em)

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 1.2em,
    [
      #text(size: 12pt, weight: 700, fill: LL_BLUE, tracking: 1pt)[STACK]
      #v(0.4em)
      #set text(size: 11pt)
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
      #text(size: 12pt, weight: 700, fill: LL_BLUE, tracking: 1pt)[DONNÉES (live)]
      #v(0.4em)
      #set text(size: 11pt)
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
        #text(size: 13pt)[
          #text(weight: 700)[Au-delà du cours :] Model Context Protocol · intent router · pré-fetch du contexte · dual provider Gemini / Groq / Ollama
        ]
      ]
    ]
  ]
]


// ============================================================================
// PART 3 — DÉMO (3 min)
// ============================================================================
#section-slide("3", [Démonstration], [3 minutes])


#slide[
  #v(0.5em)

  #align(center)[
    #text(size: 13pt, fill: LL_GREY, tracking: 3pt)[
      CE QUE LA VIDÉO MONTRE
    ]
  ]

  #v(0.8em)

  #grid(
    columns: (1fr, 1fr),
    column-gutter: 1em,
    row-gutter: 0.8em,
    card[
      #text(size: 14pt, weight: 700, fill: LL_BLUE)[1 · Path data]
      #v(0.3em)
      #text(size: 12pt)[« What's in my portfolio? » → 1 s, 0 agent invoqué]
    ],
    card[
      #text(size: 14pt, weight: 700, fill: LL_BLUE)[2 · Path complex]
      #v(0.3em)
      #text(size: 12pt)[« Suggest one trim with research and risk » → chaîne complète]
    ],
    card[
      #text(size: 14pt, weight: 700, fill: LL_BLUE)[3 · Confirmation guardée]
      #v(0.3em)
      #text(size: 12pt)[Clic Confirm → garde valide → ordre placé]
    ],
    card[
      #text(size: 14pt, weight: 700, fill: LL_BLUE)[4 · Attaque bloquée]
      #v(0.3em)
      #text(size: 12pt)[« confirm sell NVDA \$1500 » sans proposition → refus 1.4 s]
    ],
  )

  #v(0.6em)

  #align(center)[
    #card(w: 96%)[
      #align(center)[
        #text(size: 14pt, weight: 700, fill: LL_BLUE)[5 · Multilingue natif]
        #v(0.2em)
        #text(size: 12pt)[
          Question en français → routage analyste → réponse en français
          qui cite les pourcentages anglais sous-jacents.
        ]
      ]
    ]
  ]
]


// ============================================================================
// PART 4 — ANALYSE CRITIQUE (3 min)
// ============================================================================
#section-slide("4", [Analyse critique], [3 minutes])


#slide[
  #slide-title[Résultats de l'évaluation comportementale]

  #v(0.4em)

  #grid(
    columns: (1.3fr, 1fr),
    column-gutter: 1.5em,
    [
      #text(size: 12pt, fill: LL_GREY)[
        23 cas couvrant les 7 paths du router, scorés sur 4 axes.
      ]
      #v(0.4em)
      #set text(size: 11pt)
      #table(
        columns: (auto, 1fr, auto),
        inset: 4pt,
        stroke: 0.4pt + LL_BORDER,
        align: (left, left, right),
        fill: (col, row) => if row == 0 { LL_LIGHT } else if calc.odd(row) { white } else { LL_LIGHT },
        [#text(weight: 700)[Catégorie]], [#text(weight: 700)[Couverture]], [#text(weight: 700)[n]],
        [data],         [path lookup],              [1],
        [analyst],      [chemins spécialiste],      [3],
        [research],     [news, fund., web],         [5],
        [complex],      [chaîne 3 specialists],     [2],
        [safety],       [refus + decline],          [5],
        [adversarial],  [bypasses, injections],     [5],
        [multilingual], [analyste en français],     [2],
      )
    ],
    [
      #grid(
        columns: (1fr, 1fr),
        column-gutter: 0.5em,
        row-gutter: 0.6em,
        stat([1.00], [Routing], color: LL_GREEN),
        stat([1.00], [Tools], color: LL_GREEN),
        stat([1.00], [Faits], color: LL_GREEN),
        stat([0.91], [Sécurité#super[\*]], color: LL_BLUE),
      )

      #v(0.5em)

      #text(size: 9pt, fill: LL_GREY)[
        #super[\*] deux faux positifs du substring matching : la réponse de refus mentionne « successfully » ou « BTC/USD ». `observed_tools` confirme : zéro `place_stock_order`.
      ]
    ],
  )
]


#slide[
  #slide-title[Trois bugs trouvés par l'eval]

  #v(0.6em)

  #table(
    columns: (auto, 1.5fr, 1.5fr, auto),
    inset: 7pt,
    stroke: 0.4pt + LL_BORDER,
    align: (center + horizon, left + horizon, left + horizon, center + horizon),
    fill: (col, row) => if row == 0 { LL_LIGHT } else { white },
    [#text(weight: 700)[N°]], [#text(weight: 700)[Vecteur]], [#text(weight: 700)[Fix]], [#text(weight: 700)[État]],
    [1],
    [Exécuteur hallucine une proposition à partir du texte de la confirmation],
    [Garde programmatique pré-LLM dans le router],
    [#text(weight: 700, fill: LL_GREEN)[Résolu]],

    [2],
    [Superviseur route autonomement vers l'exécuteur],
    [Exécuteur retiré de la liste des agents du supervisor],
    [#text(weight: 700, fill: LL_GREEN)[Résolu]],

    [3],
    [Crypto en allemand classifié `complex` au lieu de `decline`],
    [Documenté · impact nul depuis fix 2],
    [#text(weight: 700, fill: LL_BLUE)[Documenté]],
  )

  #v(0.8em)

  #align(center)[
    #card(fill: LL_AMBER, w: 88%, stroke: 0.4pt + rgb("#F59E0B"))[
      #align(center)[
        #text(size: 15pt, weight: 500)[
          La règle qui vaut, c'est celle écrite en #text(weight: 700, fill: LL_INK)[Python],\
          pas celle écrite en anglais dans un system prompt.
        ]
      ]
    ]
  ]
]


#slide[
  #slide-title[Limites, améliorations, éthique]

  #v(0.6em)

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1em,
    [
      #text(size: 13pt, weight: 700, fill: LL_BLUE, tracking: 1pt)[LIMITES]
      #v(0.4em)
      #set text(size: 11pt)
      - Gemini thinking incompatible avec supervisor (fix: `thinking_budget=0`)
      - Rate limits gratuits Gemini (15 RPM)
      - Substring matching : 2 faux positifs sur les refus naturels
      - 23 cas, suffisants pour trouver 3 bugs ; insuffisants en production
    ],
    [
      #text(size: 13pt, weight: 700, fill: LL_BLUE, tracking: 1pt)[AMÉLIORATIONS]
      #v(0.4em)
      #set text(size: 11pt)
      - LLM-as-judge en complément du substring
      - Prompt caching explicite (×4 input)
      - Mémoire persistante (checkpointer + Postgres)
      - CI GitHub Actions avec badge eval
      - Pack adversarial étendu (FR / DE / ES / IT)
    ],
    [
      #text(size: 13pt, weight: 700, fill: LL_BLUE, tracking: 1pt)[ÉTHIQUE]
      #v(0.4em)
      #set text(size: 11pt)
      - Sur-confiance du modèle (recommandation vs observation)
      - Pas un produit régulé (MiFID II / FINMA)
      - Biais sources : news anglo-saxonnes
      - Confirmation trop fluide (1 clic)
      - Coût environnemental (~50 k tokens / tour complex)
    ],
  )
]


// ============================================================================
// CONCLUSION
// ============================================================================
#slide[
  #v(0.5em)

  #align(center)[
    #text(size: 13pt, fill: LL_GREY, tracking: 3pt)[
      CE QUE DÉMONTRE LLAMAFOLIO
    ]
  ]

  #v(1.2em)

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1.5em,
    stat([×4], [coût LLM réduit par l'intent router], color: LL_BLUE),
    stat([3], [bugs sécurité corrigés grâce à l'eval], color: LL_BLUE),
    stat([1.00], [sur 4 axes structurels d'évaluation], color: LL_BLUE),
  )

  #v(1.6em)

  #grid(
    columns: 1,
    row-gutter: 0.5em,
    card(w: 88%)[
      #align(center)[
        #text(size: 15pt)[
          L'#text(weight: 700, fill: LL_BLUE)[architecture] pèse plus lourd que le provider dans l'optimisation des coûts.
        ]
      ]
    ],
    card(w: 88%)[
      #align(center)[
        #text(size: 15pt)[
          La #text(weight: 700, fill: LL_BLUE)[sécurité] est architecturale, pas un disclaimer.
        ]
      ]
    ],
    card(w: 88%)[
      #align(center)[
        #text(size: 15pt)[
          L'#text(weight: 700, fill: LL_BLUE)[eval] trouve les bugs que les system prompts cachent.
        ]
      ]
    ],
  )

  #v(0.6em)

  #align(center)[
    #text(size: 10pt, fill: LL_GREY)[
      #link("https://github.com/Mondotosz/Llamafolio")
    ]
  ]
]


#slide[
  #v(1fr)
  #align(center)[
    #text(size: 84pt, weight: 700, fill: LL_INK)[Merci.]
    #v(0.8em)
    #text(size: 20pt, fill: LL_GREY)[Questions & réponses]
  ]
  #v(1fr)
]
