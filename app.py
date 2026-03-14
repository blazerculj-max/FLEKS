import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="FLEKS Analitik", layout="wide")

st.title("📊 FLEKS Analiza: Donos vs. Stroški")

# --- STRANSKI MENI ---
with st.sidebar:
    st.header("Vnos parametrov")
    leta = st.slider("Doba varčevanja (leti)", 1, 60, 20)
    mesecno_vplacilo = st.number_input("Mesečna premija (min. 30 €)", min_value=30.0, value=100.0, step=10.0)
    zacetni_polog = st.number_input("Začetni enkratni polog (€)", min_value=0.0, value=0.0, step=500.0)
    zavarovalna_vsota = st.number_input("Zavarovalna vsota za primer smrti (€)", value=10000)
    donos_procent = st.slider("Predviden letni donos (%)", 0.0, 10.0, 5.0) / 100

# --- KONSTANTE (Fiksni parametri FLEKS) ---
VSTOPNI_STROSKI = 0.01          # 1%
STROSEK_ZAVAROVANJA = 2.0       # 2€
MEJA_ZAVAROVANJA = 3500.0       # Strošek do 3500€ stanja
PROVIZIJA_STOPNJA = 0.0049      # 0.49%
TRAJANJE_PROVIZIJE = 120        # 10 let
STEVILO_VPLACIL_ZA_OSNOVO = 24  # Provizija na prvih 24 vplačil

def izracun_fleks():
    meseci = int(leta * 12)
    mesecni_donos = (1 + donos_procent)**(1/12) - 1
    
    glavnica = zacetni_polog * (1 - VSTOPNI_STROSKI)
    bruto_brez_stroskov = zacetni_polog 
    skupaj_vplacano = zacetni_polog
    podatki = []
    
    # Neto osnova za 0.49% provizijo (od prvih 24 rednih vplačil)
    neto_redno_za_osnovo = (mesecno_vplacilo * (1 - VSTOPNI_STROSKI)) - STROSEK_ZAVAROVANJA
    
    for m in range(1, meseci + 1):
        # 1. Stroški vplačila
        v_strosek = mesecno_vplacilo * VSTOPNI_STROSKI
        trenutni_strosek_zav = STROSEK_ZAVAROVANJA if glavnica < MEJA_ZAVAROVANJA else 0
        
        glavnica += (mesecno_vplacilo - v_strosek - trenutni_strosek_zav)
        
        # 2. Posebna upravljalska provizija (0.49%)
        if m <= TRAJANJE_PROVIZIJE:
            osnova = min(m, STEVILO_VPLACIL_ZA_OSNOVO) * neto_redno_za_osnovo
            glavnica -= (osnova * PROVIZIJA_STOPNJA)
            
        # 3. Donos
        glavnica *= (1 + mesecni_donos)
        
        # Bruto za primerjavo
        bruto_brez_stroskov = (bruto_brez_stroskov + mesecno_vplacilo) * (1 + mesecni_donos)
        skupaj_vplacano += mesecno_vplacilo
        
        if m % 12 == 0 or m == 1: # Zapisujemo vsako leto za tabelo
            podatki.append({
                "Leto": int(m/12) if m >= 12 else 0,
                "Vplačano skupaj": round(skupaj_vplacano, 2),
                "Realno stanje na računu": round(glavnica, 2),
                "Zavarovalna vsota": zavarovalna_vsota,
                "Vrednost police v primeru smrti": round(max(glavnica, zavarovalna_vsota), 2)
            })
    
    return pd.DataFrame(podatki)

df_tabela = izracun_fleks()

# --- VIZUALIZACIJA ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Tabela rasti premoženja")
    st.table(df_tabela)

with c2:
    st.subheader("Uporabljeni parametri")
    st.markdown(f"""
    * **Vstopni stroški:** {VSTOPNI_STROSKI*100}%
    * **Strošek zavarovanja:** {STROSEK_ZAVAROVANJA} € / mesec
        *(preneha, ko stanje preseže {MEJA_ZAVAROVANJA} €)*
    * **Upravljalska provizija:** {PROVIZIJA_STOPNJA*100}% mesečno
        *(na prvih {STEVILO_VPLACIL_ZA_OSNOVO} vplačil, traja {TRAJANJE_PROVIZIJE/12:.0f} let)*
    * **Zavarovalna vsota:** {zavarovalna_vsota:,.0f} €
    """)
    
    st.info("💡 **Nasvet:** Pri naložbenih zavarovanjih je v primeru smrti izplačana zavarovalna vsota ali vrednost premoženja na računu (kar je višje).")

st.write("---")
# Opcijsko: Graf spodaj
df_graf = izracun_fleks() # Za graf bi lahko uporabili bolj gosto mrežo podatkov
fig = px.line(df_tabela, x="Leto", y=["Realno stanje na računu", "Vplačano skupaj"], title="Pregled rasti")
st.plotly_chart(fig, use_container_width=True)
