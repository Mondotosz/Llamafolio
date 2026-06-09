// ============================================================================
// PARTIE 1 — CAS D'USAGE (2 min)
// Problème adressé, utilisateurs cibles, valeur ajoutée de l'IA.
// ============================================================================
#import "../theme.typ": *

#section-slide("1", [Cas d'usage])


#content-slide([Le problème])[

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 1.2em,
    card[
      #text(size: 19pt, weight: 700)[Broker]
      #v(0.2em)
      #text(size: 14pt, fill: LL_GREY)[positions · équité · ordres]
    ],
    card[
      #text(size: 19pt, weight: 700)[Sites de news]
      #v(0.2em)
      #text(size: 14pt, fill: LL_GREY)[macro · sentiment · régulation]
    ],
    card[
      #text(size: 19pt, weight: 700)[Screeners]
      #v(0.2em)
      #text(size: 14pt, fill: LL_GREY)[P/E · bêta · secteur]
    ],
  )

  #v(2em)

  #align(center)[
    #text(size: 36pt, weight: 700, fill: LL_BLUE)[
      Trois sources, zéro synthèse.
    ]
  ]

  #v(1em)

  #align(center)[
    #text(size: 16pt, fill: LL_GREY)[
      L'investisseur particulier passe sa journée à corréler à la main\
      ce que devrait faire son outil principal.
    ]
  ]
]


#content-slide([Une seule conversation])[

  #align(center)[
    #text(size: 16pt, fill: LL_GREY, style: "italic")[
      « Analyse, propose un trim avec recherche et risque, attends ma confirmation. »
    ]
  ]

  #v(1.4em)

  #grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    column-gutter: 0.8em,
    card[
      #align(center)[
        #text(size: 16pt, weight: 700, fill: LL_BLUE)[Analyse]
        #v(0.2em)
        #text(size: 13pt, fill: LL_GREY)[exposition\ concentration]
      ]
    ],
    card[
      #align(center)[
        #text(size: 16pt, weight: 700, fill: LL_BLUE)[Recherche]
        #v(0.2em)
        #text(size: 13pt, fill: LL_GREY)[news\ fondamentaux]
      ]
    ],
    card[
      #align(center)[
        #text(size: 16pt, weight: 700, fill: LL_BLUE)[Risque]
        #v(0.2em)
        #text(size: 13pt, fill: LL_GREY)[volatilité\ taille de position]
      ]
    ],
    card[
      #align(center)[
        #text(size: 16pt, weight: 700, fill: LL_BLUE)[Exécution]
        #v(0.2em)
        #text(size: 13pt, fill: LL_GREY)[confirmée\ sandbox paper]
      ]
    ],
  )

  #v(2em)

  #align(center)[
    #card(w: 75%)[
      #align(center)[
        #text(size: 16pt)[
          Cible : investisseur particulier curieux ou étudiant en finance.\
          #text(fill: LL_GREY)[Hors-cible : trader professionnel, produit régulé.]
        ]
      ]
    ]
  ]
]
