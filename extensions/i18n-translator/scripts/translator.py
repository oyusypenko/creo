#!/usr/bin/env python3
import os
import json
import re
import requests
import time
import logging
from pathlib import Path
from typing import Dict, Any, Union, List, Tuple
from datetime import datetime

DEFAULT_PROMPT = """You are a professional UI translator. Translate from {source_lang} to {target_lang}.

Context — JSON key path: {key_path}
Text: {text}

Critical rules:
1. Return ONLY the translation — no arrows (->), no explanations, no alternatives, no quotes
2. This is a UI element (button, label, message, tooltip) in a web app. The JSON key path tells you the context:
   - "close" key = close/dismiss button (NOT "nearby")
   - "wizard" key = step-by-step setup wizard (NOT a magic wizard)
   - "maintenance" in goal context = maintaining current weight (NOT technical maintenance)
   - "light"/"moderate"/"active" in activityLevel = physical activity intensity
   - "muscleGain" = building muscle mass as a fitness goal
   - abbreviations like "cal", "prot", "g" = keep them short (use standard abbreviations in target language)
3. Preserve all placeholders EXACTLY: {{count}}, {{name}}, {{value}} — do NOT translate or rename them
4. Write as a native {target_lang} speaker — natural, professional UI language. Avoid literal/word-for-word translation
5. Keep the same tone and length as the original. If original is short (one word button), translation should be short too
"""

# Regex to find placeholders like {count}, {name}, etc.
PLACEHOLDER_RE = re.compile(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}')

# Regex to detect arrow artifacts like "cm -> cm" or "Standard -> Standard"
ARROW_RE = re.compile(r'^(.+?)\s*->\s*.+$')


