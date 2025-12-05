# 📘 **F1 Data Analysis Project**

---

# 🇬🇧 **F1 Data Analysis Project**

This project focuses on the analysis, cleaning, and visualization of a comprehensive Formula 1 dataset obtained from Kaggle.  
A total of 14 raw CSV files were processed to build a clean, analysis-ready data pipeline used for exploratory analysis, KPI modeling, and dashboard creation.

---

## 🏎️ **Project Overview**

The goal of this project is to understand the multi-layered structure of Formula 1 data and build a reliable model for analytical use.  
Categories of data included:

- Driver details  
- Constructor (team) details  
- Race schedule  
- Circuit information  
- Race results  
- Sprint results  
- Qualifying results  
- Lap timings  
- Pit stop records  
- Season summaries  
- Driver & constructor standings  
- Race status codes (including DNF reasons)

---

## 🧱 **Repository Structure**

```
F1_Data_Analysis_Project/
│
├── data/
│   ├── raw/            # 14 raw CSV files from Kaggle
│   └── processed/      # Cleaned clean_*.csv files
│
├── notebooks/
│   ├── 01_data_exploration.ipynb      # Exploratory Data Analysis (EDA)
│   ├── 02_data_cleaning.ipynb         # Data cleaning pipeline
│   └── 03_(model_to_be_added).ipynb   # KPI / analytical model (to be added)
│
├── formula1_page_1.png   # Dashboard preview image
└── README.md
```

---

## 🧪 **01 — Exploratory Data Analysis (EDA)**

During the EDA phase:

- Inspected row/column structures  
- Identified missing values (including `\N`)  
- Analyzed data types  
- Produced initial visual insights (driver nationality trends, races per season, grid vs finish relationships)  
- Identified all data issues to be addressed during cleaning  

This phase provided the foundation for constructing a consistent analytical dataset.

---

## 🧹 **02 — Data Cleaning**

In this phase, an analysis-ready dataset was created. Steps included:

- Converting `\N` to `NaN`  
- Converting date and time columns to proper datetime formats  
- Converting numerical fields to numeric types  
- Dropping unnecessary columns (e.g., `url`)  
- Creating new fields such as `fullName`  
- Merging race & sprint results with race status explanations  
- Exporting every cleaned file into `data/processed/` as **clean_*.csv**

This pipeline ensures a clean, reliable data foundation for KPIs, dashboards, and further analysis.

---

## 🧩 **03 — (Model to Be Added)**

This section will describe the analytical model produced in `03_(model_to_be_added).ipynb`.

**Placeholder:**

> This notebook will generate KPI tables and analytical datasets used for dashboard visualizations.  
> It will include transformations, aggregations, and additional derived metrics required by Looker Studio.  
> Once the model is finalized, detailed explanations and examples will be added here.

---

## 📊 **Dashboard (Looker Studio)**

This project includes a multi-page interactive dashboard built in Looker Studio.  
All calculations, KPIs, and transformations were implemented using **Looker Studio formulas** and **BigQuery logic**.

The dashboard includes several analytical pages such as:

- **Home Overview:** Global KPIs, constructor wins, DNF distribution, race locations  
- **Lap Performance:** Driver & team lap-time comparisons, consistency insights  
- **Excitement Analysis:** Race dynamics, position changes, action metrics  
- **Wins by Grid Position:** Grid vs final result relationships  
- **Team & Driver Insights:** Season trends, reliability, performance metrics  

Users can interactively filter the data by **year, driver, constructor, country, and Grand Prix**, allowing seamless exploration across the entire report.

*A preview of the first dashboard page is shown below.  
These visuals represent only part of the full report — you can visit the Looker Studio link to explore the complete dashboard.*

```
![Dashboard Preview](formula1_page_1.png)
```

### 🔗 **Looker Studio Dashboard Link**

👉 https://lookerstudio.google.com/reporting/790f1100-ab2f-45bd-bd97-7407dc92de00/page/p_xvx43nx1xd

---

## 🛠️ **Technologies Used**

- **Python** (pandas, numpy, matplotlib, seaborn)  
- **Jupyter Notebook**  
- **Looker Studio (Google Data Studio)**  
- **BigQuery**  
- **Git & GitHub**  
- **Virtual Environment (venv)**  

---

## 🚀 **Project Purpose**

This project aims to develop skills in data cleaning, analytics, and visualization by building an end-to-end pipeline using a large-scale Formula 1 dataset — ultimately enabling meaningful insights into the competitive landscape of F1 racing.

---

---

# 🇹🇷 **F1 Veri Analizi Projesi**

