import pytest
from testcontainers.core.container import DockerContainer

from app.domain.container_wraper import ContainerWrapper  # Import your main code to be tested
from utils.os_utils import get_internal_docker_host, get_system_ip_address


@pytest.mark.functional
def test_get_internal_docker_host():
    internal_host = get_internal_docker_host()
    assert internal_host is not None, "Expected to get a valid internal Docker host address."
    assert isinstance(internal_host, str), "Internal Docker host should be a string."


@pytest.mark.integration
def test_get_system_ip_address():
    system_ip = get_system_ip_address()
    assert system_ip is not None, "System IP address should not be None."
    assert isinstance(system_ip, str), "System IP address should be a string."
    assert len(system_ip.split('.')) == 4, "System IP should be a valid IPv4 address."


@pytest.mark.functional
def test_container_wrapper_with_testcontainers(
        logger_config,
):
    docker_container = DockerContainer(image="nginx:latest", ports=[8081], name="test-container")
    with docker_container as hw_container:
        # Verify the container is running
        assert hw_container is not None, "Container could not be started."

        # Obtain the container object from Testcontainers
        container = hw_container._container

        # Wrap the container with your `ContainerWrapper` class
        wrapper = ContainerWrapper(container)

        # Perform assertions (adjust based on your class structure and needs)
        assert wrapper.id is not None, "Container ID is expected to be not None."
        assert wrapper.name.startswith("test-container"), "Container name should match the container."
        assert "8081/tcp" in wrapper.exposed_ports, "Port 8080 should be exposed."
