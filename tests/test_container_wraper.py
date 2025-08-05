from unittest.mock import MagicMock

from app.domain.container_wraper import ContainerWrapper, ContainerLabelOptions


def test_id_property():
    mock_container = MagicMock()
    mock_container.id = "abc123"
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.id == "abc123", "Expected id to match container id."


def test_name_property():
    mock_container = MagicMock()
    mock_container.name = "test_container"
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.name == "test_container", "Expected name to match container name."


def test_labels_dict_property():
    mock_container = MagicMock()
    mock_container.labels = {"label1": "value1"}
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.labels_dict == {"label1": "value1"}, "Expected labels_dict to match container labels."


def test_attrs_property():
    mock_container = MagicMock()
    mock_container.attrs = {"key": "value"}
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.attrs == {"key": "value"}, "Expected attrs to match container attributes."


def test_disabled_property_enabled():
    mock_container = MagicMock()
    mock_container.labels = {ContainerLabelOptions.DISABLED.value: "false"}
    wrapper = ContainerWrapper(mock_container)
    assert not wrapper.disabled, "Expected disabled to be False for 'dockdns.disabled=false'."


def test_disabled_property_disabled():
    mock_container = MagicMock()
    mock_container.labels = {ContainerLabelOptions.DISABLED.value: "true"}
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.disabled, "Expected disabled to be True for 'dockdns.disabled=true'."


def test_target_hostname_property_with_label():
    mock_container = MagicMock()
    mock_container.name = "default_name"
    mock_container.labels = {ContainerLabelOptions.HOSTNAME.value: "custom_hostname"}
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.labeled_hostname == "custom_hostname", "Expected target_hostname to match labeled hostname."


def test_target_hostname_property_without_label():
    mock_container = MagicMock()
    mock_container.name = "default_name"
    mock_container.labels = {}
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.labeled_hostname == "default_name", "Expected target_hostname to default to container name."


def test_labeled_port_property_with_port():
    mock_container = MagicMock()
    mock_container.labels = {ContainerLabelOptions.PORT.value: "8080"}
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.labeled_port == "8080", "Expected labeled_port to match labeled port."


def test_labeled_port_property_without_port():
    mock_container = MagicMock()
    mock_container.labels = {}
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.labeled_port is None, "Expected labeled_port to be None when label is missing."


def test_exposed_ports_property():
    mock_container = MagicMock()
    mock_container.attrs = {"Config": {"ExposedPorts": ["80/tcp", "443/tcp"]}}
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.exposed_ports == ["80/tcp", "443/tcp"], "Expected exposed_ports to match container exposed ports."


def test_exposed_ports_property_empty():
    mock_container = MagicMock()
    mock_container.attrs = {"Config": {}}
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.exposed_ports == [], "Expected exposed_ports to be an empty list when no ports are exposed."


def test_exposed_ports_property_none():
    """
    Test the behavior of the exposed_ports property when ExposedPorts is set to None.
    """
    mock_container = MagicMock()
    mock_container.attrs = {"Config": {"ExposedPorts": None}}
    wrapper = ContainerWrapper(mock_container)

    assert wrapper.exposed_ports == [], (
        "Expected exposed_ports to return an empty list when 'ExposedPorts' is None."
    )
    assert wrapper.exposed_ports[0] if wrapper.exposed_ports else True, (
        "Expected first exposed port to be None when 'ExposedPorts' is None."
    )


def test_network_settings_ip_address_property():
    mock_container = MagicMock()
    mock_container.attrs = {"NetworkSettings": {"IPAddress": "192.168.1.1"}}
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.network_settings_ip_address == "192.168.1.1", "Expected network_settings_ip_address to match container IP."


def test_network_settings_ip_address_property_missing():
    mock_container = MagicMock()
    mock_container.attrs = {"NetworkSettings": {}}
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.network_settings_ip_address is None, "Expected network_settings_ip_address to be None when IP is missing."


def test_is_network_host_mode_true():
    mock_container = MagicMock()
    mock_container.attrs = {"HostConfig": {"NetworkMode": "host"}}
    wrapper = ContainerWrapper(mock_container)
    assert wrapper.is_network_host_mode(), "Expected is_network_host_mode to return True for host network mode."


def test_is_network_host_mode_false():
    mock_container = MagicMock()
    mock_container.attrs = {"HostConfig": {"NetworkMode": "bridge"}}
    wrapper = ContainerWrapper(mock_container)
    assert not wrapper.is_network_host_mode(), "Expected is_network_host_mode to return False for non-host network mode."


def test_str_representation():
    mock_container = MagicMock()
    mock_container.id = "abc123"
    mock_container.name = "test_container"
    mock_container.labels = {}
    mock_container.attrs = {}
    wrapper = ContainerWrapper(mock_container)
    container_str = str(wrapper)
    assert "ContainerWrapper(" in container_str, "Expected string representation to include 'ContainerWrapper('."
    assert "id=abc123" in container_str, "Expected string representation to include container id."
    assert "name=test_container" in container_str, "Expected string representation to include container name."
