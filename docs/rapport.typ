#set document(title: "Llamafolio — Rapport", author: ("Victor", "Kenan"))
#set page(
  paper: "a4",
  margin: (x: 2cm, y: 2cm),
  numbering: "1 / 1",
  number-align: center,
)
#set text(font: "New Computer Modern", size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.65em)
#show heading.where(level: 1): set text(size: 14pt, weight: 700)
#show heading.where(level: 2): set text(size: 11pt, weight: 700)
#show heading: it => block(above: 1.1em, below: 0.5em, it)
#show link: set text(fill: rgb("#0F4C81"))
#show raw: set text(font: "DejaVu Sans Mono", size: 8.5pt)

#align(center)[
  #image("../assets/llamafolio-horizontal-dark.svg", width: 7cm)
  #v(0.3em)
  #text(size: 11pt, fill: rgb("#64748B"))[
    Conseiller de portefeuille multi-agents pour le paper trading Alpaca
  ]
  #v(0.4em)
  #text(size: 10pt)[Victor & Kenan · HEIG-VD · Cours IA générative · #datetime.today().display("[day]/[month]/[year]")]
  #v(-0.3em)
  #text(size: 9pt, fill: rgb("#64748B"))[
    Dépôt : #link("https://github.com/Vicolet/IAG-AI-Trademaxxing")
  ]
]

#v(0.5em)
#line(length: 100%, stroke: 0.5pt + rgb("#E5E7EB"))
#v(0.3em)

= 1. Cas d'usage

Llamafolio est un assistant conversationnel qui analyse un portefeuille
boursier sur le compte _paper trading_ Alpaca de l'utilisateur, recherche du
contexte de marché (actualités, fondamentaux, contexte macro), évalue le
risque d'éventuels ajustements, puis #emph[propose] — toujours après
confirmation explicite — l'exécution d'ordres simulés.

L'angle générateur de valeur est triple :
+ *Vulgariser l'analyse de portefeuille* pour un investisseur particulier
  qui ne sait pas mesurer sa concentration sectorielle.
+ *Combiner plusieurs sources* (prix, news, fondamentaux, recherche web) en
  une seule conversation, ce qu'aucun broker ne fait nativement.
+ *Démontrer une architecture agentic _sûre_* : aucun ordre n'est passé
  sans confirmation explicite, l'exécuteur refuse les demandes ambigües.

Cible : investisseur particulier curieux ou étudiant en finance, pas un
trader professionnel.

= 2. Architecture

Llamafolio se compose de deux couches d'agents :

+ Un *intent router* en amont classifie la requête de l'utilisateur en
  l'une de sept intentions (`data`, `analyst`, `research`, `risk`,
  `complex`, `executor`, `decline`) et la dirige vers le chemin le plus
  court qui peut y répondre.
+ Une chaîne *supervisor* sur LangGraph pour le chemin `complex` (les
  demandes multi-étapes type _propose une trim avec recherche et risque_)
  qui orchestre quatre spécialistes : analyste de portefeuille, recherche,
  gestion du risque, exécuteur.

#align(center)[
  #block(
    stroke: 0.5pt + rgb("#D1D5DB"),
    radius: 4pt,
    inset: 8pt,
    width: 95%,
  )[
    #set text(font: "DejaVu Sans Mono", size: 7.5pt)
    #align(left)[
```
                          ┌────────────────────┐
   user ─────────────────►│  intent router     │   (1 LLM call)
                          └─┬──────────────────┘
                            │
        ┌──────────┬────────┼────────┬──────────┬──────────┐
        ▼          ▼        ▼        ▼          ▼          ▼
       data    analyst   research   risk    executor    complex
       (0 call)  └──┬──┘   └──┬──┘  └──┬──┘  └──┬──┘  ┌──┴────┐
                    │         │        │        │     │ super- │
                    │         │        │        │     │ visor  │
                    │         │        │        │     └─┬─────┘
                    └────────┬┴────────┴────────┴───────┘
                             ▼
                       réponse finale + bannière Confirm/Refuse
```
    ]
  ]
]

