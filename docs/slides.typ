#import "@preview/touying:0.5.5": *
#import themes.metropolis: *

#show: metropolis-theme.with(
  aspect-ratio: "16-9",
  config-info(
    title: [Llamafolio],
    subtitle: [Conseiller de portefeuille multi-agents pour Alpaca paper trading],
    author: [Victor & Kenan],
    date: datetime.today(),
    institution: [HEIG-VD · Cours IA générative],
    logo: image("../assets/llamafolio-icon-light.svg", width: 1.5cm),
  ),
  config-common(
    handout: false,
  ),
)

#set text(lang: "fr")

#title-slide()


= Cas d'usage

== Le problème

Un investisseur particulier dispose de plusieurs sources d'information :
prix, fondamentaux, actualités, contexte macro. Aucun broker ne les
combine nativement, et l'analyse de concentration sectorielle reste hors
de portée pour la plupart.

#v(1em)

#alternatives[
  - Trop de tableaux à croiser
][
  - Pas de synthèse claire
][
  - Aucun garde-fou contre les ordres impulsifs
]


== La valeur ajoutée

Llamafolio combine en une seule conversation :

- *L'analyse de portefeuille* (exposition sectorielle, concentration)
- *La recherche* (news, fondamentaux, contexte web)
- *L'évaluation de risque* (volatilité, bêta, taille de position)
- *L'exécution simulée* après confirmation explicite

#v(0.6em)
*Cible* : investisseur particulier curieux ou étudiant en finance — pas
un trader professionnel.


= Architecture

== Le pattern superviseur

#align(center)[
  #block(
    stroke: 0.5pt + rgb("#444444"),
    radius: 4pt,
    inset: 10pt,
    width: 90%,
  )[
    #set text(font: "DejaVu Sans Mono", size: 9pt)
    #align(left)[
```
                  ┌─────────────────┐
   user ────────► │   supervisor    │ ─── réponse finale
                  └────────┬────────┘
                           │ transfer_to_*
       ┌──────────┬────────┴────────┬──────────┐
       ▼          ▼                 ▼          ▼
  ┌────────┐ ┌─────────┐    ┌────────┐ ┌──────────┐
  │analyst │ │research │    │  risk  │ │ executor │
  └────────┘ └─────────┘    └────────┘ └──────────┘
```
    ]
  ]
]

#v(0.4em)

Chaque spécialiste a un prompt versionné en Markdown et un sous-ensemble
d'outils dédié.


== Stack et justifications

#table(
  columns: (auto, 1fr),
  inset: 6pt,
  stroke: 0.5pt + rgb("#666666"),
  align: left,
  table.header([*Couche*], [*Choix · Raison*]),
  [LLM], [Groq · Llama 3.3 70B / gpt-oss-120b — gratuit, rapide],
  [Orchestration], [LangGraph + supervisor — pattern multi-agent reconnu],
  [Trading], [Alpaca paper — sémantique réaliste, gratuit],
  [Outils], [`alpaca-mcp-server` via MCP — angle non vu en cours],
  [Recherche], [Tavily + yfinance — couverture web et fondamentaux],
  [UI], [Streamlit + Plotly — démo claire en quelques heures],
)


== L'élément expérimenté : MCP

Le _Model Context Protocol_ permet d'exposer un serveur d'outils tiers à
n'importe quel LLM compatible. On lance `alpaca-mcp-server` en
_subprocess stdio_, et on importe ses outils dans LangGraph via
`langchain-mcp-adapters`.

#v(0.6em)

Avantages :
- Outils maintenus par Alpaca, pas par nous
- Switch trivial vers `live trading` (changer une variable d'env)
- Réutilisable par d'autres clients MCP (Claude Desktop, Cursor, etc.)


= Démonstration

== Scénario

#v(1em)

+ Question : « _Analyse mon exposition sectorielle_ »
+ L'analyste détecte la concentration tech ($approx$ 48%)
+ Question : « _Propose une trim avec recherche et risque_ »
+ La recherche + le risque produisent une proposition
+ Un binôme #emph[Confirm / Refuse] apparaît
+ Clic → l'exécuteur place l'ordre paper

#v(0.6em)

#text(fill: rgb("#888888"))[
  _Vidéo de secours disponible en cas de problème réseau._
]


= Analyse critique

== Limites techniques

- *Hallucination d'outils* (Llama 3.3 invente des noms de fonctions)
  → mitigation : température basse, prompt strict, _retry_ exponentiel
- *Limites de débit gratuit* (8–12 k tokens/min, 100 k/jour)
  → mitigation : _backoff_ automatique, _free tier_ insuffisant pour
  un usage soutenu
- *Couverture _eval_ minimale* (16 cas, _substring matching_)
  → une version industrielle utiliserait des centaines de cas + _LLM-as-judge_


== Dimension éthique

- *Sur-confiance du modèle* : tendance à formuler des observations comme
  des recommandations, malgré l'instruction contraire
- *Pas un produit régulé* : ne respecte pas les obligations MiFID II /
  FINMA d'évaluation d'adéquation ; le _disclaimer_ ne dispense pas
  d'un encadrement professionnel
- *Biais des sources* : news Alpaca essentiellement anglo-saxonnes


== Améliorations envisagées

- *Streaming temps réel* (LangGraph `astream_events`)
- *LLM-as-judge* sur la qualité des sorties
- *Backtest historique* sur les recommandations passées
- *Mémoire persistante* via _checkpointer_ + Postgres
- *Boutons d'action enrichis* (édition de la quantité avant confirmation)


= Conclusion

== En résumé

Llamafolio démontre qu'un POC GenAI sérieux est possible *gratuitement*
si on accepte les limites du _free tier_ :

#v(0.6em)

- Architecture *multi-agents* propre, prompts versionnés
- Intégration *MCP* avec un serveur officiel tiers
- Couche de sécurité : *aucun ordre sans confirmation explicite*
- *Eval comportementale* couvrant routing, outils, faits, sécurité

#v(0.8em)

#text(weight: 700)[Dépôt :] #link("https://github.com/Vicolet/IAG-AI-Trademaxxing")


== Questions ?

#v(2em)

#align(center)[
  #text(size: 24pt, weight: 700)[Merci.]
  #v(0.5em)
  #text(fill: rgb("#888888"))[Q&A]
]
