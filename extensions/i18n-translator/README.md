# i18n Translator Extension for Creo

Batch translate JSON locale files to 39+ languages using LM Studio (local LLM). Preserves JSON structure, validates output, and supports incremental translation.

## What It Does

- Translates JSON locale files from a source language to multiple target languages simultaneously
- Uses a local LLM via LM Studio for privacy and speed (no API keys needed)
- Preserves all `{placeholder}` variables exactly
- Validates that translated files match the source structure (same keys, same types)
- Supports incremental translation: only re-translates changed values
- Cleans common LLM artifacts (arrow notation, extra quotes, multi-line responses)

## Prerequisites

- **Python 3.8+**
- **LM Studio** installed and running with a model loaded on port 1234
  - Download from: https://lmstudio.ai
  - Load any capable model (Mistral, Llama, Qwen, etc.)
  - Start the local server (default port 1234)
- **Creo core** must be installed first

## Install

### macOS / Linux

```bash
bash extensions/i18n-translator/install.sh
```

### Windows

```powershell
.\extensions\i18n-translator\install.ps1
```

The installer will:
1. Verify Creo core is installed
2. Check Python 3 is available
3. Copy scripts and config to `~/.claude/skills/creo-i18n/`
4. Copy the agent to `~/.claude/agents/`
5. Create a Python venv and install dependencies

## Usage

### Via Creo Commands

```
/creo i18n translate en uk,pl,de,fr
/creo i18n validate
/creo i18n status
```

### Direct Python Usage

```bash
cd your-project/i18n-directory

# 1. Set up input directory with source JSON files
mkdir -p input
cp path/to/en/*.json input/

# 2. Edit config.json
#    Set source_language, target_languages, and lm_studio_url

# 3. Run translation
python3 ~/.claude/skills/creo-i18n/scripts/run_translation.py

# 4. Find translated files in output/<lang>/
```

### Configuration

Edit `config.json` in your project's i18n directory:

```json
{
    "source_language": "en",
    "target_languages": ["uk", "pl", "de", "fr", "es", "ja"],
    "lm_studio_url": "http://localhost:1234",
    "model": "local-model",
    "temperature": 0.2,
    "request_delay": 1.0,
    "max_retries": 3,
    "retry_delay": 2.0,
    "max_tokens": 1000,
    "input_dir": "input",
    "output_dir": "output",
    "logs_dir": "logs"
}
```

Create a `config_local.json` to override settings without modifying the shared config file.

## Supported Languages

| Code | Language | Code | Language | Code | Language |
|------|----------|------|----------|------|----------|
| ar | Arabic | bg | Bulgarian | cs | Czech |
| da | Danish | de | German | el | Greek |
| en | English | es | Spanish | et | Estonian |
| fi | Finnish | fr | French | he | Hebrew |
| hi | Hindi | hr | Croatian | hu | Hungarian |
| id | Indonesian | it | Italian | ja | Japanese |
| ko | Korean | lt | Lithuanian | lv | Latvian |
| ms | Malay | nl | Dutch | no | Norwegian |
| pl | Polish | pt | Portuguese | ro | Romanian |
| ru | Russian | sk | Slovak | sl | Slovenian |
| sr | Serbian | sv | Swedish | th | Thai |
| tr | Turkish | ua | Ukrainian | vi | Vietnamese |
| zh | Chinese (Simplified) | zh-TW | Chinese (Traditional) | fil | Filipino |

Any language code supported by your loaded LLM model can be used.

## Quality Features

- **Placeholder preservation**: `{count}`, `{name}`, etc. are verified and auto-restored if the LLM modifies them
- **Artifact cleaning**: Arrow notation (`text -> translation`), wrapping quotes, and multi-line responses are handled automatically
- **Structure validation**: Post-translation check ensures every translated file has identical keys and value types
- **Incremental mode**: Stores a source snapshot so only changed values are re-translated on subsequent runs
- **Context-aware prompts**: The JSON key path is sent to the LLM so it understands the UI context (button labels, tooltips, error messages, etc.)

## Uninstall

### macOS / Linux

```bash
bash extensions/i18n-translator/uninstall.sh
```

### Windows

```powershell
.\extensions\i18n-translator\uninstall.ps1
```

This removes the extension files and agent. Your translated output files are not affected.
