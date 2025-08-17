import streamlit as st
import pandas as pd
import json
from io import BytesIO
import re
import numpy as np
import glob
import os
from datetime import datetime

def clean_value(value):
    """Membersihkan nilai dari format '1 - 1 - Description' menjadi hanya 'Description'"""
    if isinstance(value, str):
        # Pattern untuk menangkap format '1 - 1 - Description' atau '01 - 1 - Description'
        match = re.match(r'^\d+\s*-\s*\d+\s*[–-]\s*(.+)$', value)
        if match:
            return match.group(1).strip()
    return value

def read_all_supas_files():
    """Membaca semua file supas_extraction*.json di folder yang sama"""
    pattern = "supas_extraction*.json"
    files = glob.glob(pattern)
    
    if not files:
        return None, "Tidak ditemukan file supas_extraction*.json di folder ini"
    
    all_records = {}
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                records = data.get('records', [])
                
                for record in records:
                    record_id = record.get('id')
                    if record_id:
                        # Jika ID belum ada, tambahkan record
                        if record_id not in all_records:
                            all_records[record_id] = record
                        else:
                            # Jika ID sudah ada, pilih berdasarkan prioritas
                            existing_record = all_records[record_id]
                            current_status = record.get('status', '')
                            existing_status = existing_record.get('status', '')
                            
                            # Prioritas 1: status success
                            if current_status == 'success' and existing_status != 'success':
                                all_records[record_id] = record
                            elif existing_status == 'success' and current_status != 'success':
                                continue  # Keep existing
                            elif current_status == 'success' and existing_status == 'success':
                                # Prioritas 2: timestamp terbaru
                                current_timestamp = record.get('extraction_timestamp', '')
                                existing_timestamp = existing_record.get('extraction_timestamp', '')
                                
                                if current_timestamp > existing_timestamp:
                                    all_records[record_id] = record
        except Exception as e:
            st.warning(f"Error reading {file_path}: {str(e)}")
    
    # Convert back to list format
    merged_data = {
        'records': list(all_records.values()),
        'extraction_summary': {
            'total_records': len(all_records),
            'merged_from_files': len(files)
        }
    }
    
    return merged_data, f"Berhasil membaca {len(files)} file dan menggabungkan {len(all_records)} record unik"

def add_calculated_columns(df):
    """Menambahkan kolom perhitungan sesuai rumus yang diminta"""
    # Set random seed for reproducible results (optional)
    np.random.seed(42)
    
    # Kolom umur (berdasarkan Agustus 2025)
    def calculate_umur(row):
        try:
            tahun_lahir = int(row['tahun_lahir']) if row['tahun_lahir'] and str(row['tahun_lahir']).isdigit() else None
            bulan_lahir_text = str(row['bulan_lahir']).lower()
            
            if not tahun_lahir:
                return ''
            
            # Mapping bulan ke angka
            bulan_mapping = {
                'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
                'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
                'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
            }
            
            bulan_lahir_num = None
            for bulan_name, bulan_num in bulan_mapping.items():
                if bulan_name in bulan_lahir_text:
                    bulan_lahir_num = bulan_num
                    break
            
            if not bulan_lahir_num:
                return ''
            
            # Perhitungan umur berdasarkan Agustus 2025 (bulan ke-8)
            if bulan_lahir_num < 8:  # Sebelum Agustus
                umur = 2025 - tahun_lahir
            else:  # Agustus atau setelah Agustus
                umur = 2025 - tahun_lahir + 1
            
            return umur if umur >= 0 else ''
        except:
            return ''
    
    df['umur'] = df.apply(calculate_umur, axis=1)
    
    # Kolom gaji_uang
    def calculate_gaji_uang(row):
        if row['status_hubungan'] == 'Kepala Keluarga':
            return np.random.randint(185, 274) * 10000
        else:
            return ''
    
    df['gaji_uang'] = df.apply(calculate_gaji_uang, axis=1)
    
    # Kolom gaji_barang
    def calculate_gaji_barang(row):
        if row['status_hubungan'] == 'Kepala Keluarga' and row['gaji_uang'] != '':
            return abs(3000000 - row['gaji_uang'] - (np.random.randint(1, 10) * 100000))
        else:
            return ''
    
    df['gaji_barang'] = df.apply(calculate_gaji_barang, axis=1)
    
    # Kolom hari_kerja
    df['hari_kerja'] = [np.random.randint(5, 8) for _ in range(len(df))]
    
    # Kolom jam_kerja
    def calculate_jam_kerja(row):
        jumlah_anggota = str(row['jumlah_anggota_keluarga'])
        status_hubungan = row['status_hubungan']
        
        if jumlah_anggota == '1' or status_hubungan == 'Istri':
            return np.random.randint(32, 39)
        elif status_hubungan == 'Kepala Keluarga':
            return np.random.randint(26, 37)
        else:
            return np.random.randint(12, 29)
    
    df['jam_kerja'] = df.apply(calculate_jam_kerja, axis=1)
    
    # Kolom pendidikan - lulus_sd, lulus_smp, lulus_sma
    def calculate_lulus_sd(row):
        try:
            tahun_lahir = int(row['tahun_lahir']) if row['tahun_lahir'] and str(row['tahun_lahir']).isdigit() else None
            return tahun_lahir + 12 if tahun_lahir else ''
        except:
            return ''
    
    def calculate_lulus_smp(row):
        try:
            tahun_lahir = int(row['tahun_lahir']) if row['tahun_lahir'] and str(row['tahun_lahir']).isdigit() else None
            return tahun_lahir + 15 if tahun_lahir else ''
        except:
            return ''
    
    def calculate_lulus_sma(row):
        try:
            tahun_lahir = int(row['tahun_lahir']) if row['tahun_lahir'] and str(row['tahun_lahir']).isdigit() else None
            return tahun_lahir + 18 if tahun_lahir else ''
        except:
            return ''
    
    df['lulus_sd'] = df.apply(calculate_lulus_sd, axis=1)
    df['lulus_smp'] = df.apply(calculate_lulus_smp, axis=1)
    df['lulus_sma'] = df.apply(calculate_lulus_sma, axis=1)
    
    return df

