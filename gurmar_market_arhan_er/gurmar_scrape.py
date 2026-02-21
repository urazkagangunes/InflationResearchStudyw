import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime

# -------------------------------------------------------------------
# KATEGORİLER (Senin düzenlediğin temiz yapı)
# -------------------------------------------------------------------
KATEGORILER = [
    ("Meyve ve Sebze", "https://www.gurmar.com.tr/meyve-ve-sebze-c?"),
    ("Et ve Tavuk", "https://www.gurmar.com.tr/et-ve-tavuk-urunleri-c?"),
    ("Süt, Kahvaltılık, Sark.", "https://www.gurmar.com.tr/sut-kahvaltiliklar-sarkuteri-c?"),
    ("Temel Gıda", "https://www.gurmar.com.tr/temel-gida-c?"),
    ("İçecekler", "https://www.gurmar.com.tr/icecekler-c?"),
    ("Atıştırmalıklar", "https://www.gurmar.com.tr/atistirmaliklar-c?"),
    ("Bebek Ürünleri", "https://www.gurmar.com.tr/bebek-urunleri-c?"),
    ("Deterjan ve Temizlik", "https://www.gurmar.com.tr/deterjan-temizlik-c?"),
    ("Kişisel Bakım", "https://www.gurmar.com.tr/kisisel-bakim-ve-hijyen-c?"),
    ("Ev ve Yaşam", "https://www.gurmar.com.tr/ev-yasam-c?"),
    ("Kitap, Kırtasiye", "https://www.gurmar.com.tr/kitap-kirtasiye-oyuncak-c?"),
    ("Petshop", "https://www.gurmar.com.tr/petshop-c?")
]


def main():
    driver = webdriver.Chrome()
    tum_urunler = []

    for kategori_adi, link in KATEGORILER:
        print(f"\n🔍 İşleniyor: {kategori_adi} ({link})")
        driver.get(link)
        time.sleep(3)

        # 1. Alt kategorilerin ilkine tıklama
        try:
            alt_kategoriler = driver.find_elements(By.CSS_SELECTOR, ".category-list-item a, .left-menu a")
            if alt_kategoriler:
                alt_kategoriler[0].click()
                time.sleep(3)
        except Exception:
            print(f"  ℹ️ Alt kategori bulunamadı, ana linkten devam ediliyor.")

        # 2. Beklenen Toplam Ürün Sayısını Çekme
        try:
            sayi_metni = driver.find_element(By.XPATH, "//*[contains(text(), 'ürün listeleniyor')]").text
            beklenen_sayi = int(re.search(r'\d+', sayi_metni).group())
            print(f"  📦 Beklenen ürün sayısı: {beklenen_sayi}")
        except Exception:
            beklenen_sayi = -1

        # 3. Tüm ürünlerin yüklenmesi için sayfayı aşağı kaydırma (Infinite Scroll)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # 4. Ürün Kartlarını Bulma ve Veri Çekme (Senin çıkardığın HTML yolları)
        urun_kartlari = driver.find_elements(By.CSS_SELECTOR, "div.product-vertical")
        cekilen_urun_sayisi = 0

        for kart in urun_kartlari:
            try:
                isim = kart.find_element(By.CSS_SELECTOR, "div:nth-child(2) > div:nth-child(3) > a > h4 > span").text

                kg_fiyat_yolu = "div:nth-child(2) > div:nth-child(3) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > span > div"
                kg_fiyat_elementleri = kart.find_elements(By.CSS_SELECTOR, kg_fiyat_yolu)

                if len(kg_fiyat_elementleri) > 0:
                    fiyat = kg_fiyat_elementleri[0].text
                    isim = isim + "_1kg"
                else:
                    normal_fiyat_yolu = "div:nth-child(2) > div:nth-child(3) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > span"
                    fiyat = kart.find_element(By.CSS_SELECTOR, normal_fiyat_yolu).text

                    # ₺ işaretini temizlemek istersen fiyat.replace("₺", "").strip() yapabilirsin
                tum_urunler.append({
                    "product_name": isim,
                    "product_price": fiyat.replace("₺", "").strip()
                })
                cekilen_urun_sayisi += 1

            except Exception:
                continue

        # 5. Sayı Kontrolü
        if beklenen_sayi != -1:
            if cekilen_urun_sayisi == beklenen_sayi:
                print(f"  ✅ Başarılı! Çekilen: {cekilen_urun_sayisi}")
            else:
                print(f"  ⚠️ Uyuşmazlık! Beklenen: {beklenen_sayi} | Çekilen: {cekilen_urun_sayisi}")
        else:
            print(f"  ✅ Çekilen ürün sayısı: {cekilen_urun_sayisi}")

    driver.quit()

    # 6. CSV'ye Kaydetme
    # Günün tarihini YYYY-AA-GG formatında alıyoruz
    bugunun_tarihi = datetime.now().strftime("%Y-%m-%d")
    csv_dosyasi = f'gurmar_prices_{bugunun_tarihi}.csv'

    with open(csv_dosyasi, 'w', newline='', encoding='utf-8-sig') as file:
        fieldnames = ['product_name', 'product_price']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for urun in tum_urunler:
            writer.writerow(urun)

    print(f"\n🎉 İşlem tamam! Tüm veriler '{csv_dosyasi}' dosyasına kaydedildi.")


if __name__ == "__main__":
    main()