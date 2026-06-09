// ============================================================================
// Llamafolio · thème partagé (palette + composants réutilisables)
// ----------------------------------------------------------------------------
// Importé par docs/slides.typ ET par chaque fichier de docs/slides/ via
//   #import "../theme.typ": *
// Les règles set/show (page, texte, footer) vivent dans docs/slides.typ car
// elles s'appliquent à tout le document — y compris au contenu #include.
// Ici on n'expose que des bindings (couleurs + fonctions de composants).
// ============================================================================

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
// Composants
// ----------------------------------------------------------------------------
#let slide(body) = {
  pagebreak(weak: true)
  body
}

#let slide-title(title) = block(below: 0.4em)[
  #text(size: 26pt, weight: 700, fill: LL_INK)[#title]
  #v(-0.4em)
  #line(length: 100%, stroke: 0.6pt + LL_BORDER)
]

// Content slide: title fixed at top, body anchored just below it (top-aligned,
// reference-deck style) with remaining space pushed to the bottom.
#let content-slide(title, body) = slide[
  #slide-title(title)
  #v(1.1em)
  #body
  #v(1fr)
]

// Centered slide: no title bar, content centered both axes.
#let center-slide(body) = slide[
  #v(1fr)
  #align(center)[#body]
  #v(1fr)
]

#let section-slide(num, title) = slide[
  #v(1fr)
  #align(center)[
    #text(size: 16pt, fill: LL_GREY, tracking: 3pt)[
      PARTIE #num \/ 4
    ]
    #v(0.5em)
    #text(size: 64pt, weight: 700, fill: LL_INK)[#title]
  ]
  #v(1fr)
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
  #text(size: 46pt, weight: 700, fill: color)[#value]

  #text(size: 14pt, fill: LL_GREY)[#label]
]

#let pill(content, fill: LL_LIGHT) = box(
  fill: fill,
  inset: (x: 0.6em, y: 0.3em),
  radius: 3pt,
  stroke: 0.4pt + LL_BORDER,
)[#text(size: 13pt, fill: LL_INK)[#content]]