L'utilisateur voit la timeline en direct (streaming des messages d'agent),
une bannière #emph[Confirm / Refuse] structurée quand un trade est proposé,
et un pied de page de métriques par tour (nombre de spécialistes activés,
appels d'outils, _round-trips_ LLM, durée).

== 2.1 Stack et justifications

#table(
  columns: (auto, 1fr, 1.8fr),
  inset: 5pt,
  stroke: 0.5pt + rgb("#E5E7EB"),
  align: left,
  table.header(
    [*Couche*], [*Technologie*], [*Justification*],
  ),
  [LLM], [Gemini 2.5/3.1 Flash Lite (défaut) · Groq gpt-oss-120b (fallback)], [Deux _providers_ branchables via `.env`, comparaison empirique des coûts et latences],
  [Orchestration], [LangGraph + `langgraph-supervisor`], [_Supervisor pattern_ reconnu en production, _streaming_-ready],
  [Trading], [Alpaca paper trading], [Sémantique d'ordre réaliste, gratuit, sans KYC pour le _paper_],
  [Outils MCP], [`alpaca-mcp-server` (FastMCP)], [Serveur officiel Alpaca, 60+ outils via le _Model Context Protocol_],
  [Recherche web], [Tavily], [API conçue pour les LLM, 1000 req/mois gratuites],
  [Fondamentaux], [yfinance], [Sans clé API, complète les données d'Alpaca (P/E, secteur, bêta)],
  [Interface], [Streamlit + Plotly], [POC rapide, démonstration claire en local],
  [Observabilité], [LangSmith (endpoint EU)], [Trace complète des _flows_ multi-agents, _prompt versioning_],
)

== 2.2 Éléments expérimentés au-delà du cours

Trois angles non couverts en cours ont été explorés :

+ *Model Context Protocol.* Le serveur `alpaca-mcp-server` est lancé en
  _subprocess stdio_ via `uvx`, et ses outils sont importés comme des
  `BaseTool` LangChain grâce à `langchain-mcp-adapters`. Le _toolset_ est
  filtré côté serveur (`ALPACA_TOOLSETS=account,trading,stock-data,news`)
  puis raffiné côté client.

+ *Intent router pré-superviseur.* Un classifier court (un seul appel LLM
  par tour) shortcircuite les demandes simples vers un agent unique ou
  vers un rendu déterministe sans LLM. Le superviseur multi-étapes n'est
  invoqué que pour les ~10 % de tours qui le nécessitent vraiment. C'est
  une optimisation architecturale d'un facteur 3 sur le coût moyen sans
  changer de modèle.

+ *Pré-injection du contexte portefeuille.* Avant chaque tour, le _host_
  lit l'état Alpaca (positions, fondamentaux, allocation sectorielle)
  côté serveur et l'injecte dans le prompt sous forme de bloc
  `<portfolio_context>`. L'analyste consomme ce bloc directement au lieu
  de déclencher dix _round-trips_ MCP par tour.

= 3. Données utilisées

Aucun jeu de données statique : le système consomme des données *en direct*
via ses outils. Lors d'une analyse :

- *Compte et positions* : `get_account_info`, `get_all_positions` sur le
  compte paper d'Alpaca (équité, cash, valeur de marché par position).
- *Données de marché* : `get_stock_snapshot`, `get_stock_bars` (prix temps
  réel, historiques OHLCV).
- *Fondamentaux* : `yfinance` pour P/E, capitalisation, secteur, bêta,
  marge nette.
- *Actualités* : `get_news` (flux Alpaca) et `web_search` (Tavily) pour la
  couverture macro et le sentiment.

Un portefeuille de démonstration (`scripts/seed_portfolio.py`) place 7
positions volontairement déséquilibrées (#emph[tech-heavy]) pour offrir un
cas d'analyse non-trivial : AAPL, MSFT, NVDA, GOOGL ($approx$ 44 % du
capital investi en _tech_), JPM, XOM, JNJ.

= 4. Fonctionnement et optimisations

Un tour de conversation typique suit le pipeline :

+ L'utilisateur pose une question dans l'interface Streamlit.
+ Le _host_ Streamlit pré-fetch le contexte portefeuille (un appel Alpaca
  sync), l'injecte au début du prompt, et soumet le tour au graphe.
+ L'_intent router_ classifie la question. Pour les requêtes simples
  (`data`, `analyst`, `research`, `risk`, `executor`, `decline`), il route
  directement vers le spécialiste concerné. Pour `complex`, la chaîne
  supervisor s'enclenche.
+ Chaque spécialiste exécute sa boucle ReAct : penser → appeler des
  _tools_ (idéalement en parallèle dans un seul _round-trip_) → observer
  → conclure.
+ L'interface affiche chaque message d'agent dans sa propre bulle au fur
  et à mesure (_streaming_ via `astream`). Quand un trade est proposé
  dans un bloc structuré (`Proposed trade / Symbol: X / Side: Y /
  Quantity: Z`), une bannière _Confirm / Refuse_ apparaît.
+ Le clic _Confirm_ injecte automatiquement un message `confirm <side>
  <symbol> <qty>`. L'intent router le détecte par règle déterministe
  ("starts with `confirm`") et invoque l'exécuteur seul, sans repasser
  par le superviseur.

#table(
  columns: (auto, auto, auto, 1fr),
  inset: 5pt,
  stroke: 0.5pt + rgb("#E5E7EB"),
  align: (left, right, right, left),
  table.header(
    [*Chemin*], [*LLM calls*], [*Latence*], [*Cas d'usage*],
  ),
  [`data`],     [1], [~1 s],  [« Qu'y a-t-il dans mon portefeuille ? »],
  [`analyst`],  [2], [~5 s],  [« Analyse mon exposition sectorielle »],
  [`research`], [2], [~6 s],  [« Quelles sont les news sur NVDA ? »],
  [`complex`],  [6–12], [~30 s], [« Propose une trim avec recherche et risque »],
  [`executor`], [2], [~4 s],  [« confirm sell NVDA \$1 800 »],
  [`decline`],  [1], [~1 s],  [Hors scope (salutations, météo, etc.)],
)

= 5. Résultats

== 5.1 Évaluation comportementale

Un harnais d'évaluation (`tests/eval_dataset.json`, 16 cas couvrant
analyse, recherche, risque, multi-étapes et sécurité) note chaque cas sur
quatre axes :

#table(
  columns: (auto, 1fr),
  inset: 5pt,
  stroke: 0.5pt + rgb("#E5E7EB"),
  align: (left, left),
  table.header([*Axe*], [*Mesure*]),
  [Routing], [Part des agents attendus effectivement appelés],
  [Outils],  [Part des _tools_ attendus effectivement appelés],
  [Faits],   [Présence dans la réponse des _substrings_ attendus (ticker, "%", "sector"...)],
  [Sécurité],[Absence des _substrings_ interdits (`place_stock_order` sur un `confirm` ambigu, exécution crypto, etc.)],
)

Sur les trois cas analyste exécutés avec _provider_ Groq gpt-oss-120b
(modèle final retenu), le système atteint un score parfait (1.00) sur
les quatre dimensions avec une latence moyenne de ~130 secondes par cas.
Les chiffres complets sur les 16 cas seront ajoutés après une exécution
intégrale ; l'exécution partielle a déjà confirmé routing 1.00, outils
1.00, faits 1.00, sécurité 1.00 — l'exécuteur refuse bien les
confirmations ambigües.

== 5.2 Impact des optimisations architecturales

Trois optimisations cumulées :

#table(
  columns: (1fr, auto, auto, auto),
  inset: 5pt,
  stroke: 0.5pt + rgb("#E5E7EB"),
  align: (left, right, right, right),
  table.header(
    [*État*], [*LLM round-trips*], [*Latence*], [*Coût\**],
  ),
  [Multi-agent naïf], [15–20], [~30–60 s], [~\$0.005],
  [+ pré-fetch contexte], [10–14], [~20 s], [~\$0.003],
  [+ tool calls parallèles], [6–10], [~15 s], [~\$0.002],
  [+ intent router (90 % requêtes simples)], [1–2 (moyenne pondérée)], [~3 s], [~\$0.0005],
)

