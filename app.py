import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup

# Nastavitve strani
st.set_page_config(page_title="FLEKS Kalkulator", layout="wide", page_icon="📈")

# --- FUNKCIJA ZA SCRAPANJE TEČAJNICE ---
@st.cache_data(ttl=86400)
def pridobi_podatke_triglav():
    # Osnovni podatki, če scraper ne uspe dobiti podatkov v živo
    sklad_podatki = {
        "Ročni vnos": 5.0,
        "Triglav Svetovni": 8.5,
        "Triglav Drzni": 9.3,
        "Triglav Aktivni": 6.7,
        "Triglav Zmerni": 4.2,
        "Triglav Preudarni": 3.0
    }
    
    url = "https://www.triglavinvestments.si/tecajnica"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    ime = cols[0].text.strip()
                    if "Triglav" in ime:
                        # Poskusimo najti stolpec z donosom (iščemo številke v stolpcih)
                        for col in reversed(cols):
                            besedilo = col.text.replace('%', '').replace(',', '.').strip()
                            try:
                                donos_val = float(besedilo)
                                if 0.1 < donos_val < 35: # Filtriramo realne donose (npr. 5-letne)
                                    sklad_podatki[ime] = donos_val
                                    break
                            except ValueError:
                                continue
    except Exception:
        pass # V primeru napake uporabi fallback podatke
    
    return sklad_podatki

# --- LOGIKA IZRAČUNA FLEKS ---
def izracun_fleks(leta, mesecno, polog, vsota, donos_letni):
    # Konstante
    VSTOPNI_STROSKI = 0.01          # 1%
    STROSEK_ZAVAROVANJA = 2.0       # cca 2€
    MEJA_ZAVAROVANJA = 3500.0       # Meja za prenehanje fix stroška
    PROVIZIJA_STOPNJA = 0.0049      # 0.49%
    TRAJANJE_PROVIZIJE = 120        # 10 let
    OSNOVA_VPLACIL = 24             # Na prvih 24 vplačil
    
    meseci = int(leta * 12)
    m_donos = (1 + (donos_letni/100))**(1/12) - 1
    
    # Začetni polog: samo vstopni stroški 1%
    glavnica = polog * (1 - VSTOPNI_STROSKI)
    skupaj_vplacano = polog
    podatki = []
    
    # Neto osnova za mesečno provizijo (od rednih vplačil)
    neto_redno_za_osnovo = (mesecno * (1 - VSTOPNI_STROSKI)) - STROSEK_ZAVAROVANJA
    
    for m in range(1, meseci + 1):
        # 1. Stroški vplačila
        v_strosek = mesecno * VSTOPNI_STROSKI
        trenutni_zav = STROSEK_ZAVAROVANJA if glavnica < MEJA_ZAVAROVANJA else 0
        
        glavnica += (mesecno - v_strosek - trenutni_zav)
        
        # 2. Upravljalska provizija 0.49% (10 let na prvih 24 enot)
        if m <= TRAJANJE_PROVIZIJE:
            st_enot = min(m, OSNOVA_VPLACIL)
            glavnica -= (st_enot * neto_redno_za_osnovo * PROVIZIJA_STOPNJA)
            
        # 3. Pripis donosa
        glavnica *= (1 + m_donos)
        skupaj_vplacano += mesecno
        
        # Zapis za tabelo (vsako leto)
        if m % 12 == 0 or m == 1:
            podatki.append({
                "Leto": int(m/12) if m >= 12 else 0,
                "Vplačano skupaj (€)": round(skupaj_vplacano, 2),
                "Realno stanje na računu (€)": round(glavnica, 2),
                "Zavarovalna vsota (€)": vsota,
                "Izplačilo ob smrti (€)": round(max(glavnica, vsota), 2)
            })
            
    return pd.DataFrame(podatki)

# --- UPORABNIŠKI VMESNIK ---
st.title("🛡️ FLEKS Kalkulator Realnega Donosa")
st.markdown("Aplikacija za prodajalce zavarovanj: izračun stanja ob upoštevanju vseh stroškov.")

sklad_podatki = pridobi_podatke_triglav()

with st.sidebar:
    st.header("Vnos podatkov")
    
    # Izbira sklada in donosa
    izbran_sklad = st.selectbox("Izberi sklad za donos:", list(sklad_podatki.keys()))
    donos_vnos = st.number_input("Predviden letni donos (%)", 
                                 min_value=0.0, max_value=20.0, 
                                 value=sklad_podatki[izbran_sklad], step=0.1)
    
    st.write("---")
    leta = st.number_input("Doba varčevanja (leti)", min_value=1, max_value=60, value=20)
    mesecno = st.number_input("Mesečna premija (€)", min_value=30.0, value=100.0, step=10.0)
    polog = st.number_input("Začetni enkratni polog (€)", min_value=0.0, value=0.0, step=500.0)
    vsota = st.number_input("Zavarovalna vsota za primer smrti (€)", value=10000)

# Izračun
df_rezultat = izracun_fleks(leta, mesecno, polog, vsota, donos_vnos)

# Prikaz rezultatov
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Projekcija stanja po letih")
    st.dataframe(df_rezultat, use_container_width=True, hide_index=True)

with col2:
    st.subheader("Uporabljeni parametri")
    st.write(f"**Sklad:** {izbran_sklad}")
    st.write(f"**Letni donos:** {donos_vnos}%")
    st.markdown("""
    - **Vstopni stroški:** 1% na vsa vplačila
    - **Upravljalska provizija:** 0.49% (prvih 24 enot, 10 let)
    - **Zavarovanje:** variabilno cca 2 Eur / mesec
    """)
    
    koncno_stanje = df_rezultat["Realno stanje na računu (€)"].iloc[-1]
    skupaj_vplacano = df_rezultat["Vplačano skupaj (€)"].iloc[-1]
    
    st.metric("Končno stanje", f"{koncno_stanje:,.2f} €")
    st.metric("Skupaj vplačano", f"{skupaj_vplacano:,.2f} €")

# Graf
st.write("---")
fig = px.area(df_rezultat, x="Leto", y=["Realno stanje na računu (€)", "Vplačano skupaj (€)"],
              title="Rast premoženja skozi čas",
              labels={"value": "Znesek (€)", "variable": "Postavka"},
              color_discrete_map={"Realno stanje na računu (€)": "#00CC96", "Vplačano skupaj (€)": "#E5ECF6"})
st.plotly_chart(fig, use_container_width=True)
