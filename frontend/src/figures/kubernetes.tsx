import {
  Arrow,
  Box,
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
} satisfies Drawings;
