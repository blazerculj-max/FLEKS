import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup

# Nastavitve strani
st.set_page_config(page_title="FLEKS Analitik", layout="wide")

# --- FUNKCIJA ZA PRIDOBIVANJE PODATKOV (SCRAPER) ---
@st.cache_data(ttl=86400)  # Osveži podatke enkrat na dan
def pridobi_donose_triglav():
    # Osnovni podatki (če scraper odpove)
    sklad_podatki = {
        "Ročni vnos": 5.0,
        "Triglav Svetovni": 8.1,
        "Triglav Drzni": 9.4,
        "Triglav Aktivni": 6.8,
        "Triglav Zmerni": 4.5,
        "Triglav Preudarni": 3.0
    }
    
    url = "https://www.triglavskladi.si/sl/tecajnica"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Iskanje tabel na strani
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 5:
                ime = cols[0].text.strip()
                # Poskusimo najti 10-letni donos (običajno v enem od zadnjih stolpcev)
                for c in cols:
                    if "%" in c.text and "," in c.text:
                        try:
                            val = float(c.text.replace('%', '').replace(',', '.').strip())
                            if "Triglav" in ime and val > 0:
                                sklad_podatki[ime] = val
                        except:
                            continue
    except:
        pass # Če stran ne dela, uporabi osnovne podatke zgoraj
    
    return sklad_podatki

# --- ZAČETEK APLIKACIJE ---
st.title("📊 FLEKS Analiza: Realni donos in stroški")

sklad_podatki = pridobi_donose_triglav()

# --- STRANSKI MENI ---
with st.sidebar:
    st.header("1. Izbira naložbe")
    izbran_sklad = st.selectbox("Sklad (vir donosa):", list(sklad_podatki.keys()))
    
    # Donos se predizpolni glede na sklad
    privzeti_donos = sklad_podatki[izbran_sklad]
    donos_vnos = st.number_input("Predviden letni donos (%)", min_value=0.0, max_value=20.0, value=privzeti_donos, step=0.1)
    
    st.write("---")
    st.header("2. Parametri police")
    leta = st.number_input("Doba varčevanja (leti)", min_value=1, max_value=60, value=20, step=1)
    mesecno_vplacilo = st.number_input("Mesečna premija (min. 30 €)", min_value=30.0, value=100.0, step=10.0)
    zacetni_polog = st.number_input("Začetni enkratni polog (€)", min_value=0.0, value=0.0, step=500.0)
    zavarovalna_vsota = st.number_input("Zavarovalna vsota ob smrti (€)", value=10000)

# --- MATEMATIČNE KONSTANTE FLEKS ---
VSTOPNI_STROSKI = 0.01
STROSEK_ZAVAROVANJA = 2.0
MEJA_ZAVAROVANJA = 3500.0
PROVIZIJA_STOPNJA = 0.0049
TRAJANJE_PROVIZIJE_MESECEV = 120
STEVILO_VPLACIL_ZA_OSNOVO = 24

def simulacija_fleks():
    meseci = int(leta * 12)
    m_donos = (1 + (donos_vnos/100))**(1/12) - 1
    
    # Začetni polog (le 1% vstopni)
    glavnica = zacetni_polog * (1 - VSTOPNI_STROSKI)
    skupaj_vplacano = zacetni_polog
    podatki = []
    
    # Osnova za 0.49% provizijo
    osnova_vplacilo = (mesecno_vplacilo * (1 - VSTOPNI_STROSKI)) - STROSEK_ZAVAROVANJA
    
    for m in range(1, meseci + 1):
        # 1. Redno vplačilo in vstopni
        v_strosek = mesecno_vplacilo * VSTOPNI_STROSKI
        trenutni_zav_strosek = STROSEK_ZAVAROVANJA if glavnica < MEJA_ZAVAROVANJA else 0
        
        glavnica += (mesecno_vplacilo - v_strosek - trenutni_zav_strosek)
        
        # 2. Provizija 0.49% na prvih 24 vplačil (traja 10 let)
        if m <= TRAJANJE_PROVIZIJE_MESECEV:
            st_vplacil = min(m, STEVILO_VPLACIL_ZA_OSNOVO)
            osnova_provizije = st_vplacil * osnova_vplacilo
            glavnica -= (osnova_provizije * PROVIZIJA_STOPNJA)
            
        # 3. Donos
        glavnica *= (1 + m_donos)
        skupaj_vplacano += mesecno_vplacilo
        
        if m % 12 == 0 or m == 1:
            podatki.append({
                "Leto": int(m/12) if m >= 12 else 0,
                "Vplačano skupaj (€)": round(skupaj_vplacano, 2),
                "Realno stanje (€)": round(glavnica, 2),
                "Zavarovalna vsota (€)": zavarovalna_vsota,
                "Izplačilo ob smrti (€)": round(max(glavnica, zavarovalna_vsota), 2)
            })
    return pd.DataFrame(podatki)

df = simulacija_fleks()

# --- PRIKAZ REZULTATOV ---
st.info(f"Analiza naložbe v sklad: **{izbran_sklad}** s predvidenim donosom **{donos_vnos}%**")

col_t, col_p = st.columns([2, 1])
with col_t:
    st.subheader("Tabelarični prikaz rasti")
    st.dataframe(df, use_container_width=True, hide_index=True)

with col_p:
    st.subheader("Parametri izračuna")
    st.markdown(f"""
    - **Vstopni stroški:** 1%
    - **Upravljalska provizija:** 0.49% / mesec
      *(10 let na prvih 24 vplačil)*
    - **Strošek zavarovanja:** variabilno cca 2 Eur / mesec
    - **Zavarovalna vsota:** {zavarovalna_vsota:,.0f} €
    """)

# Graf
st.write("---")
fig = px.area(df, x="Leto", y=["Realno stanje (€)", "Vplačano skupaj (€)"], 
              title="Grafična projekcija akumulacije sredstev",
              color_discrete_map={"Realno stanje (€)": "#00CC96", "Vplačano skupaj (€)": "#E5ECF6"})
st.plotly_chart(fig, use_container_width=True)
