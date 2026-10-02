import {
  Arrow,
  Box,
  Diagram,
  Label,
  Region,
  Tag,
  Terminal,
  type Tone,
} from "./kit";
import type { Drawings } from "./registry";

export const cluster = {
  "runtime-layers": () => (
    <Diagram height={318}>
      <Box x={10} y={14} w={150} h={46} title="kubectl" mono />
      <Arrow
        points={[
          [160, 37],
          [226, 37],
        ]}
      />
      <Box
        x={230}
        y={14}
        w={190}
        h={46}
        title="API server"
        sub="Kubernetes objects"
      />
      <Region x={210} y={78} w={420} h={226} label="One node" />
      <Box
        x={230}
        y={104}
        w={190}
        h={46}
        title="kubelet"
        sub="the node’s agent"
      />
      <Arrow
        points={[
          [325, 60],
          [325, 100],
        ]}
        tone="muted"
        label="Pods for this node"
        labelAt={[390, 84]}
      />
      <Arrow
        points={[
          [325, 150],
          [325, 176],
        ]}
        label="CRI"
        labelAt={[350, 166]}
      />
      <Box
        x={230}
        y={180}
        w={190}
        h={46}
        title="containerd"
        sub="/run/containerd/…sock"
        tone="focus"
      />
      <Arrow
        points={[
          [325, 226],
          [325, 244],
        ]}
      />
      <Box
        x={230}
        y={248}
        w={190}
        h={44}
        title="containers"
        sub="in kubepods.slice cgroups"
        tone="good"
      />
      <Box x={460} y={150} w={150} h={40} title="crictl" mono />
      <Arrow
        points={[
          [460, 170],
          [424, 170],
          [424, 186],
        ]}
        tone="focus"
        label="through the CRI"
        labelAt={[536, 208]}
      />
      <Box x={460} y={232} w={150} h={40} title="ctr" mono />
      <Arrow
        points={[
          [460, 252],
          [424, 210],
        ]}
        tone="muted"
        dashed
      />
      <Label x={535} y={290} anchor="middle" size="small" tone="muted">
        ctr: containerd directly
      </Label>
      <Label x={10} y={100} size="small" tone="muted">
        kubectl sees objects.
      </Label>
      <Label x={10} y={118} size="small" tone="muted">
        crictl sees what is
      </Label>
      <Label x={10} y={136} size="small" tone="muted">
        really running on
      </Label>
      <Label x={10} y={154} size="small" tone="muted">
        one node.
      </Label>
    </Diagram>
  ),

  "lab-vms": () => (
    <Diagram height={266}>
      <Region x={10} y={14} w={620} h={240} label="Your computer" />
      <Terminal
        x={26}
        y={44}
        w={200}
        title="Lab terminal"
        lines={["$ kubectl get nodes", "$ limactl shell …"]}
      />
      <Region
        x={270}
        y={40}
        w={170}
        h={196}
        label="control-plane VM"
        tone="focus"
      />
      <Box x={285} y={74} w={140} h={36} title="API server" />
      <Box x={285} y={118} w={140} h={36} title="etcd" />
      <Box x={285} y={162} w={140} h={36} title="kubelet" />
      <Region x={456} y={40} w={164} h={196} label="worker VM" tone="focus" />
      <Box x={470} y={74} w={136} h={36} title="Dispatch Pods" />
      <Box x={470} y={118} w={136} h={44} title="database" sub="local volume" />
      <Box x={470} y={170} w={136} h={36} title="kubelet" />
      <Arrow
        points={[
          [226, 70],
          [281, 90],
        ]}
        tone="focus"
      />
      <Arrow
        points={[
          [126, 118],
          [126, 222],
          [270, 222],
        ]}
        dashed
        tone="muted"
      />
      <Label x={140} y={150} size="small" tone="muted">
        limactl shell opens a
      </Label>
      <Label x={140} y={168} size="small" tone="muted">
        shell inside a VM
      </Label>
    </Diagram>
  ),

  "kubelet-stopped": ({ step = 0 }) => {
    const states: {
      kubelet: [string, Tone];
      app: [string, Tone];
      lease: [string, Tone];
      node: [string, Tone];
    }[] = [
      {
        kubelet: ["active (running)", "good"],
        app: ["containers running, answering", "good"],
        lease: ["renewed every few seconds", "good"],
        node: ["Ready", "good"],
      },
      {
        kubelet: ["stopped", "bad"],
        app: ["still running, still answering", "warn"],
        lease: ["no longer renewed", "warn"],
        node: ["still Ready: stale", "warn"],
      },
      {
        kubelet: ["stopped", "bad"],
        app: ["running, but nothing restarts them", "warn"],
        lease: ["expired", "bad"],
        node: ["NotReady", "bad"],
      },
    ];
    const current = states[step];
    const rows: [string, [string, Tone]][] = [
      ["kubelet service", current.kubelet],
      ["Dispatch’s containers", current.app],
      ["node Lease", current.lease],
      ["node status", current.node],
    ];
    return (
      <Diagram height={210} step={step}>
        {rows.map(([name, [text, tone]], index) => (
          <g key={name}>
            <Label x={20} y={44 + index * 44}>
              {name}
            </Label>
            <Tag x={430} y={40 + index * 44} text={text} tone={tone} />
          </g>
        ))}
      </Diagram>
    );
  },

  "kubectl-errors": () => {
    const stages: [string, string, string][] = [
      ["connect", "is anything listening?", "connection refused"],
      ["TLS", "do I trust the server?", "x509 certificate error"],
      ["authenticate", "who is this?", "401 Unauthorized"],
      ["authorize", "may they do it?", "403 Forbidden"],
    ];
    return (
      <Diagram height={210}>
        {stages.map(([title, sub, error], index) => (
          <g key={title}>
            <Box
              x={10 + index * 158}
              y={30}
              w={142}
              h={60}
              title={title}
              sub={sub}
              tone="focus"
            />
            {index > 0 && (
              <Arrow
                points={[
                  [index * 158 - 6, 60],
                  [index * 158 + 8, 60],
                ]}
              />
            )}
            <Arrow
              points={[
                [81 + index * 158, 90],
                [81 + index * 158, 122],
              ]}
              tone="bad"
            />
            <Label
              x={81 + index * 158}
              y={142}
              anchor="middle"
              size="small"
              tone="bad"
              mono
            >
              {error}
            </Label>
          </g>
        ))}
        <Label x={320} y={184} anchor="middle" size="small" tone="muted">
          The error tells you how far the request got, and so which layer to
          fix.
        </Label>
      </Diagram>
    );
  },

  "static-pods": () => (
    <Diagram height={272}>
      <Region
        x={10}
        y={14}
        w={250}
        h={240}
        label="/etc/kubernetes/manifests"
        tone="focus"
      />
      {[
        "kube-apiserver.yaml",
        "kube-controller-manager.yaml",
        "kube-scheduler.yaml",
        "etcd.yaml",
      ].map((name, index) => (
        <Tag key={name} x={135} y={60 + index * 44} text={name} />
      ))}
      <Arrow
        points={[
          [260, 130],
          [300, 130],
        ]}
        label="reads"
        labelAt={[280, 120]}
      />
      <Box
        x={304}
        y={100}
        w={130}
        h={60}
        title="kubelet"
        sub="runs them"
        tone="focus"
      />
      <Arrow
        points={[
          [434, 130],
          [474, 130],
        ]}
      />
      <Region x={478} y={14} w={152} h={240} label="kube-system" />
      {["apiserver", "controller-mgr", "scheduler", "etcd"].map(
        (name, index) => (
          <Box
            key={name}
            x={490}
            y={42 + index * 50}
            w={128}
            h={38}
            title={name}
            tone="good"
          />
        ),
      )}
      <Label x={369} y={196} anchor="middle" size="small" tone="muted">
        Deleting one with kubectl
      </Label>
      <Label x={369} y={214} anchor="middle" size="small" tone="muted">
        does nothing lasting: the
      </Label>
      <Label x={369} y={232} anchor="middle" size="small" tone="muted">
        file brings it back.
      </Label>
    </Diagram>
  ),
} satisfies Drawings;
