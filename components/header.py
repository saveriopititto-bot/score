import streamlit as st

def render_header(user_name="Demo Runner", member_label="Premium Member",
                   avatar_url="https://picsum.photos/100/100"):
    """Responsive header: logo, nav (desktop+mobile), controls, user profile."""
    st.markdown(f"""
    <header style="background:rgba(255,255,255,0.9); backdrop-filter:blur(8px); position:sticky; top:0; z-index:50; border-bottom:1px solid #f3f4f6; box-shadow:0 1px 2px rgba(0,0,0,0.04);">
      <div style="max-width:1200px; margin:0 auto; padding:8px 16px;">
        <div class="header-inner" style="display:flex; align-items:center; justify-content:space-between; gap:16px;">

          <div style="display:flex; align-items:center; gap:32px;">
            <div style="display:flex; flex-direction:column; flex-shrink:0;">
              <div style="font-size:24px; font-weight:800; letter-spacing:-0.02em; line-height:1;">
                <span style="color:#FB4141;">s</span><span style="color:#FF8E53;">C</span><span style="color:#FFC145;">o</span><span style="color:#FB4141;">re</span>
              </div>
              <div style="font-size:9.6px; color:#9ca3af; letter-spacing:0.2em; font-weight:600; text-transform:uppercase; margin-top:2px; white-space:nowrap;">Corri. Analizza. Evolvi</div>
            </div>

            <nav class="nav-desktop" style="align-items:center; gap:4px;">
              <button class="navbtn" style="display:flex; align-items:center; gap:6px; padding:6px 12px; border-radius:8px; font-size:12px; font-weight:600; border:none; cursor:pointer; background:#f3f4f6; color:#111827;">
                <span class="mi" style="color:#60a5fa; font-size:18px;">analytics</span>Breakdown
              </button>
              <button class="navbtn" style="display:flex; align-items:center; gap:6px; padding:6px 12px; border-radius:8px; font-size:12px; font-weight:600; border:none; cursor:pointer; background:transparent; color:#6b7280;">
                <span class="mi" style="color:#c084fc; font-size:18px;">bug_report</span>Bug/Idea
              </button>
              <button class="navbtn" style="display:flex; align-items:center; gap:6px; padding:6px 12px; border-radius:8px; font-size:12px; font-weight:600; border:none; cursor:pointer; background:transparent; color:#6b7280;">
                <span class="mi" style="color:#22d3ee; font-size:18px;">menu_book</span>Legenda
              </button>
            </nav>
          </div>

          <nav class="nav-mobile" style="align-items:center; gap:4px; width:100%; order:3; overflow-x:auto;">
            <button class="navbtn" style="display:flex; align-items:center; gap:6px; padding:6px 12px; border-radius:8px; font-size:12px; font-weight:600; border:none; cursor:pointer; background:#f3f4f6; color:#111827; white-space:nowrap;">
              <span class="mi" style="color:#60a5fa; font-size:18px;">analytics</span>Breakdown
            </button>
            <button class="navbtn" style="display:flex; align-items:center; gap:6px; padding:6px 12px; border-radius:8px; font-size:12px; font-weight:600; border:none; cursor:pointer; background:transparent; color:#6b7280; white-space:nowrap;">
              <span class="mi" style="color:#c084fc; font-size:18px;">bug_report</span>Bug/Idea
            </button>
            <button class="navbtn" style="display:flex; align-items:center; gap:6px; padding:6px 12px; border-radius:8px; font-size:12px; font-weight:600; border:none; cursor:pointer; background:transparent; color:#6b7280; white-space:nowrap;">
              <span class="mi" style="color:#22d3ee; font-size:18px;">menu_book</span>Legenda
            </button>
          </nav>

          <div class="header-controls" style="display:flex; align-items:center;">
            <div style="display:flex; align-items:center; gap:12px; background:rgba(249,250,251,0.5); padding:4px; border-radius:999px; border:1px solid #f3f4f6;">
              <button class="ctrlbtn" style="display:flex; align-items:center; gap:6px; padding:4px 12px; background:#fff; border:1px solid #e5e7eb; border-radius:999px; box-shadow:0 1px 2px rgba(0,0,0,0.04); font-size:12px; font-weight:700; color:#374151; cursor:pointer;">
                <span class="mi" style="color:#3b82f6; font-size:14px;">calendar_today</span><span class="ctrl-label" style="white-space:nowrap;">90 gg</span><span class="mi ctrl-label" style="color:#9ca3af; font-size:14px;">expand_more</span>
              </button>
              <div style="width:1px; height:16px; background:#d1d5db;"></div>
              <button class="ctrlbtn" style="display:flex; align-items:center; gap:6px; padding:4px 12px; background:transparent; border:none; border-radius:999px; font-size:12px; font-weight:700; color:#4b5563; cursor:pointer;">
                <span class="mi" style="color:#eab308; font-size:16px;">emoji_events</span><span class="ctrl-label" style="white-space:nowrap;">Awards</span>
              </button>
              <button class="ctrlbtn" style="display:flex; align-items:center; gap:6px; padding:4px 12px; background:transparent; border:none; border-radius:999px; font-size:12px; font-weight:700; color:#4b5563; cursor:pointer;">
                <span class="mi" style="color:#fbbf24; font-size:16px;">folder</span><span class="ctrl-label" style="white-space:nowrap;">Archivio</span>
              </button>
            </div>

            <div style="height:24px; width:1px; background:#e5e7eb;"></div>

            <div style="display:flex; align-items:center; gap:12px;">
              <div class="user-text" style="flex-direction:column; align-items:flex-end;">
                <span style="font-size:12px; font-weight:700; color:#1f2937;">{user_name}</span>
                <span style="font-size:10px; color:#9ca3af; font-weight:500;">{member_label}</span>
              </div>
              <div style="height:36px; width:36px; border-radius:999px; background:#e5e7eb; box-shadow:0 1px 2px rgba(0,0,0,0.04); overflow:hidden; cursor:pointer;">
                <img src="{avatar_url}" alt="User" style="height:100%; width:100%; object-fit:cover;">
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
    """, unsafe_allow_html=True)
