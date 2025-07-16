import pandas as pd
from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import io
import base64
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__)

# Load DataFrame utama
excel_path = "C:/Users/DELL/Documents/Kelurahan_Tlogomas/Data_Usaha_Tlogomas.xlsx"
df = pd.read_excel(excel_path)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/profil')
def profil():
    rw_counts = df['RW'].value_counts().sort_index().to_dict()

    kategori_colors = {}
    if 'Kategori Lapangan Usaha' in df.columns:
        kategori_list = df['Kategori Lapangan Usaha'].dropna().unique()
        for i, kat in enumerate(sorted(kategori_list)):
            # Buat warna random tapi konsisten
            hash_val = sum(ord(c) for c in kat)
            r = (hash_val * 123) % 256
            g = (hash_val * 321) % 256
            b = (hash_val * 213) % 256
            warna = f'rgb({r},{g},{b})'
            kategori_colors[kat] = warna

    # Marker data
    if {'Latitude', 'Longitude', 'Kategori Lapangan Usaha'}.issubset(df.columns):
        df_marker = df[['Nama Usaha', 'Latitude', 'Longitude', 'Kategori Lapangan Usaha']].dropna()
        markers = df_marker.to_dict(orient='records')
    else:
        markers = []

    return render_template('profil.html', rw_counts=rw_counts, markers=markers, kategori_colors=kategori_colors)

@app.route('/detail-data', methods=['GET', 'POST'])
def data_usaha():
    list_kategori = sorted(df['Kategori Lapangan Usaha'].dropna().unique())
    list_rt = sorted(df['RT'].dropna().astype(str).unique())
    list_rw = sorted(df['RW'].dropna().astype(str).unique())

    kategori = request.form.get('kategori', 'ALL')
    rt = request.form.get('rt', 'ALL')
    rw = request.form.get('rw', 'ALL')

    df_filtered = df.copy()
    if kategori != 'ALL':
        df_filtered = df_filtered[df_filtered['Kategori Lapangan Usaha'] == kategori]
    if rt != 'ALL':
        df_filtered = df_filtered[df_filtered['RT'] == int(rt)]
    if rw != 'ALL':
        df_filtered = df_filtered[df_filtered['RW'] == int(rw)]

    total_usaha = df_filtered.shape[0]
    kategori_terbanyak = "-"
    jumlah_kategori_terbanyak = 0

    if not df_filtered.empty:
        vc = df_filtered['Kategori Lapangan Usaha'].value_counts()
        kategori_terbanyak = vc.idxmax()
        jumlah_kategori_terbanyak = vc.max()

    jumlah_gabung = df_filtered[df_filtered['Status Gabungan'] == 'Gabung'].shape[0]
    jumlah_independen = df_filtered[df_filtered['Status Gabungan'] == 'Independent (Tidak Gabung)'].shape[0]

    df_reg = df_filtered[['Latitude', 'Longitude', 'Kategori Lapangan Usaha']].copy()
    df_reg = df_reg[pd.to_numeric(df_reg['Latitude'], errors='coerce').notna()]
    df_reg = df_reg[pd.to_numeric(df_reg['Longitude'], errors='coerce').notna()]
    df_reg['Latitude'] = df_reg['Latitude'].astype(float)
    df_reg['Longitude'] = df_reg['Longitude'].astype(float)

    plot_url = None
    kategori_colors = {}

    if not df_reg.empty:
        le_kategori = LabelEncoder()
        df_reg['kategori_encoded'] = le_kategori.fit_transform(df_reg['Kategori Lapangan Usaha'])
        label_kategori = le_kategori.classes_.tolist()

        from matplotlib.cm import get_cmap
        cmap = get_cmap('tab10')
        for idx, kat in enumerate(label_kategori):
            rgba = cmap(idx % 10)
            hex_color = '#%02x%02x%02x' % tuple(int(255*x) for x in rgba[:3])
            kategori_colors[kat] = hex_color

        fig, ax = plt.subplots(figsize=(6, 5))
        scatter = ax.scatter(
            df_reg['Longitude'],
            df_reg['Latitude'],
            c=df_reg['kategori_encoded'],
            cmap='tab10',
            alpha=0.8,
            edgecolors='face'
        )

        ax.set_title("Peta Persebaran Usaha Berdasarkan Kategori")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.grid(True)

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plot_url = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()

    regresi_plot = None

    return render_template(
        "data_usaha.html",
        df_filtered=df_filtered,
        list_kategori=list_kategori,
        list_rt=list_rt,
        list_rw=list_rw,
        kategori=kategori,
        rt=rt,
        rw=rw,
        total_usaha=total_usaha,
        kategori_terbanyak=kategori_terbanyak,
        jumlah_kategori_terbanyak=jumlah_kategori_terbanyak,
        jumlah_gabung=jumlah_gabung,
        jumlah_independen=jumlah_independen,
        plot_url=plot_url,
        regresi_plot=regresi_plot,
        kategori_colors=kategori_colors
    )

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
