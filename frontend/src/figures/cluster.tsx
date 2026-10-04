import {
  Arrow,
  Box,
  Cylinder,
  Diagram,
  File,
  Label,
  Line,
  Region,
  Reveal,
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
  "kubeadm-init": ({ step = 0 }) => {
    const phases: [string, string][] = [
      ["preflight", "runtime works, swap off, ports free"],
      ["certificates", "a cluster CA and a certificate per component"],
      ["static Pods", "manifests written; the kubelet starts them"],
      ["credentials", "admin.conf and the stored configuration"],
    ];
    return (
      <Diagram height={286} step={step}>
        {phases.map(([title, sub], index) => (
          <Box
            key={title}
            x={10}
            y={14 + index * 54}
            w={300}
            h={46}
            title={title}
            sub={sub}
            tone={index < step ? "good" : index === step ? "focus" : "muted"}
            dashed={index > step}
          />
        ))}
        <Region x={340} y={14} w={290} h={256} label="control-plane VM" />
        <Reveal from={1}>
          <File x={380} y={46} name="pki/ca.crt" tone="good" />
        </Reveal>
        <Reveal from={2}>
          {["API server", "controller manager", "scheduler", "etcd"].map(
            (name, index) => (
              <Box
                key={name}
                x={450}
                y={42 + index * 40}
                w={164}
                h={32}
                title={name}
                tone="good"
              />
            ),
          )}
        </Reveal>
        <Reveal from={3}>
          <File x={380} y={130} name="admin.conf" tone="warn" />
          <Tag x={485} y={222} text="node NotReady: no CNI" tone="warn" />
          <Label x={485} y={250} anchor="middle" size="small" tone="muted">
            expected until the next lesson
          </Label>
        </Reveal>
        <Label x={10} y={242} size="small" tone="muted">
          kubeadm init does not install a Pod
        </Label>
        <Label x={10} y={260} size="small" tone="muted">
          network or add other machines.
        </Label>
      </Diagram>
    );
  },

  "cidr-separation": () => (
    <Diagram height={250}>
      <Region
        x={10}
        y={14}
        w={620}
        h={180}
        label="VM network: 192.168.104.0/24"
      />
      {(
        [
          [30, "control-plane VM", "", "10.244.0.0/24"],
          [330, "worker VM", "", "10.244.1.0/24"],
        ] as [number, string, string, string][]
      ).map(([x, name, ip, pods]) => (
        <g key={name}>
          <Region
            x={x}
            y={44}
            w={280}
            h={134}
            label={ip ? `${name}: ${ip}` : name}
            tone="focus"
          />
          <Box
            x={x + 20}
            y={84}
            w={240}
            h={74}
            title="its Pods"
            sub={`addresses from ${pods}`}
            tone="good"
          />
        </g>
      ))}
      <Tag
        x={320}
        y={220}
        text="Pod network 10.244.0.0/16 does not overlap"
        tone="good"
      />
    </Diagram>
  ),

  "kubeadm-join": ({ step = 0 }) => (
    <Diagram height={250} step={step}>
      <Box
        x={10}
        y={80}
        w={180}
        h={66}
        title="worker VM"
        sub={step === 3 ? "joined: NotReady until CNI" : "kubeadm join"}
        tone={step === 3 ? "warn" : "focus"}
      />
      <Box
        x={450}
        y={80}
        w={180}
        h={66}
        title="API server"
        sub="control-plane VM"
      />
      <Reveal from={0}>
        <Arrow
          points={[
            [190, 96],
            [446, 96],
          ]}
          tone={step === 0 ? "focus" : "good"}
          label="1. is this the right cluster? (CA hash)"
          labelAt={[318, 86]}
        />
      </Reveal>
      <Reveal from={1}>
        <Arrow
          points={[
            [190, 130],
            [446, 130],
          ]}
          tone={step === 1 ? "focus" : "good"}
          label="2. am I allowed to join? (bootstrap token)"
          labelAt={[318, 152]}
        />
      </Reveal>
      <Reveal from={2}>
        <Arrow
          points={[
            [540, 146],
            [540, 200],
            [100, 200],
            [100, 150],
          ]}
          tone="good"
          label="3. permanent kubelet credentials"
          labelAt={[320, 192]}
        />
      </Reveal>
      <Label x={320} y={34} anchor="middle" size="small" tone="muted">
        Skipping the CA hash check removes the protection against an impostor.
      </Label>
    </Diagram>
  ),

  "cni-vxlan": () => (
    <Diagram height={258}>
      <Region x={10} y={14} w={280} h={170} label="control-plane VM" />
      <Region x={350} y={14} w={280} h={170} label="worker VM" />
      <Box
        x={40}
        y={54}
        w={220}
        h={56}
        title="frontend Pod"
        sub="10.244.0.12"
        tone="focus"
      />
      <Box
        x={380}
        y={54}
        w={220}
        h={56}
        title="API Pod"
        sub="10.244.1.7"
        tone="good"
      />
      <Box x={40} y={128} w={220} h={40} title="calico-node" mono />
      <Box x={380} y={128} w={220} h={40} title="calico-node" mono />
      <Arrow
        points={[
          [150, 110],
          [150, 124],
        ]}
        tone="focus"
      />
      <Arrow
        points={[
          [260, 148],
          [376, 148],
        ]}
        tone="focus"
      />
      <Arrow
        points={[
          [490, 128],
          [490, 114],
        ]}
        tone="focus"
      />
      <Label x={318} y={140} anchor="middle" size="small" tone="focus">
        VXLAN
      </Label>
      <Tag
        x={320}
        y={212}
        text="Pod to Pod, wrapped in a VM-to-VM packet"
        tone="focus"
      />
      <Label x={320} y={246} anchor="middle" size="small" tone="muted">
        Ready nodes do not prove this path works; a real cross-node request
        does.
      </Label>
    </Diagram>
  ),

  "ha-topology": () => (
    <Diagram height={262}>
      <Box x={10} y={20} w={150} h={50} title="kubectl" sub="and kubelets" />
      <Arrow
        points={[
          [160, 45],
          [226, 45],
        ]}
      />
      <Box
        x={230}
        y={16}
        w={180}
        h={58}
        title="HAProxy"
        sub="one stable address"
        tone="focus"
      />
      {[0, 1, 2].map((index) => (
        <g key={index}>
          <Region
            x={10 + index * 210}
            y={110}
            w={200}
            h={150}
            label={`control plane ${index + 1}`}
            labelBelow
          />
          <Box
            x={30 + index * 210}
            y={140}
            w={160}
            h={36}
            title="API server"
            tone="good"
          />
          <Cylinder
            x={30 + index * 210}
            y={186}
            w={160}
            h={46}
            title="etcd member"
          />
          <Arrow
            points={[
              [320, 74],
              [110 + index * 210, 136],
            ]}
            tone="muted"
          />
        </g>
      ))}
      <Label x={430} y={50} size="small" tone="muted">
        forwards only to healthy
      </Label>
      <Label x={430} y={68} size="small" tone="muted">
        API servers
      </Label>
    </Diagram>
  ),
  "cordon-drain": ({ step = 0 }) => {
    const worker: [string, string, Tone][] = [
      ["API copy", "ready", "good"],
      ["PostgreSQL", "local volume", "good"],
      ...(step === 3
        ? [["API copy", "replacement, ready", "good"] as [string, string, Tone]]
        : []),
    ];
    const worker2: [string, string, Tone][] =
      step < 2
        ? [
            ["API copy", "ready", "good"],
            ["calico-node", "DaemonSet", "default"],
          ]
        : [["calico-node", "DaemonSet, ignored", "muted"]];
    const notes: [string, Tone][] = [
      ["Before: one API copy on each worker.", "muted"],
      ["Cordon: no new Pods may land on worker2. Running Pods stay.", "warn"],
      [
        "Evict: the budget allows one disruption, so the API copy leaves.",
        "warn",
      ],
      [
        "Replace and schedule: the Deployment’s new Pod lands on worker.",
        "good",
      ],
    ];
    return (
      <Diagram height={262} step={step}>
        <Tag x={160} y={20} text="PDB: minAvailable 1" tone="focus" />
        <Region x={10} y={40} w={300} h={180} label="worker" />
        <Region
          x={330}
          y={40}
          w={300}
          h={180}
          label={step === 0 ? "worker2" : "worker2: SchedulingDisabled"}
          tone={step === 0 ? "default" : "warn"}
        />
        {worker.map(([title, sub, tone], index) => (
          <Box
            key={`${title}-${index}`}
            x={30}
            y={72 + index * 48}
            w={260}
            h={40}
            title={title}
            sub={sub}
            tone={tone}
          />
        ))}
        {worker2.map(([title, sub, tone], index) => (
          <Box
            key={`${title}-${index}`}
            x={350}
            y={72 + index * 48}
            w={260}
            h={40}
            title={title}
            sub={sub}
            tone={tone}
            dashed={tone === "muted"}
          />
        ))}
        <Label
          x={320}
          y={248}
          anchor="middle"
          size="small"
          tone={notes[step][1]}
        >
          {notes[step][0]}
        </Label>
      </Diagram>
    );
  },

  "upgrade-order": () => {
    const control = [
      "upgrade the kubeadm package",
      "kubeadm upgrade plan",
      "kubeadm upgrade apply v1.37.1",
      "drain, then upgrade kubelet and kubectl",
      "daemon-reload, restart kubelet",
      "uncordon",
    ];
    const worker = [
      "upgrade the kubeadm package",
      "kubeadm upgrade node",
      "drain, then upgrade kubelet and kubectl",
      "daemon-reload, restart kubelet",
      "uncordon",
    ];
    return (
      <Diagram height={308}>
        <Tag x={160} y={18} text="1.36.5" />
        <Arrow
          points={[
            [206, 18],
            [266, 18],
          ]}
          label="one minor version"
          labelAt={[236, 36]}
        />
        <Tag x={310} y={18} text="1.37.1" tone="good" />
        <Region
          x={10}
          y={50}
          w={300}
          h={236}
          label="1. Control-plane node"
          tone="focus"
        />
        {control.map((text, index) => (
          <Label
            key={text}
            x={26}
            y={100 + index * 30}
            size="small"
            mono={index > 0 && index < 3}
          >
            {`${index + 1}. ${text}`}
          </Label>
        ))}
        <Region
          x={330}
          y={50}
          w={300}
          h={236}
          label="2. Each worker, one at a time"
        />
        {worker.map((text, index) => (
          <Label
            key={text}
            x={346}
            y={100 + index * 30}
            size="small"
            mono={index === 1}
          >
            {`${index + 1}. ${text}`}
          </Label>
        ))}
        <Label x={346} y={264} size="small" tone="warn">
          never kubeadm upgrade apply on a worker
        </Label>
      </Diagram>
    );
  },

  "cert-renewal": ({ step = 0 }) => {
    const file = step === 0 ? "A" : "B";
    const served = step === 2 ? "B" : "A";
    return (
      <Diagram height={250} step={step}>
        <Region x={10} y={14} w={620} h={190} label="control-plane VM" />
        <File
          x={50}
          y={50}
          name="apiserver.crt"
          tone={step >= 1 ? "good" : "default"}
        />
        <Label x={130} y={62}>
          {`serial ${file}`}
        </Label>
        <Label x={130} y={82} size="small" tone="muted">
          signed by the same cluster CA
        </Label>
        <Box
          x={360}
          y={44}
          w={250}
          h={64}
          title="kube-apiserver"
          sub={`serving serial ${served}`}
          tone={step === 1 ? "warn" : step === 2 ? "good" : "default"}
        />
        <Reveal from={1} until={1}>
          <Label x={485} y={136} anchor="middle" size="small" tone="warn">
            still holds the old certificate in memory
          </Label>
        </Reveal>
        <Reveal from={2}>
          <Arrow
            points={[
              [485, 170],
              [485, 112],
            ]}
            tone="good"
            label="crictl stop; the kubelet starts it again"
            labelAt={[400, 186]}
          />
        </Reveal>
        <Label x={320} y={236} anchor="middle" size="small" tone="muted">
          Deleting its mirror Pod with kubectl would not reload anything.
        </Label>
      </Diagram>
    );
  },
  "two-paths": () => (
    <Diagram height={262}>
      <Region x={10} y={14} w={250} h={200} label="control-plane VM" />
      <Region x={380} y={14} w={250} h={200} label="worker VM" />
      <Box
        x={26}
        y={46}
        w={218}
        h={44}
        title="API server"
        sub="receives node status"
      />
      <Box
        x={396}
        y={46}
        w={218}
        h={44}
        title="kubelet"
        sub="reports Ready"
        tone="good"
      />
      <Box x={26} y={146} w={218} h={44} title="frontend Pod" tone="focus" />
      <Box x={396} y={146} w={218} h={44} title="API Pod" tone="good" />
      <Arrow
        points={[
          [392, 68],
          [248, 68],
        ]}
        tone="good"
        label="node network: status"
        labelAt={[320, 58]}
      />
      <Arrow
        points={[
          [392, 162],
          [248, 162],
        ]}
        tone="bad"
        dashed
        label="VXLAN, UDP 4789"
        labelAt={[320, 152]}
      />
      <Arrow
        points={[
          [248, 176],
          [392, 176],
        ]}
        tone="focus"
        dashed
      />
      <Tag x={135} y={122} text="raw PREROUTING: DROP udp 4789" tone="bad" />
      <Label x={320} y={240} anchor="middle" size="small" tone="muted">
        Both nodes stay Ready, yet replies from the worker never reach the
        frontend.
      </Label>
    </Diagram>
  ),

  "testing-layers": () => {
    const tests: [string, string][] = [
      ["request the API Pod IP", "packet delivery between nodes"],
      ["request the Service name", "+ DNS and Service routing"],
      ["GET /healthz", "+ the process answers"],
      ["GET /readyz, or a real job", "+ its database and queue"],
    ];
    return (
      <Diagram height={232}>
        {tests.map(([test, proves], index) => (
          <g key={test}>
            <Box
              x={10 + index * 40}
              y={14 + index * 52}
              w={250}
              h={42}
              title={test}
              tone="focus"
            />
            <Label x={290 + index * 40} y={40 + index * 52} size="small">
              {proves}
            </Label>
          </g>
        ))}
      </Diagram>
    );
  },

  "dns-vs-proxy": () => (
    <Diagram height={286}>
      <Box
        x={10}
        y={100}
        w={150}
        h={60}
        title="frontend Pod"
        sub="dispatch:8080"
        tone="focus"
      />
      <Box x={250} y={14} w={180} h={60} title="CoreDNS" sub="reads Services" />
      <Arrow
        points={[
          [90, 100],
          [90, 44],
          [246, 44],
        ]}
        label="1. what is dispatch?"
        labelAt={[160, 34]}
      />
      <Arrow
        points={[
          [340, 74],
          [340, 96],
          [164, 112],
        ]}
        tone="good"
        label="ClusterIP 10.96.…"
        labelAt={[256, 92]}
      />
      <Box
        x={250}
        y={170}
        w={180}
        h={60}
        title="node rules"
        sub="programmed by kube-proxy"
      />
      <Arrow
        points={[
          [160, 140],
          [246, 190],
        ]}
        label="2. connect"
        labelAt={[190, 182]}
      />
      <Box x={480} y={170} w={150} h={60} title="dispatch Pod" tone="good" />
      <Arrow
        points={[
          [430, 200],
          [476, 200],
        ]}
        tone="good"
      />
      <Label x={480} y={40} size="small" tone="muted">
        DNS fails, IP works:
      </Label>
      <Label x={480} y={58} size="small" tone="warn">
        look at CoreDNS
      </Label>
      <Label x={480} y={100} size="small" tone="muted">
        DNS works, IP fails:
      </Label>
      <Label x={480} y={118} size="small" tone="warn">
        look at kube-proxy
      </Label>
      <Label x={320} y={268} anchor="middle" size="small" tone="muted">
        Test with a new Service: routes kube-proxy set up earlier keep working
        after it stops.
      </Label>
    </Diagram>
  ),

  "csi-chain": ({ step = 0 }) => {
    const onWorker = step !== 1;
    return (
      <Diagram height={298} step={step}>
        <Region x={10} y={14} w={290} h={250} label="control-plane VM" />
        <Region x={340} y={14} w={290} h={250} label="worker VM" tone="focus" />
        <Box
          x={360}
          y={44}
          w={250}
          h={40}
          title="CSI node plugin"
          sub="registered here"
          tone="good"
        />
        <Box
          x={360}
          y={186}
          w={250}
          h={60}
          title="volume: hostpath folder"
          sub="PV data-db-0, same handle"
          tone="focus"
        />
        {onWorker ? (
          <Box
            x={360}
            y={104}
            w={250}
            h={56}
            title="db-0"
            sub="attached and mounted"
            tone="good"
            mono
          />
        ) : (
          <>
            <Box
              x={30}
              y={104}
              w={250}
              h={56}
              title="db-0"
              sub="cannot use its volume"
              tone="bad"
              mono
            />
            <Label x={155} y={196} anchor="middle" size="small" tone="bad">
              no driver here, and the
            </Label>
            <Label x={155} y={214} anchor="middle" size="small" tone="bad">
              data lives on the worker
            </Label>
          </>
        )}
        {onWorker && (
          <Arrow
            points={[
              [485, 160],
              [485, 182],
            ]}
            tone="good"
          />
        )}
        <Label x={320} y={290} anchor="middle" size="small" tone="muted">
          {
            [
              "Provisioned, attached, and mounted on the worker: the whole chain works.",
              "Moved to the control plane, db-0 cannot reach its volume.",
              "Placed on the worker again, db-0 reuses the original claim and data.",
            ][step]
          }
        </Label>
      </Diagram>
    );
  },
  "etcd-scope": () => (
    <Diagram height={254}>
      <Region
        x={10}
        y={14}
        w={300}
        h={210}
        label="etcd snapshot: Kubernetes objects"
        tone="focus"
      />
      {[
        "Deployments and Services",
        "ConfigMaps and Secrets",
        "the database’s StatefulSet",
        "its PersistentVolumeClaim",
      ].map((text, index) => (
        <Tag key={text} x={160} y={60 + index * 40} text={text} tone="good" />
      ))}
      <Region
        x={330}
        y={14}
        w={300}
        h={210}
        label="PostgreSQL on the worker’s volume"
      />
      <Cylinder
        x={385}
        y={60}
        w={190}
        h={90}
        title="Dispatch’s jobs"
        sub="rows in the database"
      />
      <Label x={480} y={186} anchor="middle" size="small" tone="warn">
        not in any etcd snapshot
      </Label>
      <Label x={320} y={246} anchor="middle" size="small" tone="muted">
        Application data needs its own backups.
      </Label>
    </Diagram>
  ),

  "etcd-restore": ({ step = 0 }) => {
    const sentinel: [string, Tone][] = [
      ["maintenance-sentinel, UID 7f3…", "good"],
      ["deleted", "bad"],
      ["deleted", "bad"],
      ["maintenance-sentinel, UID 7f3…", "good"],
    ];
    return (
      <Diagram height={272} step={step}>
        <Region
          x={10}
          y={14}
          w={620}
          h={190}
          label="control-plane VM: /var/lib/etcd"
        />
        <Box
          x={30}
          y={46}
          w={170}
          h={56}
          title="member/"
          sub={step === 3 ? "no longer used" : "etcd’s live data"}
          tone={step === 3 ? "muted" : "default"}
          dashed={step === 3}
          mono
        />
        <Reveal from={0}>
          <File x={290} y={50} name="dockyard-recovery.db" tone="focus" />
          <Arrow
            points={[
              [200, 74],
              [280, 74],
            ]}
            tone="focus"
            label="snapshot save"
            labelAt={[240, 66]}
          />
        </Reveal>
        <Reveal from={2}>
          <Box
            x={430}
            y={46}
            w={180}
            h={56}
            title="dockyard-restored/"
            sub="revision bumped ahead"
            tone="good"
            mono
          />
          <Arrow
            points={[
              [330, 74],
              [426, 74],
            ]}
            tone="good"
            label="snapshot restore"
            labelAt={[378, 66]}
          />
        </Reveal>
        <Reveal from={3}>
          <Box
            x={300}
            y={130}
            w={310}
            h={56}
            title="etcd.yaml hostPath"
            sub="now the restored directory"
            tone="good"
            mono
          />
          <Arrow
            points={[
              [520, 130],
              [520, 106],
            ]}
            tone="good"
          />
        </Reveal>
        <Label x={10} y={232} size="small" tone="muted">
          the ConfigMap in the API:
        </Label>
        <Tag
          x={340}
          y={228}
          text={sentinel[step][0]}
          tone={sentinel[step][1]}
        />
        <Label x={10} y={262} size="small" tone="muted">
          Recreating it by hand would give it a new UID; only the restore brings
          back the original.
        </Label>
      </Diagram>
    );
  },

  "static-pod-repair": ({ step = 0 }) => {
    const filesIn =
      step === 0
        ? ["etcd", "kube-apiserver", "kube-controller-manager"]
        : [
            "etcd",
            "kube-apiserver",
            "kube-controller-manager",
            "kube-scheduler",
          ];
    const kubelet = step === 2;
    return (
      <Diagram height={286} step={step}>
        <Region
          x={10}
          y={14}
          w={290}
          h={220}
          label="/etc/kubernetes/manifests"
          tone="focus"
        />
        {filesIn.map((name, index) => (
          <Tag
            key={name}
            x={155}
            y={56 + index * 40}
            text={`${name}.yaml`}
            tone={name === "kube-scheduler" ? "good" : "default"}
          />
        ))}
        {step === 0 && (
          <Label x={30} y={214} size="small" tone="bad">
            kube-scheduler.yaml was moved away
          </Label>
        )}
        <Box
          x={340}
          y={30}
          w={290}
          h={56}
          title="kubelet"
          sub={
            kubelet
              ? "running: watches the folder"
              : "stopped: nothing watches the folder"
          }
          tone={kubelet ? "good" : "bad"}
        />
        <Box
          x={340}
          y={104}
          w={290}
          h={56}
          title="scheduler"
          sub={kubelet ? "running again" : "not running"}
          tone={kubelet ? "good" : "bad"}
        />
        <Box
          x={340}
          y={178}
          w={290}
          h={56}
          title="a brand-new Pod"
          sub={kubelet ? "gets a node" : "Pending, no node"}
          tone={kubelet ? "good" : "warn"}
        />
        <Label x={320} y={268} anchor="middle" size="small" tone="muted">
          Pods that already had a node keep running throughout.
        </Label>
      </Diagram>
    );
  },

  "apiserver-etcd": ({ step = 0 }) => {
    const fixed = step === 1;
    return (
      <Diagram height={250} step={step}>
        <Region x={10} y={14} w={620} h={176} label="control-plane VM" />
        <Box
          x={30}
          y={50}
          w={250}
          h={70}
          title="kube-apiserver"
          sub={
            fixed ? "connected: ready" : "exits and restarts, again and again"
          }
          tone={fixed ? "good" : "bad"}
        />
        <Box
          x={380}
          y={50}
          w={230}
          h={70}
          title="etcd"
          sub="listening on 127.0.0.1:2379"
          tone="good"
        />
        <Arrow
          points={[
            [280, 85],
            [376, 85],
          ]}
          tone={fixed ? "good" : "bad"}
          dashed={!fixed}
          label={fixed ? "2379" : "wrong port"}
          labelAt={[328, 77]}
        />
        <Tag
          x={155}
          y={152}
          text={fixed ? "--etcd-servers=…:2379" : "--etcd-servers=…:WRONG"}
          tone={fixed ? "good" : "bad"}
        />
        <Label x={10} y={222}>
          kubectl says:
        </Label>
        <Tag
          x={330}
          y={218}
          text={fixed ? "/readyz: ok" : "cannot connect"}
          tone={fixed ? "good" : "bad"}
        />
      </Diagram>
    );
  },
  "triage-loop": () => {
    const stages: [string, string][] = [
      ["observe", "the symptom, in a user’s words"],
      ["guess", "one cause that explains it"],
      ["test", "a command that proves it either way"],
      ["change", "one thing, if the test agrees"],
      ["check", "did the symptom change?"],
    ];
    return (
      <Diagram height={232}>
        {stages.map(([title, sub], index) => (
          <g key={title}>
            <Box
              x={10 + index * 126}
              y={30}
              w={116}
              h={76}
              title={title}
              tone={index === 3 ? "warn" : "focus"}
            />
            <Label
              x={68 + index * 126}
              y={126}
              anchor="middle"
              size="small"
              tone="muted"
            >
              {sub.split(" ").slice(0, 3).join(" ")}
            </Label>
            <Label
              x={68 + index * 126}
              y={144}
              anchor="middle"
              size="small"
              tone="muted"
            >
              {sub.split(" ").slice(3).join(" ")}
            </Label>
            {index > 0 && (
              <Arrow
                points={[
                  [index * 126, 68],
                  [index * 126 + 8, 68],
                ]}
              />
            )}
          </g>
        ))}
        <Arrow
          points={[
            [625, 106],
            [625, 178],
            [15, 178],
            [15, 110],
          ]}
          tone="muted"
          dashed
          label="repeat until the symptom is gone"
          labelAt={[320, 170]}
        />
        <Label x={320} y={222} anchor="middle" size="small" tone="muted">
          If a test disagrees with your guess, change the guess, not the
          cluster.
        </Label>
      </Diagram>
    );
  },

  "request-path-steps": ({ step = 0 }) => {
    const parts: [string, string, Tone][][] = [
      [
        ["Service", "no endpoints", "bad"],
        ["API", "healthy, but unreached", "muted"],
        ["worker", "unknown yet", "muted"],
        ["PostgreSQL", "unknown yet", "muted"],
      ],
      [
        ["Service", "endpoints found", "good"],
        ["API", "stores the job: queued", "good"],
        ["worker", "0/0: scaled to zero", "bad"],
        ["PostgreSQL", "job waits, queued", "warn"],
      ],
      [
        ["Service", "endpoints found", "good"],
        ["API", "stores the job", "good"],
        ["worker", "processes it", "good"],
        ["PostgreSQL", "result saved: done", "good"],
      ],
    ];
    return (
      <Diagram height={176} step={step}>
        {parts[step].map(([title, sub, tone], index) => (
          <g key={title}>
            <Box
              x={10 + index * 158}
              y={30}
              w={146}
              h={66}
              title={title}
              sub={sub}
              tone={tone}
            />
            {index > 0 && (
              <Arrow
                points={[
                  [index * 158 - 2, 63],
                  [index * 158 + 8, 63],
                ]}
                tone={tone === "muted" ? "muted" : "default"}
              />
            )}
          </g>
        ))}
        <Label x={320} y={140} anchor="middle" size="small" tone="muted">
          {
            [
              "The first broken step hides everything after it.",
              "Fixing the route reveals the next fault: jobs stay queued.",
              "Every step works, so a new job reaches done.",
            ][step]
          }
        </Label>
      </Diagram>
    );
  },

  "capacity-sums": () => {
    const metrics: [string, string, number[]][] = [
      ["CPU requests", "budget 1 CPU", [50 / 1000, 75 / 1000, 100 / 1000]],
      ["memory requests", "budget 512 MiB", [64 / 512, 96 / 512, 128 / 512]],
      ["memory limits", "budget 1 GiB", [384 / 1024, 576 / 1024, 768 / 1024]],
    ];
    const totals = [
      ["50m", "75m", "100m"],
      ["64 MiB", "96 MiB", "128 MiB"],
      ["384 MiB", "576 MiB", "768 MiB"],
    ];
    const width = 400;
    return (
      <Diagram height={300}>
        <Label x={10} y={20} size="small" tone="muted">
          per copy: requests 25m CPU and 32 MiB, limits 300m CPU and 192 MiB;
          bars show 2, 3, and 4 copies
        </Label>
        {metrics.map(([name, budget, values], row) => (
          <g key={name}>
            <Label x={10} y={58 + row * 82}>
              {name}
            </Label>
            <Label x={10} y={76 + row * 82} size="small" tone="muted">
              {budget}
            </Label>
            {values.map((value, index) => (
              <g key={index}>
                <Box
                  x={180}
                  y={42 + row * 82 + index * 20}
                  w={Math.max(4, value * width)}
                  h={14}
                  tone={index === 2 ? "focus" : "default"}
                />
                <Label
                  x={186 + value * width}
                  y={53 + row * 82 + index * 20}
                  size="small"
                  tone="muted"
                >
                  {totals[row][index]}
                </Label>
              </g>
            ))}
            <Line
              points={[
                [180 + width, 38 + row * 82],
                [180 + width, 104 + row * 82],
              ]}
              tone="warn"
            />
          </g>
        ))}
        <Label x={580} y={290} anchor="middle" size="small" tone="warn">
          budget
        </Label>
      </Diagram>
    );
  },

  "rollout-columns": ({ step = 0 }) => {
    const fixed = step === 1;
    const columns: [string, number][] = [
      ["desired", 2],
      ["UP-TO-DATE", fixed ? 2 : 1],
      ["AVAILABLE", 2],
      ["total", fixed ? 2 : 3],
    ];
    return (
      <Diagram height={264} step={step}>
        {columns.map(([name, value], index) => (
          <g key={name}>
            <Label
              x={90 + index * 150}
              y={24}
              anchor="middle"
              size="small"
              tone="muted"
              mono
            >
              {name}
            </Label>
            <Label
              x={90 + index * 150}
              y={56}
              anchor="middle"
              size="large"
              tone={fixed ? "good" : value === 2 ? "default" : "warn"}
            >
              {String(value)}
            </Label>
          </g>
        ))}
        <Region x={10} y={80} w={300} h={130} label="previous ReplicaSet" />
        <Region
          x={330}
          y={80}
          w={300}
          h={130}
          label="newest ReplicaSet"
          tone={fixed ? "good" : "bad"}
        />
        {[0, 1].map((index) => (
          <Box
            key={index}
            x={30 + index * 140}
            y={124}
            w={120}
            h={50}
            title="Pod"
            sub={fixed ? "scaled away" : "ready, serving"}
            tone={fixed ? "muted" : "good"}
            dashed={fixed}
          />
        ))}
        {fixed ? (
          [0, 1].map((index) => (
            <Box
              key={index}
              x={350 + index * 140}
              y={124}
              w={120}
              h={50}
              title="Pod"
              sub="ready, serving"
              tone="good"
            />
          ))
        ) : (
          <Box
            x={350}
            y={124}
            w={260}
            h={50}
            title="Pod"
            sub="ErrImageNeverPull"
            tone="bad"
          />
        )}
        <Label
          x={320}
          y={246}
          anchor="middle"
          size="small"
          tone={fixed ? "good" : "warn"}
        >
          {fixed
            ? "All four agree: the rollout has finished."
            : "Still answering, but the counts disagree: the rollout is stuck."}
        </Label>
      </Diagram>
    );
  },
} satisfies Drawings;
