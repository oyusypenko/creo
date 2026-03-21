# i18n Translation Reference Guide

## Supported Languages (39)

| Code | Language | Script |
|------|----------|--------|
| `ua` | Ukrainian | Cyrillic |
| `de` | German | Latin |
| `fr` | French | Latin |
| `es` | Spanish | Latin |
| `it` | Italian | Latin |
| `pl` | Polish | Latin |
| `nl` | Dutch | Latin |
| `pt` | Portuguese | Latin |
| `cs` | Czech | Latin |
| `sk` | Slovak | Latin |
| `hu` | Hungarian | Latin |
| `ro` | Romanian | Latin |
| `bg` | Bulgarian | Cyrillic |
| `hr` | Croatian | Latin |
| `sl` | Slovenian | Latin |
| `sr` | Serbian | Cyrillic/Latin |
| `mk` | Macedonian | Cyrillic |
| `sq` | Albanian | Latin |
| `mt` | Maltese | Latin |
| `et` | Estonian | Latin |
| `lv` | Latvian | Latin |
| `lt` | Lithuanian | Latin |
| `fi` | Finnish | Latin |
| `sv` | Swedish | Latin |
| `no` | Norwegian | Latin |
| `da` | Danish | Latin |
| `is` | Icelandic | Latin |
| `el` | Greek | Greek |
| `tr` | Turkish | Latin |
| `ka` | Georgian | Georgian |
| `hy` | Armenian | Armenian |
| `az` | Azerbaijani | Latin |
| `kk` | Kazakh | Cyrillic |
| `ky` | Kyrgyz | Cyrillic |
| `uz` | Uzbek | Latin |
| `tg` | Tajik | Cyrillic |
| `mn` | Mongolian | Cyrillic |
| `be` | Belarusian | Cyrillic |
| `mo` | Moldovan | Latin |

---

## Localization Best Practices

### 1. Placeholder Handling

JSON values may contain placeholders that MUST NOT be translated:

| Pattern | Example | Keep As-Is |
|---------|---------|------------|
| `{variable}` | `Hello, {name}!` | `{name}` |
| `{{variable}}` | `{{count}} items` | `{{count}}` |
| `{variable, type}` | `{count, number}` | `{count, number}` |
| ICU plurals | `{count, plural, one {# item} other {# items}}` | Structure + `#` |

### 2. HTML in Translations

Some locale strings contain HTML tags. Preserve tag structure:
```
Source: "Click <strong>here</strong> to start"
Target: Translate text, keep <strong> tags intact
```

### 3. Keys That Should NOT Be Translated

- URLs and links (`https://...`)
- Image paths (`/images/...`)
- CSS class names
- Email addresses
- Enum values (`SHARED`, `INDIVIDUAL`)
- Brand names (keep original or use official localized name)
- Technical identifiers

### 4. Gender and Plurals

- Slavic languages: 3 genders, complex plural forms
- Romance languages: 2 genders, different plural rules
- Turkic languages: no gender, agglutinative morphology
- Finno-Ugric languages: extensive case systems

### 5. Text Length

Translations often differ in length from source:
- German: typically 20-30% longer than English
- Chinese/Japanese: can be 30-50% shorter
- Russian/Ukrainian: similar to English length
- Finnish: can be 30-40% longer

Ensure UI can handle variable text lengths.

### 6. Cultural Adaptation

- Date formats: US (MM/DD/YYYY) vs European (DD.MM.YYYY)
- Number formats: 1,000.50 (EN) vs 1.000,50 (DE) vs 1 000,50 (FR)
- Currency placement: $100 (EN) vs 100 $ (FR)
- Text direction: Most supported languages are LTR

---

## Quality Checklist

After translation, verify:

- [ ] All JSON files have identical structure to source
- [ ] No untranslated strings remain (unless intentionally kept)
- [ ] Placeholders (`{variable}`) are preserved exactly
- [ ] HTML tags are preserved and properly closed
- [ ] No truncated or incomplete translations
- [ ] Professional tone maintained across languages
- [ ] Domain-specific terms translated consistently
- [ ] Brand names kept as-is (or official localization used)
