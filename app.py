import streamlit as st
import pandas as pd
import plotly.express as px

# Nastavitve strani
st.set_page_config(page_title="FLEKS Kalkulator", layout="wide", page_icon="💰")

# --- NASLOV IN OPIS ---
st.title("🛡️ FLEKS Kalkulator Realnega Donosa")
st.markdown("Enostaven in natančen izračun stanja na polici ob upoštevanju vseh stroškov zavarovanja FLEKS.")

# --- STRANSKI MENI ZA VNOS ---
with st.sidebar:
    st.header("Parametri izračuna")
    
    # Ročni vnos donosa in dobe
    leta = st.number_input("Doba varčevanja (leti)", min_value=1, max_value=60, value=20, step=1)
    donos_vnos = st.number_input("Predviden letni donos (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1)
    
    st.write("---")
    # Vnosi za premije
    mesecno = st.number_input("Mesečna premija (€)", min_value=30.0, value=100.0, step=10.0)
    polog = st.number_input("Začetni enkratni polog (€)", min_value=0.0, value=0.0, step=500.0)
    vsota = st.number_input("Zavarovalna vsota za primer smrti (€)", value=10000)

# --- MATEMATIČNA LOGIKA (FLEKS SPECIFIKACIJE) ---
def izracun_fleks(leta, mesecno, polog, vsota, donos_letni):
    # Fiksni stroški po tvojih navodilih
    VSTOPNI_STROSKI = 0.01          # 1% na vsa vplačila
    STROSEK_ZAVAROVANJA = 2.0       # variabilno cca 2€
    MEJA_ZAVAROVANJA = 3500.0       # Fix strošek se neha nad tem zneskom
    PROVIZIJA_STOPNJA = 0.0049      # 0.49% upravljalska provizija
    TRAJANJE_PROVIZIJE = 120        # Traja 10 let (120 mesecev)
    OSNOVA_VPLACIL = 24             # Obračunava se na prvih 24 rednih vplačil
    
    meseci = int(leta * 12)
    m_donos = (1 + (donos_letni/100))**(1/12) - 1
    
    # Začetni polog: obremenjen le z 1% vstopnih stroškov
    glavnica = polog * (1 - VSTOPNI_STROSKI)
    skupaj_vplacano = polog
    podatki = []
    
    # Izračun neto rednega vplačila za osnovo provizije
    neto_redno_za_osnovo = (mesecno * (1 - VSTOPNI_STROSKI)) - STROSEK_ZAVAROVANJA
    
    for m in range(1, meseci + 1):
        # 1. Obračun vplačila in vstopnih stroškov (1%)
        v_strosek = mesecno * VSTOPNI_STROSKI
        # Strošek zavarovanja (2€), dokler stanje ne preseže 3500€
        trenutni_zav = STROSEK_ZAVAROVANJA if glavnica < MEJA_ZAVAROVANJA else 0
        
        glavnica += (mesecno - v_strosek - trenutni_zav)
        
        # 2. Posebna upravljalska provizija 0.49% (na prvih 24 vplačil, 10 let)
        if m <= TRAJANJE_PROVIZIJE:
            st_vplacil_v_osnovi = min(m, OSNOVA_VPLACIL)
            glavnica -= (st_vplacil_v_osnovi * neto_redno_za_osnovo * PROVIZIJA_STOPNJA)
            
        # 3. Pripis donosa
        glavnica *= (1 + m_donos)
        skupaj_vplacano += mesecno
        
        # Zapis za tabelo po letih
        if m % 12 == 0 or m == 1:
            podatki.append({
                "Leto": int(m/12) if m >= 12 else 0,
                "Vplačano skupaj (€)": round(skupaj_vplacano, 2),
                "Realno stanje na računu (€)": round(glavnica, 2),
                "Zavarovalna vsota (€)": vsota,
                "Izplačilo ob smrti (€)": round(max(glavnica, vsota), 2)
            })
            
    return pd.DataFrame(podatki)

# --- IZVEDBA IN PRIKAZ ---
df_rezultat = izracun_fleks(leta, mesecno, polog, vsota, donos_vnos)

# Glavni kazalniki (Metrike)
c1, c2, c3 = st.columns(3)
koncno_stanje = df_rezultat["Realno stanje na računu (€)"].iloc[-1]
skupaj_vplacano = df_rezultat["Vplačano skupaj (€)"].iloc[-1]
cisti_donos = koncno_stanje - skupaj_vplacano

c1.metric("Predvideno stanje", f"{koncno_stanje:,.2f} €")
c2.metric("Skupaj vplačano", f"{skupaj_vplacano:,.2f} €")
c3.metric("Čisti donos", f"{cisti_donos:,.2f} €", delta=f"{donos_vnos}% letno")

st.write("---")

# Tabela in Parametri
col_tab, col_par = st.columns([2, 1])

with col_tab:
    st.subheader("Pregled rasti po letih")
    st.dataframe(df_rezultat, use_container_width=True, hide_index=True)

with col_par:
    st.subheader("Upoštevani stroški")
    st.markdown(f"""
    - **Vstopni stroški:** 1%
    - **Strošek zavarovanja:** variabilno cca 2 Eur / mesec
    - **Upravljalska provizija:** 0.49% mesečno
      *(na prvih 24 rednih vplačil, prvih 10 let)*
    - **Začetni polog:** brez dodatnih provizij (le 1% vstopni)
    """)
    st.info("💡 Izplačilo ob smrti je zavarovalna vsota ali stanje na računu (kar je višje).")

# Graf
st.write("---")
fig = px.area(df_rezultat, x="Leto", y=["Realno stanje na računu (€)", "Vplačano skupaj (€)"],
              title="Projekcija akumulacije sredstev",
              labels={"value": "Znesek (€)", "variable": "Postavka"},
              color_discrete_map={"Realno stanje na računu (€)": "#00CC96", "Vplačano skupaj (€)": "#E5ECF6"})
st.plotly_chart(fig, use_container_width=True)
