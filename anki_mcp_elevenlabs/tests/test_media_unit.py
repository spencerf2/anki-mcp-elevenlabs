from unittest.mock import Mock, patch

import pytest
import requests

# Import the functions we want to test
from anki_mcp_elevenlabs.server import (
    delete_media_file,
    get_media_directory,
    list_media_files,
    media_file_exists,
    retrieve_media_file,
)

# Mock data based on real responses
MOCK_MEDIA_FILES = [
    "00igloo.jpg",
    "1-A-Arpa-Speaker2-1.mp3",
    "test_audio.mp3",
    "sample_image.jpg",
    "chinese_word.mp3",
]

MOCK_MP3_FILES = ["1-A-Arpa-Speaker2-1.mp3", "test_audio.mp3", "chinese_word.mp3"]


class TestListMediaFiles:
    """Test list_media_files function"""

    @patch("anki_mcp_elevenlabs.server.requests.post")
    @pytest.mark.asyncio
    async def test_list_all_files_success(self, mock_post):
        """Test listing all media files successfully"""
        # Mock successful AnkiConnect response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": MOCK_MEDIA_FILES, "error": None}
        mock_post.return_value = mock_response

        result = await list_media_files()

        assert result["success"] is True
        assert result["count"] == 5
        assert result["pattern"] is None
        assert "00igloo.jpg" in result["files"]
        assert "test_audio.mp3" in result["files"]
        # Verify files are sorted
        assert result["files"] == sorted(MOCK_MEDIA_FILES)

    @patch("anki_mcp_elevenlabs.server.requests.post")
    @pytest.mark.asyncio
    async def test_list_files_with_pattern(self, mock_post):
        """Test listing files with pattern filter"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": MOCK_MP3_FILES, "error": None}
        mock_post.return_value = mock_response

        result = await list_media_files(pattern="*.mp3")

        assert result["success"] is True
        assert result["count"] == 3
        assert result["pattern"] == "*.mp3"
        assert all(f.endswith(".mp3") for f in result["files"])

    @patch("anki_mcp_elevenlabs.server.requests.post")
    @pytest.mark.asyncio
    async def test_list_files_ankiconnect_error(self, mock_post):
        """Test handling AnkiConnect API errors"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": None,
            "error": "Collection not open",
        }
        mock_post.return_value = mock_response

        result = await list_media_files()

        assert result["success"] is False
        assert "Collection not open" in result["error"]

    @patch("anki_mcp_elevenlabs.server.requests.post")
    @pytest.mark.asyncio
    async def test_list_files_connection_error(self, mock_post):
        """Test handling connection failures"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = await list_media_files()

        assert result["success"] is False
        assert "500" in result["error"]


class TestMediaFileExists:
    """Test media_file_exists function"""

    @patch("anki_mcp_elevenlabs.server.requests.post")
    @pytest.mark.asyncio
    async def test_file_exists_true(self, mock_post):
        """Test checking existing file"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "base64_file_data_here",  # Non-false result means exists
            "error": None,
        }
        mock_post.return_value = mock_response

        result = await media_file_exists("test_audio.mp3")

        assert result["success"] is True
        assert result["exists"] is True
        assert result["filename"] == "test_audio.mp3"

    @patch("anki_mcp_elevenlabs.server.requests.post")
    @pytest.mark.asyncio
    async def test_file_exists_false(self, mock_post):
        """Test checking non-existent file"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": False,  # False result means file doesn't exist
            "error": None,
        }
        mock_post.return_value = mock_response

        result = await media_file_exists("missing_file.mp3")

        assert result["success"] is True
        assert result["exists"] is False
        assert result["filename"] == "missing_file.mp3"


class TestRetrieveMediaFile:
    """Test retrieve_media_file function"""

    @patch("anki_mcp_elevenlabs.server.requests.post")
    @pytest.mark.asyncio
    async def test_retrieve_existing_file_with_base64(self, mock_post):
        """Test retrieving existing file with base64 data"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "base64_encoded_file_data",
            "error": None,
        }
        mock_post.return_value = mock_response

        result = await retrieve_media_file("test_audio.mp3", return_base64=True)

        assert result["success"] is True
        assert result["exists"] is True
        assert result["filename"] == "test_audio.mp3"
        assert result["base64_data"] == "base64_encoded_file_data"

    @patch("anki_mcp_elevenlabs.server.requests.post")
    @pytest.mark.asyncio
    async def test_retrieve_existing_file_without_base64(self, mock_post):
        """Test retrieving existing file without base64 data"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "base64_encoded_file_data",
            "error": None,
        }
        mock_post.return_value = mock_response

        result = await retrieve_media_file("test_audio.mp3", return_base64=False)

        assert result["success"] is True
        assert result["exists"] is True
        assert result["filename"] == "test_audio.mp3"
        assert "base64_data" not in result
        assert "exists (content not returned)" in result["message"]

    @patch("anki_mcp_elevenlabs.server.requests.post")
    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_file(self, mock_post):
        """Test retrieving non-existent file"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": False,  # False means file not found
            "error": None,
        }
        mock_post.return_value = mock_response

        result = await retrieve_media_file("missing_file.mp3")

        assert result["success"] is True
        assert result["exists"] is False
        assert result["filename"] == "missing_file.mp3"
        assert "not found" in result["message"]


class TestDeleteMediaFile:
    """Test delete_media_file function"""

    @pytest.mark.asyncio
    async def test_delete_without_confirmation(self):
        """Test delete fails without confirm=True"""
        result = await delete_media_file("test_file.mp3", confirm=False)

        assert result["success"] is False
        assert "confirm=True" in result["error"]
        assert result["filename"] == "test_file.mp3"

    @patch("anki_mcp_elevenlabs.server.media_file_exists")
    @patch("anki_mcp_elevenlabs.server.requests.post")
    @pytest.mark.asyncio
    async def test_delete_existing_file(self, mock_post, mock_exists):
        """Test deleting existing file"""
        # Mock file exists check
        mock_exists.return_value = {"success": True, "exists": True}

        # Mock successful deletion
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": None, "error": None}
        mock_post.return_value = mock_response

        result = await delete_media_file("test_file.mp3", confirm=True)

        assert result["success"] is True
        assert result["deleted"] is True
        assert result["filename"] == "test_file.mp3"
        assert "deleted successfully" in result["message"]

    @patch("anki_mcp_elevenlabs.server.media_file_exists")
    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, mock_exists):
        """Test deleting non-existent file"""
        # Mock file doesn't exist
        mock_exists.return_value = {"success": True, "exists": False}

        result = await delete_media_file("missing_file.mp3", confirm=True)

        assert result["success"] is True
        assert result["deleted"] is False
        assert result["filename"] == "missing_file.mp3"
        assert "does not exist" in result["message"]


class TestGetMediaDirectory:
    """Test get_media_directory function"""

    @patch("anki_mcp_elevenlabs.server.requests.post")
    @pytest.mark.asyncio
    async def test_get_media_directory_success(self, mock_post):
        """Test getting media directory path successfully"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "/Users/sf/Library/Application Support/Anki2/User 1/collection.media",
            "error": None,
        }
        mock_post.return_value = mock_response

        result = await get_media_directory()

        assert result["success"] is True
        assert "collection.media" in result["path"]
        assert "Media directory:" in result["message"]


if __name__ == "__main__":
    # Run with: python -m pytest test_media_unit.py -v
    print("Run tests with: python -m pytest test_media_unit.py -v")
    print("Or install pytest: pip install pytest pytest-asyncio")
