import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. KONFIGURASI KONEKSI GOOGLE SHEETS
# ==========================================
# Membangun koneksi ke awan
conn = st.connection("gsheets", type=GSheetsConnection)
WORKSHEET_NAME = "attendanceAPPDB" # Nama tab di bawah Google Sheets-mu
ANGGOTA_TIM = ['Andy', 'Rakha', 'Amar', 'Agil', 'Satrio']

def load_data():
    """Memuat data langsung dari Google Sheets."""
    try:
        # ttl=0 memastikan aplikasi selalu mengambil data paling baru (live)
        df = conn.read(worksheet=WORKSHEET_NAME, ttl=0)
        # Membersihkan baris kosong (bug bawaan membaca sheet kosong)
        df = df.dropna(how="all")
        return df
    except Exception as e:
        st.error(f"Gagal terhubung ke Google Sheets. Cek konfigurasi rahasia. Error: {e}")
        return pd.DataFrame(columns=['Tanggal', 'Nama', 'Status', 'Waktu_Absen'])

def save_data(df):
    """Menyimpan / menimpa pembaruan data ke Google Sheets."""
    conn.update(worksheet=WORKSHEET_NAME, data=df)
    st.cache_data.clear() # Reset memori agar tabel langsung ter-refresh

# ==========================================
# 2. LOGIKA BISNIS (Business Logic)
# ==========================================
def catat_kehadiran(nama, tanggal, status):
    df = load_data()
    # Memastikan format waktu akurat di Waktu Indonesia Barat (WIB)
    waktu_sekarang = pd.Timestamp.now(tz='Asia/Jakarta').strftime("%H:%M:%S")
    
    # Amankan tipe data kolom Tanggal
    if 'Tanggal' in df.columns:
        df['Tanggal'] = df['Tanggal'].astype(str)
    
    mask = (df['Tanggal'] == str(tanggal)) & (df['Nama'] == nama)
    
    if mask.any():
        # Update waktu jika dia sudah absen sebelumnya di hari yang sama
        df.loc[mask, 'Status'] = status
        df.loc[mask, 'Waktu_Absen'] = waktu_sekarang
    else:
        # Tambah entri baris baru
        data_baru = pd.DataFrame({
            'Tanggal': [str(tanggal)], 
            'Nama': [nama], 
            'Status': [status],
            'Waktu_Absen': [waktu_sekarang]
        })
        df = pd.concat([df, data_baru], ignore_index=True)
    
    save_data(df)

# ==========================================
# 3. ANTARMUKA PENGGUNA (UI)
# ==========================================
def main():
    st.set_page_config(page_title="Vibes Attendance", page_icon="✨", layout="centered")
    
    st.title("✨ Vibes Attendance Tracker")
    st.markdown("Sistem absensi *real-time* yang tersinkronisasi ke Google Sheets. ☁️")
    st.divider()

    st.subheader("📅 Absensi Hari Ini")
    hari_ini = st.date_input("Pilih Tanggal:", date.today())
    
    cols = st.columns(3) 
    
    for idx, nama in enumerate(ANGGOTA_TIM):
        col = cols[idx % 3]
        with col:
            # Spinner yang estetik selagi data diproses ke awan
            if st.button(f"👋 {nama} Hadir", key=nama, use_container_width=True):
                with st.spinner("Menyimpan ke awan... ☁️"):
                    catat_kehadiran(nama, hari_ini, "Hadir")
                st.success(f"Mantap! {nama} berhasil absen.")

    st.divider()

    st.subheader("📊 Data Live dari Google Sheets")
    df_historis = load_data()
    
    if not df_historis.empty:
        st.dataframe(
            df_historis.sort_values(by=['Tanggal', 'Waktu_Absen'], ascending=[False, False]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Belum ada data kehadiran di Google Sheets-mu.")

if __name__ == "__main__":
    main()