class JSONTranslator:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # Merge local config overrides if present
        local_path = config_path.replace('.json', '_local.json')
        if os.path.exists(local_path):
            with open(local_path, 'r', encoding='utf-8') as f:
                self.config.update(json.load(f))

        self.source_lang = self.config['source_language']
        self.target_languages = self.config.get('target_languages', [self.config.get('target_language')])
        self.lm_studio_url = self.config['lm_studio_url']
        self.max_string_length = self.config.get('max_string_length', 800)
        self.request_delay = self.config.get('request_delay', 1.0)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 2.0)
        self.request_timeout = self.config.get('request_timeout', 60)

        # Configurable directories (defaults to relative paths)
        self.input_dir = Path(self.config.get('input_dir', 'input'))
        self.output_dir = Path(self.config.get('output_dir', 'output'))
        self.logs_dir = Path(self.config.get('logs_dir', 'logs'))

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.setup_logging()

    def setup_logging(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Main log
        log_filename = self.logs_dir / f"translation_log_{timestamp}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Error log for failed translations
        self.error_log_filename = self.logs_dir / f"translation_errors_{timestamp}.log"
        self.error_logger = logging.getLogger('translation_errors')
        self.error_logger.setLevel(logging.ERROR)
        error_handler = logging.FileHandler(self.error_log_filename, encoding='utf-8')
        error_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.error_logger.addHandler(error_handler)

    def _extract_placeholders(self, text: str) -> List[str]:
        """Extract all {variable} placeholders from text."""
        return PLACEHOLDER_RE.findall(text)

    def _restore_placeholders(self, original: str, translated: str) -> str:
        """Ensure all placeholders from original are present in translated text."""
        original_phs = self._extract_placeholders(original)
        if not original_phs:
            return translated

        translated_phs = self._extract_placeholders(translated)

        # If all placeholders are already present, return as-is
        if set(original_phs) == set(translated_phs):
            return translated

        # If model renamed placeholders (e.g. {count} -> {liczba}), restore originals
        # Strategy: find placeholders in translated that aren't in original — those are renamed
        extra_in_translated = set(translated_phs) - set(original_phs)
        missing_in_translated = list(set(original_phs) - set(translated_phs))

        if extra_in_translated and missing_in_translated:
            # Try to restore by replacing extra with missing (in order)
            result = translated
            for extra_ph in extra_in_translated:
                if missing_in_translated:
                    result = result.replace(extra_ph, missing_in_translated.pop(0), 1)
            return result

        # If placeholders are just missing entirely, log warning but return as-is
        if missing_in_translated:
            self.logger.warning(f"Placeholders lost in translation: {missing_in_translated} | Original: {original[:50]} | Translated: {translated[:50]}")

        return translated

    def _clean_response(self, translation: str, original: str) -> str:
        """Clean up common LLM artifacts from the translation response."""
        # Remove leading/trailing quotes if model wrapped the response
        if len(translation) >= 2:
            if (translation[0] == '"' and translation[-1] == '"') or \
               (translation[0] == "'" and translation[-1] == "'"):
                translation = translation[1:-1]

        # Remove arrow artifacts: "cm -> cm" -> "cm"
        arrow_match = ARROW_RE.match(translation)
        if arrow_match:
            translation = arrow_match.group(1).strip()

        # If multi-line response, pick the best line
        lines = translation.split('\n')
        if len(lines) > 1:
            clean_lines = [
                line.strip() for line in lines
                if line.strip()
                and not line.strip().startswith('-')
                and 'translat' not in line.lower()
                and 'note:' not in line.lower()
                and '->' not in line
            ]
            if clean_lines:
                # Prefer lines similar in length to original
                original_len = len(original)
                translation = min(clean_lines, key=lambda l: abs(len(l) - original_len))

        return translation.strip()

    def translate_text(self, text: str, target_lang: str, key_path: str = "") -> str:
        if not text or not text.strip():
            return text

        if len(text) > self.max_string_length:
            self.logger.warning(f"Text too long ({len(text)} chars), skipping: {text[:50]}...")
            return text

        # Use configurable prompt template
        prompt_template = self.config.get('prompt_template', DEFAULT_PROMPT)
        prompt = prompt_template.format(
            source_lang=self.source_lang,
            target_lang=target_lang,
            text=text,
            key_path=key_path or "unknown"
        )

        payload = {
            "model": self.config.get('model', 'local-model'),
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.get('temperature', 0.3),
            "max_tokens": self.config.get('max_tokens', 1000),
            "stream": False
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.lm_studio_url}/v1/chat/completions",
                    json=payload,
                    timeout=self.request_timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    translation = result['choices'][0]['message']['content'].strip()

                    # Clean up LLM artifacts
                    translation = self._clean_response(translation, text)

                    # Restore placeholders if model renamed/removed them
                    translation = self._restore_placeholders(text, translation)

                    self.logger.info(f"[{key_path}] {text[:50]} -> {translation[:50]}")
                    time.sleep(self.request_delay)
                    return translation
                else:
                    self.logger.error(f"API error {response.status_code}: {response.text}")

            except Exception as e:
                self.logger.error(f"Translation attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

        self.logger.warning(f"Failed to translate after {self.max_retries} attempts, keeping original: {text}")
        self.error_logger.error(f"TRANSLATION_FAILED: key={key_path} | text='{text}' | Source: {self.source_lang} | Target: {target_lang}")
        return text

    def translate_json_recursive(
        self,
        data: Union[Dict, list, str, int, float, bool, None],
        target_lang: str,
        existing_data: Union[Dict, list, str, int, float, bool, None] = None,
        stored_source: Union[Dict, list, str, int, float, bool, None] = None,
        key_path: str = ""
    ) -> tuple:
        if isinstance(data, dict):
            result = {}
            source_dict = {}
            for key, value in data.items():
                child_path = f"{key_path}.{key}" if key_path else key
                existing_value = existing_data.get(key) if isinstance(existing_data, dict) else None
                stored_source_value = stored_source.get(key) if isinstance(stored_source, dict) else None
                translated_value, source_value = self.translate_json_recursive(
                    value, target_lang, existing_value, stored_source_value, child_path
                )
                result[key] = translated_value
                source_dict[key] = source_value
            return result, source_dict

        elif isinstance(data, list):
            result = []
            source_list = []
            for i, item in enumerate(data):
                child_path = f"{key_path}[{i}]"
                existing_item = existing_data[i] if isinstance(existing_data, list) and i < len(existing_data) else None
                stored_source_item = stored_source[i] if isinstance(stored_source, list) and i < len(stored_source) else None
                translated_item, source_item = self.translate_json_recursive(
                    item, target_lang, existing_item, stored_source_item, child_path
                )
                result.append(translated_item)
                source_list.append(source_item)
            return result, source_list

        elif isinstance(data, str):
            # Check if this specific value has changed by comparing with stored source
            value_unchanged = (stored_source == data)

            # If value hasn't changed and translation exists, use it
            if value_unchanged and existing_data and isinstance(existing_data, str) and existing_data.strip():
                return existing_data, data
            translated = self.translate_text(data, target_lang, key_path)
            return translated, data

        else:
            return data, data

    def process_json_file(self, input_path: Path, output_path: Path, target_lang: str):
        try:
            self.logger.info(f"Processing {input_path} -> {target_lang}")

            # Load source data
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Create path for source copy in output/en/
            relative_path = input_path.relative_to(self.input_dir)
            source_copy_path = self.output_dir / self.source_lang / relative_path

            # Use filename (without extension) as base key path for context
            base_key = relative_path.stem

            # Load stored source copy for value-level comparison
            stored_source = None
            if source_copy_path.exists():
                try:
                    with open(source_copy_path, 'r', encoding='utf-8') as f:
                        stored_source = json.load(f)
                except Exception as e:
                    stored_source = None

            # Load existing translation
            existing_data = None
            if output_path.exists():
                try:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except Exception as e:
                    existing_data = None

            translated_data, source_data = self.translate_json_recursive(
                data, target_lang, existing_data, stored_source, key_path=""
            )

            # Save translated file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(translated_data, f, ensure_ascii=False, indent=4)

            # Update source copy in output/en/ (built line by line)
            source_copy_path.parent.mkdir(parents=True, exist_ok=True)
            with open(source_copy_path, 'w', encoding='utf-8') as f:
                json.dump(source_data, f, ensure_ascii=False, indent=4)

            self.logger.info(f"Saved translated file: {output_path}")

        except Exception as e:
            self.logger.error(f"Error processing {input_path}: {str(e)}")

    def translate_all(self):
        self.logger.info(f"Starting translation to {len(self.target_languages)} languages")

        if not self.input_dir.exists():
            self.logger.error(f"Input directory not found: {self.input_dir}")
            return

        json_files = list(self.input_dir.rglob("*.json"))
        self.logger.info(f"Found {len(json_files)} JSON files to translate")

        total_files = len(json_files) * len(self.target_languages)
        current_file = 0

        for json_file in json_files:
            relative_path = json_file.relative_to(self.input_dir)

            for target_lang in self.target_languages:
                current_file += 1
                self.logger.info(f"Progress: {current_file}/{total_files} - {json_file.name} -> {target_lang}")

                target_dir = self.output_dir / target_lang
                output_file = target_dir / relative_path

                self.process_json_file(json_file, output_file, target_lang)

        self.logger.info(f"Translation completed! Processed {len(json_files)} files into {len(self.target_languages)} languages")

if __name__ == "__main__":
    translator = JSONTranslator()
    translator.translate_all()
