import os
import sys
import json
import urllib.request
import hashlib
from pathlib import Path
import subprocess
from tqdm import tqdm
import shutil
import zipfile
from datetime import datetime

def get_package_file_path():
    if sys.platform == "win32":
        return Path(os.getenv('APPDATA')) / "ravendevteam" / "toolbox" / "packages.json"
    else:
        return Path.home() / "Library" / "Application Support" / "ravendevteam" / "toolbox" / "packages.json"

def get_installation_path(package_name):
    if sys.platform == "win32":
        return Path(os.getenv('APPDATA')) / "ravendevteam" / package_name
    else:
        return Path.home() / "Library" / "Application Support" / "ravendevteam" / package_name

def handle_error(message):
    print(f"Error: {message}")
    sys.exit(1)

def get_record_file_path():
    """
    Get the path to the record.json file that tracks installed packages.
    """
    if sys.platform == "win32":
        return Path(os.getenv('APPDATA')) / "ravendevteam" / "record.json"
    else:
        return Path.home() / "Library" / "Application Support" / "ravendevteam" / "record.json"

def read_record():
    """
    Read the record.json file and return its contents as a dictionary.
    """
    record_file = get_record_file_path()
    if not record_file.exists():
        return {}
    try:
        with open(record_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_record(record):
    """
    Write the provided dictionary to the record.json file.
    """
    record_file = get_record_file_path()
    record_file.parent.mkdir(parents=True, exist_ok=True)
    with open(record_file, 'w') as f:
        json.dump(record, f, indent=4)

def uninstall_package(package_name):
    try:
        install_path = get_installation_path(package_name)

        if not install_path.exists():
            handle_error(f"Package '{package_name}' is not installed.")

        confirmation = input(f"Are you sure you want to uninstall '{package_name}'? (Y/N): ").strip().lower()
        if confirmation != 'y':
            print(f"Uninstallation of '{package_name}' cancelled.")
            return

        shutil.rmtree(install_path)
        print(f"'{package_name}' has been successfully uninstalled.")

        record = read_record()
        if package_name in record:
            del record[package_name]
            write_record(record)

    except Exception as e:
        handle_error(f"An error occurred while uninstalling '{package_name}': {str(e)}. Please try again.")

def update_packages():
    default_update_url = "https://raw.githubusercontent.com/ravendevteam/toolbox/refs/heads/main/packages.json"

    try:
        with open(get_package_file_path(), 'r') as f:
            data = json.load(f)
        update_url = data.get('updateurl', None)

    except (FileNotFoundError, json.JSONDecodeError):
        update_url = None

    if not update_url:
        update_url = default_update_url
        print(f"Warning: No update URL found or the package list is missing. Using default update URL: {default_update_url}")
        print("Please note that the above error is normal upon first time updating.")

    print("Updating package list from server...")

    try:
        urllib.request.urlretrieve(update_url, get_package_file_path())
        print("Update successful!")
    except urllib.error.HTTPError as e:
        handle_error(f"HTTP Error: {e.code} - {e.reason}. Please check the update URL or try again later.")
    except urllib.error.URLError as e:
        handle_error(f"URL Error: {str(e)}. Please check your internet connection or try again later.")
    except Exception as e:
        handle_error(f"Failed to update packages: {str(e)}. Please try again or check your settings.")

def list_packages():
    try:
        with open(get_package_file_path(), 'r') as f:
            data = json.load(f)
        
        print("Available Packages:\n")
        for package in data.get("packages", []):
            print(f"Name: {package['name']}")
            print(f"Version: {package['version']}")
            print(f"Description: {package['description']}")
            print(f"Available for: {', '.join(package['os'])}")
            print(f"Requires Path: {'Yes' if package['requirepath'] else 'No'}")
            print(f"Creates Shortcut: {'Yes' if package['shortcut'] else 'No'}")
            print("-" * 40)
    except FileNotFoundError:
        handle_error("Package list not found. Try updating the package list using 'update'.")
    except json.JSONDecodeError:
        handle_error("Failed to read package list (corrupted or invalid JSON).")

def validate_checksum(file_path, expected_hash):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_hash

def create_shortcut(target, shortcut_name):
    if sys.platform == "win32":
        from win32com.client import Dispatch
        shell = Dispatch('WScript.Shell')
        desktop = shell.SpecialFolders('Desktop')
        shortcut = shell.CreateShortCut(os.path.join(desktop, f"{shortcut_name}.lnk"))
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.IconLocation = target
        shortcut.save()
    else:
        os.symlink(target, Path.home() / "Desktop" / f"{shortcut_name}.app")

def install_package(package_name):
    try:
        with open(get_package_file_path(), 'r') as f:
            data = json.load(f)
        
        package = next((pkg for pkg in data.get("packages", []) if pkg["name"].lower() == package_name.lower()), None)
        
        if not package:
            handle_error(f"Package '{package_name}' not found in the package list.")

        platform = "Windows" if sys.platform == "win32" else "macOS"
        
        if platform not in package["os"]:
            handle_error(f"'{package_name}' is not available for your platform ({platform}).")

        url = package["url"][platform]
        sha256 = package["sha256"][platform]

        print(f"Installing {package_name} (v{package['version']}) for {platform}...")

        install_path = get_installation_path(package_name)
        install_path.mkdir(parents=True, exist_ok=True)

        download_path = install_path / f"{package_name}.{url.split('.')[-1]}"
        
        with tqdm(total=100, desc="Downloading", unit='%', bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            urllib.request.urlretrieve(url, download_path, reporthook=lambda count, block_size, total_size: pbar.update(block_size / total_size * 100))

        print(f"Downloaded {package_name} to {download_path}")

        if not validate_checksum(download_path, sha256):
            handle_error(f"Checksum mismatch for {package_name}. Installation aborted.")

        if sys.platform == "darwin" and download_path.suffix == '.zip':
            print("Extracting the package...")
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(install_path)
            print(f"Extracted {package_name} to {install_path}")

            download_path.unlink()
            print(f"Removed the ZIP file {download_path}")

        if install_path.exists():
            print(f"{package_name} installed successfully!")

            if package['shortcut']:
                target = next(install_path.glob('*'), None)
                if target:
                    create_shortcut(str(target), package_name)
                    print(f"A shortcut for {package_name} has been created on your desktop.")
                else:
                    print(f"Warning: Couldn't find the main executable for {package_name} to create a shortcut.")
            
            record = read_record()
            record[package_name] = {
                "version": package["version"],
                "installed_on": datetime.now().isoformat()
            }
            write_record(record)
        else:
            handle_error(f"Installation path does not exist after extraction. Installation failed.")

    except FileNotFoundError:
        handle_error("Package list not found. Try updating the package list using 'update'.")
    except Exception as e:
        handle_error(f"An error occurred during installation: {str(e)}.")

def display_help():
    print("Toolbox Package Manager")
    print("Version: 2.0.0")
    print("Usage: toolbox.py <command> <package>")
    print("Possible commands:")
    print("  list         - List available packages")
    print("  install      - Install a specified package")
    print("  uninstall    - Uninstall a specified package")
    print("  update       - Update the package list from the server")
    print("  json         - Print the path to the packages.json file")
    print("License: https://ravendevteam.org/files/BSD-3-Clause.txt")

def print_json_path():
    print(f"{get_package_file_path()}")

def main():
    package_file_path = get_package_file_path()

    if not package_file_path.exists():
        print("Package list not found.")
        print("It looks like you need to update the package list.")
        print("Attempting to download the latest packages.json...")
        update_packages()
        if not package_file_path.exists():
            handle_error("Failed to download the package list.")

    if len(sys.argv) < 2:
        display_help()
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "list":
        list_packages()
    elif command == "install":
        if len(sys.argv) < 3:
            handle_error("You must specify the package name to install.")
        install_package(sys.argv[2])
    elif command == "uninstall":
        if len(sys.argv) < 3:
            handle_error("You must specify the package name to uninstall.")
        uninstall_package(sys.argv[2])
    elif command == "update":
        update_packages()
    elif command == "help":
        display_help()
    elif command == "json":
        print_json_path()
    else:
        handle_error(f"Unknown command: {command}.")

if __name__ == "__main__":
    main()