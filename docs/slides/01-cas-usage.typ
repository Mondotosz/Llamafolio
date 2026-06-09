// ============================================================================
// PARTIE 1 — CAS D'USAGE (2 min)
// Problème adressé, utilisateurs cibles, valeur ajoutée de l'IA.
// ============================================================================
#import "../theme.typ": *

#section-slide("1", [Cas d'usage])


#content-slide([Le problème])[

  #v(1em)

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1em,
    card[
      #text(size: 25pt, weight: 700)[Broker]
      #v(-1em)
      #text(size: 14pt, fill: LL_GREY)[positions · équité · ordres]
    ],
    card[
      #text(size: 25pt, weight: 700)[Sites de news]
      #v(-1em)
      #text(size: 14pt, fill: LL_GREY)[macro · sentiment · régulation]
    ],
    card[
      #text(size: 25pt, weight: 700)[Screeners]
      #v(-1em)
      #text(size: 14pt, fill: LL_GREY)[P/E · bêta · secteur]
    ],
  )


  #align(center)[
    #text(size: 36pt, weight: 700, fill: LL_BLUE)[
      Trois sources, zéro synthèse.
    ]
  ]


  #align(center)[
    #text(size: 16pt, fill: LL_GREY)[
      L'investisseur particulier passe sa journée à corréler à la main\
      ce que devrait faire son outil principal.
    ]
  ]
]


#content-slide([Une seule conversation])[
  
  #v(1em)

  #align(center)[
    #text(size: 20pt, fill: LL_GREY, style: "italic")[
      « Analyse, propose un trim avec recherche et risque, attends ma confirmation. »
    ]
  ]

  #v(1em)

  #grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    column-gutter: 0.8em,
    card[
      #align(center)[
        #text(size: 25pt, weight: 700, fill: LL_BLUE)[Analyse]
        #v(-0.5em)
        #text(size: 15pt, fill: LL_GREY)[exposition\ concentration]
      ]
    ],
    card[
      #align(center)[
        #text(size: 25pt, weight: 700, fill: LL_BLUE)[Recherche]
        #v(-0.5em)
        #text(size: 15pt, fill: LL_GREY)[news\ fondamentaux]
      ]
    ],
    card[
      #align(center)[
        #text(size: 25pt, weight: 700, fill: LL_BLUE)[Risque]
        #v(-0.5em)
        #text(size: 15pt, fill: LL_GREY)[volatilité\ taille de position]
      ]
    ],
    card[
      #align(center)[
        #text(size: 25pt, weight: 700, fill: LL_BLUE)[Exécution]
        #v(-0.5em)
        #text(size: 15pt, fill: LL_GREY)[confirmée\ sandbox paper]
      ]
    ],
  )

  #v(1em)

  #align(center)[
    #card(w: 75%)[
      #text(size: 19pt)[
        Cible : investisseur particulier curieux ou étudiant en finance.\
        #text(fill: LL_GREY)[Hors-cible : trader professionnel, produit régulé.]
      ]
    ]
  ]
]
