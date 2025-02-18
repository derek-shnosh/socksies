#!/usr/bin/env python3
# pylint: disable=missing-module-docstring, unused-argument

# Author: Derek Smiley


"""
Manage socks proxies for jump hosts connected to VPN environments.
"""

import sys
import os
import subprocess
import argparse
import yaml


# Allow CONFIG_FILE to be overwritten for pytest, allow script to find
# 'proxy-config.yml' where the script is located for symoblic links
CONFIG_FILE = os.getenv(
    "SOCKSIES_CONFIG",
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "proxy-config.yml")
)


def _proxy_search(proxy_name):
    """
    Helper function to search for 'proxy_name' in the YAML config.
    """

    proxies = parse_proxy_config()
    for proxy in proxies:
        if proxy["name"] == proxy_name:
            return proxy
    return None


def parse_proxy_config():
    """
    Reads the YAML file and returns a list of dictionaries, one for each proxy.
    """

    with open(CONFIG_FILE, "r", encoding="utf-8") as pconfig:
        proxy_config = yaml.safe_load(pconfig)

    proxies = []
    for proxy_name, proxy_data in proxy_config.items():
        # Extract fields with defaults if missing
        host = proxy_data.get("host", "--")
        port = proxy_data.get("port", "--")
        identity_file = proxy_data.get("identity_file", "")

        proxies.append(
            {
                "name": proxy_name,
                "host": host,
                "port": port,
                "identity_file": identity_file,
            }
        )

    return proxies


def proxy_list(args):
    """
    Lists all top-level proxy names from the YAML config.
    """

    print("Listing configured Proxies:")
    proxies = parse_proxy_config()
    for proxy in proxies:
        print(f"- {proxy['name']} ({proxy['host']}:{proxy['port']})")


def proxy_info(args):
    """
    Lists detailed info for he proxy matching 'proxy_name'.
    """

    proxy_name = args.proxy_name

    # Search for the requested proxy in parsed list
    found_proxy = _proxy_search(proxy_name)
    if not found_proxy:
        print(f"Error: Proxy '{proxy_name}' not found in {CONFIG_FILE}.")
        return

    # Print the found proxy's details
    print(f"Proxy: {found_proxy['name']}")
    print(f"  Host: {found_proxy['host']}")
    print(f"  Port: {found_proxy['port']}")
    print(f"  Identity File: {found_proxy['identity_file']}")


def proxy_status(args):
    """
    Lists any proxies that appear to have an active SSH process, matching the
    exact command used in proxy_connect().
    Uses 'pgrep -af' to look for matching processes.
    """

    proxies = parse_proxy_config()
    connected = []

    for proxy in proxies:
        proxy_host = proxy["host"]
        proxy_port = proxy["port"]
        proxy_id = os.path.expanduser(proxy["identity_file"])  # expand '~'

        # Build the exact command substring that proxy_connect() used:
        #   ssh -D {proxy_port} -i {proxy_id} -q -C -f -N {proxy_host}
        pattern = f"ssh -D {proxy_port} -i {proxy_id} -q -C -f -N {proxy_host}"

        # Search for any process whose command line contains the command pattern
        search_cmd = ["pgrep", "-af", pattern]
        proc = subprocess.run(search_cmd, capture_output=True, text=True, check=False)

        # If returncode == 0, pgrep found at least one matching process
        if proc.returncode == 0:
            connected.append(proxy["name"])

    if connected:
        # Verbose output.
        if getattr(args, "verbose", False):
            # Build the verbose command string
            verbose_cmd = (
                'ps aux | head -n 1 ; '
                'ps aux | grep -P "ssh.-D.\\d.*" ; '
                'echo "---" ; '
                'ss -tlnp | head -n 1 ; '
                'ss -tlnp | grep ssh'
            )
            print("Running verbose status command:")
            subprocess.run(verbose_cmd, shell=True, check=False)
            return

        print("Currently connected proxies:")
        for proxy in connected:
            print(f"- {proxy['name']} ({proxy['host']}:{proxy['port']})")
    else:
        print("No proxies appear to be connected.")


