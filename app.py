import streamlit as st
st.set_page_config(page_title="Yemek & Kalori AI", page_icon="🍔")
import requests
import base64
import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import io
import re
from sheet import veri_gonder
import pandas as pd
import matplotlib.pyplot as plt
from sheet import gunluk_kalori_ozeti
from auth import dogrula, kayit_ol
from datetime import datetime



if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:

    st.title("🍽️ Kalori Takip Uygulaması")
    st.markdown("### 🔐 Kullanıcı Girişi / Kayıt")
    

    secenek = st.radio("Ne yapmak istiyorsun?", ["Giriş Yap", "Kayıt Ol"])

    username_input = st.text_input("Kullanıcı Adı")
    password_input = st.text_input("Şifre", type="password")

    if secenek == "Giriş Yap":
        if st.button("Giriş"):
            if dogrula(username_input, password_input):
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.success(f"👋 Hoş geldin {username_input}!")
                st.rerun()
            else:
                st.error("❌ Hatalı kullanıcı adı veya şifre.")
    else:
        if st.button("Kayıt Ol"):
            if kayit_ol(username_input, password_input):
                st.success("✅ Kayıt başarılı. Artık giriş yapabilirsiniz.")
            else:
                st.warning("⚠️ Bu kullanıcı adı zaten kayıtlı.")
    st.stop()

# Oturum açıldığında varsayılan değerleri kontrol et
if "boy" not in st.session_state:
    st.session_state.boy = 170
if "kilo" not in st.session_state:
    st.session_state.kilo = 70


st.title("🍽️ AI ile Yemek Tanıma ve Kalori Hesabı")
st.write("📷 Bir yemek fotoğrafı yükle, ne olduğunu ve kaç kalori olduğunu öğren!")

st.success(f"👤 Aktif Kullanıcı: {st.session_state.username}")

st.markdown("---")
st.subheader("🎯 Günlük Kalori Hedefi")

if "kalori_hedefi" not in st.session_state:
    st.session_state.kalori_hedefi = 2000  # varsayılan

hedef_input = st.number_input("Hedef Kalori (kcal)", min_value=0, value=st.session_state.kalori_hedefi, step=50)

if st.button("🎯 Hedefi Kaydet"):
    st.session_state.kalori_hedefi = hedef_input
    st.success(f"✅ Günlük hedefiniz {hedef_input} kcal olarak ayarlandı.")



# .env'ten API key'i yükle
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# OpenRouter ayarları
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
model = "meta-llama/llama-3.2-11b-vision-instruct"

# Görseli base64'e çevirme
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode("utf-8")



# Geçmiş tahminler için session_state
if "gecmis_tahminler" not in st.session_state:
    st.session_state.gecmis_tahminler = []
if "toplam_kalori" not in st.session_state:
    st.session_state.toplam_kalori = 0



