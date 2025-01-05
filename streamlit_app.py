import streamlit as st
import requests
from pymongo import MongoClient
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import pandas as pd
import folium
from streamlit_folium import folium_static
import os

# Menggunakan environment variable untuk MongoDB URI
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://hafiizhherdian:Herdian17@cluster0.c1cmt.mongodb.net/')

# Fungsi untuk fetch data dari API BMKG
def fetch_earthquake_data():
    API_URL = "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json"
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            return data["Infogempa"]["gempa"]
        else:
            st.error(f"Error fetching data: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []

# Fungsi untuk menyimpan data ke MongoDB
def save_to_mongodb(data):
    client = MongoClient(MONGODB_URI)
    db = client["gempa"]
    collection = db["real_time_data"]
    if not collection.find_one({"Tanggal": data["Tanggal"], "Jam": data["Jam"]}):
        collection.insert_one(data)

# Fungsi untuk menampilkan peta lokasi gempa
def display_map(data):
    if data:
        m = folium.Map(location=[float(data['Lintang']), float(data['Bujur'])], zoom_start=5)
        folium.Marker(
            location=[float(data['Lintang']), float(data['Bujur'])],
            popup=f"Magnitude: {data['Magnitude']}, Kedalaman: {data['Kedalaman']}",
            icon=folium.Icon(color='red')
        ).add_to(m)
        folium_static(m)

# Fungsi untuk analisis data menggunakan Apache Spark
def analyze_data_with_spark():
    # Inisialisasi Spark Session dengan konfigurasi MongoDB
    spark = SparkSession.builder \
        .appName("EarthquakeDataAnalysis") \
        .config("spark.mongodb.input.uri", f"{MONGODB_URI}/gempa.real_time_data") \
        .config("spark.mongodb.output.uri", f"{MONGODB_URI}/gempa.real_time_data") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .master("spark://spark-master:7077") \
        .getOrCreate()

    try:
        # Baca data dari MongoDB
        df = spark.read.format("mongodb").load()

        # Contoh analisis sederhana: Hitung rata-rata magnitude gempa
        avg_magnitude = df.select(col("Magnitude").cast("float")).groupBy().avg().collect()[0][0]

        # Contoh analisis lain: Hitung jumlah gempa per wilayah
        earthquake_count_by_region = df.groupBy("Wilayah").count()

        return avg_magnitude, earthquake_count_by_region
    finally:
        # Stop Spark Session
        spark.stop()

# Tampilan aplikasi dengan Streamlit
st.title("Dashboard Data Gempa Terkini dengan Apache Spark")

# Tombol untuk mengambil data
if st.button("Ambil Data Real-Time"):
    data = fetch_earthquake_data()
    if data:
        st.success("Data berhasil diambil!")
        save_to_mongodb(data)
        st.write(data)
        display_map(data)

# Menampilkan data dari MongoDB
st.header("Data Gempa Terkini dari MongoDB")
client = MongoClient(MONGODB_URI)
db = client["gempa"]
collection = db["real_time_data"]

# Fetch data dari MongoDB
mongo_data = list(collection.find().sort("Tanggal", -1).limit(10))

if mongo_data:
    st.write("Berikut adalah data gempa terkini:")
    for item in mongo_data:
        st.write(f"**Tanggal:** {item.get('Tanggal')}, **Jam:** {item.get('Jam')}")
        st.write(f"**Magnitude:** {item.get('Magnitude')}, **Wilayah:** {item.get('Wilayah')}")
        st.write(f"**Kedalaman:** {item.get('Kedalaman')}, **Koordinat:** {item.get('Lintang')}, {item.get('Bujur')}")
        st.write("---")
else:
    st.warning("Tidak ada data di MongoDB. Klik tombol 'Ambil Data Real-Time' untuk memulai.")

# Analisis Data: Tren Gempa Berdasarkan Waktu
st.header("Analisis Tren Gempa Berdasarkan Waktu")
if mongo_data:
    df = pd.DataFrame(mongo_data)
    
    # Perbaikan timezone: Hilangkan "WIB" dari string waktu
    df['Waktu'] = pd.to_datetime(df['Tanggal'] + ' ' + df['Jam'].str.replace(" WIB", ""))
    
    # Set timezone ke Asia/Jakarta
    df['Waktu'] = df['Waktu'].dt.tz_localize('Asia/Jakarta')
    
    # Pastikan kolom 'Magnitude' ada di DataFrame
    if 'Magnitude' in df.columns:
        df.set_index('Waktu', inplace=True)
        st.line_chart(df['Magnitude'])
    else:
        st.warning("Kolom 'Magnitude' tidak ditemukan dalam data.")
else:
    st.warning("Tidak ada data untuk dianalisis.")

# Analisis Data dengan Apache Spark
st.header("Analisis Data dengan Apache Spark")
if st.button("Analisis Data dengan Spark"):
    avg_magnitude, earthquake_count_by_region = analyze_data_with_spark()
    st.write(f"**Rata-rata Magnitude Gempa:** {avg_magnitude}")
    st.write("**Jumlah Gempa per Wilayah:**")
    st.write(earthquake_count_by_region.toPandas())