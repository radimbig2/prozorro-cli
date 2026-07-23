# prozorro-cli

Невелика CLI для отримання публічних даних про тендери Prozorro за UA-ID,
внутрішнім GUID, стандартним UUID або посиланням.

## Встановлення

```powershell
pip install prozorro-cli
prozorro-cli --help
```

Для ізольованого глобального встановлення CLI також можна використати
`pipx install prozorro-cli`.

## Команди

```powershell
# Посилання на повний JSON у Public API
prozorro-cli tender UA-2026-06-15-003439-a --link

# Посилання на HTML-сторінку тендера
prozorro-cli tender UA-2026-06-15-003439-a --link-html

# Надрукувати й відкрити JSON Public API у браузері
prozorro-cli tender UA-2026-06-15-003439-a --link --open

# Надрукувати й відкрити HTML-сторінку у браузері
prozorro-cli tender UA-2026-06-15-003439-a --link-html --open

# Скорочений alias для --link-html
prozorro-cli tender UA-2026-06-15-003439-a --linkhtml --open

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

# Завантажити всі файли з data.documents за посиланням Public API
prozorro-cli documents https://public-api.prozorro.gov.ua/api/2.5/tenders/5d2590ef8a1b455f8d09ceeae474b21f --output /temp

# Те саме за UA-ID
prozorro-cli documents UA-2026-06-15-003439-a --output /temp
```

Для UA-ID і посилання на сторінку CLI спочатку отримує внутрішній `id` через
публічний endpoint `https://prozorro.gov.ua/api/tenders/<UA-ID>/summary`.
Для GUID, UUID і посилання Public API цей крок пропускається. Повний JSON
завантажується з `https://public-api.prozorro.gov.ua/api/2.5/tenders/<id>`.

Команда `documents` створює каталог із `--output`, якщо його ще немає, і
завантажує туди всі файли з `data.documents`. Імена беруться з `title`;
однакові імена не перезаписуються, а отримують суфікси `(2)`, `(3)` тощо.

## Розробка

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
python -m prozorro_cli tender UA-2026-06-15-003439-a --guid
```

## Реліз

1. Оновіть `version` у `pyproject.toml` та `__version__` у
   `src/prozorro_cli/__init__.py`.
2. Створіть і опублікуйте GitHub Release з тегом тієї ж версії, наприклад
   `v0.1.0`.
3. GitHub Actions перевірить тести, збере wheel і sdist, додасть їх до Release
   та опублікує пакет у PyPI.

Публікація використовує PyPI Trusted Publishing і GitHub environment `pypi`.
