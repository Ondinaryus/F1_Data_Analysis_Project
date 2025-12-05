# 📘 **F1 Data Analysis Project**

Bu proje, Formula 1 yarışlarına ait çok kapsamlı bir veri setinin analiz edilmesi, temizlenmesi ve görselleştirilmesi üzerine kurulmuştur. Hammadde veriler (14 adet CSV dosyası), Kaggle üzerinden alınmıştır. Proje boyunca veri temizleme, keşifsel analiz (EDA) ve dashboard oluşturma adımları uygulanmıştır.

---

## 🏎️ **Proje İçeriği**

Proje, F1 verilerinin çok katmanlı yapısını anlamayı ve analiz için güvenilir bir veri modeli oluşturmayı hedefler.
Kullanılan veri kategorileri:

* Sürücü detayları
* Takım detayları
* Yarış takvimi
* Pist bilgileri
* Yarış sonuçları
* Sprint sonuçları
* Sıralama turları sonuçları
* Tur zamanları
* Pit stop bilgileri
* Sezon özetleri
* Sıralama tablosu (driver & constructor standings)
* Yarış durumu açıklamaları (DNF nedenleri vb.)

---

## 🧱 **Klasör Yapısı**

```
F1_Data_Analysis_Project/
│
├── data/
│   ├── raw/            # Kaggle'dan indirilen 14 ham CSV
│   └── processed/      # Temizlenmiş clean_*.csv dosyaları
│
├── notebooks/
│   ├── 01_data_exploration.ipynb   # EDA aşaması
│   └── 02_data_cleaning.ipynb      # Temizlik pipeline'ı
│
├── scripts/            # (Opsiyonel) Veri işleme scriptleri
├── visuals/            # Dashboard veya görseller
│
├── venv/               # Sanal Python ortamı
└── README.md           # Proje dökümantasyonu
```

---

## 🧪 **01 — Data Exploration (EDA)**

Bu aşamada tüm ham veri setleri keşfedilerek:

* Satır/sütun yapıları incelendi
* Eksik değerler ve `\N` işaretleri tespit edildi
* Kolon tipleri analiz edildi
* İlk görsel analizler (driver nationality, races per season, grid vs final position) oluşturuldu
* Temizlik aşaması için gereksinimler belirlendi

Bu aşama sonucunda, veri modelinin tutarsızlıkları ve dönüştürülmesi gereken kolonlar netleşti.

---

## 🧹 **02 — Data Cleaning**

Bu aşamada proje için analiz-ready veri seti oluşturuldu. Yapılan işlemler:

* `\N` → `NaN` dönüşümü tüm dosyalara uygulandı
* Tarih kolonları datetime tipine dönüştürüldü
* Sayısal kolonlar numeric hale getirildi
* Gereksiz kolonlar kaldırıldı (örn. `url`)
* Yeni kolonlar oluşturuldu (`fullName` gibi)
* Race & sprint results tabloları, race status ile birleştirilerek DNF açıklamaları eklendi
* Tüm temiz veriler `data/processed/` altına **clean_*.csv** olarak kaydedildi

Bu pipeline sayesinde analiz, dashboard ve modelleme için tam uyumlu bir veri altyapısı oluşturuldu.

---

## 📊 **Dashboard (Looker Studio)**

Projenin analiz çıktıları Looker Studio üzerinden görselleştirilecektir.

Dashboard kapsamında planlanan bölümler:

* Sürücü performans analizleri
* Takım (constructor) performansı
* Pist bazlı karşılaştırmalar
* Sezon trendleri
* Yarış içi metrikler (grid vs finish, pit stop etkisi, lap time analizleri)

(Yayınlandığında buraya link eklenecek.)

---

## 🛠️ **Kullanılan Teknolojiler**

* **Python** (pandas, numpy, matplotlib, seaborn)
* **Jupyter Notebook**
* **Looker Studio (Google Data Studio)**
* **Git & GitHub**
* **Virtual Environment (venv)**

---

## 🚀 **Projenin Amacı**

Bu proje, veri temizleme, analiz ve görselleştirme becerilerini geliştirmek;
büyük ölçekli bir veri seti üzerinde uçtan uca veri pipeline'ı kurmak
ve F1 dünyasındaki rekabet dinamiklerini anlamak amacıyla oluşturulmuştur.

---

## 📥 **Reponun Çalıştırılması**

### 1) Reponun klonlanması

```bash
git clone <repo-link>
cd F1_Data_Analysis_Project
```

### 2) Sanal ortam oluşturma

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3) Gerekli paketlerin yüklenmesi

```bash
pip install -r requirements.txt  # (opsiyonel)
```

### 4) Notebookların çalıştırılması

```
notebooks/01_data_exploration.ipynb  
notebooks/02_data_cleaning.ipynb  
```

---

## 📝 **Lisans**

Bu proje eğitim ve analiz amaçlıdır.
Veri seti Kaggle üzerinden sağlanmıştır.

---
