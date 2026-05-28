"""Custom CSS for the Streamlit UI.

All visual styling lives here — design tokens (palette, spacing), brand
header, sidebar metrics & position cards, chat bubbles, agent timeline,
trade-confirm banner and the per-turn metrics footer. The `inject()`
helper writes the whole stylesheet into the page in a single
`st.markdown` call.
"""
from __future__ import annotations

import streamlit as st

CSS = """
<style>
:root {
  --bg: #FAFAFA;
  --surface: #FFFFFF;
  --surface-2: #F8FAFC;
  --border: #E5E7EB;
  --border-strong: #D1D5DB;
  --text: #0F172A;
  --text-muted: #64748B;
  --text-dim: #94A3B8;
  --accent: #0F172A;
  --accent-soft: #F1F5F9;
  --gain: #047857;
  --loss: #B91C1C;
  --gain-bg: #ECFDF5;
  --loss-bg: #FEF2F2;
}

html, body, [class*="css"], table, [data-testid="stMetricValue"] {
  font-variant-numeric: tabular-nums;
  -webkit-font-smoothing: antialiased;
}

.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 100%; }
section[data-testid="stSidebar"] > div { padding-top: 0.5rem; }
section[data-testid="stSidebar"] { background: var(--surface-2); }
[data-testid="stHeader"] { background: transparent; height: 0; }

/* -- Brand header ----------------------------------------------------------*/
.lf-brand { display: flex; align-items: center; gap: 0.85rem; }
.lf-brand-lockup {
  height: 44px;
  width: auto;
  display: block;
}
.lf-status-pill {
  font-size: 0.7rem; color: var(--text-muted);
  border: 1px solid var(--border); border-radius: 999px;
  padding: 0.22rem 0.65rem; background: var(--surface);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  display: inline-block;
  width: fit-content;
  white-space: nowrap;
}
.lf-status-dot {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 999px;
  background: var(--gain);
  margin-right: 0.4rem;
  vertical-align: middle;
}

/* -- Sidebar hero + metrics ------------------------------------------------*/
.lf-hero {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  background: var(--surface);
  margin-bottom: 0.5rem;
}
.lf-hero-label {
  font-size: 0.66rem; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-muted); margin-bottom: 0.3rem;
}
.lf-hero-value { font-size: 1.85rem; font-weight: 700; color: var(--text); line-height: 1.05; letter-spacing: -0.02em; }
.lf-hero-delta { font-size: 0.78rem; color: var(--text-muted); margin-top: 0.35rem; }

.lf-metric-mini {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.55rem 0.7rem;
  background: var(--surface);
}
.lf-metric-mini-label {
  font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-muted); margin-bottom: 0.15rem;
}
.lf-metric-mini-value { font-size: 1rem; font-weight: 600; color: var(--text); line-height: 1.1; }
.lf-metric-mini-delta { font-size: 0.7rem; color: var(--text-muted); margin-top: 1px; }

.lf-section {
  font-size: 0.66rem; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-muted); font-weight: 600;
  margin: 0.8rem 0 0.45rem 0;
}

/* -- Position cards (denser) ----------------------------------------------*/
.lf-pos {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.15rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem 0.7rem;
  background: var(--surface);
  margin-bottom: 0.35rem;
  font-size: 0.85rem;
  transition: border-color 0.12s, transform 0.12s;
}
.lf-pos:hover { border-color: var(--border-strong); }
.lf-pos-sym { font-weight: 600; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85rem; }
.lf-pos-meta { font-size: 0.68rem; color: var(--text-muted); }
.lf-pos-val { font-weight: 600; text-align: right; font-size: 0.85rem; }
.lf-pos-pl { font-size: 0.7rem; text-align: right; color: var(--text-muted); }
.gain-pill { background: var(--gain-bg); color: var(--gain); border-radius: 5px; padding: 0 5px; font-size: 0.7rem; font-weight: 600; }
.loss-pill { background: var(--loss-bg); color: var(--loss); border-radius: 5px; padding: 0 5px; font-size: 0.7rem; font-weight: 600; }

/* -- Empty-state agent cards ----------------------------------------------*/
.lf-hero-block {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 0.85rem;
  margin-bottom: 1rem;
}
.lf-intro {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.1rem 1.35rem;
  background: var(--surface);
}
.lf-intro h2 { font-size: 1.3rem; margin: 0 0 0.35rem 0; letter-spacing: -0.01em; font-weight: 600; }
.lf-intro p { color: var(--text-muted); margin: 0; font-size: 0.88rem; line-height: 1.5; }

.lf-flow {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.9rem 1.05rem;
  background: var(--surface);
}
.lf-flow-title {
  font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted); font-weight: 600; margin-bottom: 0.6rem;
}
.lf-flow-step {
  display: flex; align-items: center; gap: 0.5rem;
  font-size: 0.8rem; color: var(--text);
  padding: 0.2rem 0;
}
.lf-flow-num {
  width: 18px; height: 18px; border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 0.7rem; font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.lf-agent-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
.lf-agent-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.8rem 0.95rem;
  background: var(--surface);
  transition: border-color 0.15s, transform 0.15s;
}
.lf-agent-card:hover { border-color: var(--border-strong); }
.lf-agent-name {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.72rem; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.06em;
  margin-bottom: 0.4rem;
}
.lf-agent-role { font-size: 0.95rem; font-weight: 600; color: var(--text); margin-bottom: 0.3rem; line-height: 1.25; }
.lf-agent-desc { font-size: 0.78rem; color: var(--text-muted); line-height: 1.45; }

/* -- Suggestion chip buttons ----------------------------------------------*/
[data-testid="stHorizontalBlock"] button[kind="secondary"] {
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  border-radius: 999px !important;
  padding: 0.45rem 1.05rem !important;
  font-size: 0.86rem !important;
  font-weight: 500 !important;
  transition: border-color 0.15s, background 0.15s, transform 0.15s;
}
[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
  border-color: var(--accent) !important;
  background: var(--accent-soft) !important;
  transform: translateY(-1px);
}

/* -- Chat -----------------------------------------------------------------*/
[data-testid="stChatMessage"] {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.85rem 1.05rem;
  margin-bottom: 0.45rem;
  background: var(--surface);
}

.lf-agent-label {
  display: inline-block;
  font-size: 0.7rem; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--text-muted); font-weight: 600;
  margin-bottom: 0.5rem;
  padding: 2px 8px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.lf-step {
  display: flex; align-items: center; gap: 0.6rem;
  font-size: 0.82rem; color: var(--text);
  padding: 0.3rem 0;
  border-left: 2px solid var(--border);
  padding-left: 0.75rem;
  margin-left: 0.2rem;
}
.lf-step-kind {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.72rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  min-width: 56px;
}
.lf-step-name { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.8rem; color: var(--text); }

/* -- Trade confirm banner -------------------------------------------------*/
.lf-trade-banner {
  border: 1px solid var(--border-strong);
  border-left: 4px solid var(--accent);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  background: var(--surface);
  margin: 0.75rem 0 0.5rem 0;
}
.lf-trade-banner-title {
  font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted); font-weight: 600; margin-bottom: 0.35rem;
}
.lf-trade-banner-body { font-size: 0.92rem; color: var(--text); }

button[kind="primary"] {
  background: var(--accent) !important;
  color: #FFFFFF !important;
  border: 1px solid var(--accent) !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
}
button[kind="primary"]:hover { background: #1E293B !important; }

.lf-disclaimer {
  font-size: 0.7rem;
  color: var(--text-dim);
  margin-top: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border);
  text-align: center;
}

.lf-metrics {
  display: flex; gap: 0.85rem; justify-content: flex-end; flex-wrap: wrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.72rem; color: var(--text-muted);
  margin-top: 0.5rem;
}
.lf-metric-chip {
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.15rem 0.6rem;
  background: var(--surface);
}
.lf-metric-chip b { color: var(--text); font-weight: 600; margin-right: 0.2rem; }

/* responsive — collapse agent grid on narrow screens */
@media (max-width: 1200px) {
  .lf-agent-grid { grid-template-columns: repeat(2, 1fr); }
  .lf-hero-block { grid-template-columns: 1fr; }
}
</style>
"""


def inject() -> None:
    """Write the stylesheet into the page in a single `st.markdown` call."""
    st.markdown(CSS, unsafe_allow_html=True)
