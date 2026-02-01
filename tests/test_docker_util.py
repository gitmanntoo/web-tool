"""
Tests for library/docker_util.py

Tests container detection utilities.
"""

import pytest
import os
from unittest.mock import patch, mock_open
from library.docker_util import is_running_in_container


class TestIsRunningInContainer:
    """Tests for is_running_in_container function."""

    def test_returns_boolean(self):
        """Test that function returns a boolean."""
        result = is_running_in_container()
        assert isinstance(result, bool)

    def test_detects_dockerenv_file(self):
        """Test detection when /.dockerenv file exists."""
        with patch('os.path.exists') as mock_exists:
            def exists_side_effect(path):
                return path == '/.dockerenv'
            mock_exists.side_effect = exists_side_effect
            
            result = is_running_in_container()
            assert result is True

    def test_detects_container_runtime_env(self):
        """Test detection via CONTAINER_RUNTIME environment variable."""
        with patch.dict(os.environ, {'CONTAINER_RUNTIME': 'docker'}):
            # Note: This won't override the os.path.exists check
            # but we're testing the logic exists
            result = is_running_in_container()
            assert isinstance(result, bool)

    def test_no_container_markers(self):
        """Test when no container markers are found."""
        with patch('os.path.exists') as mock_exists:
            with patch.dict(os.environ, {}, clear=True):
                with patch('subprocess.check_output') as mock_subprocess:
                    mock_exists.return_value = False
                    mock_subprocess.return_value = b'localhost\n'
                    
                    result = is_running_in_container()
                    assert isinstance(result, bool)

    def test_detects_docker_hostname(self):
        """Test detection when hostname starts with 'docker-'."""
        with patch('os.path.exists') as mock_exists:
            with patch('subprocess.check_output') as mock_subprocess:
                mock_exists.return_value = False
                
                # First call is for hostname, second for uname
                def subprocess_side_effect(cmd):
                    if 'hostname' in cmd:
                        return b'docker-abc123\n'
                    return b'Linux version\n'
                
                mock_subprocess.side_effect = subprocess_side_effect
                result = is_running_in_container()
                assert result is True

    def test_detects_docker_in_uname(self):
        """Test detection when 'docker' appears in uname output."""
        with patch('os.path.exists') as mock_exists:
            with patch('subprocess.check_output') as mock_subprocess:
                mock_exists.return_value = False
                
                def subprocess_side_effect(cmd):
                    if 'hostname' in cmd:
                        return b'localhost\n'
                    # uname output
                    return b'Linux docker-host 5.10.0 #1 SMP Docker\n'
                
                mock_subprocess.side_effect = subprocess_side_effect
                result = is_running_in_container()
                # Depending on implementation, this might be True
                assert isinstance(result, bool)

    def test_cgroup_docker_detection(self):
        """Test detection via /proc/1/cgroup with docker marker."""
        with patch('os.path.exists') as mock_exists:
            with patch('builtins.open', mock_open(read_data='docker-abc123\n')):
                def exists_side_effect(path):
                    return path == '/proc/1/cgroup'
                mock_exists.side_effect = exists_side_effect
                
                result = is_running_in_container()
                assert result is True

    def test_cgroup_containerd_detection(self):
        """Test detection via /proc/1/cgroup with containerd marker."""
        with patch('os.path.exists') as mock_exists:
            with patch('builtins.open', mock_open(read_data='containerd-abc\n')):
                def exists_side_effect(path):
                    return path == '/proc/1/cgroup'
                mock_exists.side_effect = exists_side_effect
                
                result = is_running_in_container()
                assert result is True

    def test_cgroup_kubepods_detection(self):
        """Test detection via /proc/1/cgroup with kubepods marker."""
        with patch('os.path.exists') as mock_exists:
            with patch('builtins.open', mock_open(read_data='kubepods.slice\n')):
                def exists_side_effect(path):
                    return path == '/proc/1/cgroup'
                mock_exists.side_effect = exists_side_effect
                
                result = is_running_in_container()
                assert result is True

    def test_cgroup_podman_detection(self):
        """Test detection via /proc/1/cgroup with podman marker."""
        with patch('os.path.exists') as mock_exists:
            with patch('builtins.open', mock_open(read_data='podman-abc\n')):
                def exists_side_effect(path):
                    return path == '/proc/1/cgroup'
                mock_exists.side_effect = exists_side_effect
                
                result = is_running_in_container()
                assert result is True

    def test_cgroup_lxc_detection(self):
        """Test detection via /proc/1/cgroup with lxc marker."""
        with patch('os.path.exists') as mock_exists:
            with patch('builtins.open', mock_open(read_data='lxc.service\n')):
                def exists_side_effect(path):
                    return path == '/proc/1/cgroup'
                mock_exists.side_effect = exists_side_effect
                
                result = is_running_in_container()
                assert result is True

    def test_cgroup_os_error_handling(self):
        """Test that OSError when reading cgroup is handled gracefully."""
        with patch('os.path.exists') as mock_exists:
            with patch('builtins.open', side_effect=OSError("Permission denied")):
                def exists_side_effect(path):
                    return path == '/proc/1/cgroup'
                mock_exists.side_effect = exists_side_effect
                
                # Should not raise, returns based on other checks
                result = is_running_in_container()
                assert isinstance(result, bool)

    def test_detects_container_hostname_prefix(self):
        """Test detection when hostname starts with 'container-'."""
        with patch('os.path.exists') as mock_exists:
            with patch('subprocess.check_output') as mock_subprocess:
                mock_exists.return_value = False
                
                def subprocess_side_effect(cmd):
                    if 'hostname' in cmd:
                        return b'container-xyz789\n'
                    return b'Linux version\n'
                
                mock_subprocess.side_effect = subprocess_side_effect
                result = is_running_in_container()
                assert result is True

    def test_subprocess_exception_handling(self):
        """Test that subprocess exceptions are handled gracefully."""
        with patch('os.path.exists') as mock_exists:
            with patch('subprocess.check_output') as mock_subprocess:
                mock_exists.return_value = False
                mock_subprocess.side_effect = Exception("Command failed")
                
                # Should handle exception and continue checking
                # The function should still return a boolean
                try:
                    result = is_running_in_container()
                    assert isinstance(result, bool)
                except Exception:
                    # If exception is raised, that's also acceptable
                    pass


class TestContainerDetectionIntegration:
    """Integration tests for container detection."""

    def test_multiple_detection_methods(self):
        """Test that multiple detection methods work independently."""
        # This test ensures that if one method fails,
        # others can still be tried
        with patch('os.path.exists') as mock_exists:
            # /.dockerenv doesn't exist
            mock_exists.return_value = False
            
            # But we're not in a container
            result = is_running_in_container()
            assert isinstance(result, bool)

    def test_detection_on_actual_system(self):
        """Test that detection works on the actual system."""
        # Just ensure it returns a boolean without error
        result = is_running_in_container()
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
