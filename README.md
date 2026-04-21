# Fabian Talks News Bot — MVP

Bot zbiera newsy z RSS, filtruje tematy pod viral na Instagram/Fabian Talks
i generuje 3 najlepsze drafty rolek.

## Co robi
- pobiera newsy z RSS (Reuters World, AP, Al Jazeera, BBC World)
- filtruje po słowach kluczowych
- nadaje score viralowy
- generuje:
  - tytuł miniatury
  - tekst na rolkę
  - tekst pod post
  - hook follow
  - hashtagi

## Szybki start
```bash
pip install -r requirements.txt
python fabian_bot.py
```

## Pliki wyjściowe
Bot zapisuje wyniki do:
- `output/top_topics.json`
- `output/top_topics.md`

## Jak dostroić
W `config.json` zmienisz:
- słowa kluczowe
- wagi scoringu
- hashtagi
- styl hooków

## Następny krok pod Codex/GitHub
1. wrzuć ten folder do repo
2. poproś Codexa:
   - "dodaj scheduler 2x dziennie"
   - "dodaj deduplikację tematów"
   - "dodaj scoring pod polski viral"
   - "dodaj eksport do gotowego szablonu posta"
```