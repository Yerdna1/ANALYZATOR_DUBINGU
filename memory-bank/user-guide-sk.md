# Používateľská Príručka: Analyzátor Dabingových Scenárov

## Prehľad Aplikácie
Analyzátor Dabingových Scenárov je nástroj navrhnutý na zefektívnenie procesu analýzy a plánovania nahrávania dabingových scenárov. Aplikácia spracováva súbory vo formáte `.docx` a poskytuje komplexné štatistiky a nástroje na optimalizáciu produkcie.

## Kľúčové Funkcie

### 1. Spracovanie a Analýza Scenára
*   **Konverzia a Rozdelenie Dokumentu**: Aplikácia automaticky konvertuje nahraný `.docx` súbor a rozdelí ho na logické časti (segmenty).
*   **Extrakcia Štruktúrovaných Dát**: Identifikuje a extrahuje kľúčové informácie ako:
    *   **Rečníci**: Kto hovorí v danom segmente.
    *   **Časové kódy**: Presné časové značky pre dialógy.
    *   **Dialógy**: Samotný text, ktorý má byť nadabovaný.
    *   **Označenia Scén**: Značky pre zmeny scén.
    *   **Označenia Segmentov**: Špecifické značky pre jednotlivé segmenty.
*   **Zobrazenie Spracovaných Dát**: Všetky extrahované a spracované dáta sú prehľadne zobrazené v tabuľke pre ľahkú kontrolu.

### 2. Matica Rečník-Segment
*   **Generovanie Matice**: Aplikácia vytvorí maticu, ktorá vizuálne zobrazuje, ktorý rečník sa objavuje v ktorom segmente. To je kľúčové pre rýchlu identifikáciu obsadenia a rozloženia práce.
*   **Export do Excelu**: Maticu Rečník-Segment si môžete stiahnuť ako súbor `.xlsx` pre ďalšiu analýzu alebo zdieľanie.

### 3. Analýza Času a Nominálne Trvanie Segmentov
*   **Analýza Času Podľa Počtu Rečníkov**: Zistite celkový čas potrebný pre segmenty s 1, 2, 3, 4 alebo 5+ rečníkmi.
*   **Celkový Čas Potrebný pre Každého Rečníka**: Získajte prehľad o celkovom čase, ktorý každý rečník strávi v štúdiu.
*   **Konfigurácia Nominálneho Trvania**: Môžete si nastaviť vlastné "nominálne" trvanie pre segmenty v sekundách, v závislosti od počtu rečníkov. Tieto hodnoty sa použijú pri výpočtoch plánovania.

### 4. Plánovanie Nahrávania
*   **Dostupnosť Rečníkov**: Zadajte dostupné časové sloty pre každého rečníka (napr. "YYYY-MM-DD HH:MM-HH:MM").
*   **Globálne Časy Nahrávania**: Definujte celkové dostupné časové sloty pre nahrávanie v štúdiu.
*   **Kalendár Dostupnosti**: Prehľadný kalendár zobrazuje dostupnosť rečníkov a globálne nahrávacie sloty, čo pomáha pri vizuálnom plánovaní.
*   **Uložiť/Načítať Dostupnosť (JSON)**: Exportujte a importujte konfiguráciu dostupnosti rečníkov a nahrávacích slotov vo formáte JSON, čo umožňuje jednoduché zdieľanie a opätovné použitie plánov.
*   **Výpočet Optimálneho Plánu Nahrávania**: Aplikácia vypočíta navrhovaný plán nahrávania, ktorý priradí segmenty k dostupným časovým slotom s ohľadom na dostupnosť rečníkov. Zobrazí sa aj súhrn plánu podľa rečníka, vrátane celkového naplánovaného trvania, počtu segmentov a času nečinnosti.

## Ako Používať Aplikáciu

1.  **Prihlásenie**: Pre prístup k funkciám aplikácie sa prihláste pomocou poskytnutých prihlasovacích údajov.
2.  **Nahranie Súboru**: Kliknite na "Vyberte súbor DOCX" a nahrajte svoj dabingový scenár.
3.  **Prehľad Dát**: Po spracovaní sa zobrazia spracované dáta a matica Rečník-Segment.
4.  **Konfigurácia Plánovania**:
    *   Upravte "Nominálne Trvanie Segmentov" podľa vašich potrieb.
    *   Zadajte "Dostupnosť Rečníkov" pre každého rečníka.
    *   Zadajte "Globálne Časy Nahrávania" pre štúdio.
    *   Použite funkcie "Uložiť/Načítať Dostupnosť (JSON)" pre správu konfigurácií.
5.  **Výpočet Plánu**: Kliknite na "Vypočítať Optimálny Plán Nahrávania" pre vygenerovanie navrhovaného rozvrhu.
6.  **Export**: Stiahnite si maticu Rečník-Segment do Excelu alebo exportujte konfiguráciu dostupnosti do JSON.
