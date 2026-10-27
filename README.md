# Max Proffit — Maximum Motivation

**Trickle down motivation. He gets paid. You get made.**

Ett litet satiriskt spel där du kastar låtsaspengar på motivationsgurun Max Proffit. Fyrtio sedlar, fyrtio verkliga motivationscitat och en coach som till slut blir för motiverad för planetens eget bästa.

## Kör lokalt

Projektet har verifierats med **Python 3.14**. Python-paketet Streamlit är låst i `requirements.txt`. Inga API-nycklar, databaser, npm-paket eller byggsteg behövs.

```powershell
git clone https://github.com/bubbabucktooth/MaxProffit.git
cd MaxProffit
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

På macOS/Linux används `.venv/bin/python` i stället för `.venv\Scripts\python.exe`.

Öppna **http://127.0.0.1:8501**. Stoppa servern med Ctrl+C. Ladda om sidan efter ändringar i frontend-filerna.

## Spelet

- Klicka på **FEED THE EGO**, eller använd Tab och Enter/Space.
- Sedlarna flyger i en båge. Varje träff ger en reaktion och ett nytt citat.
- Högst 40 kast accepteras per omgång, inklusive sedlar i luften och i kön.
- Citaten blandas inför varje omgång och återanvänds aldrig under samma omgång.
- Coachen eskalerar automatiskt: Believer vid träff 1–10, Hustler vid 11–20, Maniac vid 21–30 och Maximum vid 31–40.
- Efter den fyrtionde träffen rusar han mot skärmen, kameran zoomar ut till jorden och planeten exploderar.
- **Try again.** återställer hela omgången utan sidladdning.

**Pause motion** pausar karaktären och ersätter sedlarnas flygbana med en kort toning. Systemets inställning för reducerad rörelse respekteras. Finalens berättelse behålls även när kamerarörelser, skakningar och flygande fragment tas bort. Alla pengar är fiktiva.

## Projektstruktur

```text
app.py                  Streamlit-värd och validering av innehåll
config.json             Omgångsgräns, nivåer och animationstempo
quotes.json             40 citat med talarnamn och källor
requirements.txt        Python-beroende
assets/                 Originalritad SVG: coach, sedel och jord
frontend/
  index.html            Spelscen och kontroller
  style.css             Layout, figur och träffreaktioner
  game.js               Speltillstånd, citatkortlekar och sedelkast
  animations.js         Avbrytbar tidslinje för finalen
  finale.css            Finalens scener och effekter
tests/
  test_app.py            Appstart och felaktigt innehåll
  browser_verify.py      Isolerad lokal headless-kontroll
  finale_checks.py       Hela spelcykeln och omstart
  record_finale.py       Valfri GIF-förhandsvisning
```

Python läser lokala resurser relativt `app.py` och skickar dem till en Streamlit custom component. Hela spelomgången körs i JavaScript utan reruns vid kast. Tillstånden är `idle`, `reacting`, `escalating`, `finale` och `game_over`. Omstart avbryter animationer och timers och ignorerar sena callbacks från tidigare omgångar.

`config.json` är enda källan för sedelgränsen och nivåernas träffgränser. Uppstarten validerar att varje nivå har tillräckligt många unika citat. Om gränserna höjs måste innehållet räcka för den nya omgången.

## Citat och grafik

Max Proffit är en fiktiv satirisk karaktär. Coachen, sedeln och jorden är originalritade SVG-filer. Spelet innehåller inga referensfoton eller externa grafikresurser.

Motivationscitaten kommer från Tony Robbins, Zig Ziglar, Jim Rohn och Eric Thomas. Varje post i `quotes.json` innehåller `id`, `level`, `text`, `author`, `source_url` och `verified_on`. Formuleringarna kontrollerades mot talarnas officiella webbplatser den 27 oktober 2026. Källorna belägger webbplatsernas attribution, inte vem som först formulerade uttrycket. Talarnamnet visas vid citatet. Spelets nivåindelning och satiriska framställning är projektets egna; de verkliga talarna medverkar inte i spelet. Inga källor hämtas under spel.

## Tester

Kör app- och innehållstester utan en separat server:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

Med appservern igång och Chrome/Chromium installerad:

```powershell
.\.venv\Scripts\python.exe tests\browser_verify.py
```

Testet använder en separat profil under `.verification/`. Din vanliga webbläsarprofil används inte. Om Chrome inte hittas kan `MAXPROFFIT_CHROME` ange sökvägen till dess körbara fil. Inga extra Python-paket behövs utöver appens beroenden. En GIF av finalen kan skapas med `tests\browser_verify.py --preview`.

Kontrollera radbrytning för samtliga citat vid sex skärmbredder med `tests\browser_verify.py --typography`. Ord hålls ihop; bindestreck inom ord visas som icke-brytande bindestreck utan att ändra källtexten i JSON.

Verifierat: 40 unika citat, exakta nivågränser, ökande intensitet, 100 snabba klick med högst 40 accepterade kast, en final per omgång, flera kompletta omgångar, omstart utan omladdning och reducerad rörelse. Desktop har kontrollerats vid 1440×1000 och mobil vid 390×844. Mobilkontrollerna är viewport-emulering, inte test på fysisk telefon.

## Git och körmiljö

`.gitignore` håller virtuella miljöer, testprofiler, genererade skärmbilder, loggar och lokala hemlighetsfiler utanför Git. Testkoden i `tests/` versionshanteras. `.gitattributes` normaliserar textfiler till LF.

Startfilen är **`app.py`** och Python-beroenden installeras från **`requirements.txt`**. Servern behöver hela `assets/` och `frontend/`. GitHub-repot lagrar koden; en körande webbapp behöver en separat Streamlit-kompatibel värd. Ingen appdrift publiceras automatiskt av detta projekt.

Streamlit-versionen är låst. Kontrollera helskärmslayouten och komponentintegrationen när Streamlit uppgraderas, eftersom värdens CSS använder Streamlits DOM-selektorer.
