# Terminal compatibility

Use Dockyard with your preferred terminal on a supported host.
The terminal displays the real lab shell; Docker, Kubernetes, editors, and command-line tools run normally.
Terminal choice does not change lessons, assessment, or lab ownership.

## Open a new session

Prepare a lab, choose **Terminal application**, and select **Open terminal**.
Dockyard remembers your successful selection in the current profile.
**Automatic** prefers a recognized terminal running the backend, then the first available platform option.
Detection happens on the backend computer, so a browser on another computer cannot open its own local terminal for that lab.

| Host | Detected automatic launchers |
| --- | --- |
| macOS | Terminal, iTerm2, Ghostty, WezTerm, kitty, Alacritty |
| Linux desktop | System default through `xdg-terminal-exec`, WezTerm, Ghostty, kitty, Alacritty, GNOME Terminal, GNOME Console, Konsole, Xfce Terminal, Tilix, MATE Terminal, foot, xterm, system `x-terminal-emulator` |
| Windows through WSL 2 | Windows Terminal, Windows WezTerm, Windows Alacritty; Linux desktop terminals when a graphical session is available |

Linux launchers must be installed and discoverable on `PATH`, with a working graphical session.
macOS detects standard application bundles as well as command-line launchers.
Ghostty on macOS requires version 1.3 or newer for its AppleScript interface.
iTerm2 and Ghostty may require macOS Automation permission on first use.
Dockyard does not change terminal preferences, default applications, or global shell configuration.

Windows launchers use `wsl.exe` to enter the exact distribution running Dockyard.
Keep Windows interoperability enabled and the chosen application's executable available to WSL.
Windows Terminal treats semicolons as command separators, so Dockyard directs profiles with semicolons in their paths to the copy-command workflow.
Native Windows PowerShell and Command Prompt are not lab shells; open a WSL session first.

## Use an existing session

Expand **Use an existing terminal**, then select **Copy lab command**.
Paste the command into a shell on the computer running Dockyard.
It includes the installed Python executable, profile, and activity, so it works outside the repository directory.
It opens the prepared workspace with the lab's tool paths and environment.
Run `exit` to return to the original shell.

This works in integrated editor terminals such as VS Code, other terminal applications such as Warp, Hyper, and Tabby, and terminal multiplexers such as tmux and GNU Screen.
It also works over SSH into the backend computer.
On Windows, paste it inside the correct WSL distribution.
The copied command uses POSIX shell quoting; paste it into Bash, Zsh, or a compatible shell rather than PowerShell.
Dockyard runs the lab itself in Zsh on macOS or Bash on Linux/WSL.

When no graphical terminal is detected, the copyable command appears directly.
If clipboard access is unavailable, select the displayed command and copy it manually.
If a desktop launcher fails, the same command remains available.
These sessions have your ordinary user privileges, just like a terminal opened yourself.

## Verification boundaries

The terminal adapters have automated coverage for argument boundaries, unusual paths, discovery, selection, launch errors, and authenticated API behavior.
Real terminal launches are checked separately from those contracts.
The [terminal validation record](terminal-validation.md) lists the environments exercised for this change.
An implemented launcher is not a claim that every version of that application has been tested.

Adapter references: [Windows Terminal](https://learn.microsoft.com/en-us/windows/terminal/command-line-arguments), [iTerm2 scripting](https://iterm2.com/documentation-scripting.html), [Ghostty scripting](https://ghostty.org/docs/features/applescript), [kitty invocation](https://sw.kovidgoyal.net/kitty/invocation/), and [Konsole options](https://docs.kde.org/trunk_kf6/en/konsole/konsole/command-line-options.html).
