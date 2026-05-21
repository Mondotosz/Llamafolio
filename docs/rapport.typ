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
  #text(size: 18pt, weight: 700)[Llamafolio]
  #v(-0.2em)
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

= 2. Architecture

Llamafolio implémente le _supervisor pattern_ sur LangGraph : un superviseur
LLM observe la conversation et délègue chaque tour à un agent spécialiste,
puis synthétise une réponse finale. Quatre spécialistes existent — analyste
de portefeuille, recherche, gestion du risque, exécuteur — chacun avec un
prompt et un sous-ensemble d'outils dédiés.

#align(center)[
  #block(
    stroke: 0.5pt + rgb("#D1D5DB"),
    radius: 4pt,
    inset: 8pt,
    width: 95%,
  )[
    #set text(font: "DejaVu Sans Mono", size: 8pt)
    #align(left)[
```
                    ┌─────────────────┐
   user ──────────► │   supervisor    │ ◄────── réponse finale
                    └────────┬────────┘
                             │ transfer_to_*
        ┌──────────────┬─────┴────────┬──────────────┐
        ▼              ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐
   │ analyst │   │ research │   │  risk   │   │ executor │
   └─────────┘   └──────────┘   └─────────┘   └──────────┘
   positions     news/web       beta/vol      place_order
   sector exp.   fundamentals   exposure      cancel/close
```
    ]
  ]
]

== 2.1 Choix de stack et justifications

#table(
  columns: (auto, auto, 1fr),
  inset: 5pt,
  stroke: 0.5pt + rgb("#E5E7EB"),
  align: left,
  table.header(
    [*Couche*], [*Technologie*], [*Justification*],
  ),
  [LLM], [Groq · Llama 3.3 70B / gpt-oss-120b], [Gratuit, rapide (>500 t/s), capable en _tool calling_],
  [Orchestration], [LangGraph + `langgraph-supervisor`], [Pattern multi-agent reconnu en production, _checkpointer_-ready],
  [Trading], [Alpaca paper trading], [Sémantique d'ordre réaliste, gratuit, sans KYC pour le _paper_],
  [Outils MCP], [`alpaca-mcp-server` (FastMCP)], [Serveur officiel Alpaca exposant 60+ outils via le Model Context Protocol],
  [Recherche web], [Tavily], [API conçue pour les LLM, 1000 requêtes/mois en gratuit],
  [Fondamentaux], [yfinance], [Sans clé API, complète les données d'Alpaca (P/E, secteur, bêta)],
  [Interface], [Streamlit + Plotly], [POC rapide, démonstration claire],
  [Traçabilité], [LangSmith (endpoint EU)], [Debug des flows multi-agents, prompt versioning],
)

== 2.2 Élément expérimenté au-delà du cours

L'angle non-couvert en cours est *l'utilisation du Model Context Protocol*
pour intégrer un serveur d'outils tiers à un graphe LangGraph. Le serveur
`alpaca-mcp-server` est lancé en _stdio subprocess_ via `uvx`, et ses outils
sont importés comme des `BaseTool` LangChain grâce à
`langchain-mcp-adapters`. Le _toolset_ est filtré côté serveur
(`ALPACA_TOOLSETS=account,trading,stock-data,news`) puis raffiné côté client
pour rester sous la limite de tokens-par-minute du _free tier_ Groq.

= 3. Données utilisées

Aucun jeu de données fixe : le système consomme des données *en direct* via
ses outils. Concrètement, lors d'une analyse :

- *Compte et positions* : `get_account_info`, `get_all_positions` sur le
  compte paper d'Alpaca (équité, cash, valeur de marché par position).
- *Données de marché* : `get_stock_snapshot`, `get_stock_bars` (prix temps
  réel, historiques OHLCV).
- *Fondamentaux* : `yf.Ticker.info` pour P/E, capitalisation, secteur, bêta,
  marge nette.
- *Actualités* : `get_news` (flux Alpaca) et `web_search` (Tavily) pour la
  couverture macro et la sentiment.

Un portefeuille de démonstration (`scripts/seed_portfolio.py`) place 7
positions volontairement déséquilibrées (#emph[tech-heavy]) pour offrir un
cas d'analyse non-trivial : AAPL, MSFT, NVDA, GOOGL ($\approx$ 48% du
capital investi en tech), JPM, XOM, JNJ.

= 4. Fonctionnement

Un tour de conversation suit le pipeline suivant :

+ L'utilisateur pose une question dans l'interface Streamlit.
+ Le superviseur LLM lit la question et appelle le _tool_ `transfer_to_*`
  approprié pour passer la main à un spécialiste.
+ Le spécialiste exécute sa boucle ReAct : penser → appeler un _tool_
  (Alpaca MCP, yfinance ou Tavily) → observer → recommencer jusqu'à avoir
  une réponse.
+ Le spécialiste rend la main au superviseur via `transfer_back_to_supervisor`.
+ Le superviseur _peut_ router vers un autre spécialiste (typiquement
  analyste → recherche → risque pour une demande de rebalancement) ou
  écrire la réponse finale.
+ L'interface affiche chaque message d'agent dans sa propre bulle, plus la
  synthèse finale et — quand un _trade_ est proposé — un binôme de boutons
  *Confirm* / *Refuse* qui injectent automatiquement la confirmation
  attendue par l'exécuteur.

= 5. Résultats

Une _eval_ comportementale (16 cas dans `tests/eval_dataset.json`) note
chaque cas sur quatre axes :

#table(
  columns: (auto, 1fr),
  inset: 5pt,
  stroke: 0.5pt + rgb("#E5E7EB"),
  align: (left, left),
  table.header([*Axe*], [*Mesure*]),
  [Routing], [Part des agents attendus effectivement appelés],
  [Outils],  [Part des _tools_ attendus effectivement appelés],
  [Faits],   [Présence dans la réponse des _substrings_ attendus (ticker, "%", "sector"...)],
  [Sécurité],[Absence des _substrings_ interdits (`place_stock_order` sur un "confirm" ambigu, exécution crypto, etc.)],
)

