# Terminal compatibility

Each lab's shell opens in the browser, beside the lesson.
It is a real shell on this computer, so Docker, Kubernetes, editors, and command-line tools run normally.
You can also open the same lab shell in your own terminal.
Terminal choice does not change lessons, assessment, or lab ownership.

## The built-in terminal

Prepare a lab, and the lesson moves left while a shell opens on the right.
The shell starts in the lab's workspace, with the lab's Docker endpoint, kubeconfig, and tool paths.
Its prompt shows the activity, the current folder, the Git branch, and the last command's exit code.
The terminal uses the bundled JetBrains Mono Nerd Font, so prompt icons work without installing anything.

Shells keep running on the backend when you change pages or reload the browser.
When you return, each shell reconnects and replays its recent output.
Stopping Dockyard closes every built-in shell, as closing a terminal window would.
Reset, Independent retake, and cleanup close that lab's shells, because its old workspace moves to a backup.
A fresh shell then opens in the restored workspace.

| Action | How |
| --- | --- |
| Open another shell | Select **+** beside the tabs, up to six per lab |
| Close a shell | Select its **×**, or press Delete on a focused tab |
| Find text | Cmd+F on macOS, Ctrl+Shift+F elsewhere |
| Copy and paste | Cmd+C and Cmd+V on macOS, Ctrl+Shift+C and Ctrl+Shift+V elsewhere |
| Clear the scrollback | Cmd+K on macOS, or the terminal menu |
| Move between lesson and terminal | Ctrl+` |
| Resize | Drag the divider, or focus it and use the arrow keys |

Links such as `http://127.0.0.1:8080` open in a new browser tab.
The terminal menu changes text size, stops, resumes, or resets the lab, and shows the workspace folder.
The browser connects to the shell through the same one-time sign-in as the rest of the workbench.

## Open your own terminal

Open the terminal menu, expand **Use your own terminal**, choose **Terminal application**, and select **Open terminal**.
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

In the same **Use your own terminal** section, expand **Use an existing terminal**, then select **Copy lab command**.
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

The built-in terminal has automated real-PTY coverage for size, input, exit codes, hang-up, scrollback replay, and origin and session checks.
An installed browser journey types into it and confirms the command ran in the lab workspace with the lab's settings.
The terminal adapters have automated coverage for argument boundaries, unusual paths, discovery, selection, launch errors, and authenticated API behavior.
Real terminal launches are checked separately from those contracts.
The [terminal validation record](terminal-validation.md) lists the environments exercised for this change.
An implemented launcher is not a claim that every version of that application has been tested.

Adapter references: [Windows Terminal](https://learn.microsoft.com/en-us/windows/terminal/command-line-arguments), [iTerm2 scripting](https://iterm2.com/documentation-scripting.html), [Ghostty scripting](https://ghostty.org/docs/features/applescript), [kitty invocation](https://sw.kovidgoyal.net/kitty/invocation/), and [Konsole options](https://docs.kde.org/trunk_kf6/en/konsole/konsole/command-line-options.html).
