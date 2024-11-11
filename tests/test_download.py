"""
Download Service Test Suite

This test module covers various download scenarios:
- Successful file download
- Handling of download errors
- File integrity checks
- Download progress tracking
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.download_service import DownloadService
from app.exceptions import DownloadError

class TestDownloadService:
    @pytest.fixture
    def download_service(self):
        """
        Fixture to create a DownloadService instance for testing
        """
        return DownloadService()

    @patch('app.services.download_service.requests.get')
    def test_successful_download(self, mock_get, download_service):
        """
        Test successful file download
        """
        # Mock response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'Test file content'
        mock_get.return_value = mock_response

        url = "http://example.com/testfile.txt"
        destination = "downloads/testfile.txt"

        # Perform download
        download_service.download_file(url, destination)

        # Assertions
        mock_get.assert_called_once_with(url)
        with open(destination, 'rb') as f:
            content = f.read()
            assert content == b'Test file content'

    @patch('app.services.download_service.requests.get')
    def test_download_error(self, mock_get, download_service):
        """
        Test handling of download errors
        """
        # Mock response for a failed download
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        url = "http://example.com/nonexistentfile.txt"
        destination = "downloads/nonexistentfile.txt"

        # Expect DownloadError to be raised
        with pytest.raises(DownloadError):
            download_service.download_file(url, destination)

    @patch('app.services.download_service.requests.get')
    def test_file_integrity_check(self, mock_get, download_service):
        """
        Test file integrity check after download
        """
        # Mock response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'Test file content'
        mock_get.return_value = mock_response

        url = "http://example.com/testfile.txt"
        destination = "downloads/testfile.txt"

        # Perform download
        download_service.download_file(url, destination)

        # Check file integrity
        assert download_service.check_file_integrity(destination)

    @patch('app.services.download_service.requests.get')
    def test_download_progress(self, mock_get, download_service):
        """
        Test download progress tracking
        """
        # Mock response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b'Test ', b'file ', b'content']
        mock_get.return_value = mock_response

        url = "http://example.com/testfile.txt"
        destination = "downloads/testfile.txt"

        # Perform download and track progress
        progress = download_service.download_file_with_progress(url, destination)

        # Assertions
        assert progress == 100  # Assuming the download completes successfully
        assert mock_get.call_count == 1

    @patch('app.services.download_service.requests.get')
    def test_partial_download_handling(self, mock_get, download_service):
        """
        Test handling of partial downloads
        """
        # Mock response for a partial download
        mock_response = MagicMock()
        mock_response.status_code = 206  # Partial Content
        mock_response.content = b'Partial content'
        mock_get.return_value = mock_response

        url = "http://example.com/partialfile.txt"
        destination = "downloads/partialfile.txt"

        # Perform download
        download_service.download_file(url, destination)

        # Assertions
        with open(destination, 'rb') as f:
            content = f.read()
            assert content == b'Partial content'

    @patch('app.services.download_service.requests.get')
    def test_download_timeout(self, mock_get, download_service):
        """
        Test handling of download timeout
        """
        # Mock a timeout exception
        mock_get.side_effect = TimeoutError("Connection timed out")

        url = "http://example.com/testfile.txt"
        destination = "downloads/testfile.txt"

        # Expect DownloadError to be raised
        with pytest.raises(DownloadError):
            download_service.download_file(url, destination)
          