Bu proje, Kaggle üzerinden elde edilen kapsamlı Formula 1 veri setinin analiz edilmesi, temizlenmesi ve görselleştirilmesi üzerine kurulmuştur.  
Toplam 14 ham CSV dosyası işlenerek keşifsel analiz, KPI modelleme ve dashboard oluşturma için temiz bir veri modeli elde edilmiştir.

---

## 🏎️ **Proje İçeriği**

Amaç, Formula 1 verisinin çok katmanlı yapısını anlamak ve analiz için güvenilir bir veri modeli oluşturmaktır.  
Veri kategorileri:

- Sürücü detayları  
- Takım detayları  
- Yarış takvimi  
- Pist bilgileri  
- Yarış sonuçları  
- Sprint sonuçları  
- Sıralama turları sonuçları  
- Tur zamanları  
- Pit stop kayıtları  
- Sezon özetleri  
- Sürücü & takım sıralamaları  
- Yarış durum kodları (DNF nedenleri dahil)

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
│   ├── 01_data_exploration.ipynb      # EDA aşaması
│   ├── 02_data_cleaning.ipynb         # Temizlik pipeline'ı
│   └── 03_(eklenecek model).ipynb     # KPI / analiz modeli (eklenecek)
│
├── formula1_page_1.png   # Dashboard ilk sayfa görseli
└── README.md
```

---

## 🧪 **01 — Data Exploration (EDA)**

Bu aşamada:

- Tabloların satır/sütun yapıları incelendi  
- Eksik değerler (`\N`) belirlendi  
- Kolon tipleri analiz edildi  
- İlk görsel analizler üretildi (milliyet dağılımı, sezonlara göre yarış sayısı, grid vs finish ilişkisi)  
- Temizlik aşamasında yapılacak dönüşümler planlandı  

---

## 🧹 **02 — Data Cleaning**

Bu aşamada analiz için kullanılabilir, tutarlı bir veri yapısı oluşturulmuştur. Yapılan işlemler:

- `\N` → `NaN` dönüşümü  
- Tarih kolonlarının datetime formatına çevrilmesi  
- Sayısal kolonların numeric formata dönüştürülmesi  
- Gereksiz kolonların kaldırılması  
- `fullName` gibi ek kolonların oluşturulması  
- Yarış sonuçlarının yarış durum kodları ile birleştirilmesi  
- Tüm temiz dosyaların **clean_*.csv** olarak `data/processed/` altına kaydedilmesi  

---

## 🧩 **03 — (Eklenecek Model)**

Bu bölümde, `03_(eklenecek model).ipynb` içinde oluşturulacak KPI ve analiz modellerinin açıklaması yer alacaktır.

Eklenince buraya:

- Üretilen metrikler  
- Kullanılan dönüşümler  
- Oluşturulan veri tabloları  
- Dashboard bağlantıları  

eklenecektir.

---

## 📊 **Dashboard (Looker Studio)**

Bu proje kapsamında Looker Studio üzerinde çok sayfalı interaktif bir dashboard oluşturulmuştur.  
Dashboarddaki tüm hesaplamalar, metrikler ve dönüşümler **Looker Studio formülleri** ve **BigQuery sorguları** ile yapılmıştır.

Dashboard; genel bakış, tur performansı, heyecan analizleri, grid pozisyonu etkisi, takım–sürücü analizleri gibi çeşitli sayfalardan oluşmaktadır.  
Dashboard; **yıl, sürücü, takım, ülke ve Grand Prix** filtreleriyle tamamen interaktif çalışır.

*Aşağıdaki görsel dashboard’un sadece ilk sayfasını göstermektedir.  
Raporun tamamını incelemek için Looker Studio bağlantısını ziyaret edebilirsiniz.*

```
![Dashboard Görseli](formula1_page_1.png)
```

### 🔗 **Looker Studio Dashboard Bağlantısı**

👉 https://lookerstudio.google.com/reporting/790f1100-ab2f-45bd-bd97-7407dc92de00/page/p_xvx43nx1xd

---

## 🛠️ **Kullanılan Teknolojiler**

- **Python** (pandas, numpy, matplotlib, seaborn)  
- **Jupyter Notebook**  
- **Looker Studio**  
- **BigQuery**  
- **Git & GitHub**  
- **Virtual Environment (venv)**  

---

## 🚀 **Projenin Amacı**

Bu proje, veri temizleme, analiz ve görselleştirme becerilerini geliştirmek;  
büyük F1 veri seti üzerinde uçtan uca bir veri pipeline'ı kurmak  
ve F1 dünyasının rekabetçi dinamiklerini anlamak amacıyla hazırlanmıştır.