#text(fill: rgb("#64748B"))[
  _Les scores chiffrés seront ajoutés avant la présentation après une
  exécution complète de l'_eval_. Une exécution partielle (3 cas safety)
  a déjà confirmé : routing 1.00, safety 1.00 — l'exécuteur refuse bien
  les confirmations ambigües._
]

Qualitativement, sur le flow #emph["Analyse mon exposition sectorielle et
propose une trim"] :

- L'analyste calcule correctement la concentration #emph[sur le capital
  investi] (Tech $approx$ 48%) après que le prompt initial — qui calculait
  contre l'équité totale — ait été corrigé (voir _commit_
  `fix(prompts/analyst)`).
- La recherche enchaîne `get_stock_snapshot`, `get_fundamentals`, `get_news`
  et `web_search` en série, cite ses sources entre parenthèses.
- L'exécuteur place bien l'ordre _seulement_ après #emph[confirm sell NVDA 5%]
  et refuse #emph[confirm] seul (test de sécurité).

= 6. Analyse critique

== 6.1 Limites techniques

- *Hallucination d'outils.* Llama 3.3 70B invente occasionnellement des
  noms de fonctions (#emph[trim_position_to_rebalance_portfolio]) que Groq
  rejette en _400 tool_use_failed_. Mitigations appliquées : température
  $0.1$, prompt explicite #emph["only call provided tools"], _retry_ avec
  _backoff_ exponentiel. Une solution _production-grade_ utiliserait un
  modèle plus fiable (Claude, GPT-4o) ou un schéma _function calling_
  contraint.
- *Limites de débit.* Le _free tier_ Groq plafonne à 8–12k tokens/minute
  selon le modèle, et 100k tokens/jour sur Llama 3.3. Un tour multi-agents
  consomme 3–8k tokens ; deux ou trois tours en succession suffisent à
  saisir la limite par minute. Le _retry_ absorbe les pics transitoires ;
  un _paid tier_ serait nécessaire pour un usage soutenu.
- *Couverture _eval_ minimale.* 16 cas suffisent à détecter les régressions
  sur les comportements principaux ; une version industrielle utiliserait
  des centaines de cas et un _LLM-as-judge_ pour la qualité du contenu.

== 6.2 Dimension éthique

- *Risque de sur-confiance.* Le modèle a tendance, malgré l'instruction
  contraire, à formuler ses observations comme des recommandations
  («#emph[ may be a good idea to consider investing] »). C'est dangereux sur
  un produit financier réel.
- *Pas un produit financier régulé.* Llamafolio n'est pas un conseiller
  agréé et ne respecte pas les obligations MiFID II / FINMA d'évaluation
  d'adéquation. Le _disclaimer_ #emph[paper trading · informational only · not
  investment advice] est affiché systématiquement, mais ne dispense pas
  d'un encadrement professionnel pour une mise en production.
- *Biais des sources.* Les news Alpaca sont essentiellement
  anglo-saxonnes (Benzinga, Reuters). Une couverture multilingue
  améliorerait la neutralité.

= 7. Améliorations possibles

- *Streaming des réponses* (LangGraph `astream_events`) pour une UX en
  temps réel pendant la pensée de l'agent.
- *LLM-as-judge* sur les sorties pour mesurer la qualité du contenu.
- *Backtest minimal* : faire tourner les recommandations sur des dates
  historiques et mesurer leur _hit rate_ à N jours.
- *Mémoire persistante* (LangGraph checkpointer + Postgres) pour suivre
  les recommandations dans le temps.
- *Boutons d'action enrichis* (modifier la quantité avant confirmation,
  trades multi-pattes).
