import streamlit as st
from datetime import datetime

def render_legal_section():
    year = datetime.now().year
    
    # HTML Puro per layout perfetto
    st.markdown(f"""
    <div class="footer-container">
        <div class="footer-grid">
            
            <div class="footer-col footer-brand">
                <h3 style="margin:0; color:#2D3436;">sCore Lab</h3>
                <p>
                    <strong>Versione 1.0</strong> &middot; {year}<br>
                    SCORE nasce per aiutare i runner a comprendere meglio i propri allenamenti, 
                    privilegiando la qualità dello sforzo e la sostenibilità.
                </p>
                <div style="margin-top: 15px;">
                    <a href="#" style="font-size: 1.2rem; margin-right: 10px;">GitHub 🐙</a>
                    <a href="#" style="font-size: 1.2rem;">Strava 🏃</a>
                </div>
            </div>

            <div class="footer-col">
                <h4>Prodotto</h4>
                <ul>
                    <li><a href="#">Funzionalità</a></li>
                    <li><a href="#">Roadmap</a></li>
                    <li><a href="#">Engine 4.1</a></li>
                    <li><a href="#">Changelog</a></li>
                    <li><a href="#">Demo Mode</a></li>
                </ul>
            </div>

            <div class="footer-col">
                <h4>Risorse</h4>
                <ul>
                    <li><a href="#">Guida Introduttiva</a></li>
                    <li><a href="#">Metodo sCore</a></li>
                    <li><a href="#">Calcolatore Zone</a></li>
                    <li><a href="#">Glossario Metriche</a></li>
                    <li><a href="#">Supporto</a></li>
                </ul>
            </div>

            <div class="footer-col">
                <h4>Legale</h4>
                <ul>
                    <li><a href="#">Termini di Servizio</a></li>
                    <li><a href="#">Privacy Policy</a></li>
                    <li><a href="#">Cookie Policy</a></li>
                </ul>
                
                <h4 style="margin-top: 20px;">Lingua</h4>
                <ul>
                    <li><a href="#">🇮🇹 Italiano</a></li>
                    <li><a href="#">🇬🇧 English (Coming Soon)</a></li>
                </ul>
            </div>
            
        </div>

        <div class="footer-bottom">
            <p>
                SCORE è un progetto indipendente sviluppato in Python.<br>
                <em>Non è uno strumento medico e non sostituisce il parere di un professionista. 
                I dati vanno interpretati insieme alle sensazioni personali.</em>
            </p>
            <p>&copy; {year} sCore Lab. All rights reserved.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
