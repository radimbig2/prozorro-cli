# prozorro-cli

Невелика CLI для отримання публічних даних про тендери Prozorro за UA-ID,
внутрішнім GUID, стандартним UUID або посиланням.

## Команди

```powershell
# Посилання на повний JSON у Public API
prozorro-cli tender UA-2026-06-15-003439-a --link

# Посилання на HTML-сторінку тендера
prozorro-cli tender UA-2026-06-15-003439-a --link-html

# Внутрішній id Prozorro
prozorro-cli tender UA-2026-06-15-003439-a --guid

# Той самий id у стандартному форматі UUID
prozorro-cli tender UA-2026-06-15-003439-a --guid-normal

# Повний JSON із public-api.prozorro.gov.ua
prozorro-cli tender UA-2026-06-15-003439-a

# Повний JSON за GUID без дефісів
prozorro-cli tender 5d2590ef8a1b455f8d09ceeae474b21f

# Повний JSON за стандартним UUID
prozorro-cli tender 5d2590ef-8a1b-455f-8d09-ceeae474b21f

# Повний JSON за посиланням на сторінку тендера
prozorro-cli tender https://prozorro.gov.ua/tender/UA-2026-06-15-003439-a

# Повний JSON за посиланням Public API
prozorro-cli tender https://public-api.prozorro.gov.ua/api/2.5/tenders/5d2590ef8a1b455f8d09ceeae474b21f
```

Для UA-ID і посилання на сторінку CLI спочатку отримує внутрішній `id` через
публічний endpoint `https://prozorro.gov.ua/api/tenders/<UA-ID>/summary`.
Для GUID, UUID і посилання Public API цей крок пропускається. Повний JSON
завантажується з `https://public-api.prozorro.gov.ua/api/2.5/tenders/<id>`.

## Розробка

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
python -m prozorro_cli tender UA-2026-06-15-003439-a --guid
```
