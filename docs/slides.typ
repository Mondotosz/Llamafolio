// ============================================================================
// Llamafolio · présentation (fichier principal)
// ----------------------------------------------------------------------------
// Préambule (document, page, footer, texte) + inclusion d'une partie par
// fichier. Pour réécrire le contenu, éditez les fichiers de docs/slides/ ;
// pour changer le style global, éditez docs/theme.typ ou ce préambule.
//
//   Découpage (façon SSE) :
//     docs/theme.typ              palette + composants (slide, card, stat…)
//     docs/slides/00-titre.typ            page de titre
//     docs/slides/01-cas-usage.typ        Partie 1 — Cas d'usage
//     docs/slides/02-architecture.typ     Partie 2 — Architecture technique
//     docs/slides/03-demo.typ             Partie 3 — Démonstration
//     docs/slides/04-analyse-critique.typ Partie 4 — Analyse critique
//     docs/slides/05-conclusion.typ       Conclusion + Merci
//
//   Build : typst compile --root . docs/slides.typ docs/slides.pdf
// ============================================================================
#import "theme.typ": *

// ----------------------------------------------------------------------------
// Document & page — ces règles set/show s'appliquent à TOUT le document,
// y compris au contenu amené par les #include ci-dessous.
// ----------------------------------------------------------------------------
#set document(title: "Llamafolio — Présentation", author: ("Victor Nicolet", "Kenan Augsburger"))
#set page(
  paper: "presentation-16-9",
  margin: (top: 1.3cm, bottom: 1.4cm, x: 1.6cm),
  footer-descent: 0cm,
  fill: white,
  footer: context {
    let n = here().page()
    if n > 1 {
      v(0.6em)
      let total = counter(page).final().first()
      let frac = n / total
      block(width: 100%)[
        
        #box(width: 100%, height: 2pt, fill: LL_BORDER)
        #place(top + left, box(width: frac * 100%, height: 2pt, fill: LL_BLUE))
        #v(-0.6em)
        #grid(
          columns: (1fr, auto),
          
          text(size: 10pt, fill: LL_GREY)[Llamafolio · Conseiller de portefeuille multi-agents],
          text(size: 10pt, fill: LL_GREY)[#n \/ #total],
        )
      ]
    }
  },
)
#set text(font: "Cantarell", size: 16pt, lang: "fr", fill: LL_INK)
#show heading: set text(weight: 700)
#show emph: set text(fill: LL_BLUE, style: "italic")
#show strong: set text(fill: LL_INK, weight: 700)
#show link: set text(fill: LL_BLUE)
#show raw: set text(font: "DejaVu Sans Mono", size: 14pt)

// ----------------------------------------------------------------------------
// Parties — une par fichier, modifiables indépendamment
// ----------------------------------------------------------------------------
#include "slides/00-titre.typ"             // Page de titre
#include "slides/01-cas-usage.typ"         // Partie 1 — Cas d'usage
#include "slides/02-architecture.typ"      // Partie 2 — Architecture technique
#include "slides/03-demo.typ"              // Partie 3 — Démonstration
#include "slides/04-analyse-critique.typ"  // Partie 4 — Analyse critique
#include "slides/05-conclusion.typ"        // Conclusion + Merci
