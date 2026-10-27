import re

DIAGNOSTIC_RULES = [
    {
        "keywords": ["confirm your age", "sign in to confirm your age", "age-restricted"],
        "title": "🔞 Yaş Kısıtlamalı Video",
        "solution": "Bu video yaş sınırına sahiptir. Ayarlar veya Çerezler bölümünden tarayıcınızı seçerek veya 'cookies.txt' dosyası ekleyerek indirmeyi yeniden deneyin."
    },
    {
        "keywords": ["private video", "this video is private"],
        "title": "🔒 Gizli (Özel) Video",
        "solution": "Bu video gizli veya yalnızca belirli kullanıcılara açıktır. İndirebilmek için videoya erişim izni olan bir hesabın çerezlerini (cookies) yüklemelisiniz."
    },
    {
        "keywords": ["members-only", "join this channel"],
        "title": "⭐ Katıl / Üyelere Özel Video",
        "solution": "Bu video yalnızca kanal üyelerine özeldir. Yalnızca bu kanala ücretli üye olan hesabınızın çerezlerini (cookies.txt) aktararak indirebilirsiniz."
    },
    {
        "keywords": ["n challenge solving failed", "javascript runtime", "wiki/ejs", "no supported javascript runtime"],
        "title": "⚡ JavaScript EJS Motoru Gerekli",
        "solution": "YouTube'un yeni güvenlik imzalarını çözmek için JavaScript motoru (Deno) gereklidir. Uygulamanız Deno motorunu bin/ klasörüne otomatik olarak entegre etmiştir."
    },
    {
        "keywords": ["only images are available for download", "requested format is not available"],
        "title": "⚠️ Video Akışı Bulunamadı",
        "solution": "Video akışı çekilemedi (yalnızca kapak görselleri mevcut). Bu video kısıtlı/üyelere özel olabilir veya yaş doğrulaması gerektirebilir."
    },
    {
        "keywords": ["not available in your country", "uploader has not made this video available in your country"],
        "title": "🌍 Bölge Kısıtlaması (Geo-block)",
        "solution": "Bu video ülkenizde kullanılamıyor. Ayarlar sekmesinden bir Proxy tanımlayabilir veya VPN kullanarak deneyebilirsiniz."
    },
    {
        "keywords": ["http error 403", "403: forbidden", "sign in to confirm you’re not a bot", "bot detection"],
        "title": "🛡️ YouTube Bot / 403 Koruması",
        "solution": "YouTube sunucuları doğrudan erişimi kısıtladı. Tarayıcınızdan taze çerezler (cookies) aktararak kimlik doğrulamasını yenileyin."
    },
    {
        "keywords": ["ffmpeg is not installed", "ffmpeg not found", "ffmpeg missing", "ffprobe not found"],
        "title": "⚠️ FFmpeg Bulunamadı",
        "solution": "Yüksek çözünürlüklü video birleştirme ve MP3 dönüşümleri için FFmpeg gereklidir. Ayarlar sekmesinden '⚡ 1-Tıkla FFmpeg Kur' butonuna tıklayarak otomatik kurabilirsiniz."
    },
    {
        "keywords": ["permission denied", "permissionerror", "access is denied"],
        "title": "⛔ Klasör Yazma İzni Reddedildi",
        "solution": "Seçilen kayıt klasörüne yazma izniniz yok. Lütfen 'İndirilenler' veya masaüstünde farklı bir klasör seçin ya da uygulamayı yönetici olarak başlatın."
    },
    {
        "keywords": ["no space left on device", "disk full"],
        "title": "💾 Yetersiz Disk Alanı",
        "solution": "Kayıt yapılan diskte yeterli boş alan bulunmuyor. Lütfen diskte yer açın veya başka bir sürücü seçin."
    },
    {
        "keywords": ["is not a valid url", "unsupported url"],
        "title": "🔗 Geçersiz veya Desteklenmeyen URL",
        "solution": "Girilen bağlantı geçerli bir video/ses bağlantısı değil. Lütfen URL'yi tarayıcınızdan kopyalayıp tekrar yapıştırın."
    },
    {
        "keywords": ["could not copy chrome cookie database", "could not copy", "cookie database"],
        "title": "🍪 Tarayıcı Çerez Dosyası Kilitli",
        "solution": "Seçilen tarayıcı açık olduğu için Windows çerez dosyasını kilitliyor. Çözüm: İndirme yaparken tarayıcıyı tamamen kapatın veya 'cookies.txt' dosya seçeneğini kullanın."
    },
    {
        "keywords": ["failed to decrypt with dpapi", "dpapi"],
        "title": "🔐 Windows DPAPI Koruması",
        "solution": "Windows güvenlik koruması (DPAPI) nedeniyle tarayıcıdan doğrudan çerez çekilemedi. Çözüm: 1) Normal videolarda çerez gerekmez, Çerezleri 'Kapalı' yapabilirsiniz. 2) Yaş kısıtlamalı videolar için tarayıcınıza 'Get cookies.txt' eklentisi kurup dışa aktardığınız dosyayı yükleyin."
    }
]

def diagnose(line: str) -> dict | None:
    """Verilen log satırını analiz edip varsa tanı ve Türkçe çözüm önerisi döndürür."""
    lower_line = line.lower()
    for rule in DIAGNOSTIC_RULES:
        if any(kw in lower_line for kw in rule["keywords"]):
            return {
                "title": rule["title"],
                "solution": rule["solution"]
            }
    return None
