"""Streamlit entry point.

Run with `streamlit run app.py`. The real work lives in
`llamafolio.ui.main`; this shim only exists because Streamlit looks for
a `.py` file at the repository root by convention.
"""
from llamafolio.ui import main

main()
