# Socksies

A Python script for managing SOCKS proxies via SSH. It reads configurations from a YAML file (`proxy-config.yml`) and provides commands to list, connect, disconnect, and show the status of those proxies.

## Requirements

- **Python 3.12 or higher**  
  Required to use argparse subcommand aliases (e.g., `list`/`l`, `connect`/`c`, etc.).

- **PyYAML**  
  For parsing the YAML configuration file. Install via:
  ```bash
  pip install pyyaml
  ```
  *(Or use `requirements.txt`, detailed below.)*

- **System Commands**  
  - `ssh` – for establishing SOCKS tunnels
  - `pkill` / `pgrep` – for disconnecting and checking proxy status
  - A Unix-like environment or equivalent tools on Windows (e.g., WSL) that provide these commands

### `requirements.txt`

If you prefer using a `requirements.txt` file for easy installation in a virtual environment or on other systems, you can include:

```
PyYAML>=5.4
```

Then install with:

```bash
pip install -r requirements.txt
```

## Usage

1. **Setup**  
   - Ensure you have Python 3.12+.
   - Install PyYAML (`pip install pyyaml`) or use `requirements.txt`.
   - Make sure `ssh`, `pkill`, and `pgrep` are on your system PATH.

2. **Configuration**  
   - Create or edit `proxy-config.yml` in the same directory as `socksies.py`.  
   - Each proxy is defined as a top-level key with `host`, `port`, and `identity_file` values, for example:
     ```yaml
     jump1:
       host: 172.31.0.51
       port: 9051
       identity_file: ~/.ssh/my_key

     jump2:
       host: 172.31.0.52
       port: 9052
       identity_file: ~/.ssh/my_other_key
     ```

3. **Running**  
   From the script’s directory, you can use:

   ```bash
   # Show help
   ./socksies.py --help

   # List proxies (alias: l)
   ./socksies.py list

   # Show details for one proxy (alias: i)
   ./socksies.py info jump1

   # Connect to a proxy (alias: c)
   ./socksies.py connect jump1

   # Disconnect one proxy or all (alias: d)
   ./socksies.py disconnect jump1
   ./socksies.py disconnect all

   # Show status of active connections (alias: s)
   ./socksies.py status
   ```

4. **Shebang Note**  
   - To ensure the script runs under Python 3.12, the top line can be:
     ```bash
     #!/usr/bin/env python3
     ```
   - Or you can simply invoke it with the correct interpreter:
     ```bash
     python3.12 socksies.py ...
     ```

### Running from Anywhere: Create a Symbolic Link

If you want to call the `socksies.py` script from any directory without modifying your PATH, you can create a symbolic link in a directory that is already on your system’s PATH (for example, `~/local/bin`).

1. **Ensure the Script is Executable**

   Make sure `socksies.py` has the executable permission:
   ```bash
   chmod +x /path/to/repo/socksies.py
   ```

2. **Create a Symlink**

   Create a symbolic link to the script by running:
   ```bash
   ln -s /path/to/repo/socksies.py .local/bin/socksies
   ```

3. **Run the Script**

   Now you can run the script from anywhere by simply typing:
   ```bash
   socksies [subcommand] [arguments]
   ```

   For example:
   ```bash
   socksies connect jump1
   ```

## License

Use freely or adapt as needed for your own environment. Please consult your organization’s policies on SSH usage and networking.
