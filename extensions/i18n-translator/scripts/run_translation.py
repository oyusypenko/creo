#!/usr/bin/env python3
import subprocess
import sys
import json
from pathlib import Path

def run_translation():
    print("Starting JSON Translation Process")
    print("=" * 50)

    # Resolve paths relative to this script's location (not cwd)
    script_dir = Path(__file__).parent

    # Load config from current working directory
    config_path = Path("config.json")
    if not config_path.exists():
        print(f"Error: config.json not found in {Path.cwd()}")
        print("Run this script from the i18n-translator directory")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        source_lang = config['source_language']
        target_languages = config.get('target_languages', [config.get('target_language')])
        print(f"Translating from {source_lang} to {len(target_languages)} languages: {', '.join(target_languages[:5])}{'...' if len(target_languages) > 5 else ''}")
    except Exception as e:
        print(f"Error loading config: {e}")
        return False

    # Run translation - translator.py is alongside this script, config.json is in cwd
    print("\nRunning translation...")
    try:
        result = subprocess.run(
            [sys.executable, str(script_dir / "translator.py")],
            capture_output=False, text=True
        )
        if result.returncode != 0:
            print(f"Translation failed with exit code: {result.returncode}")
            return False
    except Exception as e:
        print(f"Error running translator: {e}")
        return False

    print("\nTranslation completed!")

    # Run validation for each target language
    print("\nValidating structure...")
    all_valid = True
    for target_lang in target_languages:
        print(f"Validating {source_lang} -> {target_lang}...")
        try:
            result = subprocess.run(
                [sys.executable, str(script_dir / "validator.py"), source_lang, target_lang],
                capture_output=False, text=True
            )
            if result.returncode != 0:
                print(f"Validation failed for {target_lang}!")
                all_valid = False
        except Exception as e:
            print(f"Error validating {target_lang}: {e}")
            all_valid = False

    if all_valid:
        print("All validations passed!")
        return True
    else:
        print("Some validations failed!")
        return False

if __name__ == "__main__":
    success = run_translation()
    sys.exit(0 if success else 1)
