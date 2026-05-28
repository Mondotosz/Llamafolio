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
  config-common(handout: false),
)

#set text(lang: "fr")

#title-slide()


// ============================================================================
= Cas d'usage
// ============================================================================

== Le problème

Un investisseur particulier dispose de plusieurs sources d'information
disparates : prix, fondamentaux, actualités, contexte macro.

#v(0.8em)

Aucun broker ne les combine nativement, et l'analyse de concentration
sectorielle reste hors de portée pour la plupart.

#v(0.8em)

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

*Cible* : investisseur particulier curieux ou étudiant en finance —
pas un trader professionnel.


// ============================================================================
= Architecture
// ============================================================================

== Deux couches : router + supervisor

#align(center)[
  #block(
    stroke: 0.5pt + rgb("#444444"),
    radius: 4pt,
    inset: 10pt,
    width: 95%,
  )[
    #set text(font: "DejaVu Sans Mono", size: 8pt)
    #align(left)[
```
                          ┌────────────────────┐
   user ─────────────────►│  intent router     │   (1 LLM call)
                          └─┬──────────────────┘
                            │
        ┌──────────┬────────┼────────┬──────────┬──────────┐
        ▼          ▼        ▼        ▼          ▼          ▼
       data    analyst   research   risk    executor    complex
       (0 LLM)  (2 LLM)   (2 LLM)  (2 LLM)  (2 LLM)   (6-12 LLM)
                                                       │
                                                       │  supervisor
                                                       │  chain
                                                       ▼
                                              réponse + Confirm/Refuse
```
    ]
  ]
]

Un _intent router_ classifie chaque tour ; seuls les 10 % de requêtes
complexes empruntent la chaîne supervisor.


== Sept chemins, sept coûts

#table(
  columns: (auto, auto, auto, 1fr),
  inset: 5pt,
  stroke: 0.5pt + rgb("#666666"),
  align: (left, right, right, left),
  table.header(
    [*Intent*], [*LLM calls*], [*Latence*], [*Exemple*],
  ),
  [`data`],     [1],     [\~1 s],  [« Qu'y a-t-il dans mon portefeuille ? »],
  [`analyst`],  [2],     [\~5 s],  [« Analyse mon exposition sectorielle »],
  [`research`], [2],     [\~6 s],  [« News sur NVDA »],
  [`risk`],     [2],     [\~5 s],  [« Quel est le risque de NVDA ? »],
  [`complex`],  [6–12],  [\~30 s], [« Trim avec recherche et risque »],
  [`executor`], [2],     [\~4 s],  [« confirm sell NVDA \$1 800 »],
  [`decline`],  [1],     [\~1 s],  [Hors scope],
)


== Stack

#table(
  columns: (auto, 1fr),
  inset: 6pt,
  stroke: 0.5pt + rgb("#666666"),
  align: left,
  table.header([*Couche*], [*Choix · Raison*]),
  [LLM], [Gemini 3.1 Flash Lite · Groq gpt-oss-120b — _dual provider_ via `.env`],
  [Orchestration], [LangGraph + `langgraph-supervisor` — _streaming_ ready],
  [Trading], [Alpaca paper — sémantique réaliste, gratuit],
  [Outils], [`alpaca-mcp-server` via MCP — *angle non vu en cours*],
  [Recherche], [Tavily + yfinance — web et fondamentaux],
  [UI], [Streamlit + Plotly + Typst],
)


== Éléments expérimentés au-delà du cours

#v(0.4em)

+ *Model Context Protocol* : intégration d'un serveur d'outils tiers
  (`alpaca-mcp-server`) lancé en _subprocess stdio_ via `uvx`, importé
  dans LangGraph par `langchain-mcp-adapters`.

+ *Intent router pré-superviseur* : un classifier (1 LLM call)
  shortcircuite les requêtes simples vers un agent unique ou un rendu
  déterministe sans LLM. Réduit la latence de 30 s à 1–5 s pour 90 %
  des requêtes.

+ *Pré-injection du contexte portefeuille* : un _read_ Alpaca côté
  serveur fournit l'analyste en données ; il n'a plus besoin de
  10 _round-trips_ MCP pour décrire le portefeuille.


== L'architecture comme levier de coût

