#set document(title: "Llamafolio — Rapport", author: ("Victor", "Kenan"))
#set page(
  paper: "a4",
  margin: (x: 1.8cm, y: 1.8cm),
  numbering: "1 / 1",
  number-align: center,
)
#set text(font: "New Computer Modern", size: 9.5pt, lang: "fr")
#set par(justify: true, leading: 0.55em)
#show heading.where(level: 1): set text(size: 12pt, weight: 700)
#show heading.where(level: 2): set text(size: 10pt, weight: 700)
#show heading: it => block(above: 0.8em, below: 0.35em, it)
#show link: set text(fill: rgb("#0F4C81"))
#show raw: set text(font: "DejaVu Sans Mono", size: 8pt)

#align(center)[
  #image("../assets/llamafolio-horizontal-dark.svg", width: 5.5cm)
  #v(0.2em)
  #text(size: 10pt, fill: rgb("#64748B"))[
    Conseiller de portefeuille multi-agents pour le paper trading Alpaca
  ]
  #v(0.3em)
  #text(size: 9pt)[Victor & Kenan · HEIG-VD · Cours IA générative · #datetime.today().display("[day]/[month]/[year]")]
  #v(-0.2em)
  #text(size: 8pt, fill: rgb("#64748B"))[
    Dépôt : #link("https://github.com/Mondotosz/Llamafolio")
  ]
]

#v(0.2em)
#line(length: 100%, stroke: 0.4pt + rgb("#E5E7EB"))


= 1. Cas d'usage

L'investisseur particulier doit jongler avec des outils éclatés : son
broker affiche les positions, un site d'actualités donne le contexte
macro, un screener montre les fondamentaux. *Aucun outil ne les combine*,
et aucun ne calcule pour lui des choses pourtant essentielles comme
l'exposition sectorielle réelle ou la concentration sur un titre.

*Llamafolio* combine en une seule conversation : analyse de portefeuille,
recherche de marché (news, fondamentaux, web), évaluation de risque
(volatilité, bêta) et exécution simulée après confirmation explicite.
Cible : investisseur particulier curieux ou étudiant en finance.
*Valeur ajoutée IA :* multi-agents avec router cost-optimisé + sécurité
architecturale (proposition structurée + garde programmatique) + sortie
multilingue native.


= 2. Architecture

Deux couches : un _intent router_ classifie chaque tour en l'une de 7
intentions et route vers le _path_ minimal ; une chaîne _supervisor_
LangGraph gère uniquement les requêtes complexes multi-étapes.

#align(center)[
  #block(
    stroke: 0.4pt + rgb("#D1D5DB"),
    radius: 3pt,
    inset: 6pt,
    width: 99%,
  )[
    #set text(font: "DejaVu Sans Mono", size: 6.8pt)
    #align(left)[
```
                       ┌──────────────────┐
   user ──────────────►│  intent router   │   1 LLM call
                       └─┬────────────────┘
                         │
     ┌──────────┬────────┼────────┬────────────┬──────────┐
     ▼          ▼        ▼        ▼            ▼          ▼
    data    analyst  research   risk      executor*   complex (supervisor)
   0 LLM    2 LLM    2 LLM    2 LLM       2 LLM        6–12 LLM
                                            ▲           (analyst → research
                                            │            → risk)
                                  garde structurel programmatique :
                              refuse sans **Proposed trade** AIMessage
```
    ]
  ]
]

== 2.1 Stack et justifications

