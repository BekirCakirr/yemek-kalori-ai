import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def veri_gonder(yemek, kalori, kullanici):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("kalori").sheet1

    tarih = datetime.now().strftime("%Y-%m-%d")  # BUGÜNÜN TARİHİ

    # 3 sütun olarak gönder: Yemek, Kalori, Tarih
    sheet.append_row([kullanici, yemek, kalori, tarih])

def gunluk_kalori_ozeti(kullanici):
    # Yetkilendirme vs. aynı
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("kalori").sheet1

    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Kullanıcıya göre filtrele
    df = df[df["Kullanıcı"] == kullanici]

    df["Kalori"] = pd.to_numeric(df["Kalori"], errors="coerce")
    df_grouped = df.groupby("Tarih")["Kalori"].sum().reset_index()
    return df_grouped

    print(df.columns)

def veri_gonder(yemek, kalori, kullanici):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)  # ← BU SATIR OLMAZSA client tanımsız olur

    sheet = client.open("kalori").sheet1
    tarih = datetime.now().strftime("%Y-%m-%d")
    sheet.append_row([kullanici, yemek, kalori, tarih])

def haftalik_kalori_ortalamasi(kullanici):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("kalori").sheet1

    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df = df[df["Kullanıcı"] == kullanici]  # filtrele
    df["Tarih"] = pd.to_datetime(df["Tarih"])
    df["Kalori"] = pd.to_numeric(df["Kalori"], errors="coerce")

    # Sadece son 7 gün
    son7gun = datetime.now() - pd.Timedelta(days=7)
    df_son7 = df[df["Tarih"] >= son7gun]

    ortalama = int(df_son7["Kalori"].mean()) if not df_son7.empty else 0
    return ortalama

