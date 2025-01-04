# app.py
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

# Rest of your Streamlit app code remains the same...