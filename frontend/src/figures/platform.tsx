import {
  Arrow,
  Box,
  Code,
  Diagram,
  File,
  Label,
  Line,
  Region,
  Reveal,
  Tag,
  type Tone,
} from "./kit";
import type { Drawings } from "./registry";

/** A small Pod chip used in node and scheduling drawings. */
function Pod({
  x,
  y,
  name = "Pod",
  state,
  tone = "good",
}: {
  x: number;
  y: number;
  name?: string;
  state?: string;
  tone?: Tone;
}) {
  return (
    <Box
      x={x}
      y={y}
      w={84}
      h={state ? 44 : 32}
      title={name}
      sub={state}
      tone={tone}
      dashed={tone === "muted"}
    />
  );
}

export const platform = {
  "requests-limits": () => (
    <Diagram height={266}>
      <Label x={20} y={70}>
        CPU
      </Label>
      <Box x={140} y={50} w={58} h={28} tone="focus" />
      <Label x={140} y={42} size="small" tone="focus">
        request 50m: reserved
      </Label>
      <Line
        points={[
          [485, 40],
          [485, 92],
        ]}
        tone="warn"
      />
      <Label x={490} y={52} size="small" tone="warn">
        limit 300m
      </Label>
      <Arrow
        points={[
          [140, 104],
          [480, 104],
        ]}
        tone="warn"
        label="busy: held at the limit, so it slows down"
        labelAt={[310, 124]}
      />

      <Label x={20} y={190}>
        Memory
      </Label>
      <Box x={140} y={170} w={115} h={28} tone="focus" />
      <Label x={140} y={162} size="small" tone="focus">
        request 64Mi: reserved
      </Label>
      <Line
        points={[
          [485, 160],
          [485, 212],
        ]}
        tone="warn"
      />
      <Label x={490} y={172} size="small" tone="warn">
        limit 192Mi
      </Label>
      <Arrow
        points={[
          [140, 224],
          [560, 224],
        ]}
        tone="bad"
        label="uses more than the limit: OOMKilled"
        labelAt={[330, 244]}
      />
      <Label x={568} y={229} tone="bad">
        ✗
      </Label>
    </Diagram>
  ),

  "qos-classes": () => (
    <Diagram height={214}>
      {(
        [
          [10, "BestEffort", "no requests or limits", "bad"],
          [225, "Burstable", "some requests or limits", "warn"],
          [440, "Guaranteed", "requests equal limits", "good"],
        ] as [number, string, string, Tone][]
      ).map(([x, title, sub, tone]) => (
        <Box
          key={title}
          x={x}
          y={20}
          w={190}
          h={70}
          title={title}
          sub={sub}
          tone={tone}
        />
      ))}
      <Tag x={320} y={112} text="Dispatch’s API" tone="focus" />
      <Arrow
        points={[
          [40, 156],
          [600, 156],
        ]}
        tone="muted"
      />
      <Label x={40} y={180} size="small" tone="bad">
        evicted first
      </Label>
      <Label x={600} y={180} anchor="end" size="small" tone="good">
        evicted last
      </Label>
      <Label x={320} y={204} anchor="middle" size="small" tone="muted">
        when a node runs short of memory
      </Label>
    </Diagram>
  ),

  "taints-affinity": ({ step = 0 }) => {
    const pod = [
      "no toleration",
      "tolerates pool=apps",
      "toleration + affinity",
    ][step];
    const verdict: [string, Tone][][] = [
      [
        ["✗ untolerated taint", "bad"],
        ["✗ untolerated taint", "bad"],
        ["✗ untolerated taint", "bad"],
      ],
      [
        ["✗ untolerated taint", "bad"],
        ["✓ allowed", "good"],
        ["✓ allowed", "good"],
      ],
      [
        ["✗ not pool=apps", "bad"],
        ["", "good"],
        ["", "good"],
      ],
    ];
    const nodes: [number, string, string, string][] = [
      [10, "control plane", "control-plane:NoSchedule", ""],
      [220, "worker", "pool=apps:NoSchedule", "label pool=apps"],
      [430, "worker2", "pool=apps:NoSchedule", "label pool=apps"],
    ];
    return (
      <Diagram height={286} step={step}>
        <Box
          x={220}
          y={8}
          w={200}
          h={48}
          title="Dispatch Pod"
          sub={pod}
          tone="focus"
        />
        {nodes.map(([x, name, taint, label], index) => (
          <g key={name}>
            <Region x={x} y={74} w={200} h={170} label={name} />
            <Tag x={x + 100} y={112} text={taint} tone="warn" />
            {label && <Tag x={x + 100} y={142} text={label} />}
            {verdict[step][index][0] && (
              <Label
                x={x + 100}
                y={204}
                anchor="middle"
                size="small"
                tone={verdict[step][index][1]}
              >
                {verdict[step][index][0]}
              </Label>
            )}
            {step === 2 && index > 0 && (
              <Box
                x={x + 50}
                y={170}
                w={100}
                h={50}
                title="Pod"
                sub="placed"
                tone="good"
              />
            )}
          </g>
        ))}
        <Label
          x={320}
          y={272}
          anchor="middle"
          size="small"
          tone={step === 1 ? "warn" : "muted"}
        >
          {
            [
              "Taints keep every node closed to this Pod, so it stays Pending.",
              "A toleration allows the workers, but nothing sends the Pod there.",
              "Affinity sends it to pool=apps nodes; the taint keeps other Pods off.",
            ][step]
          }
        </Label>
      </Diagram>
    );
  },

  "topology-spread": () => (
    <Diagram height={226}>
      {(
        [
          [
            10,
            "Without a spread rule",
            [2, 0],
            "skew 2: one node holds both",
            "bad",
          ],
          [
            330,
            "maxSkew: 1, by hostname",
            [1, 1],
            "skew 0: one on each node",
            "good",
          ],
        ] as [number, string, number[], string, Tone][]
      ).map(([x, label, counts, result, tone]) => (
        <g key={label}>
          <Region x={x} y={14} w={300} h={170} label={label} tone={tone} />
          {["worker", "worker2"].map((node, index) => (
            <g key={node}>
              <Region
                x={x + 15 + index * 140}
                y={46}
                w={130}
                h={120}
                label={node}
              />
              {Array.from({ length: counts[index] }, (_, pod) => (
                <Pod key={pod} x={x + 38 + index * 140} y={78 + pod * 40} />
              ))}
            </g>
          ))}
          <Tag x={x + 150} y={206} text={result} tone={tone} />
        </g>
      ))}
    </Diagram>
  ),

  "hpa-math": () => (
    <Diagram height={272}>
      <Box
        x={10}
        y={20}
        w={170}
        h={56}
        title="Metrics Server"
        sub="measures each Pod"
      />
      <Arrow
        points={[
          [180, 48],
          [231, 48],
        ]}
      />
      <Box
        x={235}
        y={20}
        w={170}
        h={56}
        title="HPA"
        sub="compares with target"
        tone="focus"
      />
      <Arrow
        points={[
          [405, 48],
          [456, 48],
        ]}
        tone="good"
      />
      <Box
        x={460}
        y={20}
        w={170}
        h={56}
        title="Deployment"
        sub="replicas: 2 → 4"
        tone="good"
      />
      <Arrow
        points={[
          [545, 76],
          [545, 100],
          [95, 100],
          [95, 80],
        ]}
        tone="muted"
        dashed
        label="and again, every few seconds"
        labelAt={[320, 94]}
      />
      <Code
        x={10}
        y={126}
        w={620}
        lines={[
          { text: "target   50% of the 50m request   = aim for 25m per Pod" },
          {
            text: "measured average use              = 100m per Pod (200%)",
            tone: "focus",
          },
          { text: "desired  2 Pods × 200% ÷ 50%       = 8 Pods" },
          {
            text: "capped   at maxReplicas            = 4 Pods (ScalingLimited)",
            tone: "good",
          },
        ]}
      />
    </Diagram>
  ),

  "pdb-drain": ({ step = 0 }) => {
    const first: [string, string, Tone][][] = [
      [
        ["Pod A", "ready", "good"],
        ["Pod B", "ready", "good"],
      ],
      [["Pod B", "ready", "good"]],
      [["Pod B", "must wait", "warn"]],
      [],
      [],
    ];
    const second: [string, string, Tone][][] = [
      [["Pod C", "ready", "good"]],
      [
        ["Pod C", "ready", "good"],
        ["Pod A′", "starting", "warn"],
      ],
      [
        ["Pod C", "ready", "good"],
        ["Pod A′", "starting", "warn"],
      ],
      [
        ["Pod C", "ready", "good"],
        ["Pod A′", "ready", "good"],
        ["Pod B′", "starting", "warn"],
      ],
      [
        ["Pod C", "ready", "good"],
        ["Pod A′", "ready", "good"],
        ["Pod B′", "ready", "good"],
      ],
    ];
    const ready = [3, 2, 2, 2, 3][step];
    return (
      <Diagram height={252} step={step}>
        <Tag
          x={320}
          y={20}
          text="PodDisruptionBudget: minAvailable 2"
          tone="focus"
        />
        <Region
          x={10}
          y={46}
          w={300}
          h={140}
          label={step === 0 ? "worker" : "worker: cordoned, draining"}
          tone={step === 0 ? "default" : "warn"}
        />
        <Region x={330} y={46} w={300} h={140} label="worker2" />
        {first[step].map(([name, state, tone], index) => (
          <Box
            key={name}
            x={30 + index * 140}
            y={96}
            w={120}
            h={50}
            title={name}
            sub={state}
            tone={tone}
          />
        ))}
        {second[step].map(([name, state, tone], index) => (
          <Box
            key={name}
            x={345 + index * 95}
            y={96}
            w={86}
            h={50}
            title={name}
            sub={state}
            tone={tone}
          />
        ))}
        <Tag
          x={320}
          y={214}
          text={`ready: ${ready}, minimum 2`}
          tone={ready >= 2 ? "good" : "bad"}
        />
      </Diagram>
    );
  },

  "prestop-timeline": () => (
    <Diagram height={236}>
      <Label x={10} y={70} size="small" tone="muted">
        Service
      </Label>
      <Label x={10} y={144} size="small" tone="muted">
        Container
      </Label>
      <Box
        x={120}
        y={48}
        w={180}
        h={36}
        title="removing the endpoint…"
        tone="warn"
      />
      <Box
        x={300}
        y={48}
        w={320}
        h={36}
        title="no new traffic arrives"
        tone="good"
      />
      <Box
        x={120}
        y={122}
        w={180}
        h={36}
        title="preStop: sleep 5"
        tone="focus"
        mono
      />
      <Box x={300} y={122} w={140} h={36} title="SIGTERM, exit" tone="good" />
      <Arrow
        points={[
          [110, 194],
          [624, 194],
        ]}
        tone="muted"
      />
      {(
        [
          [120, "Pod deleted", "middle"],
          [300, "+5 s", "middle"],
          [600, "+20 s: grace period ends", "end"],
        ] as [number, string, "middle" | "end"][]
      ).map(([x, text, anchor]) => (
        <g key={text}>
          <Line
            points={[
              [x, 186],
              [x, 202],
            ]}
          />
          <Label
            x={anchor === "end" ? x + 24 : x}
            y={220}
            anchor={anchor}
            size="small"
            tone="muted"
          >
            {text}
          </Label>
        </g>
      ))}
    </Diagram>
  ),
  "kustomize-overlays": () => (
    <Diagram height={268}>
      <Region x={10} y={20} w={190} h={226} label="base" />
      {[
        "deployment.yaml",
        "service.yaml",
        "configmap.yaml",
        "kustomization.yaml",
      ].map((name, index) => (
        <Tag key={name} x={105} y={66 + index * 40} text={name} />
      ))}
      <Region
        x={250}
        y={20}
        w={200}
        h={104}
        label="overlays/development"
        tone="focus"
      />
      {["namespace: dispatch", "replicas: 2", "environment: development"].map(
        (line, index) => (
          <Label key={line} x={266} y={58 + index * 22} size="small" mono>
            {line}
          </Label>
        ),
      )}
      <Region x={250} y={142} w={200} h={104} label="overlays/staging" />
      {["namespace: staging", "environment: staging"].map((line, index) => (
        <Label key={line} x={266} y={180 + index * 22} size="small" mono>
          {line}
        </Label>
      ))}
      <Arrow
        points={[
          [200, 110],
          [246, 72],
        ]}
      />
      <Arrow
        points={[
          [200, 160],
          [246, 194],
        ]}
      />
      <Arrow
        points={[
          [450, 72],
          [486, 72],
        ]}
        tone="good"
      />
      <Box
        x={490}
        y={42}
        w={140}
        h={60}
        title="development"
        sub="deployed here"
        tone="good"
      />
      <Arrow
        points={[
          [450, 194],
          [486, 194],
        ]}
        tone="muted"
      />
      <Box x={490} y={164} w={140} h={60} title="staging" sub="rendered only" />
    </Diagram>
  ),

  "helm-render": () => (
    <Diagram height={214}>
      <Label x={10} y={20} size="small" tone="muted">
        Values, from lowest to highest priority
      </Label>
      <Tag x={110} y={46} text="chart’s values.yaml" />
      <Tag x={110} y={86} text="-f values-practice.yaml" tone="focus" />
      <Tag x={110} y={126} text="--set api.replicas=2" tone="good" />
      <Label x={110} y={160} anchor="middle" size="small" tone="muted">
        later values win
      </Label>
      <Arrow
        points={[
          [200, 46],
          [236, 76],
        ]}
        tone="muted"
      />
      <Arrow
        points={[
          [210, 86],
          [236, 86],
        ]}
        tone="muted"
      />
      <Arrow
        points={[
          [200, 126],
          [236, 96],
        ]}
        tone="muted"
      />
      <Box
        x={240}
        y={50}
        w={160}
        h={72}
        title="templates"
        sub="filled in with values"
        tone="focus"
      />
      <Arrow
        points={[
          [400, 86],
          [456, 86],
        ]}
        tone="good"
        label="install"
        labelAt={[428, 78]}
      />
      <Box
        x={460}
        y={50}
        w={170}
        h={72}
        title="release dispatch"
        sub="revision 1, 2, 3…"
        tone="good"
      />
      <Label x={320} y={200} anchor="middle" size="small" tone="muted">
        helm template shows the filled-in manifests without installing anything.
      </Label>
    </Diagram>
  ),

  "helm-revisions": ({ step = 0 }) => (
    <Diagram height={262} step={step}>
      <Box
        x={10}
        y={50}
        w={180}
        h={66}
        title="revision 1"
        sub="2 replicas: serving"
        tone="good"
      />
      <Reveal from={1}>
        <Arrow
          points={[
            [190, 83],
            [226, 83],
          ]}
        />
        <Box
          x={230}
          y={50}
          w={180}
          h={66}
          title="revision 2"
          sub="0 replicas"
          tone="bad"
        />
        <Tag x={320} y={140} text="helm: deployed" tone="warn" />
        <Tag x={320} y={172} text="0 Pods serving" tone="bad" />
      </Reveal>
      <Reveal from={2}>
        <Arrow
          points={[
            [410, 83],
            [446, 83],
          ]}
        />
        <Box
          x={450}
          y={50}
          w={180}
          h={66}
          title="revision 3"
          sub="rollback to 1: serving"
          tone="good"
        />
        <Arrow
          points={[
            [540, 50],
            [540, 24],
            [100, 24],
            [100, 46],
          ]}
          dashed
          tone="good"
          label="reuses revision 1’s manifests and values"
          labelAt={[320, 18]}
        />
        <File x={450} y={140} name="values-practice.yaml" tone="warn" />
        <Label x={463} y={212} anchor="middle" size="small" tone="warn">
          still says replicas: 0
        </Label>
      </Reveal>
    </Diagram>
  ),

  "operator-loop": ({ step = 0 }) => {
    const replicas = step === 1 ? 0 : 2;
    return (
      <Diagram height={262} step={step}>
        <Box
          x={10}
          y={20}
          w={180}
          h={60}
          title="WorkerPool dispatch"
          sub="spec.replicas: 2"
          tone="focus"
        />
        <Tag
          x={100}
          y={110}
          text={step === 1 ? "Ready: False" : "Ready: True"}
          tone={step === 1 ? "warn" : "good"}
        />
        <Label x={100} y={140} anchor="middle" size="small" tone="muted">
          status, written by the controller
        </Label>
        <Box
          x={230}
          y={20}
          w={190}
          h={60}
          title="workerpool-controller"
          sub="watches and corrects"
        />
        <Box
          x={460}
          y={20}
          w={170}
          h={60}
          title="dispatch-workers"
          sub={`Deployment: replicas ${replicas}`}
          tone={step === 1 ? "warn" : "good"}
        />
        <Arrow
          points={[
            [190, 50],
            [226, 50],
          ]}
        />
        <Arrow
          points={[
            [420, 50],
            [456, 50],
          ]}
          tone={step === 2 ? "good" : "default"}
        />
        <Region x={330} y={120} w={300} h={120} label="Worker Pods" />
        {[0, 1].map((index) => (
          <Box
            key={index}
            x={355 + index * 140}
            y={160}
            w={120}
            h={50}
            title="worker"
            sub={step === 1 ? "terminating" : step === 2 ? "starting" : "ready"}
            tone={step === 1 ? "muted" : step === 2 ? "warn" : "good"}
            dashed={step === 1}
          />
        ))}
        <Reveal from={1} until={1}>
          <Label x={10} y={200} size="small" tone="warn">
            Someone ran kubectl scale on the
          </Label>
          <Label x={10} y={218} size="small" tone="warn">
            Deployment, not the WorkerPool.
          </Label>
        </Reveal>
        <Reveal from={2}>
          <Label x={10} y={200} size="small" tone="good">
            The controller puts the Deployment
          </Label>
          <Label x={10} y={218} size="small" tone="good">
            back to what the WorkerPool says.
          </Label>
        </Reveal>
      </Diagram>
    );
  },
} satisfies Drawings;
