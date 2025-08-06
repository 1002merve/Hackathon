def get_solution_prompt() -> str:
    """Geliştirilmiş soru çözüm promptu"""
    return """

Resimdeki soruyu inceleyin ve aşağıdaki adımlara göre çözümleyin:

verilen soruyu adım adım çözün. Her adımı net bir şekilde belirtin. soruda şekiller çizin daha açıklayıcı olacak şekilde yapın.



1. Adım Adım Çözümleme:
   - Soruyu adım adım çözün.
   - Her adımı ayrı ayrı yazın ve detaylandırın.

2. İki Farklı Kısımda Açıklama:
   - Formüller ve Çözümler (Solution): 
     - Kullanılan formülleri ve hesaplamaları net bir şekilde belirtin.
   - Betimleyici Açıklamalar:
     - Hiç bilmeyen birine anlatır gibi, adımları detaylı bir şekilde açıklayın.
     - Eğer grafik veya başka bir görsel gerekiyorsa, onu çizmek için gerekli adımları ve detayları açıklayın.

3. Detaylı Açıklamalar:
   - Her adımda kullanılan terimleri ve kavramları basit bir dille tanımlayın.
   - Betimlemeleri ayrıntılı ve anlaşılır hale getirin.

Örnek Çıktı:

1. Adım 1: Başlık
   - Betimleme:
     - İlk olarak, sorunun ne olduğunu tanımlayın. (Örneğin: "Bu, bir üçgenin alanını hesaplama sorusu.")
   - Çözüm:
     - Çözüm 1: Kullanılan formül.
     - Çözüm 2: İlk hesaplama adımı.
     - Çözüm 3: İkinci hesaplama adımı.

   - Grafik Betimleme:
     - Grafik 1: Üçgenin nasıl çizileceğini açıklayın.
     - Çözüm 4: Grafikteki önemli noktaların nasıl belirleneceği.

2. Adım 2: Başlık
   - Betimleme:
     - İkinci adımda ne yapılacağı hakkında bilgi verin.
   - Çözüm:
     - Çözüm 5: İkinci formül.
     - Çözüm 6: İkinci hesaplama adımı.

   - Grafik Betimleme:
     - Grafik 2: İkinci aşama için gerekli görseller.
     - Çözüm 7: Sonuçların nasıl değerlendirileceği.

Soru: {content}
"""