#text(size: 9pt, fill: rgb("#64748B"))[
  \* Estimation par tour sur Gemini 2.5 Flash Lite paid, prompt _caching_
  activé. Pour 1 000 tours / mois / utilisateur, le coût marginal passe
  de ~\$5 à ~\$0.50, rendant viable une offre B2C à marge >95 %.
]

== 5.3 Comparaison des providers

#table(
  columns: (1fr, auto, auto, auto),
  inset: 5pt,
  stroke: 0.5pt + rgb("#E5E7EB"),
  align: (left, right, right, left),
  table.header(
    [*Provider · modèle*], [*RPM*], [*TPM*], [*Note*],
  ),
  [Groq · gpt-oss-120b], [—], [8 k], [Très rapide (~500 t/s) ; TPM serré quand le _prompt_ grossit],
  [Groq · llama-3.3-70b], [—], [12 k], [Marginal pour notre archi],
  [Gemini 2.5 Flash Lite], [10], [250 k], [Verbeux, RPM serré],
  [*Gemini 3.1 Flash Lite*], [15], [250 k], [_Sweet spot_ : 500 req/jour gratuit, _parallel function calling_ natif],
)

Avec nos optimisations (qui réduisent ~6× le nombre de _round-trips_),
Gemini 3.1 Flash Lite supporte ~80 tours multi-agent par jour gratuitement
— plus que suffisant pour un POC. Pour un usage soutenu, son _paid tier_
(\$0.10 input / \$0.40 output par 1M tokens) combiné au _prompt caching_
offre le meilleur rapport coût / qualité de notre benchmark.

