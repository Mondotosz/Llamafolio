// ============================================================================
// PARTIE 4 — ANALYSE CRITIQUE (3 min)
// Limites identifiées, améliorations envisagées, dimension éthique.
// ============================================================================
#import "../theme.typ": *

#section-slide("4", [Analyse critique])


#content-slide([Résultats de l'évaluation comportementale])[

  #grid(
    columns: (1.3fr, 1fr),
    column-gutter: 1.5em,
    [
      #text(size: 15pt, fill: LL_GREY)[
        23 cas couvrant les 7 paths du router, scorés sur 4 axes.
      ]
      #v(0.4em)
      #set text(size: 14pt)
      #table(
        columns: (1fr, 1fr, 0.5fr),
        inset: 4pt,
        stroke: 0.4pt + LL_BORDER,
        align: (left, left, center),
        fill: (col, row) => if row == 0 { LL_LIGHT } else if calc.odd(row) { white } else { LL_LIGHT },
        [#text(weight: 700)[Catégorie]], [#text(weight: 700)[Couverture]], [#text(weight: 700)[n]],
        [data],         [path lookup],              [1],
        [analyst],      [chemins spécialiste],      [3],
        [research],     [news, fund., web],         [5],
        [risk],         [trim hypothétique],        [1],
        [complex],      [chaîne 3 specialists],     [2],
        [safety],       [refus + decline],          [5],
        [adversarial],  [bypasses, injections],     [5],
        [multilingual], [analyste en français],     [1],
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

      #text(size: 12pt, fill: LL_GREY)[
        #super[\*] deux faux positifs du substring matching : la réponse de refus mentionne « successfully » ou « BTC/USD ». `observed_tools` confirme : zéro `place_stock_order`.
      ]
    ],
  )
]


#content-slide([Trois bugs trouvés par l'eval])[

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
        #text(size: 18pt, weight: 500)[
          La règle qui vaut, c'est celle écrite en #text(weight: 700, fill: LL_INK)[Python],\
          pas celle écrite en anglais dans un system prompt.
        ]
      ]
    ]
  ]
]


#content-slide([Limites, améliorations, éthique])[

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1em,
    [
      #text(size: 16pt, weight: 700, fill: LL_BLUE, tracking: 1pt)[LIMITES]
      #v(0.4em)
      #set text(size: 14pt)
      - Gemini thinking incompatible avec supervisor (fix: `thinking_budget=0`)
      - Rate limits gratuits Gemini (15 RPM)
      - Substring matching : 2 faux positifs sur les refus naturels
      - 23 cas, suffisants pour trouver 3 bugs ; insuffisants en production
    ],
    [
      #text(size: 16pt, weight: 700, fill: LL_BLUE, tracking: 1pt)[AMÉLIORATIONS]
      #v(0.4em)
      #set text(size: 14pt)
      - LLM-as-judge en complément du substring
      - Prompt caching explicite (×4 input)
      - Mémoire persistante (checkpointer + Postgres)
      - CI GitHub Actions avec badge eval
      - Pack adversarial étendu (FR / DE / ES / IT)
    ],
    [
      #text(size: 16pt, weight: 700, fill: LL_BLUE, tracking: 1pt)[ÉTHIQUE]
      #v(0.4em)
      #set text(size: 14pt)
      - Sur-confiance du modèle (recommandation vs observation)
      - Pas un produit régulé (MiFID II / FINMA)
      - Biais sources : news anglo-saxonnes
      - Confirmation trop fluide (1 clic)
      - Coût environnemental (≈50 k tokens / tour complex)
    ],
  )
]
