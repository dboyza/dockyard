# Platform setup

Dockyard uses one browser workbench and one Linux-container curriculum across platforms.
The backend runs on Apple Silicon macOS or ARM64/x86-64 Linux.
On Windows, run the backend inside WSL 2 and use your Windows browser and preferred terminal.
Native Windows Python and Windows containers are outside this implementation.

| Platform | Lesson backend and shell | Application labs | Advanced native-node labs |
| --- | --- | --- | --- |
| Apple Silicon macOS | macOS, Zsh | Docker Desktop and kind | Lima Virtualization.framework guests |
| Linux ARM64 or x86-64 | Linux, Bash | Local Docker Engine and kind | Lima QEMU guests with accessible KVM |
| Windows with WSL 2 | Selected Linux distribution, Bash | Docker Desktop WSL integration or a local Linux Docker Engine | Requires nested virtualization, QEMU, and accessible KVM inside the distribution |

The [platform validation record](platform-validation.md) distinguishes implemented support from the systems actually exercised.
Intel macOS, WSL 1, remote Docker daemons, and cross-processor VM emulation are not supported.

## Common prerequisites

Use a supported, current Docker Engine with API 1.49 or newer, including a matching Docker CLI, Buildx/BuildKit, and Docker Compose v2.
Dockyard uses platform-specific image inspection and save operations.
Verify `docker info`, `docker buildx version`, `docker compose version`, and `docker version` in the same host environment that runs Dockyard.
The daemon must be reachable through a local Unix socket.
Use your preferred terminal: the browser detects supported desktop applications and also provides a copyable lab command.
See [terminal compatibility](terminals.md) for automatic launch support, editor terminals, and headless sessions.
Install Git, curl, Bash, Node.js 22.12 or newer, npm, and uv before using the source installer.
The installer builds the web assets and installs Python dependencies into private project environments.
It downloads Python 3.14 through uv if necessary.

Dockyard requires at least 8 GiB of reported memory for ordinary Docker/kind practice, 10 GiB for two-node native labs, and 12 GiB for the larger native topologies.
A VM or WSL distribution reports slightly less memory than its configured allocation, so allocate additional headroom.
A 16 GiB or larger machine provides more practical headroom for the browser, editor, and cache.
Preparation checks available disk and memory, requiring at least 20 GiB free before native VM creation.
The complete image and package cache needs additional space.
Dockyard's 40 GiB cache figure is a reported soft budget, not a disk quota.

## macOS and Linux

Clone the repository into a local filesystem and run:

```sh
git clone https://github.com/dboyza/dockyard.git
cd dockyard
./scripts/install.sh
./dockyard doctor
./dockyard
```

Ubuntu 24.04 is the verified Linux baseline.
Native Linux labs also require GNU coreutils, including `stat` with creation-timestamp support.
On Linux, configure Docker access for your ordinary user using your distribution's Docker instructions.
Do not run Dockyard as root or with sudo.
For native labs, install `qemu-system-aarch64` on ARM64 or `qemu-system-x86_64` on x86-64, `qemu-img`, OpenSSH, and your distribution's matching UEFI firmware.
Package names vary by distribution; Ubuntu provides these through `qemu-system-arm` or `qemu-system-x86`, `qemu-utils`, `openssh-client`, and `qemu-efi-aarch64` or `ovmf`.
Enable virtualization in firmware and arrange read/write access to `/dev/kvm` for the ordinary user.
Lab Manager reports missing VM prerequisites separately so Docker and kind lessons remain usable.
Dockyard downloads pinned Lima binaries, guest agents, tools, images, and node packages privately.
It does not install host system packages or change group membership.

## Windows and WSL 2

Install WSL 2 and a Linux distribution, such as Ubuntu 24.04, following [Microsoft's WSL installation guide](https://learn.microsoft.com/windows/wsl/install).
Use `wsl --list --verbose` in PowerShell to confirm the distribution uses version 2.
Configure Docker Desktop's WSL integration for that distribution, following [Microsoft's Docker guidance](https://learn.microsoft.com/windows/dev-environment/docker/overview), or configure Docker Engine directly inside it.
Choose one Docker daemon for the distribution.
Use Windows Terminal or another terminal with a WSL session, and install Git, curl, Bash, uv, Node, and npm inside Linux.

Open the distribution's terminal and keep the checkout in its Linux filesystem:

```sh
mkdir -p ~/code
cd ~/code
git clone https://github.com/dboyza/dockyard.git
cd dockyard
./scripts/install.sh
./dockyard doctor
./dockyard
```

Avoid `/mnt/c` and other Windows drive mounts for the checkout, profiles, caches, and VM disks.
Linux permissions, file watching, Unix sockets, and disk identity matter to these labs.
This also follows [Microsoft's filesystem performance guidance](https://learn.microsoft.com/windows/wsl/filesystems).
The app opens the Windows browser through WSL interoperability when available.
If automatic browser opening is unavailable, copy the printed one-time local URL into your Windows browser.
Keep the server bound to loopback and use WSL's localhost forwarding; do not expose it on `0.0.0.0`.

The optional PowerShell launchers target a distribution explicitly without changing the system default:

```powershell
# Run these from a Windows-accessible copy of the repository.
# LinuxProjectPath points to the separate checkout inside WSL.
.\scripts\install-wsl.ps1 -Distribution Ubuntu -LinuxProjectPath '~/code/dockyard'
.\dockyard.ps1 -Distribution Ubuntu -LinuxProjectPath '~/code/dockyard'
.\dockyard.ps1 -Distribution Ubuntu -DockyardArguments @('doctor')
```

The launchers preserve argument boundaries and propagate the WSL process's exit code.
They do not install WSL, change execution policy, enable virtualization, or alter Docker settings.
The browser terminal picker detects supported Windows applications through WSL interoperability and enters the exact selected distribution through `wsl.exe`.
If interoperability or automatic discovery is unavailable, run the displayed lab shell command inside an existing WSL terminal.

Native kubeadm labs additionally require working nested virtualization and readable/writable `/dev/kvm` inside WSL.
Availability depends on the Windows version, processor, WSL kernel, and virtualization configuration.
See [Microsoft's WSL configuration reference](https://learn.microsoft.com/windows/wsl/wsl-config) and [Lima's VM provider documentation](https://lima-vm.io/docs/config/vmtype/).
Dockyard reports this prerequisite rather than silently attempting slow emulation.
Docker/kind lessons do not require these nested VM capabilities.
Run one active native or kind lab at a time across WSL distributions; the capacity registry coordinates profiles within one Linux distribution, not separate distributions or other computers.

## Profiles and portability

macOS preserves the existing `~/Library/Application Support/Dockyard` default.
Linux and WSL use `$XDG_DATA_HOME/dockyard`, falling back to `~/.local/share/dockyard` when XDG_DATA_HOME is unset or relative.
`DOCKYARD_DATA` and `--data-dir` override these defaults.
Use a short profile path for native labs because Lima's Unix socket paths are length-limited.
On filesystems without creation timestamps, VM ownership checks fail conservatively rather than substituting change time.
Use a local ext4 filesystem in Linux or WSL for VM profiles.

Use progress export/import to move learning evidence between machines.
Do not copy active lab databases, VM disks, kubeconfigs, or architecture-specific tool caches to another system and expect ownership to transfer.
Each machine prepares its own resources and native images.
The same source exercises and saved learning history remain portable.
