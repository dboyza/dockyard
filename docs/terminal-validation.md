# Terminal compatibility validation

Candidate: Dockyard 0.3.0, verified on 2026-09-27.
This record covers terminal integration changes, not a rerun of every curriculum lab.
The [platform validation record](platform-validation.md) retains the broader Docker, Kubernetes, and VM evidence.

## Observed execution

| Environment | Observed result |
| --- | --- |
| macOS 26.6.2 ARM64 | Terminal and WezTerm launched real child processes with a TTY, the intended workspace, and literal arguments preserved |
| Ubuntu 24.04 x86-64 in Docker, emulated on ARM64 | kitty, Alacritty, GNOME Terminal, GNOME Console, Konsole, Xfce Terminal, Tilix, MATE Terminal, and xterm passed real launches under Xvfb and a session D-Bus |
| Installed macOS browser and CLI | Copied the browser's lab command through the clipboard, executed it in a real PTY, and verified the prepared workspace, TTY, and activity environment |
| Installed browser layout | Lesson controls and timed-exam controls fit desktop and 480-pixel widths; the exam controls passed automated accessibility checks in dark and light themes |

The launch probes used a workspace containing spaces and a literal dollar sign.
Their command argument contained spaces, quotes, a dollar sign, and a semicolon.
A child process recorded the received argument, current directory, and `isatty(0)` result rather than relying on window visibility or command construction alone.
The Linux graphical checks used Ubuntu distribution packages and a virtual display; they do not establish compatibility with every desktop session or terminal version.

The GNOME check initially failed because the minimal container had a non-UTF-8 locale.
Rerunning with `LANG=C.UTF-8` and `LC_ALL=C.UTF-8` passed.
MATE's default shared-process mode returned a nonzero status after executing its child in this environment.
Its adapter now uses a standalone process through `--disable-factory` and the documented `-x` command boundary.
The corrected MATE launcher passed the same real TTY, workspace, and literal-argument probe in a separate disposable container.

## Automated checks

- 122 backend tests passed, with runtime integration tests excluded from that run.
- Backend Ruff and mypy passed.
- Frontend lint, formatting, TypeScript, and four unit tests passed.
- Three installed browser journeys passed: real lab lifecycle and copy-command execution, cancellation/recovery, and workbench accessibility.
- A separate timed-exam presentation fixture passed desktop/narrow layout and accessibility checks in both themes.
- The source installer built and installed the 0.3.0 wheel and passed the structural curriculum audit.

Terminal-specific tests cover allowlisted application selection, remembered preference, unavailable applications, headless discovery, exact argument boundaries, WSL distribution targeting, private launcher permissions, symlink preservation, early process failures, and macOS Automation denial.
The browser headless-discovery and exam-layout cases use explicit presentation fixtures.
The copied command and ordinary lab lifecycle use the installed app and real lab resources.

## Remaining platform evidence

Windows GUI launches were not executed on this macOS host.
Windows Terminal, Windows Alacritty, and the Windows terminal bridge therefore have argument-contract coverage, not a new Windows desktop end-to-end result.
iTerm2, macOS Ghostty, Linux Ghostty, foot, and system terminal dispatchers were not launched here.
macOS kitty and Alacritty were not separately exercised; their Linux launchers were.
The existing-terminal workflow avoids needing a dedicated launcher adapter for editor terminals, multiplexers, or other terminal applications.
The direct installed PTY result verifies that workflow without claiming separate end-to-end runs of every editor and multiplexer.

Next platform verification should exercise Windows Terminal in WSL 2, including a non-default distribution and profile paths containing spaces.
