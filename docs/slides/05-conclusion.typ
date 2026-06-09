// ============================================================================
// CONCLUSION + MERCI
// ============================================================================
#import "../theme.typ": *

#slide[
  #v(1fr)

  #align(center)[
    #text(size: 16pt, fill: LL_GREY, tracking: 3pt)[
      CE QUE DÉMONTRE LLAMAFOLIO
    ]
  ]

  #v(0.7em)

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1.5em,
    stat([×4], [coût LLM réduit par l'intent router], color: LL_BLUE),
    stat([3], [bugs sécurité corrigés grâce à l'eval], color: LL_BLUE),
    stat([1.00], [sur 4 axes structurels d'évaluation], color: LL_BLUE),
  )

  #v(0.8em)

  #grid(
    columns: 1,
    row-gutter: 0.45em,
    card(w: 88%)[
      #align(center)[
        #text(size: 18pt)[
          L'#text(weight: 700, fill: LL_BLUE)[architecture] pèse plus lourd que le provider dans l'optimisation des coûts.
        ]
      ]
    ],
    card(w: 88%)[
      #align(center)[
        #text(size: 18pt)[
          La #text(weight: 700, fill: LL_BLUE)[sécurité] est architecturale, pas un disclaimer.
        ]
      ]
    ],
    card(w: 88%)[
      #align(center)[
        #text(size: 18pt)[
          L'#text(weight: 700, fill: LL_BLUE)[eval] trouve les bugs que les system prompts cachent.
        ]
      ]
    ],
  )

  #v(0.5em)

  #align(center)[
    #text(size: 13pt, fill: LL_GREY)[
      #link("https://github.com/Mondotosz/Llamafolio")
    ]
  ]

  #v(1fr)
]


#slide[
  #v(1fr)
  #align(center)[
    #text(size: 96pt, weight: 700, fill: LL_INK)[Merci.]
    #v(0.8em)
    #text(size: 20pt, fill: LL_GREY)[Questions & réponses]
  ]
  #v(1fr)
]
