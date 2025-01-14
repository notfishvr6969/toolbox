
# Toolbox CLI

> [!NOTE]
> All of our free software is designed to respect your privacy, while being as simple to use as possible. Our free software is licensed under the [BSD-3-Clause license](https://ravendevteam.org/files/BSD-3-Clause.txt). By using our software, you acknowledge and agree to the terms of the license.

Package manager for Raven software.

Made for Windows 10/11 and MacOS.
## Installation
Toolbox can install itself onto your system. To do this, just run `toolbox.exe install toolbox` on Windows, and `./toolbox install toolbox` on MacOS.

To update:
- For Windows, run `toolbox.exe update` in Command Prompt.
- For MacOS or Linux, run `./toolbox update` in your terminal.Sure, here's a FAQ section for your GitHub README based on the information provided:

---

## Frequently Asked Questions (FAQ)

### What is Toolbox Package Manager?
Toolbox Package Manager is a command-line tool designed for managing software packages provided by Raven. It facilitates installation, uninstallation, updating, and listing of available packages.

### How do I use Toolbox Package Manager?

To use Toolbox Package Manager, follow this syntax:

```
toolbox.exe [-h] [-y] [{list,install,uninstall,update,help,json}] [package]
```

#### Positional Arguments:
- `{list,install,uninstall,update,help,json}`: Specifies the command to execute.
- `package`: Name of the package (required for install and uninstall operations).

#### Options:
- `-h, --help`: Displays the help message.
- `-y, --yes`: Skips confirmation prompts.

### How can I list available packages?

You can list available packages by running:
```
toolbox.exe list
```

### How do I install a package?

To install a package, use the command:
```
toolbox.exe install <package>
```
Replace `<package>` with the name of the package you want to install.

### How do I uninstall a package?

To uninstall a package, use the command:
```
toolbox.exe uninstall <package>
```
Replace `<package>` with the name of the package you want to uninstall.

### How do i update packages?

```
toolbox.exe update
```

### Is Toolbox Package Manager cross-platform?

Yes, Toolbox Package Manager supported by Windows and macOS operating systems.

## Authors & Contributors

- [Raven Development Team](https://ravendevteam.org/)
- [Icons by Icons8](https://icons8.com/)
- [notfishvr6969](https://github.com/notfishvr6969)
