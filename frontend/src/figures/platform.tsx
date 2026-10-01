import {
  Arrow,
  Box,
  Code,
  Cylinder,
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
  "evidence-types": () => (
    <Diagram height={250}>
      {(
        [
          [10, "Events", "what Kubernetes noticed"],
          [220, "Logs", "what the application said"],
          [430, "Metrics", "how it behaves over time"],
        ] as [number, string, string][]
      ).map(([x, title, sub]) => (
        <g key={title}>
          <Label x={x + 100} y={22} anchor="middle" size="large">
            {title}
          </Label>
          <Label x={x + 100} y={42} anchor="middle" size="small" tone="muted">
            {sub}
          </Label>
        </g>
      ))}
      <Code
        x={10}
        y={56}
        w={200}
        spacing={30}
        lines={[
          { text: "Scheduled  Pod placed" },
          { text: "Pulled     image ready" },
          { text: "Unhealthy  probe failed", tone: "warn" },
        ]}
      />
      <Code
        x={220}
        y={56}
        w={200}
        spacing={30}
        lines={[
          { text: "GET /jobs 200  12ms" },
          { text: "GET /jobs 200  15ms" },
          { text: "GET /jobs 200 640ms", tone: "warn" },
        ]}
      />
      <Box x={430} y={56} w={200} h={106} />
      <Line
        points={[
          [445, 140],
          [490, 136],
          [530, 138],
          [560, 110],
          [590, 78],
          [615, 72],
        ]}
        tone="warn"
      />
      <Label x={445} y={78} size="small" tone="muted">
        response time
      </Label>
      <Label x={320} y={208} anchor="middle" size="small" tone="muted">
        A Pod can be Running, with clean-looking logs, and still serve every
      </Label>
      <Label x={320} y={226} anchor="middle" size="small" tone="muted">
        request slowly. Use all three.
      </Label>
    </Diagram>
  ),

  "prometheus-scrape": () => (
    <Diagram height={262}>
      <Box
        x={10}
        y={14}
        w={170}
        h={50}
        title="Kubernetes API"
        sub="lists the Pods"
      />
      <Arrow
        points={[
          [95, 64],
          [95, 96],
        ]}
        dashed
        tone="muted"
        label="which Pods?"
        labelAt={[140, 86]}
      />
      <Box
        x={10}
        y={100}
        w={170}
        h={60}
        title="Prometheus"
        sub="scrapes every 5 s"
        tone="focus"
      />
      <Arrow
        points={[
          [180, 130],
          [216, 130],
        ]}
      />
      <Box
        x={220}
        y={100}
        w={190}
        h={60}
        title="relabel rules"
        sub="keep app=dispatch, port http"
      />
      <Box
        x={460}
        y={20}
        w={170}
        h={54}
        title="dispatch Pod A"
        sub="kept: pod=A"
        tone="good"
      />
      <Box
        x={460}
        y={103}
        w={170}
        h={54}
        title="dispatch Pod B"
        sub="kept: pod=B"
        tone="good"
      />
      <Box
        x={460}
        y={186}
        w={170}
        h={54}
        title="db Pod"
        sub="dropped"
        tone="muted"
        dashed
      />
      <Arrow
        points={[
          [410, 120],
          [456, 52],
        ]}
        tone="good"
      />
      <Arrow
        points={[
          [410, 130],
          [456, 130],
        ]}
        tone="good"
      />
      <Arrow
        points={[
          [410, 140],
          [456, 206],
        ]}
        tone="muted"
        dashed
      />
      <Label x={10} y={210} size="small" tone="muted">
        Each Pod’s /metrics is scraped
      </Label>
      <Label x={10} y={228} size="small" tone="muted">
        directly and keeps its own pod label.
      </Label>
    </Diagram>
  ),

  "counter-rate": () => (
    <Diagram height={236}>
      <Label x={60} y={16} size="small" tone="muted">
        dispatch_http_requests_total, a counter
      </Label>
      <Line
        points={[
          [60, 100],
          [620, 100],
        ]}
      />
      <Line
        points={[
          [60, 96],
          [330, 30],
          [330, 96],
          [620, 40],
        ]}
        tone="focus"
      />
      <Label x={60} y={128} size="small" tone="muted">
        rate(…[2m]): requests per second
      </Label>
      <Line
        points={[
          [60, 204],
          [620, 204],
        ]}
      />
      <Line
        points={[
          [60, 168],
          [620, 168],
        ]}
        tone="good"
      />
      <Line
        points={[
          [330, 22],
          [330, 208],
        ]}
        dashed
      />
      <Label x={620} y={226} anchor="end" size="small" tone="muted">
        the Pod restarted: its counter reset to 0, but the rate holds steady
      </Label>
    </Diagram>
  ),

  "histogram-buckets": () => {
    const buckets: [string, number][] = [
      ["≤ 0.1 s", 120],
      ["≤ 0.25 s", 170],
      ["≤ 0.5 s", 190],
      ["≤ 1 s", 198],
      ["all", 200],
    ];
    return (
      <Diagram height={260}>
        {buckets.map(([name, count], index) => {
          const height = count * 0.8;
          const x = 30 + index * 78;
          return (
            <g key={name}>
              <Box
                x={x}
                y={210 - height}
                w={60}
                h={height}
                tone={index === 1 ? "focus" : index === 4 ? "default" : "muted"}
              />
              <Label
                x={x + 30}
                y={204 - height}
                anchor="middle"
                size="small"
                mono
              >
                {String(count)}
              </Label>
              <Label
                x={x + 30}
                y={230}
                anchor="middle"
                size="small"
                tone="muted"
              >
                {name}
              </Label>
            </g>
          );
        })}
        <Label x={30} y={252} size="small" tone="muted">
          Each bucket counts every request at or under its limit.
        </Label>
        <Label x={440} y={70}>
          fast enough
        </Label>
        <Label x={440} y={90} size="small" tone="focus" mono>
          170 ÷ 200 = 85%
        </Label>
        <Label x={440} y={124}>
          too slow
        </Label>
        <Label x={440} y={144} size="small" tone="bad" mono>
          1 − 0.85 = 15%
        </Label>
        <Tag x={520} y={180} text="15% > 10%: alert" tone="bad" />
      </Diagram>
    );
  },

  "alert-states": () => (
    <Diagram height={226}>
      <Label x={10} y={70} size="small" tone="muted">
        condition
      </Label>
      <Label x={10} y={130} size="small" tone="muted">
        alert
      </Label>
      <Box x={80} y={50} w={90} h={32} title="no" tone="muted" />
      <Box
        x={170}
        y={50}
        w={370}
        h={32}
        title="slow fraction above 10%"
        tone="warn"
      />
      <Box x={540} y={50} w={80} h={32} title="no" tone="muted" />
      <Box x={80} y={110} w={90} h={32} title="inactive" tone="muted" />
      <Box
        x={170}
        y={110}
        w={160}
        h={32}
        title="pending: for 15 s"
        tone="warn"
      />
      <Box x={330} y={110} w={210} h={32} title="firing" tone="bad" />
      <Box x={540} y={110} w={80} h={32} title="resolved" tone="good" />
      <Arrow
        points={[
          [80, 172],
          [624, 172],
        ]}
        tone="muted"
      />
      {(
        [
          [170, "slowdown starts"],
          [330, "+15 s"],
          [540, "speed restored"],
        ] as [number, string][]
      ).map(([x, text]) => (
        <g key={text}>
          <Line
            points={[
              [x, 164],
              [x, 180],
            ]}
          />
          <Label x={x} y={198} anchor="middle" size="small" tone="muted">
            {text}
          </Label>
        </g>
      ))}
    </Diagram>
  ),

  "error-budget": () => (
    <Diagram height={232}>
      {Array.from({ length: 200 }, (_, index) => {
        const column = index % 20;
        const row = Math.floor(index / 20);
        const bad = index >= 190;
        return (
          <g key={index} className={`fig-box tone-${bad ? "warn" : "good"}`}>
            <rect
              x={20 + column * 18}
              y={30 + row * 18}
              width={14}
              height={14}
              rx={3}
            />
          </g>
        );
      })}
      <Label x={20} y={20} size="small" tone="muted">
        200 eligible GET /jobs reads
      </Label>
      <Label x={410} y={60}>
        objective: 95% good
      </Label>
      <Label x={410} y={84} size="small" tone="muted">
        so at most 10 may be bad
      </Label>
      <Tag x={500} y={124} text="error budget: 10 reads" tone="warn" />
      <Label x={410} y={168} size="small" tone="muted">
        A read is bad if it fails, or if it
      </Label>
      <Label x={410} y={186} size="small" tone="muted">
        succeeds but takes over 250 ms.
      </Label>
    </Diagram>
  ),
  "pipeline-gate": ({ step = 0 }) => {
    const stages: [string, string, Tone, boolean][][] = [
      [
        ["build", "image built", "good", false],
        ["test", "skipped", "muted", true],
        ["push", "pushed anyway", "bad", false],
        ["record", "digest recorded", "bad", false],
      ],
      [
        ["build", "image built", "good", false],
        ["test", "FAIL, exit 1", "bad", false],
        ["push", "not run", "muted", true],
        ["record", "not run", "muted", true],
      ],
      [
        ["build", "image built", "good", false],
        ["test", "OK, exit 0", "good", false],
        ["push", "pushed", "good", false],
        ["record", "release.json", "good", false],
      ],
    ];
    const footer: [string, Tone][] = [
      ["With tests switched off, anything that builds is published.", "bad"],
      ["A failing test stops every step after it.", "good"],
      ["release.json names the exact image digest that passed.", "good"],
    ];
    return (
      <Diagram height={190} step={step}>
        {stages[step].map(([title, sub, tone, dashed], index) => (
          <g key={title}>
            <Box
              x={10 + index * 160}
              y={50}
              w={140}
              h={60}
              title={title}
              sub={sub}
              tone={tone}
              dashed={dashed}
            />
            {index > 0 && (
              <Arrow
                points={[
                  [index * 160 - 10, 80],
                  [index * 160 + 6, 80],
                ]}
                tone={dashed ? "muted" : "default"}
              />
            )}
          </g>
        ))}
        <Label x={170 + 70} y={36} anchor="middle" size="small" tone="focus">
          the gate
        </Label>
        <Label
          x={320}
          y={160}
          anchor="middle"
          size="small"
          tone={footer[step][1]}
        >
          {footer[step][0]}
        </Label>
      </Diagram>
    );
  },

  "gitops-loop": () => (
    <Diagram height={272}>
      <Box x={10} y={20} w={150} h={56} title="You" sub="commit and push" />
      <Arrow
        points={[
          [160, 48],
          [216, 48],
        ]}
        label="push"
        labelAt={[188, 40]}
      />
      <Cylinder
        x={220}
        y={12}
        w={180}
        h={72}
        title="Git: delivery"
        sub="the desired state"
        tone="focus"
      />
      <Arrow
        points={[
          [400, 48],
          [446, 48],
        ]}
        label="fetch"
        labelAt={[423, 40]}
      />
      <Box
        x={450}
        y={20}
        w={180}
        h={56}
        title="Flux"
        sub="builds and applies"
      />
      <Arrow
        points={[
          [540, 76],
          [540, 126],
        ]}
        tone="good"
        label="applies as dispatch-deployer"
        labelAt={[540, 104]}
      />
      <Region x={300} y={130} w={330} h={120} label="Cluster: dispatch" />
      <Box
        x={330}
        y={170}
        w={270}
        h={52}
        title="Deployment dispatch"
        sub="matches what Git declares"
        tone="good"
      />
      <Box
        x={10}
        y={150}
        w={210}
        h={56}
        title="kubectl, by hand"
        sub="a change Git does not know"
        tone="warn"
      />
      <Arrow
        points={[
          [220, 178],
          [326, 196],
        ]}
        tone="warn"
        dashed
      />
      <Label x={115} y={234} anchor="middle" size="small" tone="warn">
        undone on Flux’s next pass
      </Label>
    </Diagram>
  ),

  "promotion-flow": ({ step = 0 }) => {
    const commits: [string, Tone][] = [
      ["a1  dev → sha256:7c9…", "default"],
      ["b2  staging → sha256:7c9…", "default"],
      ["c3  staging → missing:v9", "bad"],
      ["d4  Revert c3", "good"],
    ];
    const staging: [string, Tone][] = [
      ["the previous release: ready", "default"],
      ["sha256:7c9…: the same image, ready", "good"],
      ["new Pod cannot pull; old Pod still serving", "warn"],
      ["sha256:7c9…: ready again", "good"],
    ];
    return (
      <Diagram height={250} step={step}>
        <Region x={10} y={14} w={240} h={220} label="Git history in delivery" />
        {commits.slice(0, step + 1).map(([text, tone], index) => (
          <Label key={text} x={26} y={60 + index * 34} tone={tone} mono>
            {text}
          </Label>
        ))}
        <Arrow
          points={[
            [250, 124],
            [276, 124],
          ]}
          label="Flux"
          labelAt={[263, 112]}
        />
        <Box
          x={280}
          y={40}
          w={350}
          h={70}
          title="development"
          sub="sha256:7c9…: ready"
          tone="good"
        />
        <Box
          x={280}
          y={140}
          w={350}
          h={70}
          title="staging"
          sub={staging[step][0]}
          tone={staging[step][1]}
        />
      </Diagram>
    );
  },
  "rbac-scope": () => {
    const rows: [string, string, [string, Tone][]][] = [
      [
        "Role + RoleBinding",
        "rules and grant in one namespace",
        [
          ["✓", "good"],
          ["✗", "muted"],
          ["✗", "muted"],
        ],
      ],
      [
        "ClusterRole + RoleBinding",
        "shared rules, granted in one namespace",
        [
          ["✓", "good"],
          ["✗", "muted"],
          ["✗", "muted"],
        ],
      ],
      [
        "ClusterRole + ClusterRoleBinding",
        "granted across the whole cluster",
        [
          ["✓", "warn"],
          ["✓", "warn"],
          ["✓", "warn"],
        ],
      ],
    ];
    return (
      <Diagram height={262}>
        {["dispatch", "other namespaces", "nodes, PVs"].map((name, index) => (
          <Label
            key={name}
            x={400 + index * 100}
            y={24}
            anchor="middle"
            size="small"
            tone="muted"
          >
            {name}
          </Label>
        ))}
        {rows.map(([title, sub, reach], row) => (
          <g key={title}>
            <Box
              x={10}
              y={40 + row * 74}
              w={300}
              h={58}
              title={title}
              sub={sub}
            />
            {reach.map(([mark, tone], index) => (
              <Tag
                key={index}
                x={400 + index * 100}
                y={69 + row * 74}
                text={mark}
                tone={tone}
              />
            ))}
          </g>
        ))}
      </Diagram>
    );
  },

  "least-privilege": ({ step = 0 }) => {
    const answers: [string, string, Tone][][] = [
      [
        ["list pods in dispatch", "yes", "good"],
        ["get secrets in dispatch", "yes", "bad"],
        ["list pods in kube-system", "no", "good"],
      ],
      [
        ["list pods in dispatch", "yes", "good"],
        ["get secrets in dispatch", "no", "good"],
        ["list pods in kube-system", "no", "good"],
      ],
    ];
    return (
      <Diagram height={222} step={step}>
        <Label x={10} y={22} size="small" tone="muted">
          Role dispatch-pod-reader
        </Label>
        <Code
          x={10}
          y={32}
          w={280}
          lines={[
            { text: "rules:" },
            {
              text:
                step === 0
                  ? "- resources: [pods, secrets]"
                  : "- resources: [pods]",
              tone: step === 0 ? "warn" : "good",
            },
            { text: "  verbs: [get, list, watch]" },
          ]}
        />
        <Label x={330} y={22} size="small" tone="muted">
          kubectl auth can-i … as dispatch-reader
        </Label>
        {answers[step].map(([question, answer, tone], index) => (
          <g key={question}>
            <Label x={330} y={60 + index * 34}>
              {question}
            </Label>
            <Tag x={600} y={56 + index * 34} text={answer} tone={tone} />
          </g>
        ))}
        <Label x={10} y={196} size="small" tone={step === 0 ? "bad" : "good"}>
          {step === 0
            ? "The Pod reader can also read every Secret in the namespace."
            : "The useful read still works; the unneeded one is refused."}
        </Label>
      </Diagram>
    );
  },

  "netpol-default-deny": ({ step = 0 }) => {
    const edges: [string, [number, number][], boolean][] = [
      [
        "trusted → API",
        [
          [140, 70],
          [186, 82],
        ],
        true,
      ],
      [
        "untrusted → API",
        [
          [140, 130],
          [186, 98],
        ],
        false,
      ],
      [
        "API → PostgreSQL",
        [
          [310, 80],
          [476, 80],
        ],
        true,
      ],
      [
        "worker → Redis",
        [
          [310, 205],
          [476, 205],
        ],
        true,
      ],
      [
        "worker → DNS",
        [
          [190, 222],
          [144, 232],
        ],
        true,
      ],
    ];
    const footer: [string, Tone][] = [
      ["No policy: every Pod can reach every other Pod.", "muted"],
      ["Default deny: nothing connects, not even DNS lookups.", "bad"],
      [
        "Only the listed paths are allowed; everything else stays blocked.",
        "good",
      ],
    ];
    return (
      <Diagram height={286} step={step}>
        <Region x={10} y={14} w={130} h={156} label="frontend" />
        <Box x={22} y={50} w={106} h={40} title="trusted" />
        <Box x={22} y={110} w={106} h={40} title="untrusted" />
        <Box x={10} y={206} w={130} h={48} title="DNS" sub="kube-system" />
        <Region x={160} y={14} w={470} h={250} label="dispatch" tone="focus" />
        <Box x={190} y={60} w={120} h={50} title="API" />
        <Box x={190} y={186} w={120} h={50} title="worker" />
        <Cylinder x={480} y={44} w={130} h={72} title="PostgreSQL" />
        <Box x={480} y={182} w={130} h={50} title="Redis" />
        {edges.map(([name, points, allowed]) => (
          <Arrow
            key={name}
            points={points}
            tone={step === 0 ? "muted" : step === 2 && allowed ? "good" : "bad"}
            dashed={step === 1 || (step === 2 && !allowed)}
          />
        ))}
        <Label
          x={320}
          y={280}
          anchor="middle"
          size="small"
          tone={footer[step][1]}
        >
          {footer[step][0]}
        </Label>
      </Diagram>
    );
  },

  "netpol-and-or": () => (
    <Diagram height={262}>
      {(
        [
          [10, "One list item: both must match", "  podSelector:", "focus"],
          [330, "Two list items: either is enough", "- podSelector:", "warn"],
        ] as [number, string, string, Tone][]
      ).map(([x, heading, pod, tone]) => (
        <g key={heading}>
          <Label x={x} y={20} size="small" tone={tone}>
            {heading}
          </Label>
          <Code
            x={x}
            y={30}
            w={300}
            spacing={26}
            lines={[
              { text: "from:" },
              { text: "- namespaceSelector:" },
              { text: "    matchLabels: {…: frontend}" },
              { text: pod, tone },
              { text: "    matchLabels: {app: trusted}" },
            ]}
          />
        </g>
      ))}
      <Tag x={160} y={198} text="trusted Pod in frontend: ✓" tone="good" />
      <Tag x={160} y={230} text="any other Pod: ✗" tone="good" />
      <Tag x={480} y={198} text="any Pod in frontend: ✓" tone="warn" />
      <Tag x={480} y={230} text="trusted Pod anywhere here: ✓" tone="warn" />
    </Diagram>
  ),

  "admission-vs-context": () => (
    <Diagram height={286}>
      <Label x={315} y={22} anchor="middle" size="small" tone="muted">
        checked once, when the Pod is created
      </Label>
      <Box
        x={10}
        y={42}
        w={150}
        h={60}
        title="new Pod"
        sub="from a Deployment"
      />
      <Arrow
        points={[
          [160, 72],
          [206, 72],
        ]}
      />
      <Box
        x={210}
        y={34}
        w={210}
        h={76}
        title="Pod Security Admission"
        sub="namespace enforces restricted"
        tone="focus"
      />
      <Arrow
        points={[
          [420, 72],
          [456, 72],
        ]}
        tone="good"
      />
      <Tag x={535} y={72} text="accepted: created" tone="good" />
      <Arrow
        points={[
          [315, 110],
          [315, 128],
        ]}
        tone="bad"
      />
      <Tag x={315} y={140} text="rejected: never runs" tone="bad" />
      <Arrow
        points={[
          [535, 84],
          [535, 156],
        ]}
        tone="good"
      />
      <Region
        x={10}
        y={160}
        w={620}
        h={110}
        label="The running container’s securityContext, for its whole life"
        tone="good"
      />
      {(
        [
          [110, 204, "runAsUser 12000"],
          [320, 204, "capabilities: none"],
          [530, 204, "no new privileges"],
          [215, 240, "seccomp: RuntimeDefault"],
          [425, 240, "read-only root filesystem"],
        ] as [number, number, string][]
      ).map(([x, y, text]) => (
        <Tag key={text} x={x} y={y} text={text} tone="good" />
      ))}
    </Diagram>
  ),
} satisfies Drawings;
