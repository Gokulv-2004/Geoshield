# pages/3_Login.py — Simple, clean login (no duplicates, no extra boxes)

import os
import streamlit as st
from config import get_supabase, OAUTH_REDIRECT
# NOTE: skip render_top_nav on this page to avoid duplicate "Sig/Log" chips
from style import apply_theme

# 1) Config FIRST
st.set_page_config(page_title="🔐 Login — GeoShield", layout="centered", page_icon="")
apply_theme(title="🔐 Login — GeoShield", hide_sidebar=True)

# 2) Minimal CSS — keep palette, kill random boxes, make buttons readable
st.markdown("""
<style>
:root{ --beige:#efe5d3; --ink:#2b2b2b; --blue1:#0f172a; --blue2:#1e3a8a; --border:#c9bda8; --card:#EBDCC7; }
html,body,[data-testid="stAppViewContainer"]{ background:var(--beige); color:var(--ink); }
.gs-hero{
  padding:18px; margin:8px 0 18px; border-radius:16px;
  background:linear-gradient(135deg,var(--blue1),var(--blue2));
  color:#e6eef7; border:1px solid #334155; text-align:center; box-shadow:0 8px 24px rgba(15,23,42,.25);
}
.gs-hero h1{ margin:0; font-size:28px }
.gs-hero p{ margin:6px 0 0; opacity:.9; font-size:14px }

.gs-card{
  padding:18px; border:1px solid var(--border); border-radius:14px; background:var(--card);
  box-shadow:0 8px 16px rgba(0,0,0,.05);
}
.divider{ height:1px; background:#00000022; border-radius:1px; margin:12px 0 16px }

/* Make page_link / buttons readable and wide */
[data-testid="stPageLink"] button,
button[kind="primary"],
button[kind="secondary"]{
  min-width: 220px; white-space: nowrap; font-weight: 700; letter-spacing:.2px;
  border-radius:12px !important; border:1px solid var(--border) !important;
  background: var(--card) !important; color: var(--ink) !important;
}

/* Remove styling from empty containers to avoid "mystery boxes" */
section.main > div:has(> div:empty){ background:transparent; border:none; box-shadow:none }
</style>
""", unsafe_allow_html=True)

# 3) Hero
st.markdown("""
<div class="gs-hero">
  <h1>🔐 GeoShield Login</h1>
  <p>Login with email/password or sign in with Google</p>
</div>
""", unsafe_allow_html=True)

# 4) Supabase bootstrap
supabase = get_supabase()
if supabase is None:
    st.error("❌ Supabase is not configured. Add SUPABASE_URL and SUPABASE_KEY to .env")
    st.stop()

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@geoshield.com")

# 5) OAuth hash → query bridge
st.markdown("""
<script>
(function() {
  try {
    const h = window.location.hash;
    if (h && h.includes('access_token=')) {
      const hp = new URLSearchParams(h.substring(1));
      const sp = new URLSearchParams(window.location.search);
      for (const [k,v] of hp.entries()) sp.set(k,v);
      const newUrl = window.location.pathname + "?" + sp.toString();
      window.history.replaceState({}, "", newUrl);
      if (!sessionStorage.getItem("gs_oauth_reloaded")){
        sessionStorage.setItem("gs_oauth_reloaded","1"); window.location.reload();
      }
    }
  } catch (e) { console.log(e); }
})();
</script>
""", unsafe_allow_html=True)

# 6) Handle OAuth redirect
def handle_oauth_callback():
    try:
        q = st.query_params
        if "access_token" not in q: return
        if st.session_state.get("oauth_done"): return

        access_token = q["access_token"]
        refresh_token = q.get("refresh_token","")
        auth_res = supabase.auth.set_session(access_token, refresh_token)
        user = getattr(auth_res, "user", None)
        if not user or not user.email:
            st.error("OAuth failed: No user info.")
            return
        st.session_state["user"] = user.email
        st.session_state["oauth_done"] = True
        st.query_params = {}  # scrub tokens

        st.switch_page("pages/10_Admin_dashboard.py" if user.email == ADMIN_EMAIL else "pages/3_Overview.py")
    except Exception as e:
        st.error(f"OAuth failed: {e}")

handle_oauth_callback()

# 7) Simple login card
st.markdown('<div class="gs-card">', unsafe_allow_html=True)

method = st.radio("Choose login method", ["Email & Password", "Google Login"], horizontal=True, key="login_method")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

if method == "Email & Password":
    email = st.text_input("📧 Email", key="login_email", placeholder="you@example.com")
    password = st.text_input("🔐 Password", key="login_password", type="password", placeholder="Enter password")
    remember = st.checkbox("Remember me", key="login_remember")

    if st.button("🔓 Login", key="btn_login", use_container_width="stretch"):
        if not email or not password:
            st.warning("Please enter both email and password.")
        else:
            try:
                supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state["user"] = email
                st.toast(f"✅ Welcome back, {email}")
                st.switch_page("pages/10_Admin_dashboard.py" if email == ADMIN_EMAIL else "pages/3_Overview.py")
            except Exception as e:
                st.error(f"❌ Login failed: {e}")

    st.page_link("pages/1_Signup.py", label="📝 Don’t have an account? Create one")

else:
    st.write("Use your Google account to sign in.")
    if st.button("🔑 Login with Google", key="btn_google", use_container_width="stretch"):
        try:
            resp = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": { "redirect_to": OAUTH_REDIRECT, "scopes": "email profile" }
            })
            st.markdown(f'<a href="{resp.url}">Continue to Google</a>', unsafe_allow_html=True)
            st.markdown(f'<script>window.location.href = "{resp.url}";</script>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"OAuth error: {e}")

st.markdown('</div>', unsafe_allow_html=True)

st.caption("Tip: Admin users are redirected to the Admin Dashboard automatically after login.")
