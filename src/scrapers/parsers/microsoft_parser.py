"""Microsoft jobs parser - uses Microsoft's API."""
import json
from typing import List, Dict, Any
from .base_parser import BaseJobParser


class MicrosoftParser(BaseJobParser):
    """Parser for Microsoft jobs API.

    Handles both:
    - Individual position objects (when used with generic API pagination)
    - Full API response text (legacy mode)
    """

    def parse(self, position: Any) -> Dict[str, Any]:
        """
        Parse a single Microsoft position object.

        Args:
            position: Position dict or JSON response string

        Returns:
            Standardized job dictionary
        """
        # Handle legacy mode where full response text is passed
        if isinstance(position, str):
            jobs = self._parse_full_response(position)
            return jobs[0] if jobs else {}

        # Standard mode: parse individual position object
        return self._parse_position(position)

    def _parse_position(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single position object."""
        # Extract locations (join multiple locations)
        locations = position.get('locations', [])
        location = ', '.join(locations) if locations else ''

        # Build job URL
        position_url = position.get('positionUrl', '')
        url = f"https://apply.careers.microsoft.com{position_url}" if position_url else ''

        # Determine remote status
        work_option = position.get('workLocationOption', '').lower()
        is_remote = work_option in ['remote', 'hybrid']

        return {
            'external_id': str(position.get('id', position.get('displayJobId', ''))),
            'title': position.get('name', ''),
            'location': location,
            'job_url': url,
            'department': position.get('department', ''),
            'is_remote': is_remote,
            'posted_date': None,
            'description': '',
        }

    def _parse_full_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse full API response (legacy mode)."""
        jobs = []

        try:
            data = json.loads(response_text)

            # Navigate to positions array
            if 'data' in data and 'positions' in data['data']:
                positions = data['data']['positions']

                for position in positions:
                    jobs.append(self._parse_position(position))

        except Exception as e:
            print(f"Error parsing Microsoft jobs: {e}")

        return jobs

