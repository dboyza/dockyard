import {
  Arrow,
  Box,
  Code,
  Cylinder,
  Diagram,
  Label,
  Line,
  Region,
  Reveal,
  Tag,
  Terminal,
  type Tone,
} from "./kit";
import type { Drawings } from "./registry";

export const kubernetes = {
  "k8s-object-chain": () => (
    <Diagram height={262}>
      <Box
        x={20}
        y={20}
        w={170}
        h={56}
        title="Deployment"
        sub="replicas: 2"
        tone="focus"
      />
      <Arrow
        points={[
          [105, 76],
          [105, 108],
        ]}
        label="manages"
        labelAt={[146, 96]}
      />
      <Box
        x={20}
        y={112}
        w={170}
        h={56}
        title="ReplicaSet"
        sub="keeps 2 Pods running"
      />
      <Arrow
        points={[
          [190, 130],
          [256, 98],
        ]}
      />
      <Arrow
        points={[
          [190, 150],
          [256, 178],
        ]}
      />
      <Box
        x={260}
        y={70}
        w={170}
        h={56}
        title="Pod"
        sub="a Dispatch container"
        tone="good"
      />
      <Box
        x={260}
        y={150}
        w={170}
        h={56}
        title="Pod"
        sub="a Dispatch container"
        tone="good"
      />
      <Box
        x={490}
        y={110}
        w={140}
        h={56}
        title="Service"
        sub="stable address"
        tone="focus"
      />
      <Arrow
        points={[
          [490, 130],
          [434, 100],
        ]}
        dashed
        tone="focus"
      />
      <Arrow
        points={[
          [490, 146],
          [434, 176],
        ]}
        dashed
        tone="focus"
      />
      <Label x={560} y={200} anchor="middle" size="small" tone="focus">
        sends requests
      </Label>
      <Label x={320} y={248} anchor="middle" size="small" tone="muted">
        You change the Deployment; Kubernetes creates and replaces the rest.
      </Label>
    </Diagram>
  ),

  "apply-to-running": ({ step = 0 }) => (
    <Diagram height={262} step={step}>
      <Terminal
        x={10}
        y={40}
        w={190}
        lines={
          step === 3
            ? ["$ kubectl rollout …", "successfully rolled out"]
            : ["$ kubectl apply -f …", "deployment configured"]
        }
      />
      <Box
        x={240}
        y={40}
        w={170}
        h={56}
        title="API server"
        sub="stores desired state"
        tone="focus"
      />
      <Box
        x={460}
        y={40}
        w={170}
        h={56}
        title="Deployment controller"
        sub="compares and corrects"
      />
      <Region x={240} y={140} w={390} h={104} label="Node" />
      <Arrow
        points={[
          [200, 68],
          [236, 68],
        ]}
        tone="focus"
      />
      <Reveal from={0} until={0}>
        <Label x={105} y={150} anchor="middle" size="small" tone="warn">
          Accepted, but nothing
        </Label>
        <Label x={105} y={168} anchor="middle" size="small" tone="warn">
          is running yet.
        </Label>
      </Reveal>
      <Reveal from={1} until={2}>
        <Label x={545} y={120} anchor="middle" size="small" tone="focus">
          wants 2, sees 0
        </Label>
      </Reveal>
      <Reveal from={1}>
        <Arrow
          points={[
            [410, 68],
            [456, 68],
          ]}
          tone="focus"
        />
      </Reveal>
      <Reveal from={2}>
        {[0, 1].map((index) => (
          <Box
            key={index}
            x={262 + index * 186}
            y={174}
            w={170}
            h={52}
            title="Pod"
            sub={step >= 3 ? "1/1 ready" : "starting"}
            tone={step >= 3 ? "good" : "warn"}
          />
        ))}
        <Arrow
          points={[
            [325, 96],
            [325, 170],
          ]}
          tone="focus"
          label="creates Pods"
          labelAt={[325, 132]}
        />
      </Reveal>
    </Diagram>
  ),

  "labels-selectors": ({ step = 0 }) => {
    const pods: { y: number; label: string; selected: boolean }[] = [
      { y: 30, label: "app=dispatch", selected: step === 0 },
      { y: 100, label: "app=dispatch", selected: step === 0 },
      { y: 170, label: "app=worker", selected: false },
    ];
    return (
      <Diagram height={262} step={step}>
        <Box
          x={20}
          y={70}
          w={190}
          h={64}
          title="Service: dispatch"
          sub={step === 0 ? "selector app=dispatch" : "selector app=dispach"}
          tone={step === 0 ? "focus" : "bad"}
        />
        <Box
          x={20}
          y={180}
          w={190}
          h={56}
          title="EndpointSlice"
          sub={step === 0 ? "2 ready Pod addresses" : "empty"}
          tone={step === 0 ? "good" : "bad"}
        />
        <Line
          points={[
            [115, 134],
            [115, 180],
          ]}
          dashed
        />
        {pods.map((pod) => (
          <g key={pod.y}>
            <Box
              x={340}
              y={pod.y}
              w={180}
              h={50}
              title="Pod"
              sub={pod.label}
              tone={pod.selected ? "good" : "muted"}
            />
            {pod.selected && (
              <Arrow
                points={[
                  [210, 102],
                  [336, pod.y + 25],
                ]}
                tone="good"
              />
            )}
            <Label
              x={534}
              y={pod.y + 30}
              size="small"
              tone={pod.selected ? "good" : "muted"}
            >
              {pod.selected ? "✓ selected" : "✗ not selected"}
            </Label>
          </g>
        ))}
        <Reveal from={1}>
          <Label x={340} y={252} size="small" tone="bad">
            No Pod has the label app=dispach.
          </Label>
        </Reveal>
      </Diagram>
    );
  },

  namespaces: () => (
    <Diagram height={256}>
      <Region
        x={10}
        y={14}
        w={620}
        h={232}
        label="Cluster, with three namespaces"
      />
      {(
        [
          [30, "dispatch", "focus", "Service dispatch", "your Pods"],
          [230, "staging", "default", "Service dispatch", "same name, allowed"],
          [
            430,
            "kube-system",
            "muted",
            "Kubernetes itself",
            "leave this alone",
          ],
        ] as [number, string, Tone, string, string][]
      ).map(([x, label, tone, title, sub]) => (
        <g key={label}>
          <Region x={x} y={44} w={180} h={128} label={label} tone={tone} />
          <Box
            x={x + 15}
            y={84}
            w={150}
            h={56}
            title={title}
            sub={sub}
            tone={tone}
          />
        </g>
      ))}
      <Box
        x={30}
        y={188}
        w={580}
        h={40}
        title="Nodes and other cluster-wide objects belong to no namespace"
        tone="muted"
        dashed
      />
    </Diagram>
  ),

  "kubeconfig-contexts": () => (
    <Diagram height={250}>
      <Region
        x={10}
        y={14}
        w={620}
        h={200}
        label="kubeconfig, from $KUBECONFIG"
      />
      <Box
        x={30}
        y={44}
        w={170}
        h={46}
        title="cluster"
        sub="where the API is"
      />
      <Box x={30} y={102} w={170} h={46} title="user" sub="how to log in" />
      <Tag x={115} y={176} text="namespace: dispatch" />
      <Arrow
        points={[
          [200, 67],
          [296, 110],
        ]}
      />
      <Arrow
        points={[
          [200, 125],
          [296, 125],
        ]}
      />
      <Arrow
        points={[
          [182, 176],
          [296, 140],
        ]}
      />
      <Box
        x={300}
        y={92}
        w={170}
        h={66}
        title="context"
        sub="cluster + user + namespace"
        tone="focus"
      />
      <Tag x={555} y={125} text="current-context" tone="good" />
      <Arrow
        points={[
          [496, 125],
          [474, 125],
        ]}
        tone="good"
      />
      <Label x={320} y={240} anchor="middle" size="small" tone="muted">
        Every kubectl command goes to the current context.
      </Label>
    </Diagram>
  ),

  "change-workflow": () => {
    const stages: [string, string][] = [
      ["render", "fill in the image"],
      ["diff", "see what changes"],
      ["dry run", "server checks it"],
      ["apply", "saved for real"],
      ["rollout", "Pods are ready"],
    ];
    return (
      <Diagram height={172}>
        {stages.map(([title, sub], index) => (
          <g key={title}>
            <Box
              x={10 + index * 126}
              y={20}
              w={116}
              h={58}
              title={title}
              sub={sub}
              tone={index < 3 ? "good" : index === 3 ? "warn" : "focus"}
            />
            {index > 0 && (
              <Arrow
                points={[
                  [index * 126, 49],
                  [index * 126 + 8, 49],
                ]}
              />
            )}
          </g>
        ))}
        <Line
          points={[
            [12, 92],
            [12, 100],
            [376, 100],
            [376, 92],
          ]}
          tone="good"
        />
        <Label x={194} y={122} anchor="middle" size="small" tone="good">
          nothing changes yet
        </Label>
        <Line
          points={[
            [388, 92],
            [388, 100],
            [630, 100],
            [630, 92],
          ]}
          tone="warn"
        />
        <Label x={509} y={122} anchor="middle" size="small" tone="warn">
          the cluster changes
        </Label>
        <Label x={320} y={160} anchor="middle" size="small" tone="muted">
          Check which context you are using before any of these steps.
        </Label>
      </Diagram>
    );
  },
  "workload-controllers": () => (
    <Diagram height={390}>
      <Region x={10} y={14} w={200} h={170} label="Deployment" tone="focus" />
      {[30, 90, 150].map((x) => (
        <Box key={x} x={x} y={52} w={50} h={30} title="Pod" tone="good" />
      ))}
      <Label x={110} y={124} anchor="middle" size="small">
        interchangeable copies
      </Label>
      <Label x={110} y={142} anchor="middle" size="small" tone="muted">
        as many as you ask for
      </Label>

      <Region x={220} y={14} w={200} h={170} label="DaemonSet" tone="focus" />
      {[236, 326].map((x, index) => (
        <g key={x}>
          <Region x={x} y={42} w={80} h={66} label={`node ${index + 1}`} />
          <Box x={x + 15} y={68} w={50} h={30} title="Pod" tone="good" />
        </g>
      ))}
      <Label x={320} y={142} anchor="middle" size="small">
        one Pod per matching node
      </Label>

      <Region x={430} y={14} w={200} h={170} label="StatefulSet" tone="focus" />
      <Box x={450} y={46} w={74} h={30} title="db-0" tone="good" mono />
      <Box x={536} y={46} w={74} h={30} title="db-1" tone="good" mono />
      <Cylinder x={450} y={86} w={74} h={44} title="data" />
      <Cylinder x={536} y={86} w={74} h={44} title="data" />
      <Label x={530} y={160} anchor="middle" size="small">
        stable names, own storage
      </Label>

      <Region x={10} y={204} w={305} h={170} label="Job" tone="focus" />
      <Box x={40} y={252} w={100} h={44} title="Pod" sub="does the task" />
      <Arrow
        points={[
          [140, 274],
          [190, 274],
        ]}
        tone="good"
      />
      <Tag x={245} y={274} text="Completed" tone="good" />
      <Label x={162} y={338} anchor="middle" size="small">
        runs until it succeeds, then stops
      </Label>

      <Region x={325} y={204} w={305} h={170} label="CronJob" tone="focus" />
      <Tag x={386} y={274} text="0 2 * * *" tone="focus" />
      <Arrow
        points={[
          [428, 274],
          [462, 274],
        ]}
      />
      <Box x={466} y={252} w={70} h={44} title="Job" />
      <Arrow
        points={[
          [536, 274],
          [552, 274],
        ]}
      />
      <Box x={556} y={252} w={60} h={44} title="Pod" />
      <Label x={477} y={338} anchor="middle" size="small">
        creates a new Job on a schedule
      </Label>
    </Diagram>
  ),

  "daemonset-selector": ({ step = 0 }) => (
    <Diagram height={222} step={step}>
      <Box
        x={20}
        y={40}
        w={240}
        h={70}
        title="DaemonSet"
        sub={
          step === 0
            ? "nodeSelector: …/node=missing"
            : "selector matches the node"
        }
        tone={step === 0 ? "bad" : "good"}
      />
      <Tag
        x={140}
        y={140}
        text={step === 0 ? "DESIRED 0" : "DESIRED 1"}
        tone={step === 0 ? "bad" : "good"}
      />
      <Region x={330} y={14} w={300} h={196} label="The lab’s node" />
      <Tag x={480} y={62} text="kubernetes.io/os=linux" />
      <Tag x={480} y={94} text="kubernetes.io/hostname=…" />
      <Arrow
        points={[
          [260, 76],
          [326, 76],
        ]}
        tone={step === 0 ? "bad" : "good"}
        dashed={step === 0}
      />
      <Reveal from={0} until={0}>
        <Label x={480} y={160} anchor="middle" size="small" tone="bad">
          no label matches, so no Pod is placed
        </Label>
      </Reveal>
      <Reveal from={1}>
        <Box
          x={400}
          y={130}
          w={160}
          h={50}
          title="node-agent Pod"
          sub="running"
          tone="good"
        />
      </Reveal>
    </Diagram>
  ),

  "port-forward": () => (
    <Diagram height={222}>
      <Region x={10} y={14} w={260} h={194} label="Your computer" />
      <Terminal x={26} y={44} w={228} lines={["$ curl 127.0.0.1:18080/…"]} />
      <Arrow
        points={[
          [140, 99],
          [140, 126],
        ]}
        tone="focus"
      />
      <Box
        x={26}
        y={130}
        w={228}
        h={56}
        title="kubectl port-forward"
        sub="listens on 18080"
        tone="focus"
      />
      <Region x={300} y={14} w={330} h={194} label="Cluster" tone="focus" />
      <Box
        x={320}
        y={56}
        w={150}
        h={56}
        title="Service dispatch"
        sub="port 8080"
      />
      <Arrow
        points={[
          [470, 84],
          [490, 84],
        ]}
      />
      <Box
        x={494}
        y={56}
        w={120}
        h={56}
        title="Pod"
        sub="API on 8080"
        tone="good"
      />
      <Arrow
        points={[
          [254, 158],
          [395, 158],
          [395, 116],
        ]}
        tone="focus"
        dashed
        label="a temporary tunnel"
        labelAt={[470, 162]}
      />
    </Diagram>
  ),

  "pod-patterns": ({ step = 0 }) => (
    <Diagram height={250} step={step}>
      <Region
        x={10}
        y={14}
        w={620}
        h={226}
        label="One worker Pod"
        tone="focus"
      />
      <Box
        x={30}
        y={50}
        w={170}
        h={56}
        title="configure"
        sub={step === 0 ? "init container: running" : "init: completed"}
        tone={step === 0 ? "focus" : "muted"}
        mono
      />
      <Box
        x={235}
        y={50}
        w={170}
        h={56}
        title="worker"
        sub={step === 0 ? "waiting" : "main container"}
        tone={step === 0 ? "muted" : "good"}
        mono
      />
      <Box
        x={440}
        y={50}
        w={170}
        h={56}
        title="observer"
        sub={step === 0 ? "waiting" : "sidecar"}
        tone={step === 0 ? "muted" : step === 2 ? "bad" : "good"}
        mono
      />
      <Cylinder
        x={235}
        y={150}
        w={170}
        h={70}
        title="shared"
        sub="emptyDir: worker.conf"
        tone="focus"
      />
      <Reveal from={0} until={0}>
        <Arrow
          points={[
            [115, 106],
            [115, 185],
            [231, 185],
          ]}
          tone="focus"
          label="writes worker.conf"
          labelAt={[115, 140]}
        />
      </Reveal>
      <Reveal from={1}>
        <Arrow
          points={[
            [320, 106],
            [320, 146],
          ]}
          tone="good"
        />
      </Reveal>
      <Reveal from={1} until={1}>
        <Arrow
          points={[
            [525, 106],
            [525, 185],
            [409, 185],
          ]}
          tone="good"
        />
      </Reveal>
      <Reveal from={2}>
        <Cylinder
          x={460}
          y={150}
          w={150}
          h={70}
          title="scratch"
          sub="emptyDir: empty"
          tone="muted"
        />
        <Arrow
          points={[
            [535, 106],
            [535, 146],
          ]}
          tone="bad"
        />
        <Label x={115} y={180} anchor="middle" size="small" tone="bad">
          The observer mounts a
        </Label>
        <Label x={115} y={198} anchor="middle" size="small" tone="bad">
          different volume, so it
        </Label>
        <Label x={115} y={216} anchor="middle" size="small" tone="bad">
          cannot see the file.
        </Label>
      </Reveal>
    </Diagram>
  ),

  "job-parallel": () => (
    <Diagram height={250}>
      <Label x={10} y={22} size="small" tone="muted" mono>
        completions: 5 parallelism: 2 backoffLimit: 2
      </Label>
      <Label x={10} y={74} size="small" tone="muted">
        slot 1
      </Label>
      <Label x={10} y={144} size="small" tone="muted">
        slot 2
      </Label>
      {(
        [
          [90, 50, "Pod 1 ✓", "good"],
          [210, 50, "Pod 3 ✓", "good"],
          [330, 50, "Pod 5 ✓", "good"],
          [90, 120, "Pod 2 ✓", "good"],
          [210, 120, "Pod 4 ✗", "bad"],
          [330, 120, "retry ✓", "good"],
        ] as [number, number, string, Tone][]
      ).map(([x, y, title, tone]) => (
        <Box
          key={`${x}-${y}`}
          x={x}
          y={y}
          w={110}
          h={40}
          title={title}
          tone={tone}
        />
      ))}
      <Arrow
        points={[
          [80, 190],
          [460, 190],
        ]}
        tone="muted"
      />
      <Label x={460} y={210} anchor="end" size="small" tone="muted">
        time
      </Label>
      <Tag x={545} y={100} text="5/5 complete" tone="good" />
      <Label x={545} y={130} anchor="middle" size="small" tone="good">
        the Job is Complete
      </Label>
      <Label x={10} y={240} size="small" tone="muted">
        A failed Pod counts toward backoffLimit, and the Job retries with a new
        Pod.
      </Label>
    </Diagram>
  ),

  "cron-runs": () => (
    <Diagram height={232}>
      <Tag x={70} y={24} text="*/5 * * * *" tone="focus" />
      <Label x={140} y={29} size="small" tone="muted">
        every five minutes, with concurrencyPolicy: Forbid
      </Label>
      <Arrow
        points={[
          [40, 160],
          [624, 160],
        ]}
        tone="muted"
      />
      {[80, 220, 360, 500].map((x, index) => (
        <g key={x}>
          <Line
            points={[
              [x, 152],
              [x, 168],
            ]}
          />
          <Label x={x} y={186} anchor="middle" size="small" tone="muted">
            {`02:${String(index * 5).padStart(2, "0")}`}
          </Label>
        </g>
      ))}
      <Box x={80} y={100} w={110} h={40} title="Job ✓" tone="good" />
      <Box
        x={220}
        y={100}
        w={250}
        h={40}
        title="Job, still running"
        tone="warn"
      />
      <Box x={360} y={54} w={110} h={36} title="skipped" tone="muted" dashed />
      <Line
        points={[
          [360, 90],
          [360, 100],
        ]}
        tone="muted"
        dashed
      />
      <Box x={500} y={100} w={110} h={40} title="Job ✓" tone="good" />
      <Label x={10} y={220} size="small" tone="muted">
        kubectl create job --from=cronjob/… starts a run immediately, without
        waiting.
      </Label>
    </Diagram>
  ),
  "configmap-delivery": () => (
    <Diagram height={258}>
      <Label x={10} y={50} size="small" tone="muted">
        ConfigMap dispatch-settings
      </Label>
      <Code
        x={10}
        y={60}
        w={210}
        lines={[
          { text: "environment: learning", tone: "warn" },
          { text: "banner.txt: |", tone: "good" },
          { text: "  Configured through…", tone: "good" },
        ]}
      />
      <Region
        x={270}
        y={14}
        w={360}
        h={228}
        label="API container"
        tone="focus"
      />
      <Box
        x={290}
        y={44}
        w={170}
        h={60}
        title="DISPATCH_ENV"
        sub="env var: read once at start"
        tone="warn"
        mono
      />
      <Box
        x={290}
        y={160}
        w={170}
        h={60}
        title="/config/banner.txt"
        sub="file: kept up to date"
        tone="good"
        mono
      />
      <Arrow
        points={[
          [220, 88],
          [286, 74],
        ]}
        tone="warn"
      />
      <Arrow
        points={[
          [220, 132],
          [286, 190],
        ]}
        tone="good"
      />
      <Box
        x={490}
        y={102}
        w={124}
        h={60}
        title="Dispatch"
        sub="/config shows both"
      />
      <Arrow
        points={[
          [460, 74],
          [520, 98],
        ]}
        tone="muted"
      />
      <Arrow
        points={[
          [460, 190],
          [520, 166],
        ]}
        tone="muted"
      />
    </Diagram>
  ),

  "config-update-timing": ({ step = 0 }) => {
    const changed = step >= 1;
    const restarted = step >= 2;
    return (
      <Diagram height={232} step={step}>
        <Label x={10} y={50} size="small" tone="muted">
          ConfigMap
        </Label>
        <Code
          x={10}
          y={60}
          w={200}
          lines={[
            {
              text: changed ? "environment: testing" : "environment: learning",
              tone: changed ? "focus" : "default",
            },
            {
              text: changed ? "banner: v2" : "banner: v1",
              tone: changed ? "focus" : "default",
            },
          ]}
        />
        <Arrow
          points={[
            [210, 104],
            [256, 104],
          ]}
        />
        <Region
          x={260}
          y={20}
          w={370}
          h={196}
          label={restarted ? "New Pod, after rollout restart" : "Running Pod"}
          tone={restarted ? "good" : "focus"}
        />
        <Box
          x={280}
          y={56}
          w={330}
          h={56}
          title={`DISPATCH_ENV=${restarted ? "testing" : "learning"}`}
          sub={
            changed && !restarted
              ? "still the old value: read only at start"
              : "read when the container starts"
          }
          tone={changed && !restarted ? "warn" : "good"}
          mono
        />
        <Box
          x={280}
          y={132}
          w={330}
          h={56}
          title={`banner.txt: ${changed ? "v2" : "v1"}`}
          sub={
            changed
              ? "updated in place within a minute or two"
              : "a mounted file"
          }
          tone="good"
          mono
        />
      </Diagram>
    );
  },

  "secret-encoding": () => (
    <Diagram height={210}>
      <Box
        x={10}
        y={30}
        w={170}
        h={60}
        title="password: example"
        sub="what you write"
        mono
      />
      <Arrow
        points={[
          [180, 60],
          [231, 60],
        ]}
        label="base64"
        labelAt={[206, 50]}
      />
      <Box
        x={235}
        y={30}
        w={170}
        h={60}
        title="ZXhhbXBsZQ=="
        sub="what the Secret stores"
        tone="warn"
        mono
      />
      <Arrow
        points={[
          [405, 60],
          [456, 60],
        ]}
        tone="bad"
        label="decode"
        labelAt={[431, 50]}
      />
      <Box
        x={460}
        y={30}
        w={170}
        h={60}
        title="example"
        sub="for anyone who can read it"
        tone="bad"
        mono
      />
      <Label x={10} y={140} size="small" tone="muted">
        Encoding is not encryption. Real protection comes from:
      </Label>
      <Tag x={95} y={172} text="who may read Secrets" tone="good" />
      <Tag x={312} y={172} text="encryption at rest" tone="good" />
      <Tag x={528} y={172} text="apps that never log them" tone="good" />
    </Diagram>
  ),

  "projected-volume": () => (
    <Diagram height={232}>
      <Box
        x={10}
        y={30}
        w={190}
        h={60}
        title="Secret"
        sub="dispatch-database: password"
      />
      <Box
        x={10}
        y={130}
        w={190}
        h={60}
        title="ConfigMap"
        sub="dispatch-settings: 2 keys"
      />
      <Arrow
        points={[
          [200, 60],
          [246, 100],
        ]}
      />
      <Arrow
        points={[
          [200, 160],
          [246, 120],
        ]}
      />
      <Box
        x={250}
        y={80}
        w={150}
        h={60}
        title="projected"
        sub="one volume"
        tone="focus"
      />
      <Arrow
        points={[
          [400, 110],
          [436, 110],
        ]}
        tone="focus"
      />
      <Region
        x={440}
        y={20}
        w={190}
        h={180}
        label="/etc/dispatch"
        tone="focus"
      />
      <Tag x={535} y={66} text="password" tone="warn" />
      <Tag x={535} y={110} text="environment" />
      <Tag x={535} y={154} text="banner.txt" />
    </Diagram>
  ),

  "rbac-request": ({ step = 0 }) => {
    const requests: [string, string, Tone][] = [
      ["any request", "", "default"],
      ["list pods in dispatch", "200 OK", "good"],
      ["list secrets in dispatch", "403 Forbidden", "bad"],
      ["list pods in kube-system", "403 Forbidden", "bad"],
    ];
    const [request, result, tone] = requests[step];
    return (
      <Diagram height={286} step={step}>
        <Box
          x={10}
          y={30}
          w={180}
          h={56}
          title="inventory Pod"
          sub="token: dispatch-reader"
        />
        <Tag x={100} y={122} text={request} tone="focus" />
        <Arrow
          points={[
            [190, 58],
            [236, 72],
          ]}
          tone="focus"
        />
        <Region x={220} y={14} w={410} h={222} label="API server" />
        <Box
          x={240}
          y={44}
          w={170}
          h={56}
          title="Authentication"
          sub="who is asking?"
          tone={step === 0 ? "focus" : "good"}
        />
        <Arrow
          points={[
            [410, 72],
            [436, 72],
          ]}
        />
        <Box
          x={440}
          y={44}
          w={170}
          h={56}
          title="Authorization"
          sub="does RBAC allow it?"
          tone={step === 0 ? "default" : tone}
        />
        <Box
          x={236}
          y={150}
          w={124}
          h={56}
          title="ServiceAccount"
          sub="dispatch-reader"
        />
        <Box
          x={370}
          y={150}
          w={116}
          h={56}
          title="RoleBinding"
          sub="in dispatch"
        />
        <Box x={496} y={150} w={120} h={56} title="Role" sub="list pods only" />
        <Line
          points={[
            [370, 178],
            [360, 178],
          ]}
        />
        <Line
          points={[
            [486, 178],
            [496, 178],
          ]}
        />
        <Line
          points={[
            [525, 100],
            [525, 146],
          ]}
          dashed
        />
        <Reveal from={1}>
          <Tag x={100} y={184} text={result} tone={tone} />
          <Label x={100} y={160} anchor="middle" size="small" tone="muted">
            response
          </Label>
        </Reveal>
        <Label x={10} y={264} size="small" tone="muted" mono>
          identity: system:serviceaccount:dispatch:dispatch-reader
        </Label>
      </Diagram>
    );
  },
} satisfies Drawings;
