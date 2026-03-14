import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Nastavitve strani
st.set_page_config(
    page_title="FLEKS Premium Kalkulator",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Popravljen CSS za lepši izgled (brez napak)
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Naslovna vrstica
st.title("🛡️ FLEKS Premium Analitik")
st.caption("Profesionalno orodje za izračun realnega donosa z vsemi stroški")
st.write("---")

# 4. Stranski meni za vnos podatkov
with st.sidebar:
    st.header("⚙️ Parametri")
    
    leta = st.number_input("Doba varčevanja (leti)", min_value=1, max_value=60, value=20, step=1)
    donos_vnos = st.number_input("Predviden letni donos (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1)
    
    st.write("---")
    st.subheader("Vplačila")
    mesecno = st.number_input("Mesečna premija (€)", min_value=30.0, value=100.0, step=10.0)
    polog = st.number_input("Začetni enkratni polog (€)", min_value=0.0, value=0.0, step=500.0)
    vsota = st.number_input("Zavarovalna vsota ob smrti (€)", value=10000)

# 5. Matematična funkcija izračuna
def izracun_fleks(leta, mesecno, polog, vsota, donos_letni):
    # Specifični stroški FLEKS
    VSTOPNI_STROSKI = 0.01          # 1%
    STROSEK_ZAVAROVANJA = 2.0       # cca 2€
    MEJA_ZAVAROVANJA = 3500.0       # Prag za prenehanje 2€ stroška
    PROVIZIJA_STOPNJA = 0.0049      # 0.49%
    TRAJANJE_PROVIZIJE = 120        # 10 let
    OSNOVA_VPLACIL = 24             # Na prvih 24 vplačil
    
    meseci = int(leta * 12)
    # Izračun mesečnega donosa iz letnega
    m_donos = (1 + (donos_letni/100))**(1/12) - 1
    
    # Začetni polog z vstopnim stroškom
    glavnica = polog * (1 - VSTOPNI_STROSKI)
    skupaj_vplacano = polog
    podatki = []
    
    # Izračun neto osnove za 0.49% provizijo
    neto_redno_za_osnovo = (mesecno * (1 - VSTOPNI_STROSKI)) - STROSEK_ZAVAROVANJA
    
    for m in range(1, meseci + 1):
        # A. Vstopni strošek in zavarovanje
        v_strosek = mesecno * VSTOPNI_STROSKI
        trenutni_zav = STROSEK_ZAVAROVANJA if glavnica < MEJA_ZAVAROVANJA else 0
        glavnica += (mesecno - v_strosek - trenutni_zav)
        
        # B. Upravljalska provizija na 24 vplačil (10 let)
        if m <= TRAJANJE_PROVIZIJE:
            st_enot = min(m, OSNOVA_VPLACIL)
            glavnica -= (st_enot * neto_redno_za_osnovo * PROVIZIJA_STOPNJA)
            
        # C. Donos
        glavnica *= (1 + m_donos)
        skupaj_vplacano += mesecno
        
        # D. Zapis za rezultate (vsako leto)
        if m % 12 == 0 or m == 1:
            podatki.append({
                "Leto": int(m/12) if m >= 12 else 0,
                "Vplačano": round(skupaj_vplacano, 2),
                "Stanje na računu": round(glavnica, 2),
                "Izplačilo ob smrti": round(max(glavnica, vsota), 2)
            })
            
    return pd.DataFrame(podatki)

# 6. Generiranje podatkov
df = izracun_fleks(leta, mesecno, polog, vsota, donos_vnos)

# 7. Dashboard metrike
koncno_stanje = df["Stanje na računu"].iloc[-1]
vplacano = df["Vplačano"].iloc[-1]
donos_eur = koncno_stanje - vplacano

c1, c2, c3 = st.columns(3)
c1.metric("💰 Predvideno stanje", f"{koncno_stanje:,.2f} €")
c2.metric("📥 Skupaj vplačano", f"{vplacano:,.2f} €")
c3.metric("📈 Čisti donos", f"{donos_eur:,.2f} €")

st.write("")

# 8. Zavihki za graf in tabelo
t1, t2 = st.tabs(["📈 Vizualna projekcija", "📋 Letni pregled"])

with t1:
    fig = px.area(df, x="Leto", y=["Stanje na računu", "Vplačano"],
                  labels={"value": "Znesek (€)", "variable": "Postavka"},
                  color_discrete_map={"Stanje na računu": "#00CC96", "Vplačano": "#3B4C63"},
                  template="plotly_white")
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

with t2:
    st.dataframe(df, use_container_width=True, hide_index=True)

# 9. Povzetek stroškov
with st.expander("ℹ️ Upoštevana troškovna matematika"):
    st.write(f"""
    Izračun temelji na specifikacijah produkta FLEKS:
    * **1% vstopni stroški** na vsa vplačila.
    * **0,49% mesečna provizija** na prvih 24 enot rednih vplačil (trajanje 10 let).
    * **2 € fiksni strošek** zavarovanja (dokler je stanje pod 3500 €).
    * **Zavarovalna vsota ({vsota:,.0f} €):** Izplača se, če je ob smrti višja od stanja na računu.
    """)

st.success(f"Projekcija uspešno zaključena za obdobje {leta} let.")