#table(
  columns: (auto, 1fr, 1.5fr),
  inset: 3.5pt,
  stroke: 0.4pt + rgb("#E5E7EB"),
  align: left,
  table.header([*Couche*], [*Technologie*], [*Justification*]),
  [LLM], [Gemini 3.1 Flash Lite · Groq gpt-oss-120b], [Dual provider via `.env`, _failover_ sans code change],
  [Orchestration], [LangGraph + `langgraph-supervisor`], [_Supervisor pattern_ standard, _streaming_-ready],
  [Trading], [Alpaca paper], [Sémantique réaliste, gratuit, sans KYC],
  [Tools], [`alpaca-mcp-server` (MCP)], [60+ outils officiels, *angle au-delà du cours*],
  [Recherche], [Tavily + yfinance], [Web macro + fondamentaux gratuits],
  [UI], [Streamlit + Plotly], [Streaming natif, démo claire],
  [Observabilité], [LangSmith (endpoint EU)], [Tracing multi-agents, RGPD],
  [Packaging], [`uv`], [_Lockfile_ déterministe, 10× plus rapide que pip],
)

== 2.2 Au-delà du cours

+ *Model Context Protocol* — Serveur tiers (`alpaca-mcp-server`) en
  _subprocess stdio_ via `uvx`, importé par `langchain-mcp-adapters`.
+ *Intent router pré-superviseur* — Réduit le coût moyen par tour de
  ~9 à ~2.3 _round-trips_ (×4 d'économie).
+ *Pré-injection du contexte portefeuille* — Lecture Alpaca _host-side_
  injectée comme bloc `<portfolio_context>` ; l'analyste consomme
  directement, sans 8 à 10 _round-trips_ MCP supplémentaires.


= 3. Données utilisées

Aucune donnée statique : tout est consommé *en direct* via les _tools_.

#table(
  columns: (auto, 1fr, 1.2fr),
  inset: 3.5pt,
  stroke: 0.4pt + rgb("#E5E7EB"),
  align: left,
  table.header([*Source*], [*Données*], [*Fraîcheur*]),
  [Alpaca paper], [Compte, positions, équité, ordres], [Temps réel],
  [Alpaca market], [Quotes, bars OHLCV, news], [15-min retard (IEX)],
  [yfinance], [P/E, bêta, capitalisation, secteur], [Jour ouvré],
  [Tavily], [Recherche web sémantique (macro/régulation)], [Continu],
)

Le portefeuille de démo (`scripts/seed_portfolio.py`) initialise 7
positions volontairement déséquilibrées (44 % _tech_) pour offrir un
signal de concentration clair lors des démos.


= 4. Fonctionnement

Un tour typique :

+ Le _host_ Streamlit pré-fetch le _snapshot_ portefeuille Alpaca et
  l'injecte au début du _prompt_ utilisateur sous forme de bloc
  `<portfolio_context>` (positions, secteurs, ratios).
+ L'_intent router_ classifie la question. Pour `data`, `analyst`,
  `research`, `risk`, `executor`, `decline` → routage direct au
  spécialiste concerné. Pour `complex` → chaîne _supervisor_.
+ Chaque spécialiste exécute sa boucle ReAct : appels de _tools_ en
  parallèle quand possible, puis synthèse.
+ L'UI affiche chaque message en _streaming_ (`graph.astream`). Une
  bannière *Confirm / Refuse* apparaît si un bloc structuré
  `**Proposed trade**` est détecté.
+ Le clic _Confirm_ déclenche une route déterministe vers l'exécuteur.
  Avant tout appel LLM, un garde Python scanne `state["messages"]`
  pour valider qu'une proposition `AIMessage` existe ; sinon, refus.


= 5. Résultats

== 5.1 Évaluation comportementale (23 cas, 4 axes)

Le harnais `scripts/run_eval.py` exécute chaque cas à travers le _vrai_
graphe et scorre Routing / Outils / Faits / Sécurité.

