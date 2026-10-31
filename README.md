# Zakład utylizacji niewiedzy

**https://narzedzia.netlify.app**

Darmowe, interaktywne narzędzia do nauki geografii i biologii dla szkoły podstawowej i liceum, po polsku i po angielsku. Autor: Bartłomiej Wrona, nauczyciel geografii i biologii.

*Free interactive tools for learning geography and biology (primary and secondary school), in Polish and English.*

## Co tu jest

- `index.html` – strona główna z listą narzędzi, generatorami kart pracy i formularzem zgłoszeń.
- `geografia/` – narzędzia do geografii (współrzędne, skala i czas, mapy, poziomice, klimat, pogoda, ruchy Ziemi, Układ Słoneczny i inne).
- `biologia/` – narzędzia do biologii (komórki, podział komórki, DNA, laboratorium, układy narządów, genetyka, taksonomia i inne).
- `img/` – grafiki strony głównej.

Każde narzędzie to jeden samodzielny plik HTML – bez instalacji i bez budowania. Generatory kart pracy to te same pliki otwierane z parametrem `?tryb=generator`.

## Jak uruchomić u siebie

Wystarczy dowolny serwer plików, np.:

```bash
python3 -m http.server 8000
```

i otwarcie http://localhost:8000.

## Zgłoszenia i pomysły

Przycisk „Zgłoś błąd albo pomysł” na stronie albo zgłoszenie (Issue) w tym repozytorium. Zasady współpracy: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Licencja

- **Kod:** MIT.
- **Treści edukacyjne:** CC BY-NC-SA 4.0.
- **Nie są objęte licencją:** zadania z Konkursu Geograficznego województwa mazowieckiego, nazwa strony i banery oraz materiały innych autorów.

Szczegóły: [LICENSE](LICENSE).

---

This site is powered by [Netlify](https://www.netlify.com).
