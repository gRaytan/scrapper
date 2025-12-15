"""Unit tests for EmbeddedJSParser."""
import pytest
from src.scrapers.parsers.embedded_js_parser import EmbeddedJSParser


class TestEmbeddedJSParser:
    """Test suite for EmbeddedJSParser."""

    def test_parse_taboola_job(self):
        """Test parsing a Taboola job with all fields."""
        parser = EmbeddedJSParser(site_name='taboola')
        
        job_data = {
            'id': 42115,
            'title': 'Account Manager, Growth Advertisers DACH',
            'office_text': 'Berlin',
            'office_textual': 'Berlin, Germany',
            'country': 'Germany',
            'teams_text': 'Sales & Account Management',
            'greenhouse_job_id': '6793937',
            'link': 'https://www.taboola.com/careers/job/account-manager'
        }
        
        result = parser.parse(job_data)
        
        assert result['external_id'] == '6793937'
        assert result['title'] == 'Account Manager, Growth Advertisers DACH'
        assert result['location'] == 'Berlin, Germany'
        assert result['job_url'] == 'https://www.taboola.com/careers/job/account-manager'
        assert result['department'] == 'Sales & Account Management'
        assert result['is_remote'] is False

    def test_parse_remote_job(self):
        """Test that remote jobs are correctly identified."""
        parser = EmbeddedJSParser(site_name='taboola')
        
        job_data = {
            'id': 123,
            'title': 'Remote Engineer',
            'office_textual': 'Remote, USA',
            'greenhouse_job_id': '999',
            'link': 'https://example.com/job'
        }
        
        result = parser.parse(job_data)
        
        assert result['is_remote'] is True

    def test_parse_fallback_location_fields(self):
        """Test location fallback from office_textual -> office_text -> country."""
        parser = EmbeddedJSParser(site_name='taboola')
        
        # Test fallback to office_text
        job_data = {
            'id': 1,
            'title': 'Test Job',
            'office_text': 'Tel Aviv',
            'country': 'Israel',
            'link': 'https://example.com'
        }
        result = parser.parse(job_data)
        assert result['location'] == 'Tel Aviv'
        
        # Test fallback to country
        job_data = {
            'id': 2,
            'title': 'Test Job 2',
            'country': 'Israel',
            'link': 'https://example.com'
        }
        result = parser.parse(job_data)
        assert result['location'] == 'Israel'

    def test_extract_jobs_from_html(self):
        """Test extracting jobs from HTML with embedded JavaScript."""
        parser = EmbeddedJSParser(site_name='taboola')
        
        html = '''
        <html>
        <script>
        var jobs = [
            {"id": 1, "title": "Engineer", "office_textual": "Tel Aviv", "link": "/job/1"},
            {"id": 2, "title": "Manager", "office_textual": "NYC", "link": "/job/2"}
        ];
        </script>
        </html>
        '''
        
        jobs = parser.extract_jobs_from_html(html)
        
        assert len(jobs) == 2
        assert jobs[0]['title'] == 'Engineer'
        assert jobs[1]['title'] == 'Manager'

    def test_extract_jobs_with_html_entities(self):
        """Test that HTML entities are properly cleaned."""
        parser = EmbeddedJSParser(site_name='taboola')
        
        html = '''
        <script>
        var jobs = [
            {"id": 1, "title": "Senior &#8211; Engineer", "office_textual": "R&amp;D Center", "link": "/job"}
        ];
        </script>
        '''
        
        jobs = parser.extract_jobs_from_html(html)
        
        assert len(jobs) == 1
        assert jobs[0]['title'] == 'Senior - Engineer'
        assert jobs[0]['office_textual'] == 'R&D Center'

    def test_extract_jobs_no_match(self):
        """Test that empty list is returned when pattern not found."""
        parser = EmbeddedJSParser(site_name='taboola')
        
        html = '<html><body>No jobs here</body></html>'
        
        jobs = parser.extract_jobs_from_html(html)
        
        assert jobs == []

    def test_custom_config(self):
        """Test parser with custom configuration."""
        custom_config = {
            'variable_pattern': r'window\.JOBS = (\[.*?\]);',
            'field_mapping': {
                'external_id': 'job_id',
                'title': 'position',
                'location': 'city',
                'job_url': 'apply_url',
            }
        }
        
        parser = EmbeddedJSParser(config=custom_config)
        
        job_data = {
            'job_id': 'ABC123',
            'position': 'Software Developer',
            'city': 'San Francisco',
            'apply_url': 'https://example.com/apply'
        }
        
        result = parser.parse(job_data)
        
        assert result['external_id'] == 'ABC123'
        assert result['title'] == 'Software Developer'
        assert result['location'] == 'San Francisco'
        assert result['job_url'] == 'https://example.com/apply'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