with st.sidebar:
    st.markdown("## 👤 Kullanıcı")
    st.success(f"🔓 Oturum açık: {st.session_state.username}")
    if st.button("🚪 Çıkış Yap"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()


# Görsel yükleme
uploaded_file = st.file_uploader("📤 Görsel yükle (.jpg, .png)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Yüklenen Görsel", use_container_width=True)
    base64_image = encode_image(uploaded_file)

    if st.button("🧠 Tahmin Et"):
        with st.spinner("Yemek analiz ediliyor..."):
            # 1. Yemek adı tahmini
            content = [
                {"type": "text", "text": "Bu görseldeki yemeğin adı nedir? Sadece Türkçe ve sade bir yemek ismi ver."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
            response = requests.post(url, headers=headers, json={
                "model": model,
                "messages": [{"role": "user", "content": content}]
            })
            yemek_adi = response.json()['choices'][0]['message']['content'].split("\n")[0].split(";")[0].strip()
            st.success(f"🍽️ Tahmin Edilen Yemek: **{yemek_adi}**")

        with st.spinner("Kalori tahmini yapılıyor..."):
            # 2. Kalori tahmini
            kalori_prompt = f"{yemek_adi} adlı yemeğin yaklaşık kalori miktarı nedir? Sadece sayısal bir değer ver (örnek: 600 kcal)"
            response2 = requests.post(url, headers=headers, json={
                "model": model,
                "messages": [{"role": "user", "content": [{"type": "text", "text": kalori_prompt}]}]
            })
            kalori_cevap = response2.json()['choices'][0]['message']['content'].strip()
            match = re.search(r"(\d{2,5})\s?k?cal", kalori_cevap.lower())
            if match:
                kcal = int(match.group(1))
            else:
                kcal = 0
            st.info(f"🔥 Tahmini Kalori: **{kcal} kcal**")

        # 3. Geçmişe ekle ve toplam kaloriye yaz
        st.session_state.gecmis_tahminler.append({
            "Yemek": yemek_adi,
            "Kalori (kcal)": kcal
        })
        st.session_state.toplam_kalori += kcal
        veri_gonder(yemek_adi, kcal, st.session_state.username)
        veri_gonder(yemek_adi, kcal, st.session_state.username)

        tarih_saat = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dosya_adi = f"uploads/{st.session_state.username}_{tarih_saat}.jpg"

        os.makedirs("uploads", exist_ok=True)

        with open(dosya_adi, "wb") as f:
            f.write(uploaded_file.getvalue())  

        

# Geçmiş tahminleri göster
if len(st.session_state.gecmis_tahminler) > 0:
    st.markdown("---")
    st.subheader("📋 Günlük Tahmin Geçmişi")
    st.table(st.session_state.gecmis_tahminler)
    st.success(f"🔢 Toplam Kalori: **{st.session_state.toplam_kalori} kcal**")

st.markdown("---")
st.subheader("📊 Haftalık Kalori Grafiği")

df = gunluk_kalori_ozeti(st.session_state.username)

bugun = datetime.now().strftime("%Y-%m-%d")
bugun_df = df[df["Tarih"] == bugun]

if not bugun_df.empty:
    bugun_kalori = int(bugun_df["Kalori"].sum())
    hedef = st.session_state.kalori_hedefi

    if bugun_kalori >= hedef:
        st.success(f"🎉 Bugünkü hedef ({hedef} kcal) tamamlandı! Toplam: {bugun_kalori} kcal")
    else:
        kalan = hedef - bugun_kalori
        st.warning(f"📉 Hedefe ulaşmak için {kalan} kcal daha gerekiyor. (Toplam: {bugun_kalori} kcal)")



if df.empty:
    st.info("Henüz yeterli veri yok.")
else:
  fig, ax = plt.subplots()
  ax.plot(df["Tarih"], df["Kalori"], marker='o', linestyle='-', label="Günlük Kalori")
  ax.axhline(y=st.session_state.kalori_hedefi, color='r', linestyle='--', label="Hedef Kalori")
  ax.set_xlabel("Tarih")
  ax.set_ylabel("Toplam Kalori")
  ax.set_title("Günlük Kalori Tüketimi")
  ax.grid(True)
  ax.legend()
  st.pyplot(fig)


from sheet import haftalik_kalori_ortalamasi

ortalama = haftalik_kalori_ortalamasi(st.session_state.username)
hedef = st.session_state.kalori_hedefi

st.markdown("---")
st.subheader("📊 Haftalık Kalori Ortalaması")

if ortalama > 0:
    fark = ortalama - hedef
    oran = (fark / hedef) * 100 if hedef > 0 else 0
    if fark > 0:
        st.warning(f"📈 Bu haftaki günlük ortalamanız **{ortalama} kcal**. Hedefinize göre %{'{:.1f}'.format(oran)} fazla.")
    else:
        st.success(f"✅ Günlük ortalamanız **{ortalama} kcal**, hedefin altında. Harika!")
else:
    st.info("Henüz yeterli veri yok.")


# --- Sidebar'da galeri butonu ---
with st.sidebar:
    st.markdown("## 🖼️ Galeri")
    if st.button("📸 Galerimi Göster"):
        st.session_state.galeri_goster = True

# --- Galeri gösterme bloğu ---
if st.session_state.get("galeri_goster", False):
    st.markdown("---")
    st.subheader("📂 Yüklediğiniz Görseller")
    galeri_klasoru = "uploads"
    kullanici = st.session_state.username

    if os.path.exists(galeri_klasoru):
        kullanici_gorselleri = [f for f in os.listdir(galeri_klasoru) if f.startswith(kullanici)]
        if kullanici_gorselleri:
            for gorsel in sorted(kullanici_gorselleri, reverse=True):
                tarih_str = gorsel.replace(f"{kullanici}_", "").replace(".jpg", "").replace("_", " ").replace("-", ":")
                st.markdown(f"🕒 **Tarih:** {tarih_str}")
                st.image(os.path.join(galeri_klasoru, gorsel), width=300)
                st.markdown("---")
        else:
            st.info("Henüz yüklediğiniz bir görsel yok.")
    else:
        st.info("Henüz yüklediğiniz bir görsel yok.")


with st.sidebar:
    st.markdown("## ⚖️ Günlük Kalori Hedefi")
    st.session_state.boy = st.number_input("Boy (cm)", min_value=100, max_value=250, step=1, value=st.session_state.boy, key="boy_input")
    st.session_state.kilo = st.number_input("Kilo (kg)", min_value=30, max_value=200, step=1, value=st.session_state.kilo, key="kilo_input")

    if st.button("🧠 Kalori İhtiyacımı Hesapla"):
        boy = st.session_state.boy
        kilo = st.session_state.kilo

        prompt = (
            f"Boyu {boy} cm ve kilosu {kilo} kg olan bir insanın, "
            "ortalama günlük kalori ihtiyacı nedir? Sadece sayısal bir değer ver (örnek: 2200 kcal)."
        )
        response = requests.post(url, headers=headers, json={
            "model": model,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        })
        cevap = response.json()["choices"][0]["message"]["content"]
        match = re.search(r"(\d{2,5})\s?k?cal", cevap.lower())
        if match:
            hedef_kalori = int(match.group(1))
            st.success(f"🎯 Tahmini Günlük Kalori İhtiyacı: **{hedef_kalori} kcal**")
            st.session_state.hedef_kalori = hedef_kalori
        else:
            st.warning("Kalori tahmini alınamadı. Lütfen tekrar deneyin.")


if "hedef_kalori" in st.session_state:
    fark = st.session_state.hedef_kalori - st.session_state.toplam_kalori
    if fark > 0:
        st.info(f"🎯 Günlük hedefinize ulaşmak için {fark} kcal daha alabilirsiniz.")
    else:
        st.warning(f"⚠️ Günlük hedefinizi aştınız! {abs(fark)} kcal fazlanız var.")



boy = st.session_state.boy
kilo = st.session_state.kilo
hedef_kalori = int(kilo * 24)




with st.sidebar:
    st.markdown("## 🤖 Sağlık Asistanım")
    soru = st.text_input("Merak Ettiğin Herşeyi Asistan'a Sor", placeholder="Bugün ne yemeliyim?")
    if st.button("Yanıt Al") and soru:
        response = requests.post(url, headers=headers, json={
            "model": model,
            "messages": [{"role": "user", "content": [{"type": "text", "text": soru}]}]
        })
        yanit = response.json()["choices"][0]["message"]["content"]
        st.success(yanit)

 
# Daha akıllı hale getirmek için:
gecmis = "\n".join([f"- {x['Yemek']}: {x['Kalori (kcal)']} kcal" for x in st.session_state.gecmis_tahminler])
prompt = f"""
  Benim boyum {boy} cm, kilom {kilo} kg. Günlük hedef kalori ihtiyacım: {hedef_kalori} kcal.
  Bugüne kadar şunları yedim:
  {gecmis}

  Bugün akşam ne yemeliyim?
  """