# LDownloader 🎬🎵

LDownloader, Python ve Tkinter kullanılarak modern ve estetik bir SaaS tasarımı ile geliştirilmiş, arka planda `yt-dlp` gücünü kullanan, yüksek performanslı ve kullanıcı dostu bir video ve ses indirme uygulamasıdır.

![LDownloader](logo.png)

---

## ✨ Özellikler

* **Modern ve Premium Arayüz**: SaaS esintili koyu mod tasarımı, özel segmented kontrol düğmeleri ve tamamen özelleştirilmiş şık arayüz ögeleri.
* **Gerçek Zamanlı İlerleme Çubuğu**: Asenkron, tamamen arabelleksiz (unbuffered) veri akışı sayesinde donmayan ve anlık güncellenen ilerleme çubuğu, indirme hızı, boyutu ve kalan süre göstergesi.
* **Akıllı Hata Teşhis Sistemi (Diagnostics)**: Yaş sınırı, gizli videolar veya süresi geçmiş çerezler gibi hatalarda karmaşık terminal çıktıları yerine doğrudan Türkçe çözüm önerileri sunar.
* **Dinamik Seçenek Paneli**: Dikey hizada mükemmel konumlanmış, video ve ses format butonlarına göre otomatik olarak genişleyen çözünürlük ve ses kalitesi açılır menüleri.
* **"Best Quality (En İyi)" Desteği**: Tek tıkla platformun sunduğu en yüksek çözünürlüklü ve kaliteli akışları otomatik birleştirerek indirme.
* **Gelişmiş Süreç Yönetimi**: Uygulama kapatıldığında veya indirme iptal edildiğinde arka planda hiçbir `ffmpeg` veya `yt-dlp` sürecinin yetim kalmamasını sağlayan Windows süreç ağacı temizleme mekanizması.
* **Otomatik Bağımlılık Kontrolü**: Sistemde `yt-dlp` ve `ffmpeg` araçlarının kurulu olup olmadığını açılışta denetler ve bilgilendirir.
* **Otomatik Çerez (Cookies) Yönetimi**: Tarayıcılardan (Firefox, Chrome, Edge vb.) otomatik çerez çekebilir veya dizindeki `cookies.txt` dosyasını otomatik olarak algılar.
* **Playlist Desteği**: YouTube oynatma listelerini sıralı olarak ve klasör yapısını koruyarak aralık belirleme (başlangıç/bitiş) desteği ile indirebilir.

---

## 🚀 Kurulum & Çalıştırma

### Hazır Standart EXE (Windows)
Hiçbir kurulum yapmadan doğrudan hazır derlenmiş taşınabilir sürümü kullanabilirsiniz:
1. `dist/LDownloader.exe` dosyasını indirin ve çalıştırın.
2. Sisteminize `yt-dlp` ve `ffmpeg` araçlarının kurulu ve PATH üzerinde tanımlı olduğundan emin olun.

### Kaynak Koddan Çalıştırma
Projeyi kaynak koddan çalıştırmak veya kendiniz derlemek isterseniz:

1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install yt-dlp
   ```
2. Uygulamayı başlatın:
   ```bash
   python ytdlp_gui.pyw
   ```

---

## 🛠️ Derleme (EXE Paketleme)
Projeyi tek bir Windows yürütülebilir dosyası (EXE) haline getirmek için PyInstaller kullanabilirsiniz:

```bash
pyinstaller --noconfirm ytdlp_indirici.spec
```

---

## 🤝 Katkıda Bulunma
Herhangi bir hata bildirimi, özellik önerisi veya doğrudan katkı sağlamak için lütfen bir Pull Request gönderin ya da Issue oluşturun.

İyi indirmeler! 🚀
