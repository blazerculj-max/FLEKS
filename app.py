import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="FLEKS Kalkulator", layout="wide")

st.title("📊 FLEKS Kalkulator Realnega Donosa")
st.markdown("Izračun donosa naložbenega zavarovanja z upoštevanjem stroškov.")

# --- STRANSKI MENI ZA VNOS ---
with st.sidebar:
    st.header("Nastavitve parametrov")
    leta = st.slider("Doba varčevanja (leti)", 5, 40, 20)
    mesecno_vplacilo = st.number_input("Mesečna premija (€)", value=50)
    zacetni_polog = st.number_input("Začetni enkratni polog (€)", value=1000)
    
    st.subheader("Stroški in Donos")
    donos_procent = st.slider("Predviden letni donos (%)", 0.0, 10.0, 5.0) / 100
    vstopni_stroski = st.slider("Vstopni stroški (%)", 0.0, 8.0, 3.0) / 100
    upravljalska_prov = st.slider("Upravljalska provizija letno (%)", 0.0, 2.5, 1.5) / 100

# --- LOGIKA IZRAČUNA ---
def izracun_donosa():
    meseci = leta * 12
    mesecni_donos = (1 + donos_procent)**(1/12) - 1
    mesecna_provizija = upravljalska_prov / 12
    
    glavnica = zacetni_polog * (1 - vstopni_stroski)
    podatki = []
    
    skupaj_vplacano = zacetni_polog

    for m in range(1, meseci + 1):
        # Mesečno vplačilo
        neto_vplacilo = mesecno_vplacilo * (1 - vstopni_stroski)
        glavnica += neto_vplacilo
        skupaj_vplacano += mesecno_vplacilo
        
        # Donos in provizija
        glavnica *= (1 + mesecni_donos - mesecna_provizija)
        
        podatki.append({
            "Mesec": m, 
            "Stanje": round(glavnica, 2),
            "Vplačano": skupaj_vplacano
        })
    
    return pd.DataFrame(podatki)

df = izracun_donosa()

# --- PRIKAZ REZULTATOV ---
col1, col2 = st.columns(2)
koncno_stanje = df["Stanje"].iloc[-1]
skupno_vplacilo = df["Vplačano"].iloc[-1]

col1.metric("Predvideno končno stanje", f"{koncno_stanje:,.2f} €")
col2.metric("Skupaj vplačano", f"{skupno_vplacilo:,.2f} €", delta=f"{koncno_stanje - skupno_vplacilo:,.2f} € donosa")

# Graf
fig = px.line(df, x="Mesec", y=["Stanje", "Vplačano"], 
              title="Rast premoženja skozi čas",
              labels={"value": "Znesek (€)", "variable": "Tip"})
st.plotly_chart(fig, use_container_width=True)
