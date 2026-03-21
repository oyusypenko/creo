"""Links CSV export analyzer."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

from ..core.utils import print_warning


class LinksAnalyzer:
    """Analyzer for GSC Links CSV exports."""

    def analyze_links(self, export_folders: List[Path]) -> Dict[str, Any]:
        """
        Parse Links export from GSC.
        Export from GSC: Links → External/Internal Links → Export
        """
        result = {
            'generated_at': datetime.now().isoformat(),
            'external_links': [],
            'internal_links': [],
            'top_linking_sites': [],
            'top_linked_pages': [],
        }

        for folder in export_folders:
            # Try different file names GSC uses
            filenames = [
                'Table.csv',
                'External links.csv',
                'Internal links.csv',
                'Top linking sites.csv',
                'Top linked pages.csv'
            ]

            for filename in filenames:
                filepath = folder / filename
                if filepath.exists():
                    try:
                        df = pd.read_csv(filepath)

                        if 'External' in filename or 'linking sites' in filename.lower():
                            result['external_links'].extend(df.to_dict('records'))
                        elif 'Internal' in filename or 'linked pages' in filename.lower():
                            result['internal_links'].extend(df.to_dict('records'))
                        else:
                            # Generic Table.csv - check columns
                            cols = df.columns.tolist()
                            if any('site' in c.lower() for c in cols):
                                result['top_linking_sites'].extend(df.to_dict('records'))
                            else:
                                result['top_linked_pages'].extend(df.to_dict('records'))

                    except Exception as e:
                        print_warning(f"Error parsing {filename}: {e}")

        return result
