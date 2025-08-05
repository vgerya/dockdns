from unittest.mock import patch

import pytest

from agent.container_watcher import get_dns_record, process_container, destroy_container


def test_get_dns_record_valid(wrapper, config):
    config.dns_ip = "0.0.0.0"
    record = get_dns_record(wrapper, config)

    assert record.hostname == wrapper.labeled_hostname
    assert record.ip == "0.0.0.0"
    assert record.port == wrapper


def test_get_ip_from_container(wrapper, config):
    config.dns_ip = None
    wrapper._ContainerWrapper__container.attrs["NetworkSettings"]["IPAddress"] = "1.1.1.1"
    record = get_dns_record(wrapper, config)

    assert record.ip == "1.1.1.1"


@patch("os.popen")
def test_get_ip_from_container_in_host_mode(wrapper, config, mock_popen, ):
    config.dns_ip = None
    wrapper._ContainerWrapper__container.attrs["NetworkSettings"]["IPAddress"] = None
    wrapper._ContainerWrapper__container.attrs["HostConfig"]["NetworkMode"] = "host"

    mock_popen.return_value.read.return_value = "1.1.1.1 "

    record = get_dns_record(wrapper, config)

    assert record.ip == "1.1.1.1"


def test_get_ip_from_config(wrapper, config):
    config.dns_ip = "0.0.0.0"
    record = get_dns_record(wrapper, config)

    assert record.ip == "0.0.0.0"


def test_get_dns_record_missing_ip(wrapper, config):
    wrapper._ContainerWrapper__container.attrs["NetworkSettings"]["IPAddress"] = None
    config.dns_ip = None
    with pytest.raises(ValueError):
        get_dns_record(wrapper, config)


def test_process_container_dry_run(wrapper, config, caplog):
    config.dry_run = True
    with caplog.at_level("INFO"):
        process_container(wrapper, config)
    assert "[DRY RUN]" in caplog.text


def test_destroy_container_dry_run(wrapper, config, caplog):
    config.dry_run = True
    with caplog.at_level("INFO"):
        destroy_container(wrapper, config)
    assert "[DRY RUN]" in caplog.text
