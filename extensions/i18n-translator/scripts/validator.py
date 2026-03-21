#!/usr/bin/env python3
import json
import logging
from pathlib import Path
from typing import Dict, Any, Union, Set
from datetime import datetime


class JSONStructureValidator:
    def __init__(self):
        # Load config for directory paths
        config = {}
        config_path = Path("config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception:
                pass

        self.input_dir = Path(config.get('input_dir', 'input'))
        self.output_dir = Path(config.get('output_dir', 'output'))
        logs_dir = Path(config.get('logs_dir', 'logs'))

        self.setup_logging(logs_dir)

    def setup_logging(self, logs_dir: Path):
        logs_dir.mkdir(parents=True, exist_ok=True)

        log_filename = logs_dir / f"validation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def get_structure(self, data: Union[Dict, list, str, int, float, bool, None], path: str = "") -> Set[str]:
        structure = set()

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                structure.add(f"{current_path}:{type(value).__name__}")
                structure.update(self.get_structure(value, current_path))

        elif isinstance(data, list):
            structure.add(f"{path}:list[{len(data)}]")
            for i, item in enumerate(data):
                item_path = f"{path}[{i}]"
                structure.update(self.get_structure(item, item_path))

        return structure

    def load_json_safe(self, file_path: Path) -> Union[Dict, None]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load {file_path}: {str(e)}")
            return None

    def compare_files(self, input_file: Path, output_file: Path) -> bool:
        input_data = self.load_json_safe(input_file)
        output_data = self.load_json_safe(output_file)

        if input_data is None or output_data is None:
            return False

        input_structure = self.get_structure(input_data)
        output_structure = self.get_structure(output_data)

        if input_structure == output_structure:
            self.logger.info(f"Structure match: {input_file.name}")
            return True
        else:
            self.logger.error(f"Structure mismatch: {input_file.name}")

            missing_in_output = input_structure - output_structure
            extra_in_output = output_structure - input_structure

            if missing_in_output:
                self.logger.error(f"  Missing in output: {missing_in_output}")
            if extra_in_output:
                self.logger.error(f"  Extra in output: {extra_in_output}")

            return False

    def validate_translation(self, source_lang: str, target_lang: str) -> bool:
        source_dir = self.input_dir
        target_dir = self.output_dir / target_lang

        if not source_dir.exists():
            self.logger.error(f"Source directory not found: {source_dir}")
            return False

        if not target_dir.exists():
            self.logger.error(f"Target directory not found: {target_dir}")
            return False

        source_files = list(source_dir.rglob("*.json"))
        self.logger.info(f"Validating {len(source_files)} files")

        all_valid = True

        for source_file in source_files:
            relative_path = source_file.relative_to(source_dir)
            target_file = target_dir / relative_path

            if not target_file.exists():
                self.logger.error(f"Missing output file: {target_file}")
                all_valid = False
                continue

            if not self.compare_files(source_file, target_file):
                all_valid = False

        if all_valid:
            self.logger.info("All files have identical structure!")
        else:
            self.logger.error("Some files have structure mismatches")

        return all_valid

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python validator.py <source_lang> <target_lang>")
        print("Example: python validator.py en fr")
        sys.exit(1)

    source_lang = sys.argv[1]
    target_lang = sys.argv[2]

    validator = JSONStructureValidator()
    is_valid = validator.validate_translation(source_lang, target_lang)

    sys.exit(0 if is_valid else 1)
