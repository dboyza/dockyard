import {
  Arrow,
  Box,
  Cylinder,
  Diagram,
  File,
  Label,
  Region,
  Reveal,
  Tag,
  Terminal,
  type Tone,
} from "./kit";
import type { Drawings } from "./registry";

/** A box drawn with a second outline behind it, for several copies. */
function Copies({
  x,
  y,
  w,
  title,
  tone = "default",
}: {
  x: number;
  y: number;
  w: number;
  title: string;
  tone?: Tone;
}) {
  return (
    <>
      <Box x={x + 5} y={y - 5} w={w} h={34} tone="muted" />
      <Box x={x} y={y} w={w} h={34} title={title} tone={tone} />
    </>
  );
}

const stages = [
  { x: 10, heading: "Module 1", sub: "the API alone", region: "Container" },
  {
    x: 170,
    heading: "Modules 2–6",
    sub: "all four parts",
    region: "Docker Compose",
  },
  {
    x: 330,
    heading: "Modules 7–12",
    sub: "on Kubernetes",
    region: "Kubernetes",
  },
  {
    x: 490,
    heading: "Modules 13–24",
    sub: "run like a real service",
    region: "Your cluster",
  },
];

export const dispatch = {
  "dispatch-system": ({ step }) => (
    <Diagram height={304} step={step}>
      <Terminal
        x={10}
        y={40}
        w={180}
        title="You"
        lines={["$ curl -X POST …/jobs", "$ curl …/jobs"]}
      />
      <Box
        x={240}
        y={44}
        w={130}
        h={56}
        title="API"
        sub="accepts jobs"
        tone="focus"
      />
      <Box x={470} y={44} w={150} h={56} title="Redis" sub="the queue" />
      <Cylinder
        x={240}
        y={196}
        w={130}
        h={74}
        title="PostgreSQL"
        sub="jobs and results"
      />
      <Box x={470} y={206} w={150} h={56} title="Worker" sub="does the work" />
      <Reveal from={0} until={0}>
        <Arrow
          points={[
            [192, 64],
            [236, 64],
          ]}
          tone="focus"
          label="job"
          labelAt={[214, 56]}
        />
        <Tag x={100} y={140} text='title: "hello"' />
      </Reveal>
      <Reveal from={1} until={1}>
        <Arrow
          points={[
            [290, 100],
            [290, 192],
          ]}
          tone="focus"
          label="save: queued"
          labelAt={[290, 150]}
        />
        <Arrow
          points={[
            [370, 72],
            [466, 72],
          ]}
          tone="focus"
          label="notify"
          labelAt={[418, 64]}
        />
        <Arrow
          points={[
            [236, 84],
            [192, 84],
          ]}
          label="accepted"
          labelAt={[214, 130]}
        />
      </Reveal>
      <Reveal from={2} until={2}>
        <Arrow
          points={[
            [545, 100],
            [545, 202],
          ]}
          tone="focus"
          label="new job"
          labelAt={[545, 154]}
        />
        <Arrow
          points={[
            [470, 234],
            [374, 234],
          ]}
          tone="focus"
          label="save: done"
          labelAt={[422, 226]}
        />
        <Tag x={422} y={288} text='"hello" → "HELLO"' tone="good" />
      </Reveal>
      <Reveal from={3}>
        <Arrow
          points={[
            [192, 84],
            [236, 84],
          ]}
          tone="focus"
          label="ask"
          labelAt={[214, 76]}
        />
        <Arrow
          points={[
            [320, 192],
            [320, 104],
          ]}
          tone="focus"
          label="read"
          labelAt={[320, 150]}
        />
        <Tag x={100} y={140} text="status: done" tone="good" />
      </Reveal>
    </Diagram>
  ),

  "dispatch-journey": ({ step }) => (
    <Diagram height={316} step={step}>
      {stages.map((stage, index) => (
        <Reveal from={index} key={stage.heading}>
          <Label x={stage.x + 70} y={22} anchor="middle" size="large">
            {stage.heading}
          </Label>
          <Label
            x={stage.x + 70}
            y={42}
            anchor="middle"
            size="small"
            tone="muted"
          >
            {stage.sub}
          </Label>
          <Region
            x={stage.x}
            y={56}
            w={140}
            h={232}
            label={stage.region}
            tone={index === step ? "focus" : "default"}
          />
          {index > 0 && (
            <Arrow
              points={[
                [stage.x - 18, 172],
                [stage.x - 3, 172],
              ]}
            />
          )}
        </Reveal>
      ))}
      <Reveal from={0}>
        <Box x={22} y={84} w={116} h={34} title="API" tone="focus" />
      </Reveal>
      <Reveal from={1}>
        <Box x={182} y={84} w={116} h={34} title="API" tone="focus" />
        <Box x={182} y={128} w={116} h={34} title="Redis" />
        <Box x={182} y={172} w={116} h={34} title="Worker" />
        <Cylinder x={182} y={216} w={116} h={56} title="PostgreSQL" />
      </Reveal>
      <Reveal from={2}>
        <Copies x={342} y={88} w={111} title="API ×2" tone="focus" />
        <Box x={342} y={132} w={111} h={34} title="Redis" />
        <Copies x={342} y={180} w={111} title="Worker ×2" />
        <Cylinder x={342} y={224} w={116} h={56} title="PostgreSQL" />
      </Reveal>
      <Reveal from={3}>
        <Copies x={502} y={88} w={111} title="API ×3" tone="focus" />
        <Box x={502} y={132} w={111} h={34} title="Redis" />
        <Copies x={502} y={180} w={111} title="Worker ×3" />
        <Cylinder x={502} y={224} w={116} h={56} title="PostgreSQL" />
        <Label x={560} y={306} anchor="middle" size="small" tone="muted">
          + monitoring, security
        </Label>
      </Reveal>
    </Diagram>
  ),

  "dispatch-first-run": () => (
    <Diagram height={264}>
      <Region x={10} y={14} w={620} h={240} label="Your computer" />
      <Terminal
        x={26}
        y={56}
        w={170}
        title="Terminal"
        lines={["$ curl …/healthz", '{"status": "ok", …}']}
      />
      <Arrow
        points={[
          [196, 100],
          [226, 100],
        ]}
        tone="focus"
      />
      <Tag x={290} y={100} text="127.0.0.1:54321" tone="focus" />
      <Label x={290} y={126} anchor="middle" size="small" tone="focus">
        published with -p
      </Label>
      <Arrow
        points={[
          [352, 100],
          [375, 100],
        ]}
        tone="focus"
      />
      <Region x={400} y={40} w={220} h={204} label="Container" tone="focus" />
      <Tag x={400} y={100} text="8080" tone="good" />
      <Box
        x={428}
        y={72}
        w={176}
        h={56}
        title="python app.py"
        sub="Dispatch API on port 8080"
        tone="good"
        mono
      />
      <Label x={26} y={186} mono>
        $DOCKYARD_WORKSPACE/
      </Label>
      <File x={40} y={198} name="app.py" />
      <Label x={428} y={172} mono>
        /app/
      </Label>
      <File x={442} y={186} name="app.py" tone="focus" />
      <Arrow
        points={[
          [76, 212],
          [436, 212],
        ]}
        tone="focus"
        label="bind mount, read-only"
        labelAt={[250, 204]}
      />
    </Diagram>
  ),
} satisfies Drawings;
