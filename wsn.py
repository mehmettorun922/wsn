import pygame
import pygame.gfxdraw
import random
import math
import sys
import os
import pandas as pd
from datetime import datetime

ARKAPLAN_DOSYASI = "harita.png"
EKRAN_GENISLIK = 1400
EKRAN_YUKSEKLIK = 800
HARITA_GENISLIK = 1050
PANEL_GENISLIK = EKRAN_GENISLIK - HARITA_GENISLIK
FPS = 60

RENK_ARKA_PLAN = (15, 20, 25)
RENK_PANEL = (22, 28, 38)
RENK_IZGARA = (45, 55, 75) 
RENK_TURKUAZ = (0, 255, 255)
RENK_YESIL = (30, 255, 120)
RENK_SARI = (255, 220, 0)
RENK_KIRMIZI = (255, 60, 60)
RENK_BEYAZ = (250, 250, 250)
RENK_GRI = (130, 140, 150)
RENK_MOR = (180, 100, 255)

pygame.init()
ekran = pygame.display.set_mode((EKRAN_GENISLIK, EKRAN_YUKSEKLIK), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("Sensör Ağı Simülasyonu ve Veri Analizi")
saat_yoneticisi = pygame.time.Clock()

font_kucuk = pygame.font.SysFont("Consolas", 11)
font_orta = pygame.font.SysFont("Consolas", 16, bold=True)
font_buyuk = pygame.font.SysFont("Consolas", 22, bold=True)
font_baslik = pygame.font.SysFont("Consolas", 26, bold=True)


def kapak_ekrani():
    giris = True
    while giris:
        ekran.fill(RENK_ARKA_PLAN)
        t1 = font_baslik.render("Sensör Sayısı ve Veri Gönderim Sıklığının", True, RENK_TURKUAZ)
        t2 = font_baslik.render("Ağ Trafiğine Etkisinin Simülasyonu", True, RENK_TURKUAZ)
        t3 = font_orta.render("Mehmet Torun", True, RENK_BEYAZ)
        t4 = font_orta.render("24370031081", True, RENK_GRI)
        t5 = font_kucuk.render("DEVAM ETMEK İÇİN BİR TUŞA BASIN", True, RENK_SARI)
        
        ekran.blit(t1, t1.get_rect(center=(EKRAN_GENISLIK//2, 250)))
        child_rect = t2.get_rect(center=(EKRAN_GENISLIK//2, 300))
        ekran.blit(t2, child_rect)
        ekran.blit(t3, t3.get_rect(center=(EKRAN_GENISLIK//2, 450)))
        ekran.blit(t4, t4.get_rect(center=(EKRAN_GENISLIK//2, 480)))
        ekran.blit(t5, t5.get_rect(center=(EKRAN_GENISLIK//2, 650)))
        
        pygame.display.flip()
        for olay in pygame.event.get():
            if olay.type == pygame.QUIT: pygame.quit(); sys.exit()
            if olay.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]: giris = False

kapak_ekrani()

harita_katmani = pygame.Surface((HARITA_GENISLIK, EKRAN_YUKSEKLIK))
harita_katmani.fill(RENK_ARKA_PLAN)
if os.path.exists(ARKAPLAN_DOSYASI):
    try:
        ham_resim = pygame.image.load(ARKAPLAN_DOSYASI).convert()
        harita_katmani = pygame.transform.smoothscale(ham_resim, (HARITA_GENISLIK, EKRAN_YUKSEKLIK))
        maske = pygame.Surface((HARITA_GENISLIK, EKRAN_YUKSEKLIK))
        maske.fill((15, 20, 25)); maske.set_alpha(170)
        harita_katmani.blit(maske, (0, 0))
    except: pass

def ciz_parlama(yuzey, renk, merkez, maks_yaricap):
    parlama_yuzeyi = pygame.Surface((maks_yaricap * 2, maks_yaricap * 2), pygame.SRCALPHA)
    for r in range(maks_yaricap, 0, -2):
        alpha = int(255 * (1 - r / max(1, maks_yaricap))) // 4
        pygame.draw.circle(parlama_yuzeyi, (*renk, alpha), (maks_yaricap, maks_yaricap), r)
    yuzey.blit(parlama_yuzeyi, (merkez[0] - maks_yaricap, merkez[1] - maks_yaricap))

class ArayuzButonu:
    def __init__(self, x, y, w, h, metin, renk, font=font_orta):
        self.dikdortgen = pygame.Rect(x, y, w, h)
        self.metin = metin
        self.renk = renk
        self.font = font
        self.fare_uzerinde = False

    def ciz(self, yuzey, secili_mi=False):
        guncel_renk = (min(255, self.renk[0]+40), min(255, self.renk[1]+40), min(255, self.renk[2]+40)) if self.fare_uzerinde or secili_mi else self.renk
        pygame.draw.rect(yuzey, guncel_renk, self.dikdortgen, border_radius=6)
        cerceve_renk = RENK_SARI if secili_mi else RENK_TURKUAZ
        pygame.draw.rect(yuzey, cerceve_renk, self.dikdortgen, 2 if secili_mi else 1, border_radius=6)
        metin_yuzeyi = self.font.render(self.metin, True, RENK_BEYAZ)
        yuzey.blit(metin_yuzeyi, metin_yuzeyi.get_rect(center=self.dikdortgen.center))

    def guncelle(self, fare_konumu):
        self.fare_uzerinde = self.dikdortgen.collidepoint(fare_konumu)

    def tiklandi_mi(self, olay):
        return olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1 and self.dikdortgen.collidepoint(olay.pos)

class SensorDugumu:
    def __init__(self, id_no):
        self.id = id_no
        self.isim = f"Sensor_{id_no:02d}"
        self.pos_x = random.randint(150, HARITA_GENISLIK - 150)
        self.pos_y = random.randint(150, EKRAN_YUKSEKLIK - 150)
        self.batarya_seviyesi = 100.0
        self.surukleniyor = False
        self.secili = False
        self.paket_konumu = random.random()
        self.hedef_obj = None 
        self.yuk_miktari = 1 
        self.toplam_paket = 0.0

    def rota_bul(self, tum_sensorler, merkez_konum):
        if self.batarya_seviyesi <= 0:
            self.hedef_obj = None
            return
            
        en_yakin_mesafe = math.sqrt((self.pos_x - merkez_konum[0])**2 + (self.pos_y - merkez_konum[1])**2)
        self.hedef_obj = None 

        for diger in tum_sensorler:
            if diger.id == self.id or diger.batarya_seviyesi <= 0: continue
            d = math.sqrt((self.pos_x - diger.pos_x)**2 + (self.pos_y - diger.pos_y)**2)
            if d < 180: 
                d_merkez = math.sqrt((diger.pos_x - merkez_konum[0])**2 + (diger.pos_y - merkez_konum[1])**2)
                if d_merkez < en_yakin_mesafe:
                    en_yakin_mesafe = d_merkez
                    self.hedef_obj = diger

    def tuketim_hesapla(self, merkez_konum):
        hedef = (self.hedef_obj.pos_x, self.hedef_obj.pos_y) if self.hedef_obj else merkez_konum
        mesafe = math.sqrt((self.pos_x - hedef[0])**2 + (self.pos_y - hedef[1])**2)
        saatlik_joule = (0.45 + (mesafe**2) * 0.000075) * self.yuk_miktari 
        return mesafe, saatlik_joule

    def veri_akisi_guncelle(self, merkez_konum, aktif, hiz):
        if aktif and self.batarya_seviyesi > 0:
            mesafe, j_h = self.tuketim_hesapla(merkez_konum)
            tuketim_miktari = (j_h / 3600) * hiz * (60 / FPS)
            self.batarya_seviyesi -= tuketim_miktari
            
            self.toplam_paket += self.yuk_miktari * (hiz / FPS)
            
            self.paket_konumu += 0.015 * (hiz**0.4) 
            if self.paket_konumu > 1: self.paket_konumu = 0
            if self.batarya_seviyesi < 0: self.batarya_seviyesi = 0

    def gorsellestir(self, yuzey, merkez_konum, fare_konum):
        hedef = (self.hedef_obj.pos_x, self.hedef_obj.pos_y) if self.hedef_obj else merkez_konum
        mesafe, joule = self.tuketim_hesapla(merkez_konum)
        fare_uzerinde = math.sqrt((fare_konum[0] - self.pos_x)**2 + (fare_konum[1] - self.pos_y)**2) < 15
        
        renk_durumu = RENK_YESIL if self.batarya_seviyesi > 50 else (RENK_SARI if self.batarya_seviyesi > 20 else RENK_KIRMIZI)
        if self.batarya_seviyesi <= 0: renk_durumu = (70, 80, 90)

        kapsama_yuzeyi = pygame.Surface((200, 200), pygame.SRCALPHA)
        if self.batarya_seviyesi > 0:
            pygame.draw.circle(kapsama_yuzeyi, (0, 255, 255, 25), (100, 100), 100)
        else:
            pygame.draw.circle(kapsama_yuzeyi, (255, 0, 0, 50), (100, 100), 100)
        yuzey.blit(kapsama_yuzeyi, (self.pos_x - 100, self.pos_y - 100))
        
        if self.secili or fare_uzerinde:
            ciz_parlama(yuzey, RENK_TURKUAZ, (int(self.pos_x), int(self.pos_y)), 35)
            bilgi_bg = pygame.Rect(self.pos_x + 15, self.pos_y - 80, 140, 90)
            pygame.draw.rect(yuzey, (20, 30, 40), bilgi_bg, border_radius=5)
            pygame.draw.rect(yuzey, RENK_TURKUAZ, bilgi_bg, 1, border_radius=5)
            
            yuzey.blit(font_orta.render(self.isim, True, RENK_TURKUAZ), (self.pos_x + 22, self.pos_y - 75))
            yuzey.blit(font_kucuk.render(f"Mesafe: {int(mesafe)}m", True, RENK_BEYAZ), (self.pos_x + 22, self.pos_y - 57))
            yuzey.blit(font_kucuk.render(f"Anlık Yük: {self.yuk_miktari} Pkt", True, RENK_MOR), (self.pos_x + 22, self.pos_y - 43))
            yuzey.blit(font_kucuk.render(f"Top. Paket: {int(self.toplam_paket)}", True, RENK_YESIL), (self.pos_x + 22, self.pos_y - 29))
            yuzey.blit(font_kucuk.render(f"Güç: {joule:.2f}J/h", True, RENK_SARI), (self.pos_x + 22, self.pos_y - 15))

        if self.batarya_seviyesi > 0:
            pygame.draw.aaline(yuzey, (80, 100, 120), (self.pos_x, self.pos_y), hedef)
            px = self.pos_x + (hedef[0] - self.pos_x) * self.paket_konumu
            py = self.pos_y + (hedef[1] - self.pos_y) * self.paket_konumu
            pygame.gfxdraw.filled_circle(yuzey, int(px), int(py), 4, RENK_TURKUAZ)

        pygame.gfxdraw.filled_circle(yuzey, int(self.pos_x), int(self.pos_y), 8, renk_durumu)
        yuzey.blit(font_kucuk.render(f"%{int(self.batarya_seviyesi)}", True, RENK_BEYAZ), (self.pos_x - 10, self.pos_y + 12))

def excel_disa_aktar(veriler):
    if not veriler: 
        print("Kaydedilecek veri bulunamadı!")
        return
    try:
        df = pd.DataFrame(veriler)
        df.fillna(0, inplace=True) 
        zaman_damgasi = datetime.now().strftime('%Y%m%d_%H%M%S')
        dosya_adi = f"Sensor_Sistemi_Raporu_{zaman_damgasi}.xlsx"
        
        writer = pd.ExcelWriter(dosya_adi, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Veri_Analizi', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Veri_Analizi']
        worksheet.freeze_panes(1, 0)
        
        header_fmt = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#1F4E78', 'border': 1, 'align': 'center'})
        num_fmt = workbook.add_format({'align': 'center', 'num_format': '#,##0.0'})
        
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 15, num_fmt)

        worksheet.conditional_format(1, 2, len(df), 2, {
            'type': '2_color_scale',
            'min_color': "#FF0000",
            'max_color': "#00FF00"
        })

        chart_perf = workbook.add_chart({'type': 'line'})
        chart_perf.add_series({
            'name': 'Aktif Sensör Sayısı',
            'categories': ['Veri_Analizi', 1, 0, len(df), 0],
            'values':     ['Veri_Analizi', 1, 1, len(df), 1],
            'line':       {'color': '#4472C4', 'width': 2},
        })
        chart_perf.set_title({'name': 'Zaman Bazlı Sistem Sağlığı'})
        chart_perf.set_x_axis({'name': 'Simülasyon Saati'})
        chart_perf.set_y_axis({'name': 'Cihaz Sayısı'})
        worksheet.insert_chart('H2', chart_perf, {'x_scale': 1.8, 'y_scale': 1.5})

        chart_load = workbook.add_chart({'type': 'area', 'subtype': 'stacked'})
        for i, col in enumerate(df.columns):
            if 'AnlikYuk' in col:
                chart_load.add_series({
                    'name': col.replace('_AnlikYuk', ''),
                    'categories': ['Veri_Analizi', 1, 0, len(df), 0], 
                    'values':     ['Veri_Analizi', 1, i, len(df), i], 
                })

        chart_load.set_title({'name': 'Kümülatif Ağ Trafik Yükü (Düğüm Bazlı)'})
        chart_load.set_x_axis({
            'name': 'Simülasyon Süresi (Saat)',
            'name_font': {'size': 12, 'bold': True},
            'num_font':  {'italic': True}
        })
        chart_load.set_y_axis({
            'name': 'Anlık Veri Trafiği (Paket/sn)',
            'name_font': {'size': 12, 'bold': True},
            'major_gridlines': {'visible': True}
        })


        worksheet.insert_chart('H28', chart_load, {'x_scale': 1.8, 'y_scale': 1.5})

        writer.close()
        print(f"Rapor Hazır: {dosya_adi}")
    except Exception as e: 
        print(f"Excel Hatası: {e}")

def sistemi_kur():
    return [SensorDugumu(i) for i in range(10)]

sensor_listesi = sistemi_kur()
merkez_istasyon_konumu = [HARITA_GENISLIK // 2, EKRAN_YUKSEKLIK // 2]
istasyon_surukleniyor = simulasyon_aktif = False
toplam_simulasyon_saati = 0.0
simulasyon_saati = 0.0
veri_kayitlari = []
son_kayit_zamani = 0.0
KAYIT_ARALIGI = 0.5 

anlik_grafik_verisi = []
MAKS_ANLIK_VERI = 150

zaman_carpanlari = [1, 5, 20, 60, 300, 1200]
hiz_indeksi = radar_yari_cap = aktif_sayfa = 0
SAYFA_BASI_SENSOR = 8
secili_dugum = None
panel_sekmesi = 0

btn_sekme_kontrol = ArayuzButonu(HARITA_GENISLIK + 20, 20, 150, 40, "KONTROLLER", (40, 50, 70))
btn_sekme_grafik = ArayuzButonu(HARITA_GENISLIK + 180, 20, 150, 40, "DETAYLI GRAFİK", (40, 50, 70))
btn_baslat = ArayuzButonu(HARITA_GENISLIK + 40, 100, 270, 45, "SİSTEMİ BAŞLAT/DURDUR", (35, 75, 140))
btn_hiz_eksi = ArayuzButonu(HARITA_GENISLIK + 40, 155, 60, 40, "[-]", (80, 50, 110))
btn_hiz_arti = ArayuzButonu(HARITA_GENISLIK + 250, 155, 60, 40, "[+]", (80, 50, 110))
btn_sensor_ekle = ArayuzButonu(HARITA_GENISLIK + 40, 205, 130, 35, "DÜĞÜM +", (45, 110, 65))
btn_sensor_sil = ArayuzButonu(HARITA_GENISLIK + 180, 205, 130, 35, "DÜĞÜM -", (160, 60, 50))
btn_sayfa_geri = ArayuzButonu(HARITA_GENISLIK + 100, 495, 40, 25, "<", (60, 70, 85), font_kucuk)
btn_sayfa_ileri = ArayuzButonu(HARITA_GENISLIK + 210, 495, 40, 25, ">", (60, 70, 85), font_kucuk)
btn_excel = ArayuzButonu(HARITA_GENISLIK + 40, 700, 270, 40, "EXCEL'E AKTAR (GRAFİKLİ)", (40, 130, 70))
btn_reset = ArayuzButonu(HARITA_GENISLIK + 40, 750, 270, 40, "SİSTEMİ SIFIRLA", (180, 50, 50))
kontrol_butonlari = [btn_baslat, btn_hiz_eksi, btn_hiz_arti, btn_sensor_ekle, btn_sensor_sil, btn_sayfa_geri, btn_sayfa_ileri, btn_excel, btn_reset]

while True:
    ekran.fill(RENK_ARKA_PLAN)
    fare_pos = pygame.mouse.get_pos()
    toplam_sayfa = max(1, math.ceil(len(sensor_listesi) / SAYFA_BASI_SENSOR))

    for s in sensor_listesi: s.yuk_miktari = 1 
    for s in sensor_listesi:
        s.rota_bul(sensor_listesi, merkez_istasyon_konumu)
        if s.hedef_obj: s.hedef_obj.yuk_miktari += 1 

    if simulasyon_aktif:
        zaman_artisi = (zaman_carpanlari[hiz_indeksi] / 3600) * (60 / FPS)
        toplam_simulasyon_saati += zaman_artisi
        simulasyon_saati = toplam_simulasyon_saati % 24.0
        

        if toplam_simulasyon_saati - son_kayit_zamani >= KAYIT_ARALIGI:
            aktif_say = len([s for s in sensor_listesi if s.batarya_seviyesi > 0])
            ort_batarya = sum([s.batarya_seviyesi for s in sensor_listesi]) / len(sensor_listesi) if sensor_listesi else 0
            
            kayit_satiri = {
                "Zaman_Saat": round(toplam_simulasyon_saati, 2),
                "Aktif_Dugum": aktif_say,
                "Ort_Batarya": round(ort_batarya, 2)
            }
            for s in sensor_listesi:
                kayit_satiri[f"S{s.id}_AnlikYuk"] = s.yuk_miktari
                kayit_satiri[f"S{s.id}_ToplamPaket"] = round(s.toplam_paket, 1)
                
            veri_kayitlari.append(kayit_satiri)
            son_kayit_zamani = toplam_simulasyon_saati


        anlik_yuk_toplami = sum(s.yuk_miktari for s in sensor_listesi if s.batarya_seviyesi > 0)
        anlik_batarya_ort = sum([s.batarya_seviyesi for s in sensor_listesi]) / max(1, len(sensor_listesi))
        anlik_grafik_verisi.append({'yuk': anlik_yuk_toplami, 'batarya': anlik_batarya_ort})
        if len(anlik_grafik_verisi) > MAKS_ANLIK_VERI:
            anlik_grafik_verisi.pop(0)

    ekran.blit(harita_katmani, (0, 0))
    for i in range(0, HARITA_GENISLIK + 1, 150):
        pygame.draw.line(ekran, RENK_IZGARA, (i, 0), (i, EKRAN_YUKSEKLIK), 1)
        coord_txt = font_kucuk.render(f"{34.120 + i/1000:.3f}E", True, (120, 140, 160))
        ekran.blit(coord_txt, (i + 5 if i > 0 else 45, 5))
    for j in range(0, EKRAN_YUKSEKLIK + 1, 150):
        pygame.draw.line(ekran, RENK_IZGARA, (0, j), (HARITA_GENISLIK, j), 1)
        coord_txt = font_kucuk.render(f"{42.050 + j/1000:.3f}N", True, (120, 140, 160))
        ekran.blit(coord_txt, (5, j + 5 if j > 0 else 20))


    for olay in pygame.event.get():
        if olay.type == pygame.QUIT: pygame.quit(); sys.exit()
        if olay.type == pygame.MOUSEBUTTONDOWN and olay.button == 1:
            if fare_pos[0] < HARITA_GENISLIK:
                if secili_dugum: secili_dugum.secili = False
                if math.sqrt((fare_pos[0] - merkez_istasyon_konumu[0])**2 + (fare_pos[1] - merkez_istasyon_konumu[1])**2) < 25:
                    istasyon_surukleniyor = True
                for sd in sensor_listesi:
                    if math.sqrt((fare_pos[0] - sd.pos_x)**2 + (fare_pos[1] - sd.pos_y)**2) < 15:
                        sd.surukleniyor = sd.secili = True; secili_dugum = sd
            elif HARITA_GENISLIK + 20 <= fare_pos[0]:
                if panel_sekmesi == 0 and 285 <= fare_pos[1] <= 285 + (SAYFA_BASI_SENSOR * 24):
                    idx = (aktif_sayfa * SAYFA_BASI_SENSOR) + (fare_pos[1] - 285) // 24
                    if idx < len(sensor_listesi):
                        if secili_dugum: secili_dugum.secili = False
                        secili_dugum = sensor_listesi[idx]; secili_dugum.secili = True

        if olay.type == pygame.KEYDOWN and secili_dugum:
            if olay.key == pygame.K_BACKSPACE: secili_dugum.isim = secili_dugum.isim[:-1]
            elif olay.key in (pygame.K_RETURN, pygame.K_ESCAPE): secili_dugum.secili = False; secili_dugum = None
            elif len(secili_dugum.isim) < 12 and olay.unicode.isprintable(): secili_dugum.isim += olay.unicode
            
        if olay.type == pygame.MOUSEBUTTONUP:
            istasyon_surukleniyor = False
            for sd in sensor_listesi: sd.surukleniyor = False
            
        if btn_sekme_kontrol.tiklandi_mi(olay): panel_sekmesi = 0
        if btn_sekme_grafik.tiklandi_mi(olay): panel_sekmesi = 1
            
        if panel_sekmesi == 0:
            if btn_baslat.tiklandi_mi(olay): simulasyon_aktif = not simulasyon_aktif
            if btn_hiz_arti.tiklandi_mi(olay) and hiz_indeksi < len(zaman_carpanlari)-1: hiz_indeksi += 1
            if btn_hiz_eksi.tiklandi_mi(olay) and hiz_indeksi > 0: hiz_indeksi -= 1
            if btn_sensor_ekle.tiklandi_mi(olay): sensor_listesi.append(SensorDugumu(len(sensor_listesi)))
            if btn_sensor_sil.tiklandi_mi(olay) and len(sensor_listesi) > 1: sensor_listesi.pop()
            if btn_sayfa_geri.tiklandi_mi(olay) and aktif_sayfa > 0: aktif_sayfa -= 1
            if btn_sayfa_ileri.tiklandi_mi(olay) and aktif_sayfa < toplam_sayfa - 1: aktif_sayfa += 1
            if btn_excel.tiklandi_mi(olay): excel_disa_aktar(veri_kayitlari)
            if btn_reset.tiklandi_mi(olay):
                sensor_listesi = sistemi_kur(); simulasyon_aktif = False
                toplam_simulasyon_saati = 0.0; veri_kayitlari.clear(); anlik_grafik_verisi.clear()
                hiz_indeksi = 0; aktif_sayfa = 0

    if istasyon_surukleniyor: merkez_istasyon_konumu[0], merkez_istasyon_konumu[1] = fare_pos
    for sd in sensor_listesi:
        if sd.surukleniyor: sd.pos_x, sd.pos_y = fare_pos
        sd.veri_akisi_guncelle(merkez_istasyon_konumu, simulasyon_aktif, zaman_carpanlari[hiz_indeksi])
        sd.gorsellestir(ekran, merkez_istasyon_konumu, fare_pos)
    
    if simulasyon_aktif:
        radar_yari_cap += 1.5 * (zaman_carpanlari[hiz_indeksi]**0.3)
        if radar_yari_cap > 120: radar_yari_cap = 0
        radar_yuzeyi = pygame.Surface((240, 240), pygame.SRCALPHA)
        pygame.draw.circle(radar_yuzeyi, (*RENK_TURKUAZ, max(0, 255-int(radar_yari_cap*2))), (120, 120), int(radar_yari_cap), 2)
        ekran.blit(radar_yuzeyi, (merkez_istasyon_konumu[0]-120, merkez_istasyon_konumu[1]-120))

    pygame.draw.circle(ekran, RENK_BEYAZ, merkez_istasyon_konumu, 8)
    pygame.draw.circle(ekran, RENK_TURKUAZ, merkez_istasyon_konumu, 20, 2)
    ekran.blit(font_orta.render("MERKEZ ÜS", True, RENK_TURKUAZ), (merkez_istasyon_konumu[0]-35, merkez_istasyon_konumu[1]+25))

    pygame.draw.rect(ekran, RENK_PANEL, (HARITA_GENISLIK, 0, PANEL_GENISLIK, EKRAN_YUKSEKLIK))
    pygame.draw.line(ekran, RENK_TURKUAZ, (HARITA_GENISLIK, 0), (HARITA_GENISLIK, EKRAN_YUKSEKLIK), 2)
    btn_sekme_kontrol.guncelle(fare_pos); btn_sekme_kontrol.ciz(ekran, (panel_sekmesi==0))
    btn_sekme_grafik.guncelle(fare_pos); btn_sekme_grafik.ciz(ekran, (panel_sekmesi==1))

    if panel_sekmesi == 0:
        pygame.draw.rect(ekran, (30, 40, 55), (HARITA_GENISLIK + 20, 55, PANEL_GENISLIK - 40, 35), border_radius=5)
        ekran.blit(font_orta.render("SİSTEM AKTİF" if simulasyon_aktif else "BEKLEMEDE", True, RENK_YESIL if simulasyon_aktif else RENK_KIRMIZI), (HARITA_GENISLIK + 110, 63))
        hiz_txt = font_buyuk.render(f"HIZ: {zaman_carpanlari[hiz_indeksi]}x", True, RENK_SARI)
        ekran.blit(hiz_txt, hiz_txt.get_rect(center=(HARITA_GENISLIK + 175, 175)))
        panel_y = 250
        pygame.draw.rect(ekran, (30, 40, 55), (HARITA_GENISLIK + 20, panel_y, PANEL_GENISLIK - 40, 280), border_radius=8)
        ekran.blit(font_kucuk.render(f"Sayfa {aktif_sayfa+1}/{toplam_sayfa}", True, RENK_GRI), (HARITA_GENISLIK + 140, 502))
        for btn in kontrol_butonlari: btn.guncelle(fare_pos); btn.ciz(ekran)
        gosterilen = sensor_listesi[aktif_sayfa*SAYFA_BASI_SENSOR : (aktif_sayfa+1)*SAYFA_BASI_SENSOR]
        for i, s in enumerate(gosterilen):
            sy = panel_y + 35 + (i * 24)
            if s.secili: pygame.draw.rect(ekran, (50, 80, 110), (HARITA_GENISLIK+25, sy-2, PANEL_GENISLIK-50, 20), border_radius=4)
            ekran.blit(font_kucuk.render(s.isim, True, RENK_BEYAZ), (HARITA_GENISLIK + 35, sy))
            pygame.draw.rect(ekran, (50, 60, 75), (HARITA_GENISLIK + 160, sy + 4, 100, 8), border_radius=2)
            if s.batarya_seviyesi > 0:
                b_r = RENK_YESIL if s.batarya_seviyesi > 50 else (RENK_SARI if s.batarya_seviyesi > 20 else RENK_KIRMIZI)
                pygame.draw.rect(ekran, b_r, (HARITA_GENISLIK + 160, sy + 4, int(s.batarya_seviyesi), 8), border_radius=2)

        pygame.draw.rect(ekran, (25, 35, 45), (HARITA_GENISLIK + 25, 540, 300, 150), border_radius=10)
        aktif_say = len([s for s in sensor_listesi if s.batarya_seviyesi > 0])
        p_kaybi = sum(s.tuketim_hesapla(merkez_istasyon_konumu)[1] for s in sensor_listesi if s.batarya_seviyesi > 0)
        kapsama_orani = (aktif_say / len(sensor_listesi) * 100) if sensor_listesi else 0
        rapor = ["AĞ ANALİZİ", f"Sim. Saati: {int(simulasyon_saati):02d}:{int((simulasyon_saati*60)%60):02d}", f"Aktif Düğüm: {aktif_say}", f"Kapsama: %{int(kapsama_orani)}", f"Yük: {p_kaybi:.2f} J/h"]
        for i, r in enumerate(rapor): 
            renk_yazi = RENK_TURKUAZ if i==0 else (RENK_KIRMIZI if i==3 and kapsama_orani < 50 else RENK_BEYAZ)
            ekran.blit(font_orta.render(r, True, renk_yazi), (HARITA_GENISLIK + 35, 550 + i*25))


    elif panel_sekmesi == 1:
        g_x, g_y, g_w, g_h = HARITA_GENISLIK + 20, 70, PANEL_GENISLIK - 40, 700
        pygame.draw.rect(ekran, (18, 22, 28), (g_x, g_y, g_w, g_h), border_radius=8)
        

        ekran.blit(font_buyuk.render("CANLI SİSTEM ANALİZİ", True, RENK_TURKUAZ), (g_x + 15, g_y + 15))
        

        cizim_x, cizim_y, cizim_w, cizim_h = g_x + 35, g_y + 80, g_w - 70, 180
        pygame.draw.rect(ekran, (10, 15, 20), (cizim_x, cizim_y, cizim_w, cizim_h))
        for i in range(1, 5):
            hy = cizim_y + (cizim_h // 5) * i
            pygame.draw.line(ekran, (30, 40, 50), (cizim_x, hy), (cizim_x + cizim_w, hy), 1)

        if len(anlik_grafik_verisi) > 1:
            pts_yuk = []
            pts_bat = []
            for i, v in enumerate(anlik_grafik_verisi):
                nx = cizim_x + (i / (MAKS_ANLIK_VERI-1)) * cizim_w

                y_yuk = cizim_y + cizim_h - (v["yuk"] / max(30, len(sensor_listesi)*2)) * cizim_h
                y_bat = cizim_y + cizim_h - (v["batarya"] / 100) * cizim_h
                pts_yuk.append((nx, y_yuk))
                pts_bat.append((nx, y_bat))
            
            pygame.draw.lines(ekran, RENK_TURKUAZ, False, pts_yuk, 2)
            pygame.draw.lines(ekran, RENK_YESIL, False, pts_bat, 2)


        bar_y_base = cizim_y + cizim_h + 80
        bar_h_max = 280
        ekran.blit(font_orta.render("Düğüm Başına Toplam Veri Transferi", True, RENK_SARI), (cizim_x, bar_y_base - 30))
        
        if sensor_listesi:
            n = len(sensor_listesi)
            gap = 4
            available_w = cizim_w - 20
            bw = (available_w / n) - gap
            max_p = max([s.toplam_paket for s in sensor_listesi]) or 1
            

            etiket_adimi = 1 if n <= 15 else (2 if n <= 30 else 5)

            for i, s in enumerate(sensor_listesi):
                bx = cizim_x + 10 + i * (bw + gap)
                bh = (s.toplam_paket / max_p) * (bar_h_max - 60)
                

                b_renk = RENK_TURKUAZ if s.batarya_seviyesi > 0 else RENK_KIRMIZI
                if s.secili: b_renk = RENK_MOR
                
                pygame.draw.rect(ekran, b_renk, (bx, bar_y_base + bar_h_max - bh - 30, bw, bh), border_radius=2)
                

                if i % etiket_adimi == 0:
                    id_txt = font_kucuk.render(f"{s.id}", True, RENK_GRI)
                    ekran.blit(id_txt, id_txt.get_rect(center=(bx + bw/2, bar_y_base + bar_h_max - 15)))
                    
                    if n < 25: 
                        val_txt = font_kucuk.render(f"{int(s.toplam_paket)}", True, RENK_BEYAZ)
                        ekran.blit(val_txt, val_txt.get_rect(center=(bx + bw/2, bar_y_base + bar_h_max - bh - 45)))


        bar_y = cizim_y + cizim_h + 80
        bar_h = 240
        ekran.blit(font_orta.render("Sensör Başına Taşınan Toplam Veri Paketi", True, RENK_SARI), (cizim_x, bar_y - 25))
        pygame.draw.rect(ekran, (10, 15, 20), (cizim_x, bar_y, cizim_w, bar_h))

        if sensor_listesi:
            maks_paket = max([s.toplam_paket for s in sensor_listesi]) or 1 
            bar_genislik = (cizim_w - 20) / len(sensor_listesi)
            

            for i in range(1, 4):
                bh_y = bar_y + (bar_h / 4) * i
                pygame.draw.line(ekran, (30, 40, 50), (cizim_x, bh_y), (cizim_x + cizim_w, bh_y), 1)
            
            for i, s in enumerate(sensor_listesi):
                bx = cizim_x + 10 + i * bar_genislik
                bh = (s.toplam_paket / maks_paket) * (bar_h - 40)
                

                renk = RENK_TURKUAZ if s.batarya_seviyesi > 0 else RENK_KIRMIZI
                if s.secili: renk = RENK_MOR
                
                pygame.draw.rect(ekran, renk, (bx + 2, bar_y + bar_h - bh - 25, bar_genislik - 4, bh), border_radius=3)
                

                isim_txt = font_kucuk.render(f"S{s.id}", True, RENK_BEYAZ)
                deger_txt = font_kucuk.render(f"{int(s.toplam_paket)}", True, RENK_YESIL if s.batarya_seviyesi > 0 else RENK_GRI)
                
                ekran.blit(isim_txt, isim_txt.get_rect(center=(bx + bar_genislik/2, bar_y + bar_h - 12)))
                ekran.blit(deger_txt, deger_txt.get_rect(center=(bx + bar_genislik/2, bar_y + bar_h - bh - 35)))

    pygame.display.flip()
    saat_yoneticisi.tick(FPS)
