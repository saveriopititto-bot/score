import streamlit as st

def render_footer():
    st.markdown("""
    <footer style="margin-top:auto; border-top:1px solid #f3f4f6; background:#fff; padding:12px 0;">
      <div style="max-width:1200px; margin:0 auto; padding:0 16px; display:flex; flex-direction:column; align-items:center; text-align:center;">

        <div style="display:flex; flex-wrap:wrap; align-items:flex-start; justify-content:center; gap:48px; width:100%;">
          <div style="display:flex; flex-direction:column; gap:2px;">
            <h3 style="font-size:12px; font-weight:700; color:#111827; margin:0;">sCore Lab v1.0</h3>
            <p style="font-size:10px; color:#6b7280; margin:0;">Powered by <strong style="color:#374151;">sCorengine 4.1</strong></p>
            <p style="font-size:10px; color:#6b7280; margin:0;">Il nuovo standard per l'analisi della corsa.</p>
          </div>
          <div style="display:flex; flex-direction:column; align-items:center; gap:2px;">
            <h3 style="font-size:12px; font-weight:700; color:#111827; margin:0;">Legale</h3>
            <div style="display:flex; gap:12px;">
              <a href="#" style="display:flex; align-items:center; gap:4px; font-size:10px; text-decoration:none;"><span class="mi" style="color:#eab308; font-size:12px;">lock</span>Privacy Policy</a>
              <a href="#" style="display:flex; align-items:center; gap:4px; font-size:10px; text-decoration:none;"><span class="mi" style="color:#fb923c; font-size:12px;">description</span>Terms of Service</a>
            </div>
            <p style="margin:2px 0 0; font-size:9px; color:#9ca3af;">Non è uno strumento medico. Interpreta i dati con consapevolezza.</p>
          </div>
        </div>

        <div style="width:100%; display:flex; flex-direction:column; align-items:center; font-size:9px; color:#9ca3af; margin-top:4px;">
          <p style="margin:0; display:flex; gap:6px; flex-wrap:wrap; justify-content:center;"><span>© 2026 Progetto indipendente sviluppato in Python</span><span>All rights reserved - sCore Lab</span></p>
        </div>
      </div>
    </footer>
    """, unsafe_allow_html=True)