#table(
  columns: (auto, auto, auto, auto, auto, auto, auto),
  inset: 3.5pt,
  stroke: 0.4pt + rgb("#E5E7EB"),
  align: (left, right, right, right, right, right, right),
  table.header(
    [*Catégorie*], [*n*], [*Route*], [*Tools*], [*Faits*], [*Safety*], [*s*],
  ),
  [data],         [1], [1.00], [1.00], [1.00], [1.00], [6.1],
  [analyst],      [3], [1.00], [1.00], [1.00], [1.00], [5.3],
  [research],     [5], [1.00], [1.00], [1.00], [1.00], [5.7],
  [complex],      [2], [1.00], [1.00], [1.00], [1.00], [40.3],
  [safety],       [5], [1.00], [1.00], [1.00], [1.00], [7.8],
  [adversarial],  [5], [1.00], [1.00], [1.00], [0.60\*], [7.7],
  [multilingual], [1], [1.00], [1.00], [1.00], [1.00], [21.9],
)

#text(size: 8.5pt, fill: rgb("#64748B"))[
  \* Le _pack_ adversariale (ajouté en phase 2) a découvert *3 bugs* :
  (1) l'exécuteur hallucinait une proposition à partir du texte de la
  confirmation → garde programmatique ajouté ; (2) le superviseur
  pouvait router autonomement vers l'exécuteur → exécuteur retiré de
  la liste des agents du superviseur ; (3) le router ne décline pas
  les demandes crypto en allemand → documenté (impact nul depuis le
  fix #2). Les deux Safety 0.00 résiduels sont des *faux positifs du
  substring matching* (le mot « successfully » ou « BTC/USD »
  apparaît dans une réponse de refus) — `observed_tools` confirme
  qu'aucun ordre n'a été placé.
]

== 5.2 Impact des optimisations

#table(
  columns: (1fr, auto, auto, auto),
  inset: 3.5pt,
  stroke: 0.4pt + rgb("#E5E7EB"),
  align: (left, right, right, right),
  table.header(
    [*État*], [*Round-trips*], [*Latence*], [*Coût\**],
  ),
  [Multi-agent naïf], [15–20], [30–60 s], [\$0.005],
  [\+ pré-fetch contexte], [10–14], [20 s], [\$0.003],
  [\+ tool calls parallèles], [6–10], [15 s], [\$0.002],
  [*\+ intent router (mix 90/10)*], [*~2.3*], [*3–5 s*], [*\$0.0005*],
)

#text(size: 8.5pt, fill: rgb("#64748B"))[
  \* Gemini 3.1 Flash Lite _paid_, _prompt caching_ activé. *Message
  clé :* l'architecture pèse plus lourd que le _provider_ — passer de
  ~9 à ~2.3 _round-trips_ divise le coût par 4× sans changer de modèle.
]


= 6. Analyse critique

*Limites techniques* — Gemini _thinking_ incompatible avec
`langgraph-supervisor` (mitigation `thinking_budget=0`) ; _rate limits_
gratuits Gemini (15 RPM, 500 RPD) atteints sur les _runs_ d'eval
intensifs ; _substring matching_ donne 2 faux positifs sécurité sur les
cas de refus naturel (cf. § 5.1).

*Améliorations envisagées* — LLM-as-judge en complément du _substring_
pour scorer la qualité ; _prompt caching_ explicite (×4 sur coût input) ;
mémoire persistante via _checkpointer_ + Postgres ; CI GitHub Actions
avec _badge_ eval ; cas adversariaux étendus (_prompt injection_ via
news Alpaca, confirmations multilingues forgées).

*Dimension éthique* — Sur-confiance du modèle (tendance à formuler
des observations en recommandations) ; produit non régulé (pas
d'obligation MiFID II / FINMA) ; biais des sources (news Alpaca
essentiellement anglo-saxonnes) ; coût environnemental (un tour
_complex_ ≈ 50 k tokens) atténué par le router qui évite la chaîne
quand inutile ; boucle de confirmation trop fluide (un clic suffit,
une étape « justifier le trade » forcerait plus de réflexion).

#v(0.3em)
#text(size: 8.5pt, fill: rgb("#64748B"))[
  Une version étendue de ce rapport (16 pages, triptyque
  ML/MLOps/Sécurité + journal de développement détaillé) est
  disponible dans le dépôt sous `docs/rapport_extended.pdf`.
]
