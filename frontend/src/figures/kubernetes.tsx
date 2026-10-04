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
        sub="used to pick one Pod"
        tone="muted"
        dashed
      />
      <Arrow
        points={[
          [470, 84],
          [490, 84],
        ]}
        tone="muted"
        dashed
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
          [554, 158],
          [554, 116],
        ]}
        tone="focus"
        dashed
        label="a temporary tunnel to that Pod"
        labelAt={[424, 150]}
      />
      <Label x={465} y={192} anchor="middle" size="small" tone="muted">
        Requests do not pass through the Service.
      </Label>
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
  "service-types": () => (
    <Diagram height={286}>
      <Region x={190} y={14} w={440} h={256} label="Cluster" tone="focus" />
      <Box
        x={210}
        y={40}
        w={150}
        h={44}
        title="another Pod"
        sub="inside the cluster"
      />
      <Box x={10} y={120} w={110} h={46} title="your computer" />
      <Box x={10} y={200} w={110} h={46} title="outside client" />
      <Tag x={190} y={143} text="node:30080" />
      <Tag x={190} y={223} text="LB IP:8080" />
      <Arrow
        points={[
          [120, 143],
          [144, 143],
        ]}
      />
      <Arrow
        points={[
          [120, 223],
          [144, 223],
        ]}
      />
      <Box
        x={400}
        y={110}
        w={120}
        h={60}
        title="Service"
        sub="dispatch"
        tone="focus"
      />
      <Arrow
        points={[
          [360, 62],
          [420, 106],
        ]}
        label="ClusterIP"
        labelAt={[420, 70]}
      />
      <Arrow
        points={[
          [236, 143],
          [396, 143],
        ]}
        label="NodePort"
        labelAt={[316, 135]}
      />
      <Arrow
        points={[
          [236, 223],
          [460, 223],
          [460, 174],
        ]}
        label="LoadBalancer"
        labelAt={[350, 215]}
      />
      <Box x={548} y={80} w={70} h={40} title="Pod" tone="good" />
      <Box x={548} y={160} w={70} h={40} title="Pod" tone="good" />
      <Arrow
        points={[
          [520, 130],
          [544, 104],
        ]}
        tone="muted"
      />
      <Arrow
        points={[
          [520, 150],
          [544, 176],
        ]}
        tone="muted"
      />
      <Label x={410} y={262} anchor="middle" size="small" tone="muted">
        Each type builds on the one before it.
      </Label>
    </Diagram>
  ),

  "service-ports": ({ step = 0 }) => (
    <Diagram height={236} step={step}>
      <Box x={10} y={80} w={120} h={56} title="client" sub="connects to 8080" />
      <Arrow
        points={[
          [130, 108],
          [176, 108],
        ]}
        label="port"
        labelAt={[153, 100]}
      />
      <Box
        x={180}
        y={70}
        w={180}
        h={76}
        title="Service"
        sub={
          step === 0
            ? "port 8080, targetPort 8080"
            : "port 8080, targetPort 9090"
        }
        tone={step === 0 ? "focus" : "bad"}
      />
      <Arrow
        points={[
          [360, 108],
          [376, 108],
        ]}
        tone={step === 0 ? "good" : "bad"}
      />
      <Region x={400} y={30} w={230} h={170} label="Pod" />
      <Tag
        x={400}
        y={108}
        text={step === 0 ? "8080" : "9090"}
        tone={step === 0 ? "good" : "bad"}
      />
      <Box
        x={440}
        y={80}
        w={170}
        h={56}
        title="Dispatch"
        sub="listens on 8080"
        tone="good"
      />
      <Reveal from={1}>
        <Label x={320} y={226} anchor="middle" size="small" tone="bad">
          Endpoints still exist, but every connection to 9090 is refused.
        </Label>
      </Reveal>
    </Diagram>
  ),

  "ingress-routing": () => (
    <Diagram height={262}>
      <Box
        x={10}
        y={96}
        w={170}
        h={56}
        title="Your client"
        sub="https://dispatch.test/"
      />
      <Box
        x={215}
        y={10}
        w={200}
        h={50}
        title="Ingress rules"
        sub="dispatch.test/ → dispatch:8080"
      />
      <Box
        x={230}
        y={92}
        w={170}
        h={64}
        title="Traefik"
        sub="the ingress controller"
        tone="focus"
      />
      <Box
        x={230}
        y={196}
        w={170}
        h={50}
        title="Secret dispatch-tls"
        sub="tls.crt and tls.key"
        tone="warn"
      />
      <Arrow
        points={[
          [315, 60],
          [315, 88],
        ]}
        dashed
        label="reads"
        labelAt={[350, 78]}
      />
      <Arrow
        points={[
          [315, 196],
          [315, 160],
        ]}
        dashed
        tone="warn"
        label="certificate"
        labelAt={[362, 182]}
      />
      <Arrow
        points={[
          [180, 124],
          [226, 124],
        ]}
        tone="focus"
        label="HTTPS"
        labelAt={[203, 116]}
      />
      <Arrow
        points={[
          [400, 124],
          [456, 124],
        ]}
        tone="good"
        label="HTTP"
        labelAt={[428, 116]}
      />
      <Box
        x={460}
        y={96}
        w={170}
        h={56}
        title="Service dispatch"
        sub="port 8080, then Pods"
        tone="good"
      />
    </Diagram>
  ),

  "tls-checks": ({ step = 0 }) => {
    const rows: [string, string, Tone][][] = [
      [
        ["Issued by someone trusted?", "yes, --cacert", "good"],
        ["For the hostname requested?", "yes, dispatch.test", "good"],
      ],
      [
        ["Issued by someone trusted?", "no: unknown issuer", "bad"],
        ["For the hostname requested?", "not reached", "muted"],
      ],
      [
        ["Issued by someone trusted?", "skipped", "warn"],
        ["For the hostname requested?", "skipped", "warn"],
      ],
    ];
    const outcomes: [string, Tone][] = [
      ["Both checks pass, so the request continues.", "good"],
      ["curl refuses to continue.", "bad"],
      ["Encrypted, but you no longer know who answered.", "warn"],
    ];
    return (
      <Diagram height={240} step={step}>
        <Box
          x={10}
          y={20}
          w={170}
          h={56}
          title="curl"
          sub={
            step === 2
              ? "with --insecure"
              : step === 1
                ? "no --cacert"
                : "with --cacert"
          }
          tone="focus"
          mono
        />
        <Arrow
          points={[
            [180, 48],
            [226, 48],
          ]}
          tone="muted"
        />
        <Box
          x={230}
          y={20}
          w={180}
          h={56}
          title="certificate"
          sub="dispatch.test, practice CA"
          tone="warn"
        />
        <Arrow
          points={[
            [456, 48],
            [414, 48],
          ]}
          tone="muted"
        />
        <Box x={460} y={20} w={170} h={56} title="Traefik" sub="presents it" />
        {rows[step].map(([question, answer, tone], index) => (
          <g key={question}>
            <Label x={20} y={128 + index * 40}>
              {`${index + 1}. ${question}`}
            </Label>
            <Tag x={430} y={124 + index * 40} text={answer} tone={tone} />
          </g>
        ))}
        <Label x={20} y={222} size="small" tone={outcomes[step][1]}>
          {outcomes[step][0]}
        </Label>
      </Diagram>
    );
  },

  "gateway-api": ({ step = 0 }) => {
    const conditions: [string, string, Tone][] =
      step === 0
        ? [
            ["Accepted", "True", "good"],
            ["ResolvedRefs", "True", "good"],
            ["Programmed", "True", "good"],
          ]
        : [
            ["Accepted", "True", "good"],
            ["ResolvedRefs", "False: no port 9090", "bad"],
            ["Programmed", "True", "good"],
          ];
    return (
      <Diagram height={298} step={step}>
        <Box
          x={10}
          y={30}
          w={170}
          h={56}
          title="GatewayClass"
          sub="traefik: admins"
        />
        <Box
          x={230}
          y={30}
          w={180}
          h={56}
          title="Gateway"
          sub="listener :8080: platform"
        />
        <Box
          x={460}
          y={30}
          w={170}
          h={56}
          title="HTTPRoute"
          sub="app team"
          tone="focus"
        />
        <Arrow
          points={[
            [230, 58],
            [184, 58],
          ]}
          label="class"
          labelAt={[207, 50]}
        />
        <Arrow
          points={[
            [460, 58],
            [414, 58],
          ]}
          tone={step === 1 ? "bad" : "good"}
          dashed={step === 1}
          label="parentRefs"
          labelAt={[437, 108]}
        />
        <Arrow
          points={[
            [545, 86],
            [545, 150],
          ]}
          tone={step === 2 ? "bad" : "good"}
          label="backendRefs"
          labelAt={[545, 122]}
        />
        <Box
          x={460}
          y={154}
          w={170}
          h={56}
          title="Service dispatch"
          sub="port 8080"
        />
        <Region
          x={10}
          y={130}
          w={410}
          h={150}
          label="HTTPRoute status, under Parents"
        />
        {step === 1 ? (
          <>
            <Label x={30} y={200} tone="bad">
              No entry at all: parentRefs names a
            </Label>
            <Label x={30} y={222} tone="bad">
              Gateway that does not exist.
            </Label>
          </>
        ) : (
          conditions.map(([name, value, tone], index) => (
            <g key={name}>
              <Label x={30} y={180 + index * 34} mono>
                {name}
              </Label>
              <Tag x={300} y={176 + index * 34} text={value} tone={tone} />
            </g>
          ))
        )}
      </Diagram>
    );
  },
  "storage-chain": () => {
    const steps: [number, number, string, string, Tone][] = [
      [10, 30, "PostgreSQL", "writes its data folder", "good"],
      [230, 30, "volumeMounts", "container: mount data there", "default"],
      [450, 30, "volumes", "Pod: data uses the claim", "default"],
      [450, 150, "PersistentVolumeClaim", "the request, in dispatch", "focus"],
      [230, 150, "PersistentVolume", "real storage, cluster-wide", "default"],
      [10, 150, "Disk on the node", "where the bytes live", "default"],
    ];
    return (
      <Diagram height={316}>
        {steps.map(([x, y, title, sub, tone]) => (
          <Box
            key={title}
            x={x}
            y={y}
            w={180}
            h={64}
            title={title}
            sub={sub}
            tone={tone}
          />
        ))}
        <Arrow
          points={[
            [190, 62],
            [226, 62],
          ]}
        />
        <Arrow
          points={[
            [410, 62],
            [446, 62],
          ]}
        />
        <Arrow
          points={[
            [540, 94],
            [540, 146],
          ]}
          label="claimName"
          labelAt={[540, 124]}
        />
        <Arrow
          points={[
            [450, 182],
            [414, 182],
          ]}
          tone="good"
          label="Bound"
          labelAt={[432, 174]}
        />
        <Arrow
          points={[
            [230, 182],
            [194, 182],
          ]}
        />
        <Box
          x={230}
          y={250}
          w={180}
          h={54}
          title="StorageClass"
          sub="standard: creates PVs"
          dashed
        />
        <Arrow
          points={[
            [320, 250],
            [320, 218],
          ]}
          dashed
          label="provisions"
          labelAt={[366, 238]}
        />
      </Diagram>
    );
  },

  "wait-first-consumer": ({ step = 0 }) => (
    <Diagram height={250} step={step}>
      <Box
        x={10}
        y={40}
        w={190}
        h={60}
        title="PVC dispatch-data"
        sub={step === 3 ? "Bound" : "Pending"}
        tone={step === 3 ? "good" : "warn"}
      />
      <Tag x={105} y={130} text="WaitForFirstConsumer" />
      <Region x={260} y={14} w={370} h={222} label="Node" />
      <Reveal from={1}>
        <Box
          x={290}
          y={44}
          w={170}
          h={56}
          title="db Pod"
          sub={step === 3 ? "running" : "scheduled here"}
          tone={step === 3 ? "good" : "focus"}
        />
        <Arrow
          points={[
            [290, 72],
            [204, 72],
          ]}
          dashed
          label="uses"
          labelAt={[247, 64]}
        />
      </Reveal>
      <Reveal from={2}>
        <Cylinder
          x={290}
          y={140}
          w={170}
          h={74}
          title="PersistentVolume"
          sub="created on this node"
          tone={step === 3 ? "good" : "focus"}
        />
      </Reveal>
      <Reveal from={3}>
        <Arrow
          points={[
            [200, 92],
            [286, 170],
          ]}
          tone="good"
          label="Bound"
          labelAt={[230, 146]}
        />
      </Reveal>
    </Diagram>
  ),

  "statefulset-identity": ({ step = 0 }) => (
    <Diagram height={272} step={step}>
      <Box
        x={10}
        y={20}
        w={200}
        h={56}
        title="StatefulSet db"
        sub="replicas: 1"
        tone="focus"
      />
      <Box
        x={430}
        y={20}
        w={200}
        h={56}
        title="Service db-headless"
        sub="clusterIP: None"
      />
      <Label x={530} y={98} anchor="middle" size="small" tone="muted" mono>
        db-0.db-headless.dispatch…
      </Label>
      <Arrow
        points={[
          [110, 76],
          [230, 110],
        ]}
      />
      <Box
        x={220}
        y={110}
        w={200}
        h={56}
        title="db-0"
        sub={
          step === 0
            ? "UID 4c1e…"
            : step === 1
              ? "deleted"
              : "UID 9a7f…, a new Pod"
        }
        tone={step === 1 ? "muted" : step === 2 ? "good" : "default"}
        dashed={step === 1}
        mono
      />
      <Arrow
        points={[
          [530, 106],
          [424, 132],
        ]}
        dashed
        tone="muted"
      />
      <Line
        points={[
          [320, 166],
          [320, 190],
        ]}
      />
      <Cylinder
        x={220}
        y={190}
        w={200}
        h={70}
        title="data-db-0"
        sub={step === 1 ? "kept while db-0 is gone" : "claim for db-0"}
        tone="focus"
      />
    </Diagram>
  ),

  "independent-restore": () => (
    <Diagram height={262}>
      <Box
        x={10}
        y={30}
        w={170}
        h={56}
        title="db-0"
        sub="the source"
        tone="good"
        mono
      />
      <Cylinder x={10} y={112} w={170} h={60} title="data-db-0" />
      <Line
        points={[
          [95, 86],
          [95, 112],
        ]}
      />
      <Box
        x={460}
        y={30}
        w={170}
        h={56}
        title="db-restore-0"
        sub="the restore target"
        tone="focus"
        mono
      />
      <Cylinder x={460} y={112} w={170} h={60} title="data-db-restore-0" />
      <Line
        points={[
          [545, 86],
          [545, 112],
        ]}
      />
      <File x={307} y={40} name="dispatch.sql" tone="focus" />
      <Label x={320} y={110} anchor="middle" size="small" tone="muted">
        on your computer
      </Label>
      <Arrow
        points={[
          [180, 58],
          [298, 58],
        ]}
        tone="focus"
        label="pg_dump"
        labelAt={[239, 50]}
      />
      <Arrow
        points={[
          [342, 58],
          [456, 58],
        ]}
        tone="focus"
        label="psql"
        labelAt={[399, 50]}
      />
      <Label x={320} y={206} anchor="middle" size="small" tone="muted">
        Separate claims and volumes, so a bad restore cannot harm the source.
      </Label>
      <Tag
        x={320}
        y={238}
        text="--schema-only: tables, but no rows"
        tone="bad"
      />
    </Diagram>
  ),
  "probe-roles": ({ step = 0 }) => {
    const probes: [string, string][] = [
      ["startup probe", "/startupz"],
      ["liveness probe", step === 3 ? "/readyz (wrong)" : "/healthz"],
      ["readiness probe", "/readyz"],
    ];
    const states: [string, Tone][][] = [
      [
        ["checking: warming up", "warn"],
        ["waits for startup", "muted"],
        ["waits for startup", "muted"],
      ],
      [
        ["passed", "good"],
        ["passing", "good"],
        ["passing", "good"],
      ],
      [
        ["passed", "good"],
        ["passing", "good"],
        ["failing: no database", "warn"],
      ],
      [
        ["passed", "good"],
        ["failing: restarts", "bad"],
        ["failing: no database", "warn"],
      ],
    ];
    const endpoints: [string, Tone][] = [
      ["not included yet", "muted"],
      ["included", "good"],
      ["removed until ready", "warn"],
      ["removed", "warn"],
    ];
    const restarts: [string, Tone][] = [
      ["0", "default"],
      ["0", "default"],
      ["0: nothing restarts", "good"],
      ["climbing", "bad"],
    ];
    return (
      <Diagram height={238} step={step}>
        {probes.map(([name, path], index) => (
          <g key={name}>
            <Label x={20} y={50 + index * 64}>
              {name}
            </Label>
            <Label x={20} y={70 + index * 64} size="small" tone="muted" mono>
              {path}
            </Label>
            <Tag
              x={320}
              y={56 + index * 64}
              text={states[step][index][0]}
              tone={states[step][index][1]}
            />
          </g>
        ))}
        <Box
          x={460}
          y={34}
          w={170}
          h={60}
          title="Service endpoints"
          sub={endpoints[step][0]}
          tone={endpoints[step][1]}
        />
        <Box
          x={460}
          y={142}
          w={170}
          h={60}
          title="Restarts"
          sub={restarts[step][0]}
          tone={restarts[step][1]}
        />
      </Diagram>
    );
  },

  "rolling-update": ({ step = 0 }) => {
    const plan: { old: string[]; next: string[] }[] = [
      { old: ["ready", "ready"], next: [] },
      { old: ["ready", "ready"], next: ["starting"] },
      { old: ["ready"], next: ["ready"] },
      { old: ["ready"], next: ["ready", "starting"] },
      { old: [], next: ["ready", "ready"] },
    ];
    const { old, next } = plan[step];
    const total = old.length + next.length;
    return (
      <Diagram height={236} step={step}>
        <Label x={10} y={18} size="small" tone="muted" mono>
          replicas: 2 maxSurge: 1 maxUnavailable: 0
        </Label>
        <Region x={10} y={34} w={300} h={140} label="Old ReplicaSet: v1" />
        <Region
          x={330}
          y={34}
          w={300}
          h={140}
          label="New ReplicaSet: v2"
          tone="focus"
        />
        {old.map((state, index) => (
          <Box
            key={`old-${index}`}
            x={30 + index * 140}
            y={84}
            w={120}
            h={50}
            title="Pod v1"
            sub={state}
            tone="good"
          />
        ))}
        {next.map((state, index) => (
          <Box
            key={`new-${index}`}
            x={350 + index * 140}
            y={84}
            w={120}
            h={50}
            title="Pod v2"
            sub={state}
            tone={state === "ready" ? "good" : "warn"}
          />
        ))}
        <Tag
          x={320}
          y={208}
          text={`ready: 2 of 2   Pods in total: ${total}`}
          tone="good"
        />
      </Diagram>
    );
  },

  "bad-rollout": () => (
    <Diagram height={268}>
      <Label x={320} y={18} anchor="middle" size="small" tone="muted">
        The same missing image, under two update settings
      </Label>
      <Region
        x={10}
        y={30}
        w={300}
        h={196}
        label="maxUnavailable: 2, maxSurge: 0"
        tone="bad"
      />
      <Box
        x={30}
        y={62}
        w={120}
        h={46}
        title="Pod v1"
        sub="removed"
        tone="muted"
        dashed
      />
      <Box
        x={170}
        y={62}
        w={120}
        h={46}
        title="Pod v1"
        sub="removed"
        tone="muted"
        dashed
      />
      <Box
        x={30}
        y={126}
        w={120}
        h={46}
        title="Pod v2"
        sub="cannot start"
        tone="bad"
      />
      <Box
        x={170}
        y={126}
        w={120}
        h={46}
        title="Pod v2"
        sub="cannot start"
        tone="bad"
      />
      <Tag x={160} y={200} text="0 ready: an outage" tone="bad" />

      <Region
        x={330}
        y={30}
        w={300}
        h={196}
        label="maxUnavailable: 0, maxSurge: 1"
        tone="good"
      />
      <Box
        x={350}
        y={62}
        w={120}
        h={46}
        title="Pod v1"
        sub="ready"
        tone="good"
      />
      <Box
        x={490}
        y={62}
        w={120}
        h={46}
        title="Pod v1"
        sub="ready"
        tone="good"
      />
      <Box
        x={350}
        y={126}
        w={120}
        h={46}
        title="Pod v2"
        sub="cannot start"
        tone="bad"
      />
      <Tag x={480} y={200} text="2 ready: still serving" tone="good" />
      <Label x={320} y={256} anchor="middle" size="small" tone="muted">
        Either way the rollout is stuck; only one setting keeps Dispatch up.
      </Label>
    </Diagram>
  ),

  "canary-split": () => (
    <Diagram height={286}>
      <Box
        x={40}
        y={14}
        w={230}
        h={56}
        title="Service dispatch"
        sub="selects app=dispatch"
        tone="focus"
      />
      <Box
        x={390}
        y={14}
        w={230}
        h={56}
        title="Service dispatch-preview"
        sub="selects track=canary"
        tone="warn"
      />
      <Region
        x={10}
        y={118}
        w={380}
        h={140}
        label="Deployment dispatch, track=stable"
        labelBelow
      />
      <Region
        x={410}
        y={118}
        w={220}
        h={140}
        label="dispatch-canary, track=canary"
        labelBelow
        tone="warn"
      />
      <Box
        x={30}
        y={160}
        w={160}
        h={56}
        title="Pod"
        sub="release 1"
        tone="good"
      />
      <Box
        x={210}
        y={160}
        w={160}
        h={56}
        title="Pod"
        sub="release 1"
        tone="good"
      />
      <Box
        x={440}
        y={160}
        w={160}
        h={56}
        title="Pod"
        sub="release 2"
        tone="warn"
      />
      <Arrow
        points={[
          [110, 70],
          [110, 156],
        ]}
        tone="focus"
      />
      <Arrow
        points={[
          [155, 70],
          [290, 156],
        ]}
        tone="focus"
      />
      <Arrow
        points={[
          [230, 70],
          [500, 156],
        ]}
        tone="focus"
      />
      <Arrow
        points={[
          [540, 70],
          [540, 156],
        ]}
        tone="warn"
      />
      <Label x={320} y={274} anchor="middle" size="small" tone="muted">
        About one in three connections to dispatch reaches the canary.
      </Label>
    </Diagram>
  ),

  "blue-green": ({ step = 0 }) => {
    const live = step === 0 ? "blue" : "green";
    return (
      <Diagram height={250} step={step}>
        <Box
          x={210}
          y={14}
          w={220}
          h={60}
          title="Service dispatch"
          sub={`selector: version=${live}`}
          tone="focus"
        />
        {(["blue", "green"] as const).map((name, index) => {
          const x = index === 0 ? 10 : 330;
          const selected = name === live;
          return (
            <g key={name}>
              <Region
                x={x}
                y={120}
                w={300}
                h={124}
                label={
                  index === 0
                    ? "blue: the current release"
                    : "green: the new release"
                }
                tone={selected ? "good" : "default"}
              />
              {[0, 1].map((pod) => (
                <Box
                  key={pod}
                  x={x + 20 + pod * 140}
                  y={156}
                  w={120}
                  h={50}
                  title="Pod"
                  sub={index === 0 ? "release 1" : "release 2"}
                  tone={selected ? "good" : "muted"}
                />
              ))}
              {selected && (
                <>
                  <Arrow
                    points={[
                      [300, 74],
                      [x + 80, 152],
                    ]}
                    tone="good"
                  />
                  <Arrow
                    points={[
                      [340, 74],
                      [x + 220, 152],
                    ]}
                    tone="good"
                  />
                </>
              )}
            </g>
          );
        })}
      </Diagram>
    );
  },
  "downward-api": () => {
    const fact = (line: number) => 40 + 8 + 24 * (line + 0.5);
    const env = (line: number) => 52 + 8 + 22 * (line + 0.5);
    return (
      <Diagram height={282}>
        <Region
          x={10}
          y={10}
          w={290}
          h={240}
          label="Pod object in the API server"
        />
        <Code
          x={26}
          y={40}
          w={258}
          spacing={24}
          lines={[
            { text: "spec:" },
            { text: "  nodeName: worker2", tone: "focus" },
            { text: "  limits.memory: 192Mi", tone: "good" },
            { text: "metadata:" },
            { text: "  name: dispatch-x2l", tone: "focus" },
            { text: "  namespace: dispatch", tone: "focus" },
            { text: "  labels: app=dispatch", tone: "warn" },
          ]}
        />
        <Region
          x={340}
          y={10}
          w={290}
          h={240}
          label="Container api"
          tone="focus"
        />
        <Label x={356} y={46} size="small" tone="muted">
          Environment: fixed when the container starts
        </Label>
        <Code
          x={356}
          y={52}
          w={258}
          spacing={22}
          lines={[
            { text: "DISPATCH_NODE_NAME=worker2", tone: "focus" },
            { text: "DISPATCH_MEMORY_LIMIT=201326592", tone: "good" },
            { text: "DISPATCH_POD_NAME=dispatch-x2l", tone: "focus" },
            { text: "DISPATCH_POD_NAMESPACE=dispatch", tone: "focus" },
          ]}
        />
        <Label x={356} y={180} size="small" tone="muted">
          File: kept current while the Pod runs
        </Label>
        <Code
          x={356}
          y={186}
          w={258}
          spacing={20}
          lines={[
            { text: "/etc/podinfo/labels" },
            { text: 'app="dispatch"', tone: "warn" },
          ]}
        />
        <Arrow
          points={[
            [286, fact(1)],
            [352, env(0)],
          ]}
          tone="focus"
        />
        <Arrow
          points={[
            [286, fact(2)],
            [352, env(1)],
          ]}
          tone="good"
        />
        <Arrow
          points={[
            [286, fact(4)],
            [352, env(2)],
          ]}
          tone="focus"
        />
        <Arrow
          points={[
            [286, fact(5)],
            [352, env(3)],
          ]}
          tone="focus"
        />
        <Arrow
          points={[
            [286, fact(6)],
            [352, 186 + 8 + 20 * 1.5],
          ]}
          tone="warn"
        />
        <Label x={10} y={274} size="small" tone="focus">
          fieldRef
        </Label>
        <Label x={90} y={274} size="small" tone="good">
          resourceFieldRef
        </Label>
        <Label x={220} y={274} size="small" tone="warn">
          downwardAPI volume
        </Label>
      </Diagram>
    );
  },
} satisfies Drawings;
