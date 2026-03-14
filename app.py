import streamlit as st
import pandas as pd
import plotly.express as px

# Nastavitve strani za lepši prikaz
st.set_page_config(
    page_title="FLEKS Premium Kalkulator",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- STILIZACIJA (CSS) ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_stdio=True)

# --- NASLOVNA VRSTICA ---
col_logo, col_text = st.columns([1, 5])
with col_text:
    st.title("FLEKS Premium Analitik")
    st.caption("Profesionalno orodje za simulacijo naložbenega zavarovanja")

st.write("---")

# --- STRANSKI MENI ---
with st.sidebar:
    st.header("⚙️ Nastavitve")
    
    with st.container():
        st.subheader("Vstopni podatki")
        leta = st.number_input("Doba varčevanja (leti)", min_value=1, max_value=60, value=20)
        donos_vnos = st.number_input("Predviden letni donos (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1)
    
    st.write("---")
    
    with st.container():
        st.subheader("Premije")
        mesecno = st.number_input("Mesečna premija (€)", min_value=30.0, value=100.0, step=10.0)
        polog = st.number_input("Začetni enkratni polog (€)", min_value=0.0, value=0.0, step=500.0)
        vsota = st.number_input("Zavarovalna vsota ob smrti (€)", value=10000)

# --- LOGIKA IZRAČUNA ---
def izracun_fleks(leta, mesecno, polog, vsota, donos_letni):
    VSTOPNI_STROSKI = 0.01
    STROSEK_ZAVAROVANJA = 2.0
    MEJA_ZAVAROVANJA = 3500.0
    PROVIZIJA_STOPNJA = 0.0049
    TRAJANJE_PROVIZIJE = 120
    OSNOVA_VPLACIL = 24
    
    meseci = int(leta * 12)
    m_donos = (1 + (donos_letni/100))**(1/12) - 1
    glavnica = polog * (1 - VSTOPNI_STROSKI)
    skupaj_vplacano = polog
    podatki = []
    
    neto_redno_za_osnovo = (mesecno * (1 - VSTOPNI_STROSKI)) - STROSEK_ZAVAROVANJA
    
    for m in range(1, meseci + 1):
        v_strosek = mesecno * VSTOPNI_STROSKI
        trenutni_zav = STROSEK_ZAVAROVANJA if glavnica < MEJA_ZAVAROVANJA else 0
        glavnica += (mesecno - v_strosek - trenutni_zav)
        
        if m <= TRAJANJE_PROVIZIJE:
            st_enot = min(m, OSNOVA_VPLACIL)
            glavnica -= (st_enot * neto_redno_za_osnovo * PROVIZIJA_STOPNJA)
            
        glavnica *= (1 + m_donos)
        skupaj_vplacano += mesecno
        
        if m % 12 == 0 or m == 1:
            podatki.append({
                "Leto": int(m/12) if m >= 12 else 0,
                "Vplačano": round(skupaj_vplacano, 2),
                "Stanje na računu": round(glavnica, 2),
                "Izplačilo ob smrti": round(max(glavnica, vsota), 2)
            })
    return pd.DataFrame(podatki)

df = izracun_fleks(leta, mesecno, polog, vsota, donos_vnos)

# --- GLAVNI PRIKAZ (DASHBOARD) ---
koncno_stanje = df["Stanje na računu"].iloc[-1]
vplacano = df["Vplačano"].iloc[-1]
donos_eur = koncno_stanje - vplacano

# Vrstica s ključnimi metrikami
m1, m2, m3 = st.columns(3)
m1.metric("💰 Predvideno stanje", f"{koncno_stanje:,.2f} €")
m2.metric("📥 Skupaj vplačano", f"{vplacano:,.2f} €")
m3.metric("📈 Čisti donos", f"{donos_eur:,.2f} €", delta=f"{((koncno_stanje/vplacano)-1)*100:.1f} %")

st.write("")

# Razporeditev: Graf in Tabela
tab1, tab2 = st.tabs(["📈 Grafični prikaz", "📋 Podrobna tabela"])

with tab1:
    fig = px.area(df, x="Leto", y=["Stanje na računu", "Vplačano"],
                  title="Projekcija rasti premoženja",
                  labels={"value": "Znesek (€)", "variable": "Kategorija"},
                  color_discrete_map={"Stanje na računu": "#00CC96", "Vplačano": "#3B4C63"},
                  template="plotly_white")
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- DODATNE INFORMACIJE ---
with st.expander("ℹ️ Podrobnosti o stroških in zakonitostih"):
    st.write(f"""
    Izračun upošteva naslednje parametre produkta FLEKS:
    * **Vstopni stroški:** 1% od vsakega vplačila.
    * **Upravljalska provizija:** 0.49% mesečno na osnovo prvih {24} vplačil (prvih 10 let).
    * **Strošek zavarovanja:** variabilno cca 2 €/mesec (dokler je stanje pod 3500 €).
    * **Zavarovalna vsota:** {vsota:,.2f} € (zagotovljeno minimalno izplačilo ob smrti).
    """)

st.success(f"Pri {donos_vnos}% donosu bo vrednost vaše police čez {leta} let znašala {koncno_stanje:,.2f} €.")