#table(
  columns: (1fr, auto, auto, auto),
  inset: 6pt,
  stroke: 0.5pt + rgb("#666666"),
  align: (left, right, right, right),
  table.header(
    [*Configuration*], [*Round-trips*], [*Latence*], [*Coût\**],
  ),
  [Multi-agent naïf], [15–20], [30–60 s], [\$0.005],
  [+ pré-fetch contexte], [10–14], [20 s], [\$0.003],
  [+ tool calls parallèles], [6–10], [15 s], [\$0.002],
  [*+ intent router (moy. pondérée)*], [*1–2*], [*3 s*], [*\$0.0005*],
)

#text(size: 12pt, fill: rgb("#888888"))[
  \* Estimation par tour, Gemini 2.5 Flash Lite paid avec _prompt
  caching_. Pour 1 000 tours/mois/utilisateur : \~\$0.50 — viable B2C
  à marge >95 %.
]


// ============================================================================
= Démonstration
// ============================================================================

== Scénario en direct

+ Question : « _Suggest one trim with research and risk check, do not execute_ »
+ La chaîne complète s'exécute : analyste → recherche → risque
+ Le superviseur émet un bloc structuré :
  ```
  Proposed trade
  Symbol: NVDA · Side: SELL · Quantity: $1,800
  Rationale: ...
  ```
+ Une bannière *Confirm / Refuse* apparaît sous la réponse
+ Clic Confirm → l'_intent router_ détecte « confirm sell NVDA … » →
  l'exécuteur place l'ordre paper et retourne l'ID

#v(0.5em)

#text(fill: rgb("#888888"))[
  _Vidéo de secours disponible en cas de problème réseau._
]


// ============================================================================
= Analyse critique
// ============================================================================

== Limites techniques

- *Gemini _thinking_ incompatible avec supervisor* :
  les modèles 2.5/3.x _thinking_ exigent un `thought_signature` sur les
  `functionCall` historiques, que `langgraph-supervisor` ne fournit pas.
  → fix : utiliser les variantes `flash-lite` non-_thinking_.

- *Limites de débit gratuites* : Groq 8–12 k TPM, Gemini 10–20 RPM.
  → fix : optimisations architecturales ramènent la moyenne à
  ~2 _round-trips_ par tour.

- *Eval volontairement minimale* : 16 cas, _substring matching_.
  → version industrielle : centaines de cas + _LLM-as-judge_.


== Dimension éthique

- *Sur-confiance du modèle* : tendance à formuler observations comme
  recommandations. Dangereux sur un produit financier réel.

- *Pas un produit régulé* : aucune obligation MiFID II / FINMA
  d'évaluation d'adéquation. Le _disclaimer_ ne dispense pas
  d'encadrement professionnel.

- *Boucle de confirmation trop fluide* : un clic suffit. Une étape
  « justifier le trade » forcerait une décision plus réfléchie.

- *Biais linguistique* : news Alpaca quasi-exclusivement anglo-saxonnes.


== Améliorations envisagées

- *_LLM-as-judge_* sur la qualité des sorties (au-delà du _substring_)
- *Backtest historique* sur les recommandations passées
- *Mémoire persistante* via LangGraph _checkpointer_ + Postgres
- *_Prompt caching_* explicite des system prompts (diviserait encore le
  coût input par ~4×)
- *Multilingue documenté* : valoriser la capacité multilingue native des
  modèles utilisés


// ============================================================================
= Conclusion
// ============================================================================

== Ce que démontre Llamafolio

+ Un POC GenAI agentic *sérieux et gratuit* en respectant les _free
  tiers_.

+ *L'architecture pèse plus lourd que le provider* dans l'optimisation
  des coûts : passer de 6 à 2 _round-trips_ par tour divise le coût par
  3× et la latence par 5×.

+ *La sécurité est architecturale* : proposition structurée +
  confirmation explicite + exécuteur isolé. Pas un _disclaimer_.

+ *Industrialisable* : code modulaire (17 modules focalisés), _dual
  provider_, _eval_ automatique, identité visuelle complète.

#v(0.6em)

#text(weight: 700)[Dépôt :]
#link("https://github.com/Vicolet/IAG-AI-Trademaxxing")


== Questions ?

#v(2em)

#align(center)[
  #text(size: 30pt, weight: 700)[Merci.]
  #v(0.5em)
  #text(fill: rgb("#888888"), size: 14pt)[Q&A]
]