def extract_arts_from_json(json_data):
    """Ekstrak semua ART dari data JSON dan konversi ke format tabular"""
    all_arts = []
    
    records = json_data.get('records', [])
    
    for record in records:
        data = record.get('data', {})
        
        # Informasi lokasi dari page1_blok_i
        blok_i = data.get('page1_blok_i', {})
        location_info = {
            'provinsi': clean_value(blok_i.get('provinsi', '')),
            'kecamatan': clean_value(blok_i.get('kecamatan', '')),
            'desa_kelurahan': clean_value(blok_i.get('desa_kelurahan', '')),
            'nks': blok_i.get('nks', '')
        }
        
        # Informasi keluarga dari page2_blok_v
        blok_v = data.get('page2_blok_v', {})
        family_info = {
            'nama_kepala_keluarga': blok_v.get('nama_kepala_keluarga', ''),
            'keberadaan_keluarga': clean_value(blok_v.get('keberadaan_keluarga', '')),
            'alamat_tempat_tinggal': blok_v.get('alamat_tempat_tinggal', ''),
            'nomor_kartu_keluarga': blok_v.get('nomor_kartu_keluarga', ''),
            'jumlah_anggota_keluarga': blok_v.get('jumlah_anggota_keluarga', ''),
            # Simpan untuk sorting tapi akan dihapus nanti
            '_nomor_urut_bangunan_sort': blok_v.get('nomor_urut_bangunan', '')
        }
        
        # Ekstrak ART details
        art_details = data.get('art_details', [])
        
        if art_details:
            for art in art_details:
                art_info = art.get('detail_data', {})
                
                # Gabungkan semua informasi untuk setiap ART
                art_row = {
                    **location_info,
                    **family_info,
                    'art_info': art.get('art_info', ''),
                    'nomor_urut_anggota_keluarga': art_info.get('nomor_urut_anggota_keluarga', ''),
                    'nik': art_info.get('nik', ''),
                    'nama_anggota_keluarga': art_info.get('nama_anggota_keluarga', ''),
                    'keberadaan': clean_value(art_info.get('keberadaan', '')),
                    'status_hubungan': clean_value(art_info.get('status_hubungan', '')),
                    'jenis_kelamin': clean_value(art_info.get('jenis_kelamin', '')),
                    'tanggal_lahir': art_info.get('tanggal_lahir', ''),
                    'bulan_lahir': clean_value(art_info.get('bulan_lahir', '')),
                    'tahun_lahir': art_info.get('tahun_lahir', '')
                }
                
                all_arts.append(art_row)
        else:
            # Jika tidak ada ART details, tetap tambahkan record info
            art_row = {
                **location_info,
                **family_info,
                'art_info': '',
                'nomor_urut_anggota_keluarga': '',
                'nik': '',
                'nama_anggota_keluarga': '',
                'keberadaan': '',
                'status_hubungan': '',
                'jenis_kelamin': '',
                'tanggal_lahir': '',
                'bulan_lahir': '',
                'tahun_lahir': ''
            }
            all_arts.append(art_row)
    
    return all_arts

