import os
import sys
import json
import urllib.request
import hashlib
from pathlib import Path
import shutil
import zipfile
from datetime import datetime
import warnings
import platform
from tqdm import tqdm
from tqdm.std import TqdmWarning
from colorama import Fore, Style
import argparse

warnings.filterwarnings("ignore", category=TqdmWarning)

def get_package_file_path():
    if platform.system() == "Windows":
        return Path(os.getenv('APPDATA')) / "ravendevteam" / "toolbox" / "packages.json"
    else:
        return Path.home() / "Library" / "Application Support" / "ravendevteam" / "toolbox" / "packages.json"

def get_installation_path(package_name):
    if platform.system() == "Windows":
        return Path(os.getenv('APPDATA')) / "ravendevteam" / package_name
    else:
        return Path.home() / "Library" / "Application Support" / "ravendevteam" / package_name

def handle_error(message):
    print(Fore.RED + f"Error: {message}" + Style.RESET_ALL)
    sys.exit(1)

def handle_warning(message):
    print(Fore.YELLOW + f"Warning: {message}" + Style.RESET_ALL)

def get_record_file_path():
    if platform.system() == "Windows":
        return Path(os.getenv('APPDATA')) / "ravendevteam" / "record.json"
    else:
        return Path.home() / "Library" / "Application Support" / "ravendevteam" / "record.json"

def read_record():
    record_file = get_record_file_path()
    if not record_file.exists():
        return {}
    try:
        with open(record_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_record(record):
    record_file = get_record_file_path()
    record_file.parent.mkdir(parents=True, exist_ok=True)
    with open(record_file, 'w') as f:
        json.dump(record, f, indent=4)

def uninstall_package(package_name, skip_confirmation):
    try:
        install_path = get_installation_path(package_name)
        if not install_path.exists():
            handle_error(f"Package '{package_name}' is not installed.")
        if not skip_confirmation:
            confirmation = input(f"Are you sure you want to uninstall '{package_name}'? (Y/N): ").strip().lower()
            if confirmation != 'y':
                print(Fore.WHITE + f"Uninstallation of '{package_name}' cancelled." + Style.RESET_ALL)
                return
        shutil.rmtree(install_path)
        print(Fore.GREEN + f"'{package_name}' has been successfully uninstalled." + Style.RESET_ALL)
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
        update_url = data.get('updateurl', default_update_url)
    except (FileNotFoundError, json.JSONDecodeError):
        update_url = default_update_url
        print(Fore.WHITE + f"Using default update URL: {default_update_url}" + Style.RESET_ALL)
    print(Fore.WHITE + "Updating package list from server..." + Style.RESET_ALL)
    try:
        urllib.request.urlretrieve(update_url, get_package_file_path())
        print(Fore.GREEN + "Update successful!" + Style.RESET_ALL)
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
    try:
        if platform.system() == "Windows":
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
    except Exception:
        handle_warning(f"Could not create a shortcut for '{shortcut_name}'. This will not affect the installation.")

def install_package(package_name, skip_confirmation):
    try:
        with open(get_package_file_path(), 'r') as f:
            data = json.load(f)
        packages = data.get("packages", [])
        if package_name == '*':
            for package in packages:
                install_package(package['name'], skip_confirmation)
            return
        package = next((pkg for pkg in packages if pkg["name"].lower() == package_name.lower()), None)
        if not package:
            handle_error(f"Package '{package_name}' not found in the package list.")
        platform_name = platform.system()
        if platform_name not in package["os"]:
            handle_error(f"'{package_name}' is not available for your platform ({platform_name}).")
        url = package["url"][platform_name]
        sha256 = package["sha256"][platform_name]
        if not skip_confirmation:
            confirmation = input(f"Are you sure you want to install '{package_name}'? (Y/N): ").strip().lower()
            if confirmation != 'y':
                print(Fore.WHITE + f"Installation of '{package_name}' cancelled." + Style.RESET_ALL)
                return
        print(Fore.WHITE + f"Installing {package_name} (v{package['version']}) for {platform_name}..." + Style.RESET_ALL)
        install_path = get_installation_path(package_name)
        install_path.mkdir(parents=True, exist_ok=True)
        download_path = install_path / f"{package_name}.{url.split('.')[-1]}"
        with tqdm(total=100, desc="Downloading", unit='%', bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            urllib.request.urlretrieve(url, download_path, reporthook=lambda count, block_size, total_size: pbar.update(block_size / total_size * 100))
        print(Fore.WHITE + f"Downloaded {package_name} to {download_path}" + Style.RESET_ALL)
        if not validate_checksum(download_path, sha256):
            handle_error(f"Checksum mismatch for {package_name}. Installation aborted.")
        if install_path.exists():
            print(Fore.GREEN + f"{package_name} installed successfully!" + Style.RESET_ALL)
            if package['shortcut']:
                target = next(install_path.glob('*'), None)
                if target:
                    create_shortcut(str(target), package_name)
            record = read_record()
            record[package_name] = {
                "version": package["version"],
                "installed_on": datetime.now().isoformat()
            }
            write_record(record)
    except FileNotFoundError:
        handle_error("Package list not found. Try updating the package list using 'update'.")
    except Exception as e:
        handle_error(f"An error occurred during installation: {str(e)}.")

def main():
    parser = argparse.ArgumentParser(description="Toolbox Package Manager")
    parser.add_argument("command", choices=["list", "install", "uninstall", "update", "help", "json"], help="Command to execute", nargs="?")
    parser.add_argument("package", nargs="?", help="Package name (required for install and uninstall)")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompts")
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    if args.command == "list":
        list_packages()
    elif args.command == "install":
        if not args.package:
            handle_error("You must specify the package name to install.")
        install_package(args.package, args.yes)
    elif args.command == "uninstall":
        if not args.package:
            handle_error("You must specify the package name to uninstall.")
        uninstall_package(args.package, args.yes)
    elif args.command == "update":
        update_packages()
    elif args.command == "help":
        parser.print_help()
    elif args.command == "json":
        print(get_package_file_path())


if __name__ == "__main__":
    main()