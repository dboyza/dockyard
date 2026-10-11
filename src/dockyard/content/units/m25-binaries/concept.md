## Trust the bytes, not the name

Before a new kubelet or kubeadm goes onto a node, you need to know it is exactly the program the Kubernetes project released.
A binary can be altered anywhere along the way: on a compromised download mirror, in a shared folder, or by someone with access to a build machine.
An altered binary can still run normally and print the right version, so trying it tells you nothing.

The Kubernetes project publishes a **checksum** for every binary it releases.
A checksum, also called a hash, is a long number calculated from every byte of a file by a function such as SHA-512.
Changing even one byte gives a completely different checksum, and it is not practical to craft a different file with the same SHA-512 checksum.
If the checksum you calculate matches the published one, the file is the released file.

```figure
binary-verification
```

## Where the official checksums come from

The project serves each checksum next to its binary, for example `https://dl.k8s.io/release/v1.37.1/bin/linux/arm64/kubelet.sha512`.
Fetch checksums from the official source, never from the same folder as the binary you are checking: whoever could alter the binary could alter a checksum stored beside it.
This lab has no internet requirement, so Dockyard copied the official values into your workspace's `release-checksums` folder, one file per binary, each holding a single SHA-512 value.

```sh
ls release-checksums
cat release-checksums/kubelet.sha512
```

## Calculating and comparing

`sha512sum FILE` prints a file's SHA-512 checksum followed by its name.
Comparing 128 hexadecimal characters by eye is error-prone, so let `sha512sum -c` do it: it reads lines of the form `CHECKSUM  FILE`, with two spaces, calculates each file's checksum, and prints `OK` or `FAILED`.

The staged binaries are on the control-plane node and the checksums are in your workspace, so build the line on your computer and send it to the node:

```sh
echo "$(cat release-checksums/kubeadm.sha512)  /opt/dockyard/staged/kubeadm" | limactl shell "$DOCKYARD_CONTROL_PLANE" sha512sum -c -
```

The final `-` tells `sha512sum` to read the check line from standard input, which `limactl shell` passes through from your terminal.
A match prints `/opt/dockyard/staged/kubeadm: OK`.
A mismatch prints `FAILED` and a warning, and the command exits with an error.

```figure
checksum-check
```

The same idea protects other downloads.
Container images are identified by a **digest**, the checksum of their content, which is why deployments pinned by digest cannot silently change.

## The situation in this lab

A teammate staged three binaries for the next maintenance window in `/opt/dockyard/staged` on the control-plane node: `kubeadm`, `kubelet`, and `kubectl`.
Nobody has verified them.

## Fix it

1. Check each staged binary against its official checksum with `sha512sum -c`.
2. Delete every staged binary that fails with `sudo rm` on the control-plane node.
3. Keep the ones that match; they are needed for the maintenance window.

Do not change the installed binaries in `/usr/bin`; the cluster is running on them.

## If something goes wrong

- **`sha512sum` says the line is improperly formatted**: the checksum and the path must be separated by exactly two spaces.
- **Every file fails**: check you are comparing a binary with its own checksum file, for example `kubectl` with `kubectl.sha512`.
- **You deleted a binary that matched**: restore it with `sudo cp /usr/bin/NAME /opt/dockyard/staged/NAME` on the control-plane node; the installed copies are the genuine release.
