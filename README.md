# prozorro-cli

Невелика CLI для отримання публічних даних про тендери Prozorro за номером
на кшталт `UA-2026-06-15-003439-a`.

## Команди

```powershell
# Посилання на сторінку тендера (без мережевого запиту)
prozorro-cli tender UA-2026-06-15-003439-a --link

# Внутрішній id Prozorro
prozorro-cli tender UA-2026-06-15-003439-a --guid

# Той самий id у стандартному форматі UUID
prozorro-cli tender UA-2026-06-15-003439-a --guid-normal

# Повний JSON із public-api.prozorro.gov.ua
prozorro-cli tender UA-2026-06-15-003439-a
```

Спочатку CLI отримує внутрішній `id` через публічний endpoint
`https://prozorro.gov.ua/api/tenders/<UA-ID>/summary`, а потім запитує повний
JSON за адресою `https://public-api.prozorro.gov.ua/api/2.5/tenders/<id>`.

## Розробка

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
python -m prozorro_cli tender UA-2026-06-15-003439-a --guid
```
