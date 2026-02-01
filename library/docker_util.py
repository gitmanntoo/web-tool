import os
import subprocess


def is_running_in_container():
    """Run a variety of checks to determine if the script is running in a container."""

    if os.path.exists('/.dockerenv'):
        return True
    if 'CONTAINER_RUNTIME' in os.environ:
        return True
    if os.path.exists('/proc/1/cgroup'):
        try:
            with open('/proc/1/cgroup', 'r', encoding='utf-8') as f:
                cgroup_data = f.read()
            cgroup_markers = (
                'docker',
                'containerd',
                'kubepods',
                'podman',
                'lxc',
            )
            if any(marker in cgroup_data for marker in cgroup_markers):
                return True
        except OSError:
            pass

    hostname = subprocess.check_output(['hostname']).decode('utf-8').strip()
    if hostname.startswith('docker-') or hostname.startswith('container-'):
        return True
    uname_output = subprocess.check_output(['uname', '-a']).decode('utf-8').strip()
    if 'docker' in uname_output or 'container' in uname_output:
        return True
    return False