def proxy_connect(args):
    """
    Establish an SSH SOCKS connection to the specified proxy name.
    Command syntax:
        ssh -D {proxy_port} -i {proxy_identity} -q -C -f -N {proxy_host}
    """

    proxy_name = args.proxy_name

    # Validate the proxy is found in the yaml config
    found_proxy = _proxy_search(proxy_name)
    if not found_proxy:
        print(f"Error: Proxy '{proxy_name}' not found in {CONFIG_FILE}.")
        return

    proxy_host = found_proxy["host"]
    proxy_port = found_proxy["port"]
    proxy_id = found_proxy["identity_file"]

    # Validate yaml config for the proxy
    if not proxy_host or not proxy_port or not proxy_id:
        print(f"Error: Incomplete config for '{proxy_name}'. Check host, port, and identity_file.")
        return

    # Expand '~' in the identity file path, if needed
    proxy_id = os.path.expanduser(proxy_id)

    # Build the SSH command as a list (one arg per item)
    connect_cmd = [
        "ssh",
        "-D", str(proxy_port),
        "-i", proxy_id,
        "-q",
        "-C",
        "-f",
        "-N",
        proxy_host
    ]

    print(f"Establishing SOCKS proxy with: {proxy_name} ({proxy_host}:{proxy_port})")
    print(f"SSH command: {" ".join(connect_cmd)}")

    # Run the SSH command to connect to the proxy
    try:
        subprocess.run(connect_cmd, check=True)
        print(f"Connection established to {proxy_host} on SOCKS port {proxy_port}.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to connect to '{proxy_name}' ({proxy_host}:{proxy_port}).\n{e}")


def proxy_disconnect(args):
    """
    Disconnect (kill) the SSH SOCKS proxy process for the specified proxy name.
    If 'proxy_name' is 'all', disconnect all active proxies.
    """

    proxy_name = args.proxy_name

    # For "all", loop through each defined proxy & kill any active sessions
    if proxy_name == "all":
        proxies = parse_proxy_config()

        # Set any_disconnected to False
        any_disconnected = False

        print("Disconnecting from all configured proxies.")
        # Attempt to disconnect from all configured proxies, set
        # any_disconnected to True
        for proxy in proxies:
            if _disconnect_single_proxy(proxy):
                any_disconnected = True

        # If any_disconnected still False, print message
        if not any_disconnected:
            print("No active proxies were found to disconnect.")

        return

    # For individual, disconnect a single named proxy
    found_proxy = _proxy_search(proxy_name)
    if not found_proxy:
        print(f"Error: Proxy '{proxy_name}' not found in {CONFIG_FILE}.")
        return

    _disconnect_single_proxy(found_proxy)


def _disconnect_single_proxy(proxy_dict):
    """
    Helper function to kill one proxy process if it's active.
    Returns True if a process was found & killed, False otherwise.
    """

    proxy_name = proxy_dict["name"]
    proxy_host = proxy_dict["host"]
    proxy_port = proxy_dict["port"]
    proxy_id   = os.path.expanduser(proxy_dict["identity_file"])  # expand '~'

    # Build the exact ssh command pattern used in proxy_connect()
    ssh_cmd_pattern = f"ssh -D {proxy_port} -N {proxy_host} -q -C -f -i {proxy_id}"

    # Use 'pkill -f "pattern"' to find & kill processes matching that substring
    pkill_cmd = ["pkill", "-f", ssh_cmd_pattern]

    # print(f"Attempting to disconnect '{proxy_name}' with pkill on: {ssh_cmd_pattern}")
    try:
        subprocess.run(pkill_cmd, check=True)
        print(f"Disconnected proxy: {proxy_name} ({proxy_host}:{proxy_port})")
        return True
    except subprocess.CalledProcessError:
        # print(f"No active process found for '{proxy_name}'.")
        return False


def main():
    """
    Main function to handle logic based on parsed arguments.
    """

    parser = argparse.ArgumentParser(description="Manage SOCKS proxies from a YAML config.")
    subparsers = parser.add_subparsers(help="Available subcommands")

    # Subcommand: status
    status_parser = subparsers.add_parser(
        "status", help="List any connected proxies", aliases=["s"]
    )
    status_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose status output"
    )
    status_parser.set_defaults(func=proxy_status)

    # Subcommand: list
    list_parser = subparsers.add_parser("list", help="List all proxies", aliases=["l"])
    list_parser.set_defaults(func=proxy_list)

    # Subcommand: info
    info_parser = subparsers.add_parser(
        "info", help="Show details for a single proxy", aliases=["i"]
    )
    info_parser.add_argument("proxy_name", help="Name of the proxy to show info for")
    info_parser.set_defaults(func=proxy_info)

    # Subcommand: connect
    connect_parser = subparsers.add_parser(
        "connect", help="Connect to a proxy via SSH SOCKS", aliases=["c"]
    )
    connect_parser.add_argument("proxy_name", help="Name of the proxy to connect to")
    connect_parser.set_defaults(func=proxy_connect)

    # Subcommand: disconnect
    disconnect_parser = subparsers.add_parser(
        "disconnect", help="Disconnect (kill) the SOCKS proxy process", aliases=["d"]
    )
    disconnect_parser.add_argument(
        "proxy_name", help="Name of the proxy to disconnect, or 'all' to kill every active proxy"
    )
    disconnect_parser.set_defaults(func=proxy_disconnect)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":

    # Check python version.
    if sys.version_info < (3, 12):
        sys.exit("This script requires Python 3.12 or higher.")

    main()