def create_excel_file(df):
    """Membuat file Excel dari DataFrame"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet utama dengan data ART
        df.to_excel(writer, sheet_name='Data ART', index=False)
        
        # Auto-adjust column width
        worksheet = writer.sheets['Data ART']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)  # Max width 50
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return output

def main():
    st.set_page_config(
        page_title="SUPAS JSON to Excel Converter",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 SUPAS JSON to Excel Converter")
    st.markdown("Konversi data SUPAS menjadi format Excel dengan filter interaktif")
    
    # Sidebar dengan informasi
    with st.sidebar:
        st.header("ℹ️ Informasi")
        st.markdown("""
        **Program ini akan:**
        1. Membaca semua file `supas_extraction*.json` di folder ini
        2. Menggabungkan data dengan prioritas:
           - Status 'success' lebih diutamakan
           - Timestamp terbaru jika status sama
        3. Menyediakan filter interaktif
        4. Menghasilkan file Excel dengan data terfilter
        
        **Kolom perhitungan otomatis:**
        - **Umur**: Berdasarkan Agustus 2025
        - Gaji uang & barang untuk Kepala Keluarga
        - Hari kerja & jam kerja 
        - Tahun lulus SD, SMP, SMA
        
        **Filter tersedia:**
        - Provinsi → Kecamatan → Desa → Kepala Keluarga
        - Tabel detail muncul saat pilih Kepala Keluarga
        """)
    
    # Baca semua file SUPAS
    with st.spinner('Membaca file SUPAS...'):
        json_data, message = read_all_supas_files()
    
    if json_data is None:
        st.error(message)
        st.info("Pastikan ada file dengan format `supas_extraction*.json` di folder yang sama dengan program ini")
        return
    
    st.success(message)
    
    # Process data
    with st.spinner('Memproses data...'):
        arts_data = extract_arts_from_json(json_data)
        df_full = pd.DataFrame(arts_data)
        df_full = add_calculated_columns(df_full)
        
        # Sort berdasarkan nks dan nomor_urut_bangunan
        df_full['_nks_sort'] = pd.to_numeric(df_full['nks'], errors='coerce').fillna(0)
        df_full['_nomor_urut_bangunan_sort_num'] = pd.to_numeric(df_full['_nomor_urut_bangunan_sort'], errors='coerce').fillna(0)
        
        df_full = df_full.sort_values(['_nks_sort', '_nomor_urut_bangunan_sort_num'])
        
        # Hapus kolom helper untuk sorting
        df_full = df_full.drop(columns=['_nks_sort', '_nomor_urut_bangunan_sort_num', '_nomor_urut_bangunan_sort'])
    
    st.success(f"Data berhasil diproses: {len(df_full)} baris ART")
    
    # Filter Section
    st.header("🔍 Filter Data")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Filter Provinsi
    with col1:
        provinsi_options = ['Semua'] + sorted([p for p in df_full['provinsi'].unique() if p and str(p) != 'nan'])
        selected_provinsi = st.selectbox("Provinsi", provinsi_options)
    
    # Filter data berdasarkan provinsi
    if selected_provinsi != 'Semua':
        df_filtered = df_full[df_full['provinsi'] == selected_provinsi]
    else:
        df_filtered = df_full.copy()
    
    # Filter Kecamatan
    with col2:
        kecamatan_options = ['Semua'] + sorted([k for k in df_filtered['kecamatan'].unique() if k and str(k) != 'nan'])
        selected_kecamatan = st.selectbox("Kecamatan", kecamatan_options)
    
    # Filter data berdasarkan kecamatan
    if selected_kecamatan != 'Semua':
        df_filtered = df_filtered[df_filtered['kecamatan'] == selected_kecamatan]
    
    # Filter Desa
    with col3:
        desa_options = ['Semua'] + sorted([d for d in df_filtered['desa_kelurahan'].unique() if d and str(d) != 'nan'])
        selected_desa = st.selectbox("Desa/Kelurahan", desa_options)
    
    # Filter data berdasarkan desa
    if selected_desa != 'Semua':
        df_filtered = df_filtered[df_filtered['desa_kelurahan'] == selected_desa]
    
    # Filter Kepala Keluarga
    with col4:
        kepala_keluarga_options = ['Semua'] + sorted([k for k in df_filtered['nama_kepala_keluarga'].unique() if k and str(k) != 'nan'])
        selected_kepala_keluarga = st.selectbox("Kepala Keluarga", kepala_keluarga_options)
    
    # Filter data berdasarkan kepala keluarga
    if selected_kepala_keluarga != 'Semua':
        df_filtered = df_filtered[df_filtered['nama_kepala_keluarga'] == selected_kepala_keluarga]
    
    # Tampilkan hasil filter
    st.subheader("📋 Hasil Filter")
    
    # Hitung data yang ditemukan
    df_ditemukan_filtered = df_filtered[df_filtered['keberadaan'] == 'Ditemukan']
    
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.metric("Total Data Awal", len(df_full))
    with col_b:
        st.metric("Data Setelah Filter", len(df_filtered))
    with col_c:
        st.metric("Data Ditemukan", len(df_ditemukan_filtered))
    with col_d:
        percentage = (len(df_ditemukan_filtered) / len(df_full) * 100) if len(df_full) > 0 else 0
        st.metric("% Ditemukan", f"{percentage:.1f}%")
    
    if len(df_filtered) == 0:
        st.warning("Tidak ada data yang sesuai dengan filter yang dipilih")
        return
    
    # Warning jika tidak ada data ditemukan
    df_ditemukan_check = df_filtered[df_filtered['keberadaan'] == 'Ditemukan']
    if len(df_ditemukan_check) == 0:
        st.warning("⚠️ Tidak ada ART dengan status 'Ditemukan' pada filter ini")
        st.info("Data tetap bisa didownload, namun tabel detail tidak akan muncul karena tidak ada ART yang ditemukan")
    
    # Tampilkan ringkasan data yang difilter
    with st.expander("📊 Ringkasan Data Terfilter"):
        col_x, col_y = st.columns(2)
        
        with col_x:
            st.write("**Jumlah Keluarga:**", df_filtered['nama_kepala_keluarga'].nunique())
            st.write("**Jumlah ART (Total):**", len(df_filtered))
            # Tambah info ART yang ditemukan
            df_ditemukan_all = df_filtered[df_filtered['keberadaan'] == 'Ditemukan']
            st.write("**Jumlah ART (Ditemukan):**", len(df_ditemukan_all))
            
        with col_y:
            kepala_keluarga_count = len(df_filtered[df_filtered['status_hubungan'] == 'Kepala Keluarga'])
            kepala_keluarga_ditemukan = len(df_ditemukan_all[df_ditemukan_all['status_hubungan'] == 'Kepala Keluarga'])
            
            st.write("**Kepala Keluarga:**", kepala_keluarga_count)
            st.write("**Kepala Keluarga (Ditemukan):**", kepala_keluarga_ditemukan)
            st.write("**Anggota Lain (Ditemukan):**", len(df_ditemukan_all) - kepala_keluarga_ditemukan)
    
    # Tampilkan tabel jika filter sampai kepala keluarga
    if selected_kepala_keluarga != 'Semua':
        st.subheader("📋 Data Anggota Keluarga")
        
        # Filter hanya ART dengan keberadaan = "Ditemukan"
        df_ditemukan = df_filtered[df_filtered['keberadaan'] == 'Ditemukan']
        
        if len(df_ditemukan) == 0:
            st.warning("Tidak ada anggota keluarga dengan status 'Ditemukan'")
        else:
            # Pilih kolom yang penting untuk ditampilkan (termasuk semua kolom perhitungan)
            display_columns = [
                'nomor_urut_anggota_keluarga', 'nama_anggota_keluarga', 'status_hubungan', 
                'jenis_kelamin', 'tanggal_lahir', 'bulan_lahir', 'tahun_lahir', 'umur',
                'gaji_uang', 'gaji_barang', 'hari_kerja', 'jam_kerja', 
                'lulus_sd', 'lulus_smp', 'lulus_sma'
            ]
            
            # Filter hanya kolom yang ada di dataframe
            available_columns = [col for col in display_columns if col in df_ditemukan.columns]
            
            if available_columns:
                display_df = df_ditemukan[available_columns].copy()
                
                # Rename kolom untuk tampilan yang lebih baik
                column_rename = {
                    'nomor_urut_anggota_keluarga': 'No. Urut',
                    'nama_anggota_keluarga': 'Nama',
                    'status_hubungan': 'Status',
                    'jenis_kelamin': 'Jenis Kelamin',
                    'tanggal_lahir': 'Tgl Lahir',
                    'bulan_lahir': 'Bulan Lahir',
                    'tahun_lahir': 'Tahun Lahir',
                    'umur': 'Umur',
                    'gaji_uang': 'Gaji Uang (Rp)',
                    'gaji_barang': 'Gaji Barang (Rp)',
                    'hari_kerja': 'Hari Kerja',
                    'jam_kerja': 'Jam Kerja',
                    'lulus_sd': 'Lulus SD',
                    'lulus_smp': 'Lulus SMP',
                    'lulus_sma': 'Lulus SMA'
                }
                
                display_df = display_df.rename(columns=column_rename)
                
                # Format kolom gaji untuk display yang lebih baik
                for col in ['Gaji Uang (Rp)', 'Gaji Barang (Rp)']:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].apply(
                            lambda x: f"Rp {x:,.0f}" if x != '' and pd.notna(x) else x
                        )
                
                # Tampilkan tabel
                st.dataframe(
                    display_df, 
                    use_container_width=True,
                    hide_index=True
                )
                
                # Informasi tambahan dengan breakdown kolom perhitungan
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.info(f"👨‍👩‍👧‍👦 **Keluarga:** {selected_kepala_keluarga}")
                    st.info(f"📍 **Lokasi:** {selected_desa}, {selected_kecamatan}")
                
                with col_info2:
                    # Hitung statistik berdasarkan data yang ditemukan saja
                    total_anggota_ditemukan = len(df_ditemukan)
                    kepala_keluarga_ditemukan = len(df_ditemukan[df_ditemukan['status_hubungan'] == 'Kepala Keluarga']) if 'status_hubungan' in df_ditemukan.columns else 0
                    
                    st.info(f"👥 **Total Anggota (Ditemukan):** {total_anggota_ditemukan}")
                    
                    # Tampilkan range umur jika ada data umur
                    if 'Umur' in display_df.columns:
                        umur_data = display_df['Umur'][display_df['Umur'] != '']
                        if len(umur_data) > 0:
                            try:
                                umur_min = min(umur_data)
                                umur_max = max(umur_data)
                                st.info(f"🎂 **Range Umur:** {umur_min} - {umur_max} tahun")
                            except:
                                pass
            else:
                st.warning("Tidak ada data untuk ditampilkan")
    
    # Download Section
    st.header("📥 Download Data")
    
    col_download1, col_download2 = st.columns([2, 1])
    
    with col_download1:
        if st.button("📥 Generate & Download Excel", type="primary", use_container_width=True):
            with st.spinner('Membuat file Excel...'):
                excel_file = create_excel_file(df_filtered)
                
                # Generate filename with current timestamp and filter info
                timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
                filter_info = ""
                if selected_provinsi != 'Semua':
                    filter_info += f"_{selected_provinsi.replace(' ', '_')}"
                if selected_kecamatan != 'Semua':
                    filter_info += f"_{selected_kecamatan.replace(' ', '_')}"
                if selected_desa != 'Semua':
                    filter_info += f"_{selected_desa.replace(' ', '_')}"
                
                filename = f"supas_art_data{filter_info}_{timestamp}.xlsx"
                
                st.download_button(
                    label="📥 Download File Excel",
                    data=excel_file,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    with col_download2:
        df_ditemukan_download = df_filtered[df_filtered['keberadaan'] == 'Ditemukan']
        st.info(f"📄 **{len(df_filtered)}** total baris\n✅ **{len(df_ditemukan_download)}** ditemukan\n🏠 **{df_filtered['nama_kepala_keluarga'].nunique()}** keluarga")

if __name__ == "__main__":
    main()