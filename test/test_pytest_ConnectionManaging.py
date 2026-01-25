import sys
import os
from unittest.mock import MagicMock, patch, call
import pytest

# Add the project root to the path to allow importing ConnectionManaging from the parent directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock MicroPython-specific modules before they are imported by the class under test.
# This is a common pattern when testing code that relies on environment-specific libraries.
mock_network = MagicMock()
mock_urequests = MagicMock()
mock_time = MagicMock()
mock_gc = MagicMock()

sys.modules['network'] = mock_network
sys.modules['urequests'] = mock_urequests
sys.modules['time'] = mock_time
sys.modules['gc'] = mock_gc

# Now, we can safely import the class we want to test.
from Manager.ConnectionManager import ConnectionManaging

# --- Pytest Fixtures ---

@pytest.fixture
def mock_station():
    """Fixture to provide a mocked WLAN station object."""
    station = MagicMock()
    # Reset mocks before each test that uses this fixture
    station.reset_mock()
    mock_network.WLAN.return_value = station
    return station

@pytest.fixture
def conn_manager(mock_station):
    """Fixture to provide an instance of ConnectionManaging with a mocked station."""
    # The mock_station fixture will be automatically used here
    manager = ConnectionManaging(ssid="test_ssid", password="test_password", host="testhost.com")
    # Suppress log messages during tests for cleaner output
    manager.log_message = MagicMock()
    return manager

# --- Test Cases ---

class TestConnectionManaging:
    """Group tests for the ConnectionManaging class."""

    def test_initialization(self, conn_manager, mock_station):
        """Test that the class initializes correctly."""
        assert conn_manager.ssid == "test_ssid"
        assert conn_manager.password == "test_password"
        assert conn_manager.host == "testhost.com"
        mock_network.WLAN.assert_called_once_with(mock_network.STA_IF)
        assert conn_manager._station is mock_station

    def test_properties(self, conn_manager):
        """Test the getters and setters."""
        conn_manager.ssid = "new_ssid"
        assert conn_manager.ssid == "new_ssid"

        conn_manager.password = "new_password"
        assert conn_manager.password == "new_password"

        conn_manager.host = "newhost.com"
        assert conn_manager.host == "newhost.com"

    def test_connect_success_first_try(self, conn_manager, mock_station):
        """Test successful connection when already connected."""
        mock_station.isconnected.return_value = True
        mock_station.ifconfig.return_value = ('192.168.1.100',)
        
        assert conn_manager.connect() is True
        mock_station.active.assert_called_once_with(True)
        mock_station.connect.assert_not_called()

    def test_connect_success_after_retries(self, conn_manager, mock_station):
        """Test successful connection after a few retries."""
        mock_station.isconnected.side_effect = [False, False, False, True]
        mock_station.ifconfig.return_value = ('192.168.1.100',)
        
        assert conn_manager.connect() is True
        mock_station.active.assert_called_once_with(True)
        mock_station.connect.assert_called_once_with("test_ssid", "test_password")
        assert mock_time.sleep.call_count == 3

    def test_connect_failure(self, conn_manager, mock_station):
        """Test connection failure after all attempts."""
        mock_station.isconnected.return_value = False
        
        assert conn_manager.connect() is False
        mock_station.active.assert_has_calls([call(True), call(False)])
        mock_station.connect.assert_called_once_with("test_ssid", "test_password")
        assert mock_time.sleep.call_count == 40

    def test_disconnect_when_connected(self, conn_manager, mock_station):
        """Test disconnecting when there is an active connection."""
        mock_station.isconnected.return_value = True
        
        assert conn_manager.disconnect() is True
        mock_station.disconnect.assert_called_once()
        mock_station.active.assert_called_once_with(False)

    def test_disconnect_when_not_connected(self, conn_manager, mock_station):
        """Test disconnecting when there is no active connection."""
        mock_station.isconnected.return_value = False
        
        assert conn_manager.disconnect() is True
        mock_station.disconnect.assert_not_called()
        mock_station.active.assert_not_called()

    @pytest.mark.parametrize("status_code, expected_string", [
        (mock_network.STAT_IDLE, "NO CONNECTION"),
        (mock_network.STAT_CONNECTING, "CONNECTING"),
        (mock_network.STAT_WRONG_PASSWORD, "WRONG PASSWORD"),
        (mock_network.STAT_NO_AP_FOUND, "NO AP FOUND"),
        (mock_network.STAT_GOT_IP, "CONNECTED"),
        (12345, "OTHER"), # Test a generic, non-defined status
    ])
    def test_connection_status(self, conn_manager, mock_station, status_code, expected_string):
        """Test connection_status for all possible statuses using parametrization."""
        mock_station.status.return_value = status_code
        assert conn_manager.connection_status() == expected_string

    def test_post_https_request_success(self, conn_manager):
        """Test a successful POST request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "ok"}'
        mock_urequests.post.return_value = mock_response
        
        url = "http://testhost.com/api"
        data = {"key": "value"}
        
        result = conn_manager._post_https_request(url, data)
        
        assert result == '{"status": "ok"}'
        mock_urequests.post.assert_called_once_with(url, json=data, timeout=15)
        mock_response.close.assert_called_once()
        mock_gc.collect.assert_called_once()

    def test_post_https_request_http_error(self, conn_manager):
        """Test a POST request that fails with an HTTP server error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = b"Internal Server Error"
        mock_response.text = "Server Error"
        mock_urequests.post.return_value = mock_response

        result = conn_manager._post_https_request("http://testhost.com/api", {})
        
        assert result is None
        mock_urequests.post.assert_called_once()
        mock_response.close.assert_called_once()

    def test_post_https_request_network_error_with_retry(self, conn_manager):
        """Test a request that fails with OSError and then succeeds on retry."""
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.text = '{"status": "ok"}'
        
        mock_urequests.post.side_effect = [OSError("Network down"), mock_success_response]
        
        result = conn_manager._post_https_request("http://testhost.com/api", {}, max_retries=3)
        
        assert result == '{"status": "ok"}'
        assert mock_urequests.post.call_count == 2
        mock_time.sleep.assert_called_once_with(2)

    def test_send_value_to_web_success(self, conn_manager):
        """Test the send_value_to_web method for a successful scenario."""
        with patch.object(conn_manager, 'connect', return_value=True) as mock_connect, \
             patch.object(conn_manager, '_post_https_request', return_value='{"status": "ok"}') as mock_post, \
             patch.object(conn_manager, 'disconnect') as mock_disconnect:
            
            timestamp = "2023-10-27T10:00:00Z"
            result = conn_manager.send_value_to_web(value=25.5, key="Temp", timestamp=timestamp)
            
            assert result is True
            mock_connect.assert_called_once()
            
            expected_url = f"http://{conn_manager.host}/takeTemp.php"
            expected_data = {"Temp": 25.5, "Date": timestamp}
            mock_post.assert_called_once_with(expected_url, expected_data)
            
            mock_disconnect.assert_called_once()

    def test_send_value_to_web_connection_fails(self, conn_manager):
        """Test send_value_to_web when the WiFi connection fails."""
        with patch.object(conn_manager, 'connect', return_value=False) as mock_connect, \
             patch.object(conn_manager, '_post_https_request') as mock_post:

            result = conn_manager.send_value_to_web(123, "key", "ts")
            
            assert result is False
            mock_connect.assert_called_once()
            mock_post.assert_not_called()
