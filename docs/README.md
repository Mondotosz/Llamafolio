# Documentation

| File | Contenu |
| --- | --- |
| [architecture.md](architecture.md) | Vue d'ensemble technique (agents, outils, sécurité, eval, limites). |
| [rapport.typ](rapport.typ) | Rapport 2-3 pages (livrable du cours, en français). |
| [slides.typ](slides.typ) | Slides de présentation 10 minutes (Touying + Metropolis, en français). |

## Construire les PDF

Installer [Typst](https://typst.app/docs/installation/) :

```bash
# macOS
brew install typst
# Linux (via uv ou cargo)
cargo install --locked typst-cli
# ou via Snap
snap install typst
```

Puis depuis la racine du dépôt :

```bash
# Rapport (2-3 pages)
typst compile docs/rapport.typ docs/rapport.pdf

# Slides (Touying + Metropolis)
typst compile docs/slides.typ docs/slides.pdf
```

Pour itérer sur les sources avec _hot reload_ :

```bash
typst watch docs/slides.typ
```

## Dépendances Typst

Les slides utilisent le package [`touying`](https://typst.app/universe/package/touying)
(version 0.5.5) avec le thème Metropolis. Typst gère le téléchargement
automatique des packages depuis Typst Universe à la première compilation.
