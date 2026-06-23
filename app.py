import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. KONFIGURASI KONEKSI GOOGLE SHEETS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
WORKSHEET_NAME = "attendanceAPPDB" # Nama tab di bawah Google Sheets-mu
ANGGOTA_TIM = ['Andy', 'Rakha', 'Amar', 'Agil', 'Satrio']

def load_data():
    """Memuat data langsung dari Google Sheets."""
    try:
        df = conn.read(worksheet=WORKSHEET_NAME, ttl=0)
        df = df.dropna(how="all")
        return df
    except Exception as e:
        st.error(f"Gagal terhubung ke Google Sheets. Error: {e}")
        return pd.DataFrame(columns=['Tanggal', 'Nama', 'Status', 'Waktu_Absen', 'Keterangan'])

def save_data(df):
    """Menyimpan pembaruan data ke Google Sheets."""
    conn.update(worksheet=WORKSHEET_NAME, data=df)
    st.cache_data.clear() # Bersihkan cache agar tabel langsung ter-refresh

# ==========================================
# 2. LOGIKA BISNIS (Business Logic)
# ==========================================
def catat_kehadiran(nama, tanggal, status, keterangan):
    df = load_data()
    waktu_sekarang = pd.Timestamp.now(tz='Asia/Jakarta').strftime("%H:%M:%S")
    
    # Amankan tipe data kolom Tanggal
    if 'Tanggal' in df.columns:
        df['Tanggal'] = df['Tanggal'].astype(str)
    
    mask = (df['Tanggal'] == str(tanggal)) & (df['Nama'] == nama)
    
    # Berikan nilai default jika keterangan kosong
    if not keterangan.strip():
        keterangan = "-" if status == "Hadir" else "Tanpa Keterangan"

    if mask.any():
        # Update data jika sudah absen sebelumnya di hari yang sama
        df.loc[mask, 'Status'] = status
        df.loc[mask, 'Waktu_Absen'] = waktu_sekarang
        df.loc[mask, 'Keterangan'] = keterangan
    else:
        # Tambah entri baris baru jika belum ada
        data_baru = pd.DataFrame({
            'Tanggal': [str(tanggal)], 
            'Nama': [nama], 
            'Status': [status],
            'Waktu_Absen': [waktu_sekarang],
            'Keterangan': [keterangan]
        })
        df = pd.concat([df, data_baru], ignore_index=True)
    
    save_data(df)

# ==========================================
# 3. COMPONENT: POP-UP DIALOG (Modal)
# ==========================================
@st.dialog("Konfirmasi Absensi")
def konfirmasi_absen_dialog(nama, tanggal):
    """Memunculkan pop-up modal untuk memilih status dan mengisi alasan."""
    st.write(f"Halo **{nama}**, silakan pilih status kehadiranmu untuk tanggal {tanggal}:")
    
    # Input Pilihan Status
    status_pilihan = st.radio("Status:", ["Hadir", "Tidak Hadir"], index=0, horizontal=True)
    
    # Input Keterangan / Alasan
    placeholder_teks = "Contoh: Di kantor / WFH" if status_pilihan == "Hadir" else "Contoh: Sakit, Izin, Cuti"
    keterangan = st.text_input("Keterangan / Alasan:", placeholder=placeholder_teks)
    
    st.write("") # Spacer
    
    # Tombol Submit di dalam dialog
    if st.button("Kirim Absen", use_container_width=True, type="primary"):
        with st.spinner("Mengirim ke Google Sheets... ☁️"):
            catat_kehadiran(nama, tanggal, status_pilihan, keterangan)
        st.success(f"Absen {nama} berhasil dicatat!")
        st.rerun() # Refresh halaman untuk menutup dialog otomatis

# ==========================================
# 4. ANTARMUKA PENGGUNA UTAMA (UI)
# ==========================================
def main():
    st.set_page_config(page_title="Vibes Attendance Pro", page_icon="✨", layout="centered")
    
    st.title("✨ Vibes Attendance Tracker Pro")
    st.markdown("Sistem absensi *real-time* dengan fitur Keterangan & Alasan. ☁️")
    st.divider()

    # Bagian Input Kehadiran Hari Ini
    st.subheader("📅 Pilih Anggota Tim")
    hari_ini = st.date_input("Pilih Tanggal:", date.today())
    
    st.write("Klik nama kamu untuk melakukan absensi atau izin:")
    
    # Tampilan Grid Tombol Nama Anggota
    cols = st.columns(3) 
    for idx, nama in enumerate(ANGGOTA_TIM):
        col = cols[idx % 3]
        with col:
            # Mengubah alur kerja: klik tombol nama -> memicu pop-up dialog
            if st.button(f"👤 {nama}", key=nama, use_container_width=True):
                konfirmasi_absen_dialog(nama, hari_ini)

    st.divider()

    # Bagian Monitoring Historis (Spreadsheet view)
    st.subheader("📊 Data Live dari Google Sheets")
    df_historis = load_data()
    
    if not df_historis.empty:
        # Menampilkan data dengan sorting terbaru di atas
        st.dataframe(
            df_historis.sort_values(by=['Tanggal', 'Waktu_Absen'], ascending=[False, False]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Belum ada data kehadiran di Google Sheets-mu.")

if __name__ == "__main__":
    main()