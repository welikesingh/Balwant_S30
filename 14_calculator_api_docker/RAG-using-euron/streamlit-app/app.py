"""Streamlit Calculator UI — calls the FastAPI calculator API."""

import httpx
import streamlit as st

API_URL = "http://localhost:5000"


def api_post(endpoint: str, payload: dict) -> dict | None:
    """POST to the API; return result dict or None (error shown in UI)."""
    try:
        r = httpx.post(f"{API_URL}{endpoint}", json=payload, timeout=5)
        if r.status_code == 400:
            st.error(r.json().get("detail", str(r.text)))
            return None
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        st.error("Cannot connect to the calculator API — is it running at http://localhost:5000 ?")
        return None
    except httpx.HTTPStatusError as exc:
        st.error(f"API error: {exc.response.status_code} — {exc.response.text}")
        return None


def fetch_history() -> list:
    """GET /history, return list of history items."""
    try:
        r = httpx.get(f"{API_URL}/history", timeout=5)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        return []
    except httpx.HTTPStatusError:
        return []


# ── Page setup ──────────────────────────────────────────────────────
st.set_page_config(page_title="Calculator", page_icon="🔢", layout="wide")
st.title("🔢 Calculator")

col_main, col_history = st.columns([3, 1])

# ── Main calculator panel ───────────────────────────────────────────
with col_main:
    # Display
    session_result = st.session_state.get("result", "0")
    st.markdown(
        f"""<div style="background:#1e1e2f;color:#0f0;padding:16px 20px;
        font-size:2.2rem;font-family:monospace;border-radius:8px;
        text-align:right;min-height:32px;word-break:break-all;">{session_result}</div>""",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Operator selection
    op = st.selectbox(
        "Operation",
        ("add ➕", "subtract ➖", "multiply ✖️", "divide ➗", "power 🔷", "calculate 🧮"),
    )

    if "calculate 🧮" in op:
        expr = st.text_input("Expression (e.g. 2+3*4)", key="expr")
        if st.button("Evaluate", type="primary", use_container_width=True):
            if expr.strip():
                data = api_post("/calculate", {"expression": expr})
                if data:
                    st.session_state.result = data["result"]
                    st.rerun()
            else:
                st.warning("Enter an expression first.")
    else:
        op_map = {
            "add ➕": "add",
            "subtract ➖": "subtract",
            "multiply ✖️": "multiply",
            "divide ➗": "divide",
            "power 🔷": "power",
        }
        endpoint = op_map[op]
        c1, c2 = st.columns(2)
        with c1:
            a = st.number_input("A", key="num_a", step=1.0)
        with c2:
            b = st.number_input("B", key="num_b", step=1.0)
        if st.button(f"={op}", type="primary", use_container_width=True):
            data = api_post(f"/{endpoint}", {"a": float(a), "b": float(b)})
            if data:
                st.session_state.result = data["result"]
                st.rerun()

    # Quick digit buttons (send directly to /calculate)
    st.markdown("### Quick Calculate")
    digits = [
        ["7", "8", "9", "/"],
        ["4", "5", "6", "*"],
        ["1", "2", "3", "-"],
        ["C", "0", "=", "+"],
    ]
    for row in digits:
        cols = st.columns(len(row))
        for i, btn in enumerate(row):
            if cols[i].button(btn, use_container_width=True, key=f"btn_{btn}"):
                if btn == "C":
                    st.session_state.result = "0"
                    st.rerun()
                elif btn == "=":
                    expr = st.session_state.get("build_expr", "")
                    if expr:
                        data = api_post("/calculate", {"expression": expr})
                        if data:
                            st.session_state.result = data["result"]
                            st.session_state.build_expr = ""
                            st.rerun()
                else:
                    current = st.session_state.get("build_expr", "")
                    st.session_state.build_expr = current + btn
                    st.rerun()

    st.caption(f"Building: {st.session_state.get('build_expr', '')}")


# ── History panel ───────────────────────────────────────────────────
with col_history:
    st.markdown("### 📜 History")
    history = fetch_history()
    if history:
        for entry in reversed(history):
            result = entry["result"]
            # Format nicely: remove .0 for integers
            result_str = f"{result:g}"
            st.markdown(
                f"""<div style="padding:6px 8px;margin-bottom:4px;
                background:#f0f2f6;border-radius:6px;font-size:0.85rem;">
                <strong>{entry['operation']}</strong><br/>
                {entry['details']} → <span style="color:#0a0;font-weight:bold;">{result_str}</span>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.caption("No calculations yet.")


# ── Footer ──────────────────────────────────────────────────────────
st.caption(f"Connected to {API_URL}")