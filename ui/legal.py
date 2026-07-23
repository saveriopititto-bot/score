import streamlit as st
from datetime import datetime

def render_legal_section():
    year = datetime.now().year
    
    st.markdown(f"""
    <footer class="mt-auto border-t border-gray-100 bg-white py-6 mt-12">
      <div class="container mx-auto px-4 flex flex-col items-center text-center">
        
        <!-- Main Info Block - Centered -->
        <div class="flex flex-col items-center gap-4 mb-6">
          <div class="space-y-1">
            <h3 class="text-xs font-bold text-gray-900">sCore Lab v1.0</h3>
            <p class="text-[10px] text-gray-500">
              Powered by <strong class="text-gray-700">sCorengine 4.1</strong>
            </p>
            <p class="text-[10px] text-gray-500">
              Il nuovo standard per l'analisi della corsa.
            </p>
          </div>
        </div>

        <!-- Bottom Copyright Block - Centered -->
        <div class="border-t border-gray-100 pt-4 w-full flex flex-col items-center gap-4">
          
          <!-- Legale Section -->
          <div class="flex flex-col items-center space-y-1">
            <h3 class="text-xs font-bold text-gray-900">Legale</h3>
            <div class="flex gap-3">
                <a href="#" class="flex items-center gap-1 text-[10px] text-gray-600 hover:text-score-red transition-colors">
                    <span class="material-icons-round text-yellow-500 text-[12px]">lock</span> Privacy Policy
                </a>
                <a href="#" class="flex items-center gap-1 text-[10px] text-gray-600 hover:text-score-red transition-colors">
                    <span class="material-icons-round text-score-orange text-[12px]">description</span> Terms of Service
                </a>
            </div>
          </div>

          <!-- Copyright Text -->
          <div class="flex flex-col items-center text-[9px] text-gray-400 gap-1.5">
            <p>© {year} Progetto indipendente sviluppato in Python</p>
            <p>Non è uno strumento medico. Interpreta i dati con consapevolezza.</p>
            <p>All rights reserved - sCore Lab</p>
          </div>
        </div>
      </div>
    </footer>
    """, unsafe_allow_html=True)
