# Weather APP 
Tento dokument popisuje architekturu a distribuovaný systém pro webovou aplikaci Weather APP. Aplikace slouží k poskytování aktuálních informací o počasí na základě zeměpisných poloh uživatelů.

## Architektura

### Frontend
Frontend aplikace je implementován pomocí technologií HTML, CSS a JavaScript. 

### Backend
Backend aplikace je postaven na platformě Python, konkrétně frameworku Flask.

### Databáze
Databáze aplikace je v podobě .json souborů v složce "data"

### API
Používané API třetích stran je OpenWeatherMap

## Implementace
Aplikace má přihlašování a registraci přes vlastní REST API, vlastní REST API na volání API třetích stran pro získání informace o počasí. Registrovaní uživatelé mají možnost nahlédnout do své historie hledání a mají možnost si zakoupit prémiový účet, který jim umožní ukládání oblíbených míst, ke kterým kromě aktuálního počasí dostanou také historii počasí 5 dní zpět. Při vstupu na webovou stránku se aplikace dotáže uživatele, zda může použít jeho polohu pro automatické získání informace o počasí v aktuální oblasti.

Aplikace je otestována pomocí Python knihovny pytest a coverage je zjištěn pomocí Python knihovny coverage
## Nasazení
Aplikace je nasazena na Azure serveru pomocí github Actions. CI/CD Pipeline soubor je automaticky generovaný službou Azure.
