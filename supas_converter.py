import streamlit as st
import pandas as pd
import json
import glob
import os

# Konfigurasi halaman
st.set_page_config(
    page_title="Data Keluarga Papua Pegunungan",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

@st.cache_data
def load_all_json_files():
    """Membaca semua file data*.json di folder yang sama"""
    # Mencari semua file yang dimulai dengan 'data' dan berekstensi .json
    json_files = glob.glob("data*.json")
    
    all_data = []
    
    if not json_files:
        st.error("Tidak ditemukan file data*.json di folder ini")
        return pd.DataFrame()
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                # Menambahkan nama file sebagai kolom tambahan untuk tracking
                for record in data:
                    record['source_file'] = os.path.basename(file_path)
                all_data.extend(data)
        except Exception as e:
            st.warning(f"Error membaca file {file_path}: {str(e)}")
    
    if not all_data:
        st.error("Tidak ada data yang berhasil dimuat")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_data)
    return df

def main():
    st.title("🏘️ Sistem Data Keluarga Papua Pegunungan")
    st.markdown("---")
    
    # Load data
    with st.spinner("Memuat data..."):
        df = load_all_json_files()
    
    if df.empty:
        st.stop()
    
    # Informasi umum
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", len(df))
    with col2:
        total_keluarga = df['nomor_kartu_keluarga'].nunique()
        st.metric("Total Keluarga", total_keluarga)
    with col3:
        total_ditemukan = len(df[df['keberadaan'] == 'Ditemukan'])
        st.metric("Anggota Ditemukan", total_ditemukan)
    
    st.markdown("---")
    
    # Filter Section
    st.header("🔍 Filter Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filter Kecamatan
        kecamatan_options = ['Semua'] + sorted(df['kecamatan'].dropna().unique().tolist())
        selected_kecamatan = st.selectbox("Pilih Kecamatan:", kecamatan_options)
    
    # Filter berdasarkan kecamatan yang dipilih
    if selected_kecamatan != 'Semua':
        df_filtered = df[df['kecamatan'] == selected_kecamatan]
    else:
        df_filtered = df.copy()
    
    with col2:
        # Filter Desa/Kelurahan
        desa_options = ['Semua'] + sorted(df_filtered['desa_kelurahan'].dropna().unique().tolist())
        selected_desa = st.selectbox("Pilih Desa/Kelurahan:", desa_options)
    
    # Filter berdasarkan desa yang dipilih
    if selected_desa != 'Semua':
        df_filtered = df_filtered[df_filtered['desa_kelurahan'] == selected_desa]
    
    with col3:
        # Filter Nama Kepala Keluarga
        kepala_keluarga_options = ['Semua'] + sorted(df_filtered['nama_kepala_keluarga'].dropna().unique().tolist())
        selected_kepala = st.selectbox("Pilih Kepala Keluarga:", kepala_keluarga_options)
    
    # Filter berdasarkan kepala keluarga yang dipilih
    if selected_kepala != 'Semua':
        df_filtered = df_filtered[df_filtered['nama_kepala_keluarga'] == selected_kepala]
    
    st.markdown("---")
    
    # Hasil Filter
    if not df_filtered.empty:
        st.header("📊 Ringkasan Keluarga")
        
        # Groupby untuk mendapatkan ringkasan per keluarga
        keluarga_summary = df_filtered.groupby(['nomor_kartu_keluarga', 'nama_kepala_keluarga']).agg({
            'keberadaan': lambda x: (x == 'Ditemukan').sum(),
            'jumlah_anggota_keluarga': 'first',
            'alamat_tempat_tinggal': 'first',
            'kecamatan': 'first',
            'desa_kelurahan': 'first'
        }).reset_index()
        
        keluarga_summary.columns = [
            'Nomor KK', 'Nama Kepala Keluarga', 'Anggota Ditemukan', 
            'Total Anggota', 'Alamat', 'Kecamatan', 'Desa/Kelurahan'
        ]
        
        # Tampilkan ringkasan keluarga
        st.subheader("🏠 Daftar Keluarga")
        st.dataframe(
            keluarga_summary,
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        
        # Detail Anggota Keluarga
        st.header("👥 Detail Anggota Keluarga")
        
        # Filter hanya yang ditemukan
        show_all = st.checkbox("Tampilkan semua anggota (termasuk yang tidak ditemukan)", value=False)
        
        if not show_all:
            df_detail = df_filtered[df_filtered['keberadaan'] == 'Ditemukan'].copy()
        else:
            df_detail = df_filtered.copy()
        
        if not df_detail.empty:
            # Pilih kolom yang akan ditampilkan
            display_columns = [
                'nomor_kartu_keluarga', 'nama_kepala_keluarga', 'nomor_urut_anggota_keluarga',
                'nik', 'nama_anggota_keluarga', 'keberadaan', 'status_hubungan', 
                'jenis_kelamin', 'tanggal_lahir', 'bulan_lahir', 'tahun_lahir', 'umur',
                'gaji_uang', 'gaji_barang', 'hari_kerja', 'jam_kerja', 'Pendidikan',
                'Lulus_SD', 'Lulus_SMP', 'Lulus_SMA',
                'alamat_tempat_tinggal'
            ]
            
            # Filter kolom yang ada di dataframe
            available_columns = [col for col in display_columns if col in df_detail.columns]
            
            df_display = df_detail[available_columns].copy()
            
            # Rename kolom untuk tampilan yang lebih baik
            column_mapping = {
                'nomor_kartu_keluarga': 'No. KK',
                'nama_kepala_keluarga': 'Kepala Keluarga',
                'nomor_urut_anggota_keluarga': 'No. Urut',
                'nik': 'NIK',
                'nama_anggota_keluarga': 'Nama',
                'keberadaan': 'Status',
                'status_hubungan': 'Hub. Keluarga',
                'jenis_kelamin': 'Jenis Kelamin',
                'umur': 'Umur',
                'tanggal_lahir': 'Tgl',
                'bulan_lahir': 'Bulan',
                'tahun_lahir': 'Tahun',
                'gaji_uang': 'Gaji (Rp)',
                'gaji_barang': 'Gaji Barang (Rp)',
                'hari_kerja': 'Hari Kerja',
                'jam_kerja': 'Jam Kerja',
                'Pendidikan': 'Pendidikan',
                'Lulus_SD': 'Lulus SD',
                'Lulus_SMP': 'Lulus SMP', 
                'Lulus_SMA': 'Lulus SMA',
                'alamat_tempat_tinggal': 'Alamat'
            }
            
            df_display = df_display.rename(columns=column_mapping)
            
            # Sorting berdasarkan No. KK dan No. Urut
            if 'No. KK' in df_display.columns and 'No. Urut' in df_display.columns:
                df_display = df_display.sort_values(['No. KK', 'No. Urut'])
            
            # Tampilkan tabel
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
            
            # Statistik tambahan
            st.subheader("📈 Statistik")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_anggota = len(df_detail)
                st.metric("Total Anggota", total_anggota)
            
            with col2:
                if not show_all:
                    ditemukan = len(df_detail)
                else:
                    ditemukan = len(df_detail[df_detail['keberadaan'] == 'Ditemukan'])
                st.metric("Ditemukan", ditemukan)
            
            with col3:
                laki_laki = len(df_detail[df_detail['jenis_kelamin'] == 'Laki-laki'])
                st.metric("Laki-laki", laki_laki)
            
            with col4:
                perempuan = len(df_detail[df_detail['jenis_kelamin'] == 'Perempuan'])
                st.metric("Perempuan", perempuan)
            
            # Download data
            st.markdown("---")
            st.subheader("💾 Download Data")
            
            # Convert to CSV
            csv_data = df_display.to_csv(index=False)
            st.download_button(
                label="📄 Download sebagai CSV",
                data=csv_data,
                file_name=f"data_keluarga_{selected_kecamatan}_{selected_desa}_{selected_kepala}.csv",
                mime="text/csv"
            )
            
        else:
            st.warning("Tidak ada data anggota keluarga yang ditemukan dengan filter yang dipilih.")
    
    else:
        st.warning("Tidak ada data yang sesuai dengan filter yang dipilih.")

if __name__ == "__main__":
    main()
