LOGIC TOOL: THE MARKET SCRAPER
Ini BUKAN agen LLM. Ini adalah script Python keras (hardcode) yang mengeksekusi pencarian YouTube dan web scraping berdasarkan perintah The Trend Researcher.
1. CARA KERJA (THE ALGORITHM)
Tool ini menggantikan jari bos yang biasanya mencari video secara manual di YouTube.
Terima Keyword & Filter Waktu: Python menerima keyword (misal: "NTE hidden lore") dan filter_waktu (misal: "This Month") dari The Trend Researcher.
Hit YouTube Search API: Mencari maksimal 50 hasil pencarian teratas.
Hit YouTube Video API (Statistik): Mengecek views, likes, dan jumlah subscriber dari 50 video tersebut.
Filtering & Outlier Math (Logic Python):
Buang video dengan views < 100.000 (kecuali V/S ratio-nya gila).
Hitung V/S Ratio (Views dibagi Subscribers). Jika channel dengan 1.000 subs mendapat 50.000 views, ini adalah Outlier (Skor tinggi).
Ambil Top 10 Video paling berpotensi.
Deep Dive Extraction (Hanya untuk Top 10):
Tarik URL Thumbnail.
Tarik 50 Top Comments menggunakan YouTube Comment API.
Sedot Auto-Generated Captions (Transkrip) menggunakan library pihak ketiga, potong HANYA 60 detik pertamanya (ini adalah area Hook).
2. OUTPUT TOOL (HANDOFF KE THE TREND RESEARCHER)
Tool ini akan mengembalikan data JSON mentah yang sangat padat berisi daftar 10 video kompetitor, lengkap dengan judul, skor outlier, teks 50 komentar, URL thumbnail, dan teks transkrip 1 menit pertama mereka. Data ini akan dibaca dan dianalisis oleh otak The Trend Researcher.
