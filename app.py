import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="FLEKS Analitik", layout="wide")

st.title("📊 FLEKS Analiza: Donos vs. Stroški")

# --- STRANSKI MENI ---
with st.sidebar:
    st.header("Vnos parametrov")
    # Zamenjano: number_input namesto sliderja
    leta = st.number_input("Doba varčevanja (leti)", min_value=1, max_value=60, value=20, step=1)
    mesecno_vplacilo = st.number_input("Mesečna premija (min. 30 €)", min_value=30.0, value=100.0, step=10.0)
    zacetni_polog = st.number_input("Začetni enkratni polog (€)", min_value=0.0, value=0.0, step=500.0)
    zavarovalna_vsota = st.number_input("Zavarovalna vsota za primer smrti (€)", value=10000)
    
    # Zamenjano: number_input za donos
    donos_vnos = st.number_input("Predviden letni donos (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1)
    donos_procent = donos_vnos / 100

# --- KONSTANTE (Fiksni parametri FLEKS) ---
VSTOPNI_STROSKI = 0.01          # 1%
STROSEK_ZAVAROVANJA = 2.0       # cca 2€
MEJA_ZAVAROVANJA = 3500.0       # Interni prag za simulacijo
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
    
    neto_redno_za_osnovo = (mesecno_vplacilo * (1 - VSTOPNI_STROSKI)) - STROSEK_ZAVAROVANJA
    
    for m in range(1, meseci + 1):
        v_strosek = mesecno_vplacilo * VSTOPNI_STROSKI
        trenutni_strosek_zav = STROSEK_ZAVAROVANJA if glavnica < MEJA_ZAVAROVANJA else 0
        
        glavnica += (mesecno_vplacilo - v_strosek - trenutni_strosek_zav)
        
        if m <= TRAJANJE_PROVIZIJE:
            osnova = min(m, STEVILO_VPLACIL_ZA_OSNOVO) * neto_redno_za_osnovo
            glavnica -= (osnova * PROVIZIJA_STOPNJA)
            
        glavnica *= (1 + mesecni_donos)
        bruto_brez_stroskov = (bruto_brez_stroskov + mesecno_vplacilo) * (1 + mesecni_donos)
        skupaj_vplacano += mesecno_vplacilo
        
        if m % 12 == 0 or m == 1:
            podatki.append({
                "Leto": int(m/12) if m >= 12 else 0,
                "Vplačano skupaj (€)": round(skupaj_vplacano, 2),
                "Realno stanje na računu (€)": round(glavnica, 2),
                "Zavarovalna vsota (€)": zavarovalna_vsota,
                "Izplačilo ob smrti (€)": round(max(glavnica, zavarovalna_vsota), 2)
            })
    
    return pd.DataFrame(podatki)

df_tabela = izracun_fleks()

# --- VIZUALIZACIJA ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Preglednica rasti po letih")
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)

with c2:
    st.subheader("Uporabljeni parametri FLEKS")
    st.markdown(f"""
    * **Vstopni stroški:** {VSTOPNI_STROSKI*100}% na vsa vplačila.
    * **Strošek zavarovanja:** variabilno cca 2 Eur / mesec.
    * **Upravljalska provizija:** {PROVIZIJA_STOPNJA*100}% mesečno na prvih {STEVILO_VPLACIL_ZA_OSNOVO} vplačil (obračunava se {TRAJANJE_PROVIZIJE/12:.0f} let).
    * **Zavarovalna vsota:** {zavarovalna_vsota:,.0f} € (minimalno zagotovljeno izplačilo ob smrti).
    """)
    
    st.info(f"**Predviden donos:** Izračun temelji na {donos_vnos}% letni stopnji rasti.")

st.write("---")
fig = px.area(df_tabela, x="Leto", y=["Realno stanje na računu (€)", "Vplačano skupaj (€)"], 
              title="Grafični prikaz akumulacije sredstev",
              labels={"value": "Znesek (€)", "variable": "Postavka"},
              color_discrete_map={"Realno stanje na računu (€)": "#00CC96", "Vplačano skupaj (€)": "#E5ECF6"})
st.plotly_chart(fig, use_container_width=True)
