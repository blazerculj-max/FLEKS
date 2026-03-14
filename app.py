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
    donos_procent = st.slider("Predviden letni donos (%)", 0.0, 10.0, 5.0) / 100

# --- KONSTANTE FLEKS ---
VSTOPNI_STROSKI = 0.01  # 1%
FIX_ZAVAROVANJE = 2.0   # 2€ do 3500€ stanja
PROVIZIJA_24 = 0.0049   # 0.49% mesečno na prvih 24 rednih vplačil
TRAJANJE_PROVIZIJE_24 = 120 # 10 let (v mesecih)

def izracun_fleks():
    meseci = int(leta * 12)
    mesecni_donos = (1 + donos_procent)**(1/12) - 1
    
    # Začetni polog: samo vstopni stroški, brez 0.49% provizije
    glavnica = zacetni_polog * (1 - VSTOPNI_STROSKI)
    bruto_brez_stroskov = zacetni_polog 
    
    skupaj_vplacano = zacetni_polog
    podatki = []
    
    # Neto osnova za mesečno provizijo (samo od rednih vplačil)
    # Redno vplačilo - 1% - 2€ (dokler je stanje pod 3500)
    # Ker se 2€ lahko spreminja, za osnovo provizije vzamemo fiksni neto del rednega vplačila
    neto_redno_za_osnovo = (mesecno_vplacilo * (1 - VSTOPNI_STROSKI)) - FIX_ZAVAROVANJE
    
    for m in range(1, meseci + 1):
        # 1. Redno mesečno vplačilo in vstopni stroški
        vstopni = mesecno_vplacilo * VSTOPNI_STROSKI
        strosek_zavarovanja = FIX_ZAVAROVANJE if glavnica < 3500 else 0
        
        neto_vplacilo = mesecno_vplacilo - vstopni - strosek_zavarovanja
        glavnica += neto_vplacilo
        
        # 2. Obračun posebne 0.49% provizije (velja le za redna vplačila)
        if m <= TRAJANJE_PROVIZIJE_24:
            stevilka_vplacil_za_osnovo = min(m, 24)
            osnova = stevilka_vplacil_za_osnovo * neto_redno_za_osnovo
            strosek_provizije_24 = osnova * PROVIZIJA_24
            glavnica -= strosek_provizije_24
            
        # 3. Pripis donosa na celotno stanje (polog + redna vplačila)
        glavnica *= (1 + mesecni_donos)
        
        # 4. Primerjava (Bruto svet brez kakršnihkoli stroškov)
        bruto_brez_stroskov += mesecno_vplacilo
        bruto_brez_stroskov *= (1 + mesecni_donos)
        
        skupaj_vplacano += mesecno_vplacilo
        
        podatki.append({
            "Leto": round(m/12, 1),
            "Realno Stanje": round(glavnica, 2),
            "Brez Stroškov": round(bruto_brez_stroskov, 2),
            "Vplačano": skupaj_vplacano
        })
    
    return pd.DataFrame(podatki)

df = izracun_fleks()

# --- PRIKAZ REZULTATOV ---
koncno_stanje = df["Realno Stanje"].iloc[-1]
brez_stroskov = df["Brez Stroškov"].iloc[-1]
vpliv_stroskov = brez_stroskov - koncno_stanje
skupaj_vplacano = df["Vplačano"].iloc[-1]

c1, c2, c3 = st.columns(3)
c1.metric("Predvideno stanje", f"{koncno_stanje:,.2f} €")
c2.metric("Skupaj vplačano", f"{skupaj_vplacano:,.2f} €")
c3.metric("Čisti donos", f"{koncno_stanje - skupaj_vplacano:,.2f} €")

st.write("---")
st.subheader("Analiza stroškov")
col_a, col_b = st.columns(2)

with col_a:
    st.info(f"**Vpliv stroškov:** Stroški in provizije so zmanjšali končni znesek za **{vpliv_stroskov:,.2f} €** v primerjavi z bruto investicijo.")
with col_b:
    delez = (koncno_stanje / brez_stroskov) * 100
    st.warning(f"**Učinkovitost:** Stranka obdrži **{round(delez, 1)}%** vseh donosov in vplačil.")

# Graf
fig = px.area(df, x="Leto", y=["Brez Stroškov", "Realno Stanje"], 
              title="Primerjava: Bruto investicija vs. Realno stanje FLEKS",
              labels={"value": "Znesek (€)", "variable": "Legenda"},
              color_discrete_map={"Brez Stroškov": "#E5ECF6", "Realno Stanje": "#00CC96"})
st.plotly_chart(fig, use_container_width=True)