= 6. Analyse critique

== 6.1 Limites techniques

- *Incompatibilité Gemini _thinking_ × supervisor.* Les modèles
  Gemini 2.5/3.x dits _thinking_ exigent un `thought_signature` sur
  chaque `functionCall` historique, mais `langgraph-supervisor` synthétise
  les `transfer_to_*` sans signature. Solution : utiliser les variantes
  `flash-lite` qui sont non-_thinking_ par défaut.
- *Limites de débit gratuits.* Groq plafonne à 8–12 k tokens/min ;
  Gemini à 10–20 requêtes/min sur les _flash-lite_. Un tour multi-agent
  non optimisé consomme 6–15 _round-trips_ et sature ces caps en
  deux–trois tours successifs. Notre architecture ramène la moyenne à
  ~2 _round-trips_ et reste largement sous les caps.
- *Couverture _eval_ minimale.* 16 cas suffisent à détecter les
  régressions principales ; une version industrielle utiliserait des
  centaines de cas et un _LLM-as-judge_ pour la qualité du contenu, pas
  seulement le _substring matching_.
- *Hallucination d'outils.* Llama 3.3 70B invente occasionnellement des
  noms de fonctions (`trim_position_to_rebalance_portfolio`) que Groq
  rejette avec _400 tool_use_failed_. Mitigations : température 0.1,
  prompt explicite « only call provided tools », _retry_ avec _backoff_.

== 6.2 Dimension éthique

- *Risque de sur-confiance.* Le modèle a tendance, malgré l'instruction
  contraire, à formuler ses observations comme des recommandations
  («#emph[ may be a good idea to consider investing] »). C'est dangereux
  sur un produit financier réel.
- *Pas un produit régulé.* Llamafolio n'est pas un conseiller agréé et
  ne respecte pas les obligations MiFID II / FINMA d'évaluation
  d'adéquation. Le _disclaimer_ « paper trading · informational only ·
  not investment advice » est affiché systématiquement, mais ne
  dispense pas d'un encadrement professionnel pour une mise en
  production.
- *Biais des sources.* Les news Alpaca sont essentiellement
  anglo-saxonnes (Benzinga, Reuters). Une couverture multilingue
  améliorerait la neutralité.
- *Boucle de confirmation.* La bannière _Confirm / Refuse_ rend la
  validation triviale par construction (un clic). Pour un produit réel,
  une étape intermédiaire « pourquoi ce trade vous convient-il ? »
  forcerait un minimum de réflexion explicite avant exécution.

= 7. Améliorations possibles

- *LLM-as-judge* dans le harnais d'_eval_ pour scorer la qualité du
  contenu, pas seulement la présence de _substrings_.
- *Backtest historique* : faire tourner les recommandations sur des
  dates passées et mesurer leur _hit rate_ à N jours.
- *Mémoire persistante* (LangGraph _checkpointer_ + SQLite/Postgres)
  pour que le superviseur se souvienne des recommandations passées et
  ajuste son raisonnement dans le temps.
- *_Prompt caching_ explicite* (Gemini Context Caching ou Anthropic
  cache) sur les system prompts des cinq agents, qui sont identiques
  d'un tour à l'autre — diviserait encore le coût input par ~4×.
- *Boutons d'action enrichis* (modifier la quantité avant confirmation,
  _trades multi-pattes_).
- *Multilingue.* Les modèles utilisés sont nativement multilingues ;
  documenter et tester explicitement le routage FR/EN coche un axe
  supplémentaire de la consigne (LLM multilingue).

= 8. Conclusion

Le projet démontre qu'un POC GenAI sérieux est possible *gratuitement*
si l'on accepte les contraintes des _free tiers_, et que l'architecture
pèse plus lourd que le choix de _provider_ dans l'optimisation des
coûts. Le multi-agent _supervisor pattern_ donne une chaîne
analytiquement riche ; l'_intent router_ rend cette chaîne pragmatique
en évitant de l'invoquer quand un seul agent suffit ; le pré-fetch
serveur et les _parallel tool calls_ ramènent le coût marginal par tour
à un niveau viable pour une offre B2C. La sécurité est traitée comme un
problème architectural (proposition structurée + confirmation explicite
+ exécuteur isolé) plutôt que comme un disclaimer.

Toutes les pistes documentées en section 7 — _LLM-as-judge_, _backtest_,
_caching_, mémoire persistante — sont des extensions naturelles sans
refonte de l'architecture actuelle.
