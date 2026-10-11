import {
  Arrow,
  Box,
  Code,
  Diagram,
  File,
  Label,
  Region,
  Reveal,
  Tag,
  Terminal,
} from "./kit";
import type { Drawings } from "./registry";

// Figures for the CKS security phase.
export const security = {
  "cis-benchmark": ({ step = 0 }) => {
    const findings: [string, string, string][] = [
      ["4.2.1", "kubelet anonymous auth", "worker"],
      ["4.2.2", "kubelet authorization mode", "worker"],
      ["1.2.15", "API server profiling", "control plane"],
    ];
    return (
      <Diagram height={304} step={step}>
        <Region x={10} y={30} w={250} h={110} label="Control-plane node" />
        <Box
          x={26}
          y={62}
          w={218}
          h={58}
          title="kube-apiserver"
          sub={step === 0 ? "--profiling (default on)" : "--profiling=false"}
          tone={step === 0 ? "bad" : "good"}
        />
        <Region x={10} y={160} w={250} h={110} label="Worker node" />
        <Box
          x={26}
          y={192}
          w={218}
          h={58}
          title="kubelet config.yaml"
          sub={
            step === 0
              ? "anonymous: on · AlwaysAllow"
              : "anonymous: off · Webhook"
          }
          tone={step === 0 ? "bad" : "good"}
        />
        <Arrow
          points={[
            [264, 150],
            [330, 150],
          ]}
          label="kube-bench"
          labelAt={[297, 138]}
        />
        <Region x={340} y={30} w={290} h={240} label="CIS checks" />
        {findings.map(([id, text, node], index) => (
          <g key={id}>
            <Tag
              x={356}
              y={70 + index * 66}
              anchor="start"
              text={step === 0 ? `${id} FAIL` : `${id} PASS`}
              tone={step === 0 ? "bad" : "good"}
            />
            <Label x={356} y={98 + index * 66} size="small">
              {text}
            </Label>
            <Label
              x={614}
              y={98 + index * 66}
              anchor="end"
              size="small"
              tone="muted"
            >
              {node}
            </Label>
          </g>
        ))}
        <Reveal from={1}>
          <Label x={320} y={292} anchor="middle" size="small" tone="muted">
            restart the kubelet; the edited manifest restarts the API server
          </Label>
        </Reveal>
      </Diagram>
    );
  },
  "node-endpoints": () => (
    <Diagram height={280}>
      <Region x={10} y={30} w={620} h={220} label="One node" />
      <Box
        x={30}
        y={110}
        w={170}
        h={62}
        title="Pod"
        sub="untrusted-client"
        tone="focus"
      />
      <Box
        x={400}
        y={56}
        w={210}
        h={62}
        title="Metadata service"
        sub="169.254.169.254 · credentials"
        tone="bad"
      />
      <Box
        x={400}
        y={164}
        w={210}
        h={62}
        title="kubelet API"
        sub="node address :10250"
        tone="bad"
      />
      <Arrow
        points={[
          [204, 130],
          [300, 130],
          [300, 87],
          [396, 87],
        ]}
        tone="bad"
        label="borrow the node's identity"
        labelAt={[300, 74]}
      />
      <Arrow
        points={[
          [204, 152],
          [300, 152],
          [300, 195],
          [396, 195],
        ]}
        tone="bad"
        label="probe or attack the node"
        labelAt={[300, 216]}
      />
      <Label x={115} y={198} anchor="middle" size="small" tone="muted">
        default: no policy, any destination
      </Label>
    </Diagram>
  ),
  "egress-allowlist": ({ step = 0 }) => {
    const targets: [string, string, boolean][] = [
      ["CoreDNS", "kube-system · port 53", true],
      ["Dispatch API", "dispatch · port 8080", true],
      ["Metadata service", "169.254.169.254:80", false],
      ["kubelet API", "node addresses :10250", false],
    ];
    return (
      <Diagram height={300} step={step}>
        <Region x={10} y={30} w={210} h={240} label="frontend namespace" />
        <Box x={26} y={70} w={178} h={56} title="trusted-client" tone="focus" />
        <Box
          x={26}
          y={150}
          w={178}
          h={56}
          title="untrusted-client"
          tone="focus"
        />
        <Label x={115} y={236} anchor="middle" size="small" tone="muted">
          {step === 0
            ? "egress: - {}  (allow all)"
            : "egress: DNS + Dispatch only"}
        </Label>
        {targets
          .map((target, index) => [target, index] as const)
          .sort(
            ([a], [b]) =>
              Number(step === 0 || a[2]) - Number(step === 0 || b[2]),
          )
          .map(([[title, sub, needed], index]) => {
            const allowed = step === 0 || needed;
            const y = 34 + index * 62;
            return (
              <g key={title}>
                <Arrow
                  points={[
                    [224, 150],
                    [330, 150],
                    [330, y + 26],
                    [404, y + 26],
                  ]}
                  tone={allowed ? (needed ? "good" : "bad") : "muted"}
                  dashed={!allowed}
                />
                <Box
                  x={408}
                  y={y}
                  w={222}
                  h={52}
                  title={(allowed ? "✓ " : "✗ ") + title}
                  sub={sub}
                  tone={allowed ? (needed ? "good" : "bad") : "muted"}
                />
              </g>
            );
          })}
      </Diagram>
    );
  },
  "binary-verification": ({ step = 0 }) => {
    const rows: [string, boolean][] = [
      ["kubeadm", true],
      ["kubelet", true],
      ["kubectl", false],
    ];
    return (
      <Diagram height={280} step={step}>
        <Region x={10} y={30} w={200} h={220} label="Official release" />
        <Box
          x={26}
          y={110}
          w={168}
          h={60}
          title="*.sha512"
          sub="dl.k8s.io checksums"
          tone="focus"
        />
        <Region x={430} y={30} w={200} h={220} label="/opt/dockyard/staged" />
        {rows
          .map((row, index) => [row, index] as const)
          .sort(([a], [b]) => Number(a[1]) - Number(b[1]))
          .map(([[name, genuine], index]) => {
            const y = 60 + index * 64;
            const removed = step === 1 && !genuine;
            return (
              <g key={name}>
                <Box
                  x={446}
                  y={y}
                  w={168}
                  h={48}
                  title={removed ? "deleted" : name}
                  sub={step === 0 ? "unverified" : genuine ? "OK" : "FAILED"}
                  tone={step === 0 ? "default" : genuine ? "good" : "bad"}
                  dashed={removed}
                />
                <Arrow
                  points={[
                    [198, 140],
                    [320, 140],
                    [320, y + 24],
                    [442, y + 24],
                  ]}
                  tone={step === 0 ? "muted" : genuine ? "good" : "bad"}
                />
              </g>
            );
          })}
        <Label x={320} y={268} anchor="middle" size="small" tone="muted">
          sha512sum -c compares every byte, not the version string
        </Label>
      </Diagram>
    );
  },
  "anonymous-requests": ({ step = 0 }) => (
    <Diagram height={300} step={step}>
      <Box
        x={10}
        y={50}
        w={150}
        h={62}
        title="curl"
        sub="no certificate, no token"
      />
      <Arrow
        points={[
          [164, 81],
          [206, 81],
        ]}
      />
      <Box
        x={210}
        y={50}
        w={200}
        h={62}
        title="Authentication"
        sub={
          step === 0 ? "→ system:anonymous" : "anonymous only for health paths"
        }
        tone="focus"
      />
      <Reveal from={0} until={0}>
        <Arrow
          points={[
            [414, 81],
            [456, 81],
          ]}
        />
        <Box x={460} y={50} w={170} h={62} title="Authorization" sub="RBAC" />
        <Box
          x={410}
          y={156}
          w={220}
          h={62}
          title="public-status binding"
          sub="system:unauthenticated → read"
          tone="bad"
        />
        <Arrow
          points={[
            [545, 152],
            [545, 116],
          ]}
          tone="bad"
        />
        <Label x={320} y={260} anchor="middle" size="small" tone="bad">
          200 OK: ConfigMaps returned to anyone
        </Label>
      </Reveal>
      <Reveal from={1}>
        <Arrow
          points={[
            [310, 116],
            [310, 166],
          ]}
          tone="bad"
        />
        <Box
          x={210}
          y={170}
          w={200}
          h={52}
          title="401 Unauthorized"
          sub="/api/... and /version"
          tone="bad"
        />
        <Arrow
          points={[
            [414, 81],
            [456, 81],
          ]}
          tone="good"
        />
        <Box
          x={460}
          y={50}
          w={170}
          h={62}
          title="200 OK"
          sub="/livez /readyz /healthz"
          tone="good"
        />
        <Label x={320} y={260} anchor="middle" size="small" tone="muted">
          rejected before RBAC is consulted
        </Label>
      </Reveal>
    </Diagram>
  ),
  "static-pod-mounts": () => (
    <Diagram height={250}>
      <Region x={10} y={30} w={620} h={200} label="Control-plane node" />
      <Box
        x={26}
        y={80}
        w={250}
        h={62}
        title="File on the node"
        sub="/etc/kubernetes/auth-config.yaml"
        tone="focus"
      />
      <Region
        x={340}
        y={56}
        w={274}
        h={154}
        label="kube-apiserver container"
        tone="focus"
      />
      <Box x={356} y={86} w={242} h={48} title="volumeMount, same path" />
      <Box
        x={356}
        y={148}
        w={242}
        h={48}
        title="--authentication-config=…"
        mono
      />
      <Arrow
        points={[
          [280, 111],
          [352, 111],
        ]}
        tone="focus"
      />
      <Label x={151} y={176} anchor="middle" size="small" tone="muted">
        hostPath volume carries it in
      </Label>
    </Diagram>
  ),
  "service-account-tokens": ({ step = 0 }) => (
    <Diagram height={300} step={step}>
      <Region x={10} y={30} w={620} h={240} label="reports namespace" />
      <Box
        x={30}
        y={70}
        w={180}
        h={58}
        title="report-builder Pod"
        sub={step === 0 ? "as default" : "as report-builder"}
        tone="focus"
      />
      <Box
        x={30}
        y={170}
        w={180}
        h={58}
        title="report-viewer Pod"
        sub={step === 0 ? "token mounted" : "no token"}
        tone={step === 0 ? "bad" : "good"}
      />
      <Box
        x={420}
        y={70}
        w={190}
        h={58}
        title={step === 0 ? "default account" : "report-builder account"}
        sub={step === 0 ? "bound to edit" : "get one ConfigMap"}
        tone={step === 0 ? "bad" : "good"}
      />
      <Arrow
        points={[
          [214, 99],
          [416, 99],
        ]}
        label="bound token, renewed"
        labelAt={[315, 88]}
      />
      <Reveal from={0} until={0}>
        <Arrow
          points={[
            [214, 199],
            [320, 199],
            [320, 112],
            [416, 112],
          ]}
          tone="bad"
        />
        <Box
          x={420}
          y={176}
          w={190}
          h={52}
          title="default-token-legacy"
          sub="Secret · never expires"
          tone="bad"
        />
      </Reveal>
      <Reveal from={1}>
        <Box
          x={420}
          y={176}
          w={190}
          h={52}
          title="legacy token deleted"
          sub="revoked"
          tone="muted"
          dashed
        />
      </Reveal>
    </Diagram>
  ),
  "least-privilege-identity": ({ step = 0 }) => {
    const permissions: [string, boolean][] = [
      ["get configmap/report-settings", true],
      ["read other ConfigMaps", false],
      ["list Secrets", false],
      ["create Pods", false],
    ];
    return (
      <Diagram height={290} step={step}>
        <Box
          x={10}
          y={110}
          w={226}
          h={62}
          title={
            step === 0 ? "ClusterRole edit" : "Role report-settings-reader"
          }
          sub={
            step === 0 ? "almost everything" : "resourceNames: report-settings"
          }
          tone={step === 0 ? "bad" : "good"}
        />
        {permissions
          .map((permission, index) => [permission, index] as const)
          .sort(
            ([a], [b]) =>
              Number(step === 0 || a[1]) - Number(step === 0 || b[1]),
          )
          .map(([[text, needed], index]) => {
            const granted = step === 0 || needed;
            const y = 40 + index * 58;
            return (
              <g key={text}>
                <Arrow
                  points={[
                    [240, 141],
                    [316, 141],
                    [316, y + 22],
                    [366, y + 22],
                  ]}
                  tone={granted ? (needed ? "good" : "bad") : "muted"}
                  dashed={!granted}
                />
                <Box
                  x={370}
                  y={y}
                  w={266}
                  h={44}
                  title={(granted ? "yes · " : "no · ") + text}
                  tone={granted ? (needed ? "good" : "bad") : "muted"}
                />
              </g>
            );
          })}
        <Label x={320} y={282} anchor="middle" size="small" tone="muted">
          kubectl auth can-i … --as=system:serviceaccount:reports:report-builder
        </Label>
      </Diagram>
    );
  },
  "rbac-audit": () => (
    <Diagram height={290}>
      <Label x={90} y={24} anchor="middle" size="small" tone="muted">
        Subjects
      </Label>
      <Label x={320} y={24} anchor="middle" size="small" tone="muted">
        ClusterRoleBindings
      </Label>
      <Label x={540} y={24} anchor="middle" size="small" tone="muted">
        ClusterRoles
      </Label>
      <Box
        x={10}
        y={50}
        w={160}
        h={58}
        title="ci/deployer"
        sub="ServiceAccount"
        tone="focus"
      />
      <Box
        x={10}
        y={160}
        w={160}
        h={58}
        title="dispatch-operators"
        sub="Group"
        tone="focus"
      />
      <Box x={224} y={50} w={192} h={58} title="ci-deployer-admin" />
      <Box x={224} y={160} w={192} h={58} title="dispatch-operators-all" />
      <Box
        x={460}
        y={50}
        w={170}
        h={58}
        title="cluster-admin"
        sub="everything"
        tone="bad"
      />
      <Box
        x={460}
        y={160}
        w={170}
        h={58}
        title="dispatch-ops"
        sub="* on * in *"
        tone="bad"
      />
      {[79, 189].map((y) => (
        <g key={y}>
          <Arrow
            points={[
              [174, y],
              [226, y],
            ]}
          />
          <Arrow
            points={[
              [414, y],
              [456, y],
            ]}
            tone="bad"
          />
        </g>
      ))}
      <Label x={320} y={262} anchor="middle" size="small" tone="muted">
        kubectl get clusterrolebindings -o wide · kubectl auth can-i --list
        --as=…
      </Label>
    </Diagram>
  ),
  "host-footprint": ({ step = 0 }) => {
    const needed = ["kubelet", "containerd", "calico-node", "ssh"];
    return (
      <Diagram height={290} step={step}>
        <Region x={10} y={30} w={620} h={230} label="Worker node" />
        <Label x={40} y={78} size="small" tone="muted">
          What the node needs
        </Label>
        {needed.map((name, index) => (
          <Box
            key={name}
            x={30 + (index % 2) * 150}
            y={92 + Math.floor(index / 2) * 70}
            w={136}
            h={52}
            title={name}
            tone="good"
          />
        ))}
        <Label x={360} y={78} size="small" tone="muted">
          Extra attack surface
        </Label>
        <Box
          x={350}
          y={92}
          w={260}
          h={52}
          title={step === 0 ? "report-share" : "report-share: masked"}
          sub={step === 0 ? "0.0.0.0:8081, serves files" : "port closed"}
          tone={step === 0 ? "bad" : "muted"}
          dashed={step === 1}
        />
        <Box
          x={350}
          y={162}
          w={260}
          h={52}
          title={step === 0 ? "backup account" : "backup: retired"}
          sub={step === 0 ? "passwordless sudo" : "nologin, no sudo"}
          tone={step === 0 ? "bad" : "muted"}
          dashed={step === 1}
        />
      </Diagram>
    );
  },
  "listening-ports": () => (
    <Diagram height={250}>
      <Terminal
        x={10}
        y={20}
        w={620}
        title="Worker node"
        lines={[
          "$ sudo ss -ltnp",
          "State   Local Address:Port   Process",
          "LISTEN  127.0.0.1:10248      kubelet",
          "LISTEN  *:10250              kubelet",
          "LISTEN  0.0.0.0:22           sshd",
          "LISTEN  0.0.0.0:8081         python3  ← report-share",
        ]}
      />
      <Label x={20} y={196} size="small" tone="muted">
        127.0.0.1 accepts connections only from the node itself;
      </Label>
      <Label x={20} y={216} size="small" tone="muted">
        0.0.0.0 and * accept them from anywhere that can reach the node.
      </Label>
    </Diagram>
  ),
  "apparmor-profile": () => (
    <Diagram height={290}>
      <Box
        x={10}
        y={110}
        w={150}
        h={62}
        title="processor"
        sub="root, in a container"
        tone="focus"
      />
      <Label x={180} y={100} anchor="middle" size="small" tone="muted">
        every access
      </Label>
      <Arrow
        points={[
          [164, 141],
          [196, 141],
        ]}
      />
      <Box
        x={200}
        y={100}
        w={170}
        h={82}
        title="Kernel: AppArmor"
        sub="profile dockyard-processor"
      />
      {(
        [
          ["read /usr/lib/…", "allowed", true, 40],
          ["write /data/results/7.txt", "allowed", true, 110],
          ["write /etc/passwd", "Permission denied", false, 180],
        ] as const
      ).map(([action, outcome, allowed, y]) => (
        <g key={action}>
          <Arrow
            points={[
              [374, 141],
              [390, 141],
              [390, y + 24],
              [406, y + 24],
            ]}
            tone={allowed ? "good" : "bad"}
          />
          <Box
            x={410}
            y={y}
            w={220}
            h={48}
            title={action}
            sub={outcome}
            tone={allowed ? "good" : "bad"}
          />
        </g>
      ))}
      <Label x={320} y={270} anchor="middle" size="small" tone="muted">
        enforce mode refuses what the profile does not allow, even for root
      </Label>
    </Diagram>
  ),

  "apparmor-loading": () => (
    <Diagram height={300}>
      <File x={66} y={40} name="dockyard-processor" />
      <Label x={82} y={118} anchor="middle" size="small" tone="muted">
        your workspace
      </Label>
      {(
        [
          ["Control-plane node", 30, true],
          ["Worker node", 160, true],
        ] as const
      ).map(([title, y]) => (
        <g key={title}>
          <Arrow
            points={[
              [124, 70],
              [160, 70],
              [160, y + 50],
              [196, y + 50],
            ]}
            label={y === 30 ? "tee + apparmor_parser" : undefined}
            labelAt={[170, 22]}
          />
          <Region x={200} y={y} w={430} h={110} label={title} />
          <Box
            x={216}
            y={y + 30}
            w={190}
            h={60}
            title="/etc/apparmor.d"
            sub="loaded at boot"
            mono
          />
          <Box
            x={420}
            y={y + 30}
            w={194}
            h={60}
            title="kernel: enforce"
            sub="dockyard-processor"
            tone="good"
          />
        </g>
      ))}
      <Label x={415} y={292} anchor="middle" size="small" tone="muted">
        a Pod naming the profile can start on either node
      </Label>
    </Diagram>
  ),
  "seccomp-filter": () => (
    <Diagram height={280}>
      <Box
        x={10}
        y={110}
        w={160}
        h={62}
        title="processor"
        sub="system calls"
        tone="focus"
      />
      <Box
        x={220}
        y={96}
        w={170}
        h={90}
        title="seccomp filter"
        sub="defaultAction: ALLOW"
      />
      <Arrow
        points={[
          [174, 141],
          [216, 141],
        ]}
      />
      {(
        [
          ["openat, write, read", "allowed", true, 40],
          ["connect, futex, …", "allowed", true, 110],
          ["chmod, fchmodat", "EPERM", false, 180],
        ] as const
      ).map(([calls, outcome, allowed, y]) => (
        <g key={calls}>
          <Arrow
            points={[
              [394, 141],
              [420, 141],
              [420, y + 24],
              [446, y + 24],
            ]}
            tone={allowed ? "good" : "bad"}
          />
          <Box
            x={450}
            y={y}
            w={180}
            h={48}
            title={calls}
            sub={outcome}
            tone={allowed ? "good" : "bad"}
            mono
          />
        </g>
      ))}
      <Label x={320} y={266} anchor="middle" size="small" tone="muted">
        the kernel checks every call before running it
      </Label>
    </Diagram>
  ),
  "seccomp-profile-types": () => (
    <Diagram height={260}>
      {(
        [
          ["Unconfined", "no filter · Seccomp: 0", "bad"],
          ["RuntimeDefault", "runtime's built-in profile", "good"],
          ["Localhost", "your file on the node", "good"],
        ] as const
      ).map(([type, sub, tone], index) => (
        <Box
          key={type}
          x={10 + index * 210}
          y={40}
          w={196}
          h={62}
          title={type}
          sub={sub}
          tone={tone}
        />
      ))}
      <Arrow
        points={[
          [528, 106],
          [528, 146],
        ]}
      />
      <Box
        x={330}
        y={150}
        w={300}
        h={62}
        title="/var/lib/kubelet/seccomp/"
        sub="+ localhostProfile: profiles/no-chmod.json"
        mono
      />
      <Label x={110} y={150} anchor="middle" size="small" tone="muted">
        a Pod with no seccompProfile
      </Label>
      <Label x={110} y={170} anchor="middle" size="small" tone="muted">
        runs Unconfined
      </Label>
    </Diagram>
  ),
  "encryption-at-rest": ({ step = 0 }) => (
    <Diagram height={260} step={step}>
      <Box
        x={10}
        y={90}
        w={150}
        h={62}
        title="kubectl / Pod"
        sub="reads the Secret"
      />
      <Arrow
        points={[
          [164, 121],
          [216, 121],
        ]}
        both
      />
      <Box
        x={220}
        y={80}
        w={190}
        h={82}
        title="API server"
        sub={step === 0 ? "no encryption" : "aescbc, key1"}
        tone={step === 0 ? "default" : "good"}
      />
      <Arrow
        points={[
          [414, 121],
          [466, 121],
        ]}
        both
      />
      <Box
        x={470}
        y={80}
        w={160}
        h={82}
        title="etcd"
        sub={step === 0 ? "k8s\\0…password…" : "k8s:enc:aescbc:v1:key1:…"}
        tone={step === 0 ? "bad" : "good"}
        mono
      />
      <Label x={540} y={192} anchor="middle" size="small" tone="muted">
        {step === 0 ? "backups hold plain data too" : "backups hold ciphertext"}
      </Label>
      <Label x={85} y={192} anchor="middle" size="small" tone="muted">
        sees the value either way
      </Label>
    </Diagram>
  ),
  "reencrypt-secrets": ({ step = 0 }) => {
    const secrets = [
      "dispatch-database",
      "bootstrap tokens in kube-system",
      "any other Secret from before",
    ];
    return (
      <Diagram height={250} step={step}>
        <Region x={10} y={30} w={300} h={190} label="etcd" />
        {secrets.map((name, index) => (
          <Box
            key={name}
            x={26}
            y={56 + index * 52}
            w={268}
            h={42}
            title={name}
            sub={step === 0 ? "plain (written before)" : "k8s:enc:aescbc"}
            tone={step === 0 ? "bad" : "good"}
          />
        ))}
        <Box
          x={380}
          y={92}
          w={250}
          h={70}
          title="kubectl replace"
          sub="get every Secret, write it back unchanged"
          tone="focus"
        />
        <Arrow
          points={[
            [376, 127],
            [314, 127],
          ]}
          tone="focus"
        />
      </Diagram>
    );
  },
  "wireguard-tunnel": ({ step = 0 }) => (
    <Diagram height={270} step={step}>
      <Region x={10} y={30} w={200} h={170} label="Control-plane node" />
      <Box
        x={26}
        y={80}
        w={168}
        h={60}
        title="trusted-client"
        sub="frontend Pod"
        tone="focus"
      />
      <Region x={430} y={30} w={200} h={170} label="Worker node" />
      <Box
        x={446}
        y={80}
        w={168}
        h={60}
        title="dispatch"
        sub="API Pod"
        tone="focus"
      />
      <Arrow
        points={[
          [198, 110],
          [442, 110],
        ]}
        tone={step === 0 ? "bad" : "good"}
        both
      />
      <Box
        x={240}
        y={130}
        w={160}
        h={56}
        title={step === 0 ? "VXLAN" : "wireguard.cali"}
        sub={step === 0 ? "POST /jobs readable" : "encrypted"}
        tone={step === 0 ? "bad" : "good"}
      />
      <Label x={320} y={236} anchor="middle" size="small" tone="muted">
        {step === 0
          ? "encapsulated, not encrypted: anyone on the node network can read it"
          : "each node encrypts with the other's public key"}
      </Label>
    </Diagram>
  ),
  "wireguard-check": () => (
    <Diagram height={260}>
      <Terminal
        x={10}
        y={10}
        w={620}
        lines={[
          "$ kubectl get nodes -o custom-columns=NAME:…,WIREGUARD:…",
          "lima-…-cp1      Ua3x…= (public key)",
          "lima-…-worker   8bQe…= (public key)",
          '$ limactl shell "$DOCKYARD_WORKER" ip -s link show wireguard.cali',
          "wireguard.cali: <POINTOPOINT,NOARP,UP> mtu 1370",
          "    RX: bytes 48210   TX: bytes 51388   ← grows with cross-node traffic",
        ]}
      />
    </Diagram>
  ),
  "sandbox-kernel": ({ step = 0 }) => (
    <Diagram height={290} step={step}>
      <Box
        x={10}
        y={30}
        w={250}
        h={56}
        title="template-preview"
        sub="untrusted code"
        tone="focus"
      />
      <Arrow
        points={[
          [135, 90],
          [135, 126],
        ]}
        label="system calls"
        labelAt={[180, 112]}
      />
      <Reveal from={0} until={0}>
        <Box
          x={10}
          y={130}
          w={250}
          h={70}
          title="Node's Linux kernel"
          sub="answers every call directly"
          tone="bad"
        />
        <Label x={430} y={160} anchor="middle" size="small" tone="bad">
          a kernel bug reachable by one call
        </Label>
        <Label x={430} y={180} anchor="middle" size="small" tone="bad">
          can mean escaping to the node
        </Label>
      </Reveal>
      <Reveal from={1}>
        <Box
          x={10}
          y={130}
          w={250}
          h={56}
          title="gVisor Sentry"
          sub="a kernel in user space"
          tone="good"
        />
        <Arrow
          points={[
            [135, 190],
            [135, 216],
          ]}
          label="few, fixed calls"
          labelAt={[190, 206]}
        />
        <Box
          x={10}
          y={220}
          w={250}
          h={50}
          title="Node's Linux kernel"
          sub="much less exposed"
        />
        <Label x={430} y={160} anchor="middle" size="small" tone="muted">
          cost: slower system calls,
        </Label>
        <Label x={430} y={180} anchor="middle" size="small" tone="muted">
          some calls unsupported
        </Label>
      </Reveal>
    </Diagram>
  ),
  "runtimeclass-flow": () => (
    <Diagram height={280}>
      <Box
        x={10}
        y={40}
        w={180}
        h={62}
        title="Pod"
        sub="runtimeClassName: gvisor"
        tone="focus"
      />
      <Arrow
        points={[
          [194, 71],
          [236, 71],
        ]}
      />
      <Box
        x={240}
        y={30}
        w={180}
        h={82}
        title="RuntimeClass gvisor"
        sub="handler: runsc · nodeSelector"
      />
      <Arrow
        points={[
          [424, 71],
          [466, 71],
        ]}
        label="runs on"
        labelAt={[445, 60]}
      />
      <Region
        x={470}
        y={20}
        w={160}
        h={240}
        label="Labelled worker"
        tone="good"
      />
      <Box
        x={486}
        y={56}
        w={128}
        h={52}
        title="containerd"
        sub="handler runsc"
        mono
      />
      <Arrow
        points={[
          [550, 112],
          [550, 146],
        ]}
      />
      <Box x={486} y={150} w={128} h={52} title="gVisor sandbox" tone="good" />
      <Label x={215} y={176} anchor="middle" size="small" tone="muted">
        the selector keeps the Pod off nodes
      </Label>
      <Label x={215} y={196} anchor="middle" size="small" tone="muted">
        that have no runsc handler
      </Label>
    </Diagram>
  ),
  "audit-pipeline": () => (
    <Diagram height={280}>
      <Box
        x={10}
        y={50}
        w={160}
        h={62}
        title="Request"
        sub="get a Secret"
        tone="focus"
      />
      <Arrow
        points={[
          [174, 81],
          [216, 81],
        ]}
      />
      <Box
        x={220}
        y={40}
        w={180}
        h={82}
        title="API server"
        sub="audit policy"
      />
      <Region x={220} y={146} w={180} h={110} label="Rules, first match wins" />
      {["None: events", "Metadata: secrets", "Metadata: everything"].map(
        (rule, index) => (
          <Label key={rule} x={236} y={182 + index * 22} size="small" mono>
            {rule}
          </Label>
        ),
      )}
      <Arrow
        points={[
          [404, 81],
          [446, 81],
        ]}
        label="writes"
        labelAt={[425, 70]}
      />
      <Box
        x={450}
        y={40}
        w={180}
        h={82}
        title="audit.log"
        sub="user, verb, object, time"
        tone="good"
        mono
      />
    </Diagram>
  ),
  "audit-levels": () => {
    const levels: [string, string, string][] = [
      ["None", "nothing", "muted"],
      ["Metadata", "who, what, when, result", "good"],
      ["Request", "+ the body sent", "default"],
      ["RequestResponse", "+ the body returned", "bad"],
    ];
    return (
      <Diagram height={280}>
        {levels.map(([name, records, tone], index) => (
          <Box
            key={name}
            x={10}
            y={20 + index * 62}
            w={360}
            h={50}
            title={name}
            sub={records}
            tone={tone as "muted" | "good" | "default" | "bad"}
          />
        ))}
        <Label x={400} y={110} size="small" tone="good">
          Secrets: Metadata
        </Label>
        <Label x={400} y={232} size="small" tone="bad">
          for a Secret, the returned
        </Label>
        <Label x={400} y={252} size="small" tone="bad">
          body is the password
        </Label>
      </Diagram>
    );
  },
  "immutable-container": () => (
    <Diagram height={270}>
      <Region x={10} y={30} w={620} h={210} label="uploader container (root)" />
      <Box
        x={30}
        y={70}
        w={300}
        h={150}
        title="Image filesystem"
        sub="readOnlyRootFilesystem: true"
        tone="good"
      />
      <Label x={180} y={184} anchor="middle" size="small" mono>
        /usr /etc /bin /app
      </Label>
      <Label x={180} y={206} anchor="middle" size="small" tone="bad">
        writes fail: Read-only file system
      </Label>
      <Box
        x={370}
        y={70}
        w={240}
        h={60}
        title="/tmp"
        sub="emptyDir · writable"
        tone="focus"
      />
      <Box
        x={370}
        y={150}
        w={240}
        h={60}
        title="/var/cache/uploads"
        sub="emptyDir · writable"
        tone="focus"
      />
    </Diagram>
  ),
  "replica-fingerprints": () => (
    <Diagram height={260}>
      {(
        [
          ["uploader-…-4kx2p", "9f2c…", true],
          ["uploader-…-7hd9q", "e31a…", false],
          ["uploader-…-m8vtz", "9f2c…", true],
        ] as const
      ).map(([pod, print, same], index) => (
        <g key={pod}>
          <Box
            x={10}
            y={30 + index * 70}
            w={260}
            h={54}
            title={pod}
            sub="same image"
            mono
          />
          <Arrow
            points={[
              [274, 57 + index * 70],
              [356, 57 + index * 70],
            ]}
            label={index === 0 ? "fingerprint" : undefined}
            labelAt={[315, 44]}
          />
          <Box
            x={360}
            y={30 + index * 70}
            w={270}
            h={54}
            title={print}
            sub={same ? "matches the others" : "differs: files changed"}
            tone={same ? "good" : "bad"}
            mono
          />
        </g>
      ))}
    </Diagram>
  ),
  "falco-pipeline": () => (
    <Diagram height={260}>
      <Box
        x={10}
        y={60}
        w={130}
        h={62}
        title="Containers"
        sub="system calls"
        tone="focus"
      />
      <Arrow
        points={[
          [144, 91],
          [176, 91],
        ]}
      />
      <Box
        x={180}
        y={50}
        w={180}
        h={82}
        title="eBPF in the kernel"
        sub="sees every call"
      />
      <Arrow
        points={[
          [364, 91],
          [396, 91],
        ]}
      />
      <Box
        x={400}
        y={50}
        w={120}
        h={82}
        title="Falco"
        sub="+ Pod, namespace"
        tone="focus"
      />
      <Arrow
        points={[
          [524, 91],
          [546, 91],
        ]}
      />
      <Box
        x={550}
        y={50}
        w={80}
        h={82}
        title="Alert"
        sub="journal"
        tone="bad"
      />
      <Label x={320} y={180} anchor="middle" size="small" tone="muted">
        behavior, not signatures: a shell starting in a web server
      </Label>
      <Label x={320} y={200} anchor="middle" size="small" tone="muted">
        is suspicious whatever it runs
      </Label>
    </Diagram>
  ),

  "falco-rule": () => (
    <Diagram height={300}>
      <Code
        x={10}
        y={20}
        w={620}
        lines={[
          { text: "- rule: Shell in application container" },
          { text: "  condition: >" },
          { text: "    spawned_process and container", tone: "focus" },
          { text: "    and proc.name in (sh, bash, dash, ash)", tone: "focus" },
          {
            text: "    and k8s.ns.name in (billing, dispatch, frontend)",
            tone: "focus",
          },
          {
            text: "  output: Shell (namespace=%k8s.ns.name pod=%k8s.pod.name ...)",
            tone: "good",
          },
          { text: "  priority: WARNING" },
        ]}
      />
      <Label x={20} y={284} size="small" tone="muted">
        condition: which events match · output: what the alert says · priority:
        how urgent
      </Label>
    </Diagram>
  ),
  "static-analysis": () => (
    <Diagram height={270}>
      <File x={40} y={40} name="resizer.yaml" />
      <Arrow
        points={[
          [90, 74],
          [130, 74],
        ]}
      />
      <Box
        x={134}
        y={44}
        w={150}
        h={60}
        title="Rendered manifest"
        sub="render.py output"
        tone="focus"
      />
      {(
        [
          ["KubeLinter", "rules · exit code gate", 20],
          ["kubesec", "risk score · advice", 120],
        ] as const
      ).map(([tool, sub, y]) => (
        <g key={tool}>
          <Arrow
            points={[
              [288, 74],
              [320, 74],
              [320, y + 30],
              [352, y + 30],
            ]}
          />
          <Box x={356} y={y} w={160} h={60} title={tool} sub={sub} />
        </g>
      ))}
      <Arrow
        points={[
          [520, 100],
          [536, 100],
        ]}
      />
      <Box
        x={540}
        y={70}
        w={90}
        h={60}
        title="Fix"
        sub="then deploy"
        tone="good"
      />
      <Label x={320} y={236} anchor="middle" size="small" tone="muted">
        nothing runs: problems are found in the text before it reaches a cluster
      </Label>
    </Diagram>
  ),
  "risk-score": ({ step = 0 }) => {
    const items: [string, string, boolean][] = [
      ["privileged: true", "critical −30", false],
      ["runAsNonRoot, runAsUser, runAsGroup", "+3", true],
      ["readOnlyRootFilesystem", "+1", true],
      ["requests and limits", "+4", true],
      ["drop ALL capabilities", "+2", true],
      ["ServiceAccount, no token", "+4", true],
    ];
    return (
      <Diagram height={300} step={step}>
        {items.map(([setting, points, good], index) => {
          const present = step === 0 ? !good : good;
          return (
            <Box
              key={setting}
              x={10}
              y={20 + index * 42}
              w={380}
              h={34}
              title={`${setting} · ${points}`}
              tone={present ? (good ? "good" : "bad") : "muted"}
              dashed={!present}
            />
          );
        })}
        <Box
          x={430}
          y={100}
          w={200}
          h={80}
          title={step === 0 ? "score -30" : "score 14"}
          sub={step === 0 ? "1 critical finding" : "no critical findings"}
          tone={step === 0 ? "bad" : "good"}
        />
      </Diagram>
    );
  },
  "image-footprint": ({ step = 0 }) => {
    const extras: [string, string][] = [
      ["BusyBox", "sh, ash, and 300 commands"],
      ["Package managers", "apk, pip"],
    ];
    return (
      <Diagram height={290} step={step}>
        <Region x={10} y={30} w={620} h={230} label="Dispatch image" />
        <Box
          x={30}
          y={70}
          w={260}
          h={150}
          title="What Dispatch needs"
          sub="Python, its libraries, app.py"
          tone="good"
        />
        <Label x={160} y={200} anchor="middle" size="small" tone="muted">
          {step === 0 ? "runs as root" : "runs as user 10001"}
        </Label>
        {extras.map(([title, sub], index) => (
          <Box
            key={title}
            x={330}
            y={70 + index * 58}
            w={280}
            h={48}
            title={title}
            sub={step === 0 ? sub : "removed"}
            tone={step === 0 ? "bad" : "muted"}
            dashed={step === 1}
          />
        ))}
        <Box
          x={330}
          y={186}
          w={280}
          h={48}
          title="setuid files"
          sub={
            step === 0
              ? "none here; many images have some"
              : "bits cleared if any appear"
          }
          tone="muted"
          dashed
        />
      </Diagram>
    );
  },
  "exec-form": () => (
    <Diagram height={250}>
      <Box
        x={10}
        y={30}
        w={300}
        h={62}
        title="CMD python app.py"
        sub="shell form"
        tone="bad"
        mono
      />
      <Arrow
        points={[
          [160, 96],
          [160, 136],
        ]}
      />
      <Box
        x={10}
        y={140}
        w={300}
        h={62}
        title="/bin/sh -c 'python app.py'"
        sub="needs a shell in the image"
        tone="bad"
        mono
      />
      <Box
        x={340}
        y={30}
        w={290}
        h={62}
        title='CMD ["python", "app.py"]'
        sub="exec form"
        tone="good"
        mono
      />
      <Arrow
        points={[
          [485, 96],
          [485, 136],
        ]}
      />
      <Box
        x={340}
        y={140}
        w={290}
        h={62}
        title="python app.py"
        sub="started directly, no shell"
        tone="good"
        mono
      />
    </Diagram>
  ),
  "image-signing": () => (
    <Diagram height={290}>
      <Box
        x={10}
        y={40}
        w={170}
        h={62}
        title="Release team"
        sub="cosign.key (private)"
        tone="focus"
      />
      <Arrow
        points={[
          [184, 71],
          [236, 71],
        ]}
        label="sign the digest"
        labelAt={[210, 58]}
      />
      <Region x={240} y={20} w={220} h={180} label="Registry" />
      <Box
        x={256}
        y={50}
        w={188}
        h={52}
        title="dispatch@sha256:9f…"
        tone="good"
        mono
      />
      <Box
        x={256}
        y={120}
        w={188}
        h={52}
        title="signature"
        sub="stored beside it"
      />
      <Arrow
        points={[
          [464, 110],
          [506, 110],
        ]}
        label="verify"
        labelAt={[485, 98]}
      />
      <Box
        x={510}
        y={78}
        w={120}
        h={62}
        title="Anyone"
        sub="cosign.pub"
        tone="good"
      />
      <Label x={320} y={250} anchor="middle" size="small" tone="muted">
        a signature belongs to one digest; moving a tag does not move it
      </Label>
    </Diagram>
  ),
  "release-admission": () => {
    const cases: [string, string, boolean][] = [
      ["busybox:1.37", "other registry", false],
      ["REGISTRY/dispatch:1.0", "tag, not digest", false],
      ["REGISTRY/dispatch@sha256:…", "release, by digest", true],
    ];
    return (
      <Diagram height={270}>
        <Box
          x={290}
          y={96}
          w={130}
          h={70}
          title="Admission"
          sub="production"
          tone="focus"
        />
        {cases.map(([image, why, allowed], index) => {
          const y = 30 + index * 76;
          return (
            <g key={image}>
              <Box x={10} y={y} w={250} h={56} title={image} sub={why} />
              <Arrow
                points={[
                  [264, y + 28],
                  [276, y + 28],
                  [276, 131],
                  [286, 131],
                ]}
              />
              <Arrow
                points={[
                  [424, 131],
                  [442, 131],
                  [442, y + 28],
                  [456, y + 28],
                ]}
                tone={allowed ? "good" : "bad"}
              />
              <Box
                x={460}
                y={y}
                w={170}
                h={56}
                title={allowed ? "admitted" : "refused"}
                tone={allowed ? "good" : "bad"}
              />
            </g>
          );
        })}
      </Diagram>
    );
  },
  "kubelet-api-access": ({ step = 0 }) => {
    const rows: [string, string, string, string, string, boolean][] = [
      [
        "Any Pod",
        "no credentials",
        step === 0 ? "anonymous: on" : "anonymous: off",
        step === 0 ? "AlwaysAllow" : "not reached",
        step === 0 ? "exec, logs allowed" : "401 Unauthorized",
        step !== 0,
      ],
      [
        "API server",
        "client certificate",
        "certificate accepted",
        step === 0 ? "AlwaysAllow" : "Webhook: RBAC",
        "exec, logs allowed",
        true,
      ],
    ];
    return (
      <Diagram height={250} step={step}>
        <Label x={235} y={24} anchor="middle" size="small" tone="muted">
          Authentication
        </Label>
        <Label x={400} y={24} anchor="middle" size="small" tone="muted">
          Authorization
        </Label>
        {rows.map(([who, how, authn, authz, outcome, safe], index) => {
          const y = 40 + index * 100;
          return (
            <g key={who}>
              <Box
                x={10}
                y={y}
                w={140}
                h={58}
                title={who}
                sub={how}
                tone="focus"
              />
              <Box
                x={165}
                y={y}
                w={140}
                h={58}
                title={authn}
                tone={index === 0 && step === 0 ? "bad" : "good"}
              />
              <Box
                x={330}
                y={y}
                w={140}
                h={58}
                title={authz}
                tone={
                  authz === "not reached"
                    ? "muted"
                    : step === 0
                      ? "bad"
                      : "good"
                }
                dashed={authz === "not reached"}
              />
              <Box
                x={495}
                y={y}
                w={135}
                h={58}
                title={outcome}
                tone={safe ? "good" : "bad"}
              />
              <Arrow
                points={[
                  [154, y + 29],
                  [161, y + 29],
                ]}
              />
              <Arrow
                points={[
                  [309, y + 29],
                  [326, y + 29],
                ]}
              />
              <Arrow
                points={[
                  [474, y + 29],
                  [491, y + 29],
                ]}
              />
            </g>
          );
        })}
      </Diagram>
    );
  },

  "checksum-check": () => (
    <Diagram height={250}>
      <Terminal
        x={10}
        y={10}
        w={620}
        lines={[
          '$ echo "$(cat release-checksums/kubeadm.sha512)  /opt/dockyard/staged/kubeadm" \\',
          '    | limactl shell "$DOCKYARD_CONTROL_PLANE" sha512sum -c -',
          "/opt/dockyard/staged/kubeadm: OK",
          '$ echo "$(cat release-checksums/kubectl.sha512)  /opt/dockyard/staged/kubectl" \\',
          '    | limactl shell "$DOCKYARD_CONTROL_PLANE" sha512sum -c -',
          "/opt/dockyard/staged/kubectl: FAILED",
          "sha512sum: WARNING: 1 computed checksum did NOT match",
        ]}
      />
    </Diagram>
  ),
} satisfies Drawings;
