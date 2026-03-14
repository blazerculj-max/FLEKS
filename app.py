import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="FLEKS Analitik", layout="wide")

st.title("📊 FLEKS Analiza: Donos vs. Stroški")

# --- STRANSKI MENI ---
with st.sidebar:
    st.header("Vnos podatkov")
    leta = st.slider("Doba varčevanja (leti)", 10, 40, 20)
    mesecno_vplacilo = st.number_input("Mesečna premija (€)", value=100)
    zacetni_polog = st.number_input("Začetni enkratni polog (€)", value=0)
    donos_procent = st.slider("Predviden letni donos (%)", 0.0, 10.0, 5.0) / 100

# --- KONSTANTE FLEKS ---
VSTOPNI_STROSKI = 0.01  # 1%
FIX_ZAVAROVANJE = 2.0   # 2€ do 3500€ stanja
PROVIZIJA_24 = 0.0049   # 0.49% mesečno na prvih 24 vplačil
TRAJANJE_PROVIZIJE_24 = 120 # 10 let (v mesecih)

def izracun_fleks():
    meseci = leta * 12
    mesecni_donos = (1 + donos_procent)**(1/12) - 1
    
    glavnica = zacetni_polog * (1 - VSTOPNI_STROSKI)
    bruto_brez_stroskov = zacetni_polog # Za primerjavo vpliva stroškov
    
    skupaj_vplacano = zacetni_polog
    podatki = []
    
    # Prvih 24 neto vplačil (za osnovo provizije)
    neto_vplacilo_za_osnovo = (mesecno_vplacilo * (1 - VSTOPNI_STROSKI)) - FIX_ZAVAROVANJE
    
    for m in range(1, meseci + 1):
        # 1. Obračun vplačila in vstopnih stroškov
        vstopni = mesecno_vplacilo * VSTOPNI_STROSKI
        strosek_zavarovanja = FIX_ZAVAROVANJE if glavnica < 3500 else 0
        
        neto_vplacilo = mesecno_vplacilo - vstopni - strosek_zavarovanja
        glavnica += neto_vplacilo
        
        # 2. Obračun posebne 0.49% provizije (prvih 10 let)
        strosek_provizije_24 = 0
        if m <= TRAJANJE_PROVIZIJE_24:
            # Osnova so vplačila do 24. meseca
            stevilka_vplacil_za_osnovo = min(m, 24)
            osnova = stevilka_vplacil_za_osnovo * neto_vplacilo_za_osnovo
            strosek_provizije_24 = osnova * PROVIZIJA_24
            glavnica -= strosek_provizije_24
            
        # 3. Pripis donosa
        glavnica *= (1 + mesecni_donos)
        
        # 4. Primerjava (Bruto brez stroškov)
        bruto_brez_stroskov += mesecno_vplacilo
        bruto_brez_stroskov *= (1 + mesecni_donos)
        
        skupaj_vplacano += mesecno_vplacilo
        
        podatki.append({
            "Mesec": m, 
            "Realno Stanje": round(glavnica, 2),
            "Brez Stroškov": round(bruto_brez_stroskov, 2),
            "Vplačano": skupaj_vplacano
        })
    
    return pd.DataFrame(podatki)

df = izracun_fleks()

# --- PRIKAZ ---
koncno_stanje = df["Realno Stanje"].iloc[-1]
brez_stroskov = df["Brez Stroškov"].iloc[-1]
vpliv_stroskov = brez_stroskov - koncno_stanje

c1, c2, c3 = st.columns(3)
c1.metric("Realno stanje", f"{koncno_stanje:,.2f} €")
c2.metric("Vpliv stroškov", f"-{vpliv_stroskov:,.2f} €", delta_color="inverse")
c3.metric("Skupaj vplačano", f"{df['Vplačano'].iloc[-1]:,.2f} €")

st.info(f"Stroški so vam znižali končni donos za {round((vpliv_stroskov/brez_stroskov)*100, 1)}%.")

# Graf
fig = px.area(df, x="Mesec", y=["Brez Stroškov", "Realno Stanje"], 
              title="Razlika med bruto donosom in realnim stanjem (vpliv stroškov)",
              color_discrete_map={"Brez Stroškov": "lightgrey", "Realno Stanje": "#00CC96"})
st.plotly_chart(fig, use_container_width=True)
