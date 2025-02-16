# pylint: disable=missing-module-docstring, missing-function-docstring, protected-access

import socksies


def test_parse_proxy_config():
    """Test for two proxies defined in the sample config; proxy1, proxy2."""
    proxies = socksies.parse_proxy_config()
    assert len(proxies) == 2
    names = {proxy["name"] for proxy in proxies}
    assert "proxy1" in names
    assert "proxy2" in names


def test_proxy_search_found():
    """Test search and validate data for a valid proxy."""
    proxy = socksies._proxy_search("proxy1")
    assert proxy is not None
    assert proxy["host"] == "172.31.0.51"
    assert proxy["port"] == 9051
    assert proxy["identity_file"] == "~/.ssh/private_key"


def test_proxy_search_not_found():
    proxy = socksies._proxy_search("nonexistent")
    assert proxy is None
