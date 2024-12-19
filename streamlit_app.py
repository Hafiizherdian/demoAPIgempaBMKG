import streamlit as st
import requests
from pymongo import MongoClient

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
    client = MongoClient("mongodb://localhost:27017/")
    db = client["gempa"]
    collection = db["real_time_data"]
    collection.insert_one(data)

# Tampilan aplikasi dengan Streamlit
st.title("Dashboard Data Gempa Terkini")

# Tombol untuk mengambil data
if st.button("Ambil Data Real-Time"):
    data = fetch_earthquake_data()
    if data:
        st.success("Data berhasil diambil!")
        save_to_mongodb(data)
        st.write(data)

# Menampilkan data dari MongoDB
st.header("Data Gempa Terkini dari MongoDB")
client = MongoClient("mongodb://localhost:27017/")
db = client["gempa"]
collection = db["real_time_data"]

# Fetch data dari MongoDB
mongo_data = list(collection.find().sort("Tanggal", -1).limit(10))

if mongo_data:
    st.write("Berikut adalah data gempa terkini:")
    for item in mongo_data:
        st.write(f"**Tanggal:** {item.get('Tanggal')}, **Jam:** {item.get('Jam')}")
        st.write(f"**Magnitudo:** {item.get('Magnitudo')}, **Wilayah:** {item.get('Wilayah')}")
        st.write("---")
else:
    st.warning("Tidak ada data di MongoDB. Klik tombol 'Ambil Data Real-Time' untuk memulai.")

