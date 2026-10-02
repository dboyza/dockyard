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
  type Point,
  type Tone,
} from "./kit";
import type { Drawings } from "./registry";

/** Figures for the foundation primers in the reference desk. */

type TreeNode = { name: string; depth: number; parent: number | null };

const tree: TreeNode[] = [
  { name: "/", depth: 0, parent: null },
  { name: "home/", depth: 1, parent: 0 },
  { name: "you/", depth: 2, parent: 1 },
  { name: "lab/", depth: 3, parent: 2 },
  { name: "Dockerfile", depth: 4, parent: 3 },
  { name: "site/", depth: 4, parent: 3 },
  { name: "index.html", depth: 5, parent: 5 },
  { name: "tmp/", depth: 1, parent: 0 },
  { name: "example", depth: 2, parent: 7 },
];
const rowY = (index: number) => 40 + index * 27;
const nodeX = (index: number) => 30 + tree[index].depth * 28;

function Connector({ child, tone }: { child: number; tone?: Tone }) {
  const parent = tree[child].parent!;
  const px = nodeX(parent) + 10;
  const points: Point[] = [
    [px, rowY(parent) + 11],
    [px, rowY(child)],
    [nodeX(child), rowY(child)],
  ];
  return <Line points={points} tone={tone} />;
}

function TreePath({ nodes, tone }: { nodes: number[]; tone: Tone }) {
  return (
    <>
      {nodes.map((index) =>
        tree[index].parent === null ? null : (
          <Connector key={`line-${index}`} child={index} tone={tone} />
        ),
      )}
      {nodes.map((index) => (
        <Tag
          key={`tag-${index}`}
          x={nodeX(index)}
          y={rowY(index)}
          text={tree[index].name}
          tone={tone}
          anchor="start"
        />
      ))}
    </>
  );
}

/** A square bracket under a span of a drawing, with a label below it. */
function Bracket({
  from,
  to,
  y,
  label,
  sub,
  tone = "default",
}: {
  from: number;
  to: number;
  y: number;
  label: string;
  sub?: string;
  tone?: Tone;
}) {
  return (
    <g>
      <Line
        points={[
          [from, y - 6],
          [from, y],
          [to, y],
          [to, y - 6],
        ]}
        tone={tone === "default" ? "muted" : tone}
      />
      <Label x={(from + to) / 2} y={y + 20} anchor="middle" tone={tone}>
        {label}
      </Label>
      {sub && (
        <Label
          x={(from + to) / 2}
          y={y + 38}
          anchor="middle"
          size="small"
          tone="muted"
        >
          {sub}
        </Label>
      )}
    </g>
  );
}

/** A vertical bracket beside lines of code, with a label to its right. */
function SideBracket({
  x,
  top,
  bottom,
  tone = "focus",
}: {
  x: number;
  top: number;
  bottom: number;
  tone?: Tone;
}) {
  return (
    <Line
      points={[
        [x - 6, top],
        [x, top],
        [x, bottom],
        [x - 6, bottom],
      ]}
      tone={tone}
    />
  );
}

export const reference = {
  "shell-role": () => (
    <Diagram height={172}>
      <Terminal
        x={10}
        y={40}
        w={170}
        lines={["$ docker ps", "CONTAINER ID …"]}
      />
      <Arrow
        points={[
          [182, 76],
          [236, 76],
        ]}
        label="your line"
        labelAt={[209, 66]}
      />
      <Box
        x={240}
        y={40}
        w={200}
        h={72}
        title="The shell"
        sub="reads it and fills in values"
        tone="focus"
      />
      <Arrow
        points={[
          [440, 76],
          [494, 76],
        ]}
        label="starts"
        labelAt={[467, 66]}
      />
      <Box
        x={498}
        y={40}
        w={132}
        h={72}
        title="docker"
        sub="does the work"
        mono
      />
      <Arrow
        points={[
          [564, 112],
          [564, 146],
          [95, 146],
          [95, 118],
        ]}
        tone="good"
        label="its output appears in the terminal"
        labelAt={[330, 138]}
      />
      <Label x={320} y={166} anchor="middle" size="small" tone="muted">
        docker and kubectl are ordinary programs; the shell starts them for you.
      </Label>
    </Diagram>
  ),

  "relative-absolute-paths": ({ step }) => (
    <Diagram height={278} step={step}>
      {tree.map((node, index) =>
        node.parent === null ? null : (
          <Connector key={node.name} child={index} />
        ),
      )}
      {tree.map((node, index) => (
        <Tag
          key={node.name}
          x={nodeX(index)}
          y={rowY(index)}
          text={node.name}
          anchor="start"
        />
      ))}

      <Reveal from={0} until={2}>
        <TreePath nodes={[3]} tone="focus" />
        <Label x={166} y={rowY(3) + 4} size="small" tone="focus">
          ← working directory
        </Label>
      </Reveal>
      <Reveal from={0} until={0}>
        <Terminal x={320} y={40} w={300} lines={["$ pwd", "/home/you/lab"]} />
        <Label x={320} y={150} size="small" tone="muted">
          pwd prints where you are as an absolute path.
        </Label>
      </Reveal>

      <Reveal from={1} until={1}>
        <TreePath nodes={[5, 6]} tone="good" />
        <Terminal
          x={320}
          y={40}
          w={300}
          lines={["$ cat site/index.html", "<h1>Hello</h1>"]}
        />
        <Label x={320} y={150} size="small">
          site/index.html, starting from lab/, means
        </Label>
        <Label x={320} y={170} mono tone="good">
          /home/you/lab/site/index.html
        </Label>
      </Reveal>

      <Reveal from={2} until={2}>
        <TreePath nodes={[0, 7, 8]} tone="good" />
        <Terminal x={320} y={40} w={300} lines={["$ cat /tmp/example"]} />
        <Label x={320} y={132} size="small">
          A leading / starts at the top folder,
        </Label>
        <Label x={320} y={150} size="small">
          so this means the same file wherever you are.
        </Label>
      </Reveal>

      <Reveal from={3}>
        <TreePath nodes={[2]} tone="focus" />
        <Label x={138} y={rowY(2) + 4} size="small" tone="focus">
          ← working directory
        </Label>
        <Terminal
          x={320}
          y={40}
          w={300}
          lines={["$ cd ..", "$ pwd", "/home/you"]}
        />
        <Label x={320} y={170} size="small" tone="muted">
          .. always means the folder one level up.
        </Label>
      </Reveal>
    </Diagram>
  ),

  "command-anatomy": () => (
    <Diagram height={250}>
      <Box x={30} y={30} w={90} h={40} title="kubectl" mono tone="focus" />
      <Box x={130} y={30} w={60} h={40} title="get" mono tone="good" />
      <Box x={200} y={30} w={66} h={40} title="pods" mono tone="good" />
      <Box x={276} y={30} w={120} h={40} title="-n dispatch" mono tone="warn" />
      <Bracket from={30} to={120} y={86} label="program" tone="focus" />
      <Bracket from={130} to={266} y={86} label="arguments" tone="good" />
      <Bracket from={276} to={396} y={86} label="option" tone="warn" />
      <Label x={336} y={124} anchor="middle" size="small" tone="muted">
        a setting and its value
      </Label>
      <Label x={420} y={46} size="small" tone="muted">
        -n names a Kubernetes namespace,
      </Label>
      <Label x={420} y={64} size="small" tone="muted">
        not a folder on your computer.
      </Label>

      <Label x={30} y={160} size="small" tone="muted">
        In a lesson
      </Label>
      <Box
        x={30}
        y={168}
        w={248}
        h={40}
        title="docker logs <container name>"
        mono
      />
      <Arrow
        points={[
          [280, 188],
          [340, 188],
        ]}
        label="you type"
        labelAt={[310, 178]}
      />
      <Label x={344} y={160} size="small" tone="muted">
        In your terminal
      </Label>
      <Box
        x={344}
        y={168}
        w={180}
        h={40}
        title="docker logs web"
        mono
        tone="good"
      />
      <Label x={30} y={234} size="small">
        Replace the whole placeholder, angle brackets included: the shell reads
        &lt; and &gt; as redirection.
      </Label>
    </Diagram>
  ),

  "shell-streams": ({ step }) => (
    <Diagram height={218} step={step}>
      <Reveal from={0} until={0}>
        <Box
          x={20}
          y={70}
          w={210}
          h={60}
          title="ls site missing"
          sub="one folder exists, one does not"
          mono
        />
        <Terminal
          x={400}
          y={56}
          w={230}
          lines={["index.html", "ls: missing: No such file…"]}
        />
        <Arrow
          points={[
            [230, 100],
            [396, 100],
          ]}
          tone="good"
          label="standard output"
          labelAt={[313, 90]}
        />
        <Arrow
          points={[
            [230, 119],
            [396, 119],
          ]}
          tone="warn"
          label="standard error"
          labelAt={[313, 138]}
        />
      </Reveal>

      <Reveal from={1} until={1}>
        <Box
          x={20}
          y={66}
          w={230}
          h={60}
          title="ls site missing > out.txt"
          sub="output goes to a file"
          mono
        />
        <Terminal
          x={400}
          y={40}
          w={230}
          lines={["ls: missing: No such file…"]}
        />
        <Arrow
          points={[
            [250, 84],
            [396, 84],
          ]}
          tone="warn"
          label="standard error"
          labelAt={[323, 74]}
        />
        <Arrow
          points={[
            [250, 112],
            [330, 112],
            [330, 176],
            [432, 176],
          ]}
          tone="good"
          label="standard output"
          labelAt={[384, 166]}
        />
        <File x={440} y={160} name="out.txt" tone="good" />
      </Reveal>

      <Reveal from={2} until={2}>
        <Box
          x={20}
          y={80}
          w={200}
          h={44}
          title={"printf 'worker\\napi\\n'"}
          mono
        />
        <Arrow
          points={[
            [220, 102],
            [276, 102],
          ]}
          tone="focus"
          label="| pipe"
          labelAt={[248, 92]}
        />
        <Box x={280} y={80} w={90} h={44} title="sort" mono />
        <Arrow
          points={[
            [370, 102],
            [410, 102],
          ]}
          tone="good"
        />
        <Terminal x={414} y={66} w={216} lines={["api", "worker"]} />
        <Label x={20} y={180} size="small" tone="muted">
          printf’s output becomes sort’s input; only sort’s output reaches the
          screen.
        </Label>
      </Reveal>

      <Reveal from={3}>
        <Box x={20} y={30} w={170} h={44} title="mkdir notes" mono />
        <Arrow
          points={[
            [190, 52],
            [236, 52],
          ]}
          tone="good"
        />
        <Tag x={282} y={52} text="exit 0" tone="good" />
        <Arrow
          points={[
            [324, 52],
            [370, 52],
          ]}
          tone="good"
        />
        <Box
          x={374}
          y={30}
          w={256}
          h={44}
          title="&& the next command runs"
          tone="good"
        />

        <Box x={20} y={110} w={170} h={44} title="cat missing" mono />
        <Arrow
          points={[
            [190, 132],
            [236, 132],
          ]}
          tone="bad"
        />
        <Tag x={282} y={132} text="exit 1" tone="bad" />
        <Arrow
          points={[
            [324, 132],
            [370, 132],
          ]}
          tone="bad"
          dashed
        />
        <Box
          x={374}
          y={110}
          w={256}
          h={44}
          title="&& the next command is skipped"
          tone="muted"
          dashed
        />
        <Label x={20} y={196} size="small" tone="muted">
          echo $? prints the exit status of the command you just ran.
        </Label>
      </Reveal>
    </Diagram>
  ),

  "yaml-building-blocks": ({ step }) => {
    const top = (line: number) => 18 + line * 22;
    const middle = (line: number) => top(line) + 15;
    return (
      <Diagram height={254} step={step}>
        <Code
          x={10}
          y={10}
          w={250}
          spacing={22}
          lines={[
            { text: "service:" },
            { text: "  name: report-worker" },
            { text: "  replicas: 2" },
            { text: "  enabled: true" },
            { text: '  release: "1.0"' },
            { text: "  labels:" },
            { text: "    team: platform" },
            { text: "  ports:" },
            { text: "    - name: http" },
            { text: "      port: 8080" },
          ]}
        />

        <Reveal from={0} until={0}>
          <SideBracket x={276} top={top(1) + 2} bottom={top(10) - 2} />
          <Label x={292} y={top(5) + 4} tone="focus">
            A mapping belonging to service:
          </Label>
          <Label x={292} y={top(5) + 22} size="small" tone="muted">
            six keys, each indented two spaces
          </Label>
        </Reveal>

        <Reveal from={1} until={1}>
          <SideBracket x={276} top={top(8) + 2} bottom={top(10) - 2} />
          <Label x={292} y={top(8) + 14} tone="focus">
            A list belonging to ports:
          </Label>
          <Label x={292} y={top(8) + 32} size="small" tone="muted">
            each item starts with a dash and a space
          </Label>
        </Reveal>

        <Reveal from={2} until={2}>
          {(
            [
              [1, "report-worker → text"],
              [2, "2 → a number"],
              [3, "true → a yes/no value"],
              [4, '"1.0" → text, kept by the quotes'],
            ] as const
          ).map(([line, note]) => (
            <g key={line}>
              <Arrow
                points={[
                  [266, middle(line) - 4],
                  [286, middle(line) - 4],
                ]}
                tone="focus"
              />
              <Label x={292} y={middle(line)} size="small" tone="focus">
                {note}
              </Label>
            </g>
          ))}
        </Reveal>

        <Reveal from={3}>
          <Label x={300} y={30} size="small" tone="muted">
            The same file with labels: moved left
          </Label>
          <Code
            x={300}
            y={40}
            w={330}
            spacing={22}
            lines={[
              { text: "service:" },
              { text: "  name: report-worker" },
              { text: "  …" },
              { text: "labels:", tone: "warn" },
              { text: "  team: platform", tone: "warn" },
            ]}
          />
          <Label x={300} y={192} tone="warn">
            labels: now sits beside service:
          </Label>
          <Label x={300} y={212} size="small" tone="muted">
            Still valid YAML, so nothing warns you.
          </Label>
        </Reveal>
      </Diagram>
    );
  },

  "yaml-three-checks": () => {
    const checks = [
      {
        title: "1. Valid YAML?",
        sub: "can it be read at all?",
        lines: ["spec:", "⇥ replicas: 2"],
        fault: "✗ indented with a tab",
      },
      {
        title: "2. Valid object?",
        sub: "are the fields right?",
        lines: ["spec:", "  replica: 2"],
        fault: "✗ unknown field “replica”",
      },
      {
        title: "3. Does it work?",
        sub: "does the system behave?",
        lines: ["selector:", "  app: exampel"],
        fault: "✗ matches no Pods",
      },
    ];
    return (
      <Diagram height={226}>
        {checks.map((check, index) => {
          const x = 10 + index * 215;
          return (
            <g key={check.title}>
              <Box
                x={x}
                y={20}
                w={190}
                h={60}
                title={check.title}
                sub={check.sub}
                tone="focus"
              />
              {index < 2 && (
                <Arrow
                  points={[
                    [x + 192, 50],
                    [x + 213, 50],
                  ]}
                  tone="focus"
                />
              )}
              <Code
                x={x}
                y={100}
                w={190}
                spacing={22}
                lines={[
                  { text: check.lines[0] },
                  { text: check.lines[1], tone: "bad" },
                ]}
              />
              <Label x={x + 95} y={182} anchor="middle" tone="bad">
                {check.fault}
              </Label>
            </g>
          );
        })}
        <Label x={320} y={214} anchor="middle" size="small" tone="muted">
          The third file passes checks 1 and 2: only the running result shows
          the mistake.
        </Label>
      </Diagram>
    );
  },

  "yaml-two-label-sets": () => (
    <Diagram height={288}>
      <Code
        x={10}
        y={10}
        w={290}
        spacing={22}
        lines={[
          { text: "kind: Deployment" },
          { text: "metadata:" },
          { text: "  name: example" },
          { text: "  labels:" },
          { text: "    owner: practice", tone: "warn" },
          { text: "spec:" },
          { text: "  replicas: 2" },
          { text: "  template:" },
          { text: "    metadata:" },
          { text: "      labels:" },
          { text: "        app: example", tone: "focus" },
        ]}
      />
      <Arrow
        points={[
          [302, 111],
          [336, 111],
        ]}
        tone="warn"
      />
      <Box
        x={340}
        y={86}
        w={130}
        h={50}
        title="Deployment"
        sub="owner=practice"
        tone="warn"
      />
      <Arrow
        points={[
          [405, 136],
          [405, 166],
        ]}
        dashed
        tone="muted"
        label="creates"
        labelAt={[434, 156]}
      />
      <Region x={330} y={166} w={150} h={114} label="Its Pods" tone="focus" />
      <Box
        x={340}
        y={196}
        w={130}
        h={32}
        title="app=example"
        mono
        tone="focus"
      />
      <Box
        x={340}
        y={236}
        w={130}
        h={32}
        title="app=example"
        mono
        tone="focus"
      />
      <Arrow
        points={[
          [302, 249],
          [326, 249],
        ]}
        tone="focus"
      />

      <Box
        x={510}
        y={190}
        w={120}
        h={56}
        title="Service"
        sub="app=example"
        tone="good"
      />
      <Arrow
        points={[
          [510, 206],
          [474, 212],
        ]}
        tone="good"
      />
      <Arrow
        points={[
          [510, 230],
          [474, 252],
        ]}
        tone="good"
      />
      <Label x={570} y={270} anchor="middle" size="small" tone="good">
        ✓ selects both Pods
      </Label>

      <Box
        x={510}
        y={60}
        w={120}
        h={56}
        title="Service"
        sub="owner=practice"
        tone="bad"
        dashed
      />
      <Label x={570} y={136} anchor="middle" size="small" tone="bad">
        ✗ selects nothing
      </Label>
      <Label x={570} y={154} anchor="middle" size="small" tone="muted">
        no Pod has that label
      </Label>
    </Diagram>
  ),

  "http-exchange": () => (
    <Diagram height={236}>
      <Box x={10} y={10} w={120} h={40} title="curl" mono />
      <Box x={510} y={10} w={120} h={40} title="Dispatch" />
      <Arrow
        points={[
          [130, 22],
          [506, 22],
        ]}
        tone="focus"
        label="request"
        labelAt={[320, 14]}
      />
      <Arrow
        points={[
          [510, 40],
          [134, 40],
        ]}
        tone="good"
        label="response"
        labelAt={[320, 60]}
      />
      <Code
        x={10}
        y={76}
        w={300}
        spacing={24}
        lines={[
          { text: "POST /jobs", tone: "focus" },
          { text: "Content-Type: application/json" },
          { text: "" },
          { text: '{"title":"hello"}' },
        ]}
      />
      <Label x={10} y={210} size="small" tone="muted">
        First the method and path, then headers,
      </Label>
      <Label x={10} y={228} size="small" tone="muted">
        a blank line, and the body.
      </Label>
      <Code
        x={330}
        y={76}
        w={300}
        spacing={24}
        lines={[
          { text: "201 Created", tone: "good" },
          { text: "Content-Type: application/json" },
          { text: "" },
          { text: '{"id":"9f2c…","title":"hello"}' },
        ]}
      />
      <Label x={330} y={210} size="small" tone="muted">
        First the status, then headers,
      </Label>
      <Label x={330} y={228} size="small" tone="muted">
        a blank line, and the body.
      </Label>
    </Diagram>
  ),

  "url-anatomy": () => (
    <Diagram height={268}>
      <Box x={140} y={20} w={60} h={40} title="http" mono />
      <Label x={216} y={45} anchor="middle" mono>
        ://
      </Label>
      <Box x={232} y={20} w={110} h={40} title="127.0.0.1" mono tone="focus" />
      <Label x={350} y={45} anchor="middle" mono>
        :
      </Label>
      <Box x={358} y={20} w={64} h={40} title="8080" mono tone="good" />
      <Box x={430} y={20} w={70} h={40} title="/jobs" mono tone="warn" />
      <Label x={170} y={82} anchor="middle" size="small">
        protocol
      </Label>
      <Label x={287} y={82} anchor="middle" size="small" tone="focus">
        machine
      </Label>
      <Label x={390} y={82} anchor="middle" size="small" tone="good">
        service
      </Label>
      <Label x={465} y={82} anchor="middle" size="small" tone="warn">
        path
      </Label>

      <Region
        x={60}
        y={104}
        w={520}
        h={152}
        label="The machine at 127.0.0.1"
        tone="focus"
      />
      <Region
        x={84}
        y={134}
        w={300}
        h={104}
        label="Dispatch, listening on port 8080"
        tone="good"
      />
      <Tag x={170} y={186} text="/jobs" tone="warn" />
      <Tag x={290} y={186} text="/healthz" />
      <Label x={234} y={224} anchor="middle" size="small" tone="muted">
        the path picks one of these
      </Label>
      <Cylinder
        x={420}
        y={146}
        w={136}
        h={72}
        title="database"
        sub="port 5432"
        tone="muted"
      />
    </Diagram>
  ),

  "request-stages": ({ step }) => {
    const stages = [
      {
        title: "Resolve",
        sub: "name → address",
        notes: ["Could not resolve host"],
        tone: "bad" as Tone,
      },
      {
        title: "Connect",
        sub: "to the port",
        notes: ["Connection refused", "or Timed out"],
        tone: "bad" as Tone,
      },
      {
        title: "Verify TLS",
        sub: "https only",
        notes: ["certificate or", "TLS error"],
        tone: "bad" as Tone,
      },
      {
        title: "Answer",
        sub: "any HTTP status",
        notes: ["200, 404, 503…", "the request arrived"],
        tone: "good" as Tone,
      },
    ];
    return (
      <Diagram height={184} step={step}>
        <Label x={10} y={24} size="small" tone="muted">
          curl → … → the application
        </Label>
        {stages.map((stage, index) => {
          const x = 10 + index * 160;
          return (
            <Reveal key={stage.title} from={index}>
              {index > 0 && (
                <Arrow
                  points={[
                    [x - 23, 68],
                    [x - 3, 68],
                  ]}
                />
              )}
              <Box
                x={x}
                y={40}
                w={136}
                h={56}
                title={`${index + 1}. ${stage.title}`}
                sub={stage.sub}
                tone={stage.tone === "good" ? "good" : "default"}
              />
              <Label
                x={x + 68}
                y={122}
                anchor="middle"
                size="small"
                tone={stage.tone}
              >
                {stage.tone === "bad"
                  ? `✗ ${stage.notes[0]}`
                  : `✓ ${stage.notes[0]}`}
              </Label>
              {stage.notes[1] && (
                <Label
                  x={x + 68}
                  y={140}
                  anchor="middle"
                  size="small"
                  tone={stage.tone}
                >
                  {stage.notes[1]}
                </Label>
              )}
            </Reveal>
          );
        })}
        <Label x={320} y={172} anchor="middle" size="small" tone="muted">
          Find the furthest stage the request reached, then look there.
        </Label>
      </Diagram>
    );
  },

  "dns-search-suffixes": ({ step }) => {
    const attempt = (
      namespace: string,
      lookup: string,
      tried: { text: string; tone: Tone }[],
      result: { text: string; tone: Tone },
    ) => (
      <>
        <Box
          x={10}
          y={40}
          w={130}
          h={56}
          title="Pod"
          sub={`namespace ${namespace}`}
        />
        <Label x={214} y={56} anchor="middle" size="small" tone="muted">
          looks up
        </Label>
        <Arrow
          points={[
            [142, 68],
            [290, 68],
          ]}
          tone="focus"
        />
        <Tag x={214} y={92} text={lookup} tone="focus" />
        <Code x={296} y={40} w={334} spacing={26} lines={tried} />
        <Label
          x={296}
          y={40 + tried.length * 26 + 40}
          size="small"
          tone={result.tone}
        >
          {result.text}
        </Label>
      </>
    );
    return (
      <Diagram height={192} step={step}>
        <Label x={296} y={28} size="small" tone="muted">
          Names DNS is asked for, in order
        </Label>
        <Reveal from={0} until={0}>
          {attempt(
            "dispatch",
            "dispatch",
            [{ text: "dispatch.dispatch.svc.cluster.local ✓", tone: "good" }],
            { text: "→ the Service’s ClusterIP", tone: "good" },
          )}
        </Reveal>
        <Reveal from={1} until={1}>
          {attempt(
            "web",
            "dispatch",
            [
              { text: "dispatch.web.svc.cluster.local ✗", tone: "bad" },
              { text: "dispatch.svc.cluster.local ✗", tone: "bad" },
              { text: "dispatch.cluster.local ✗", tone: "bad" },
            ],
            { text: "→ not found", tone: "bad" },
          )}
        </Reveal>
        <Reveal from={2}>
          {attempt(
            "web",
            "dispatch.dispatch",
            [
              {
                text: "dispatch.dispatch.web.svc.cluster.local ✗",
                tone: "bad",
              },
              { text: "dispatch.dispatch.svc.cluster.local ✓", tone: "good" },
            ],
            { text: "→ the Service’s ClusterIP", tone: "good" },
          )}
        </Reveal>
      </Diagram>
    );
  },

  "service-name-to-pod": ({ step }) => (
    <Diagram height={226} step={step}>
      <Box x={10} y={95} w={120} h={50} title="client Pod" />
      <Box
        x={200}
        y={10}
        w={170}
        h={50}
        title="Cluster DNS"
        sub="dispatch → 10.96.0.42"
      />
      <Arrow
        points={[
          [70, 95],
          [70, 35],
          [196, 35],
        ]}
        both
        tone="focus"
        label="dispatch?"
        labelAt={[120, 27]}
      />
      <Box
        x={200}
        y={95}
        w={170}
        h={50}
        title="Service dispatch"
        sub="ClusterIP 10.96.0.42"
        tone="focus"
      />

      <Reveal from={1} until={1}>
        <Arrow
          points={[
            [130, 120],
            [196, 120],
          ]}
          tone="good"
          label="request"
          labelAt={[163, 110]}
        />
        <Box
          x={470}
          y={60}
          w={150}
          h={50}
          title="Pod"
          sub="ready"
          tone="good"
        />
        <Box
          x={470}
          y={140}
          w={150}
          h={50}
          title="Pod"
          sub="ready"
          tone="good"
        />
        <Arrow
          points={[
            [370, 112],
            [466, 88],
          ]}
          tone="good"
        />
        <Arrow
          points={[
            [370, 128],
            [466, 162],
          ]}
          tone="muted"
          dashed
        />
        <Label x={545} y={214} anchor="middle" size="small" tone="muted">
          ready endpoints
        </Label>
      </Reveal>

      <Reveal from={2}>
        <Arrow
          points={[
            [130, 120],
            [196, 120],
          ]}
          tone="bad"
          label="request"
          labelAt={[163, 110]}
        />
        <Box
          x={470}
          y={60}
          w={150}
          h={50}
          title="Pod"
          sub="not ready"
          tone="bad"
          dashed
        />
        <Box
          x={470}
          y={140}
          w={150}
          h={50}
          title="Pod"
          sub="not ready"
          tone="bad"
          dashed
        />
        <Label x={285} y={176} anchor="middle" size="small" tone="bad">
          ✗ no ready endpoints:
        </Label>
        <Label x={285} y={194} anchor="middle" size="small" tone="bad">
          nowhere to send the request
        </Label>
        <Label x={545} y={214} anchor="middle" size="small" tone="muted">
          the name still resolves
        </Label>
      </Reveal>
    </Diagram>
  ),

  "dns-blocked-by-policy": () => (
    <Diagram height={214}>
      <Box x={10} y={90} w={120} h={56} title="CoreDNS" sub="port 53" />
      <Region
        x={226}
        y={50}
        w={180}
        h={130}
        label="egress: TCP 5432 only"
        tone="warn"
      />
      <Box x={242} y={90} w={148} h={56} title="api Pod" tone="focus" />
      <Arrow
        points={[
          [242, 118],
          [134, 118],
        ]}
        tone="bad"
        dashed
        label="1. postgres?"
        labelAt={[188, 108]}
      />
      <Label x={188} y={140} anchor="middle" size="small" tone="bad">
        ✗ blocked
      </Label>
      <Cylinder
        x={500}
        y={80}
        w={120}
        h={76}
        title="postgres"
        sub="port 5432"
      />
      <Arrow
        points={[
          [406, 118],
          [496, 118],
        ]}
        tone="muted"
        dashed
        label="2. never made"
        labelAt={[452, 108]}
      />
      <Label x={320} y={204} anchor="middle" size="small" tone="muted">
        Also allow UDP and TCP port 53 to the cluster’s DNS, or no name can be
        found.
      </Label>
    </Diagram>
  ),

  "file-mode-bits": ({ step }) => {
    const groups = [
      {
        start: 120,
        label: "owner",
        sub: "UID 10001: read, write",
        tone: "focus" as Tone,
        chars: "rw-",
        sum: "4+2+0 = 6",
      },
      {
        start: 250,
        label: "group",
        sub: "group 10001: read",
        tone: "good" as Tone,
        chars: "r--",
        sum: "4+0+0 = 4",
      },
      {
        start: 380,
        label: "everyone else",
        sub: "no access",
        tone: "warn" as Tone,
        chars: "---",
        sum: "0+0+0 = 0",
      },
    ];
    return (
      <Diagram height={214} step={step}>
        <Label x={20} y={22} mono tone="muted">
          -rw-r----- 1 10001 10001 12288 Sep 28 10:00 jobs.db
        </Label>
        <Box x={60} y={44} w={36} h={40} title="-" mono tone="muted" />
        <Bracket
          from={60}
          to={96}
          y={98}
          label="type"
          sub="a file"
          tone="muted"
        />
        {groups.map((group) => (
          <g key={group.label}>
            {[...group.chars].map((char, index) => (
              <Box
                key={index}
                x={group.start + index * 36}
                y={44}
                w={32}
                h={40}
                title={char}
                mono
                tone={char === "-" ? "muted" : group.tone}
              />
            ))}
            <Bracket
              from={group.start}
              to={group.start + 104}
              y={98}
              label={group.label}
              sub={group.sub}
              tone={group.tone}
            />
          </g>
        ))}
        <Reveal from={1}>
          {groups.map((group) => (
            <g key={group.label}>
              {["4", "2", "1"].map((value, index) => (
                <Label
                  key={value}
                  x={group.start + 16 + index * 36}
                  y={38}
                  anchor="middle"
                  size="small"
                  tone="muted"
                >
                  {value}
                </Label>
              ))}
              <Label
                x={group.start + 52}
                y={176}
                anchor="middle"
                mono
                tone={group.tone}
              >
                {group.sum}
              </Label>
            </g>
          ))}
          <Label x={530} y={70} size="large">
            → 640
          </Label>
          <Label x={320} y={204} anchor="middle" size="small" tone="muted">
            r = 4, w = 2, x = 1, added up separately for each set.
          </Label>
        </Reveal>
      </Diagram>
    );
  },

  "container-shared-kernel": () => {
    const containers = [
      {
        x: 170,
        name: "Container A",
        process: "app · PID 1",
        limit: "cgroup: 256 MiB",
      },
      {
        x: 410,
        name: "Container B",
        process: "worker · PID 1",
        limit: "cgroup: 0.5 CPU",
      },
    ];
    return (
      <Diagram height={278}>
        <Region x={10} y={10} w={620} h={260} label="One Linux machine" />
        <Box
          x={30}
          y={110}
          w={120}
          h={50}
          title="a process"
          sub="no container"
          tone="muted"
        />
        <Arrow
          points={[
            [90, 160],
            [90, 208],
          ]}
          tone="muted"
        />
        {containers.map((container) => (
          <g key={container.name}>
            <Region
              x={container.x}
              y={34}
              w={210}
              h={170}
              label={container.name}
              tone="focus"
            />
            <Box
              x={container.x + 16}
              y={62}
              w={178}
              h={32}
              title={container.process}
            />
            <Label x={container.x + 16} y={114} size="small" tone="muted">
              namespaces give it its own:
            </Label>
            {["process list", "network and localhost", "files"].map(
              (item, index) => (
                <Label
                  key={item}
                  x={container.x + 24}
                  y={132 + index * 16}
                  size="small"
                >
                  • {item}
                </Label>
              ),
            )}
            <Tag
              x={container.x + 16}
              y={186}
              text={container.limit}
              tone="warn"
              anchor="start"
            />
            <Arrow
              points={[
                [container.x + 105, 204],
                [container.x + 105, 208],
              ]}
              tone="muted"
            />
          </g>
        ))}
        <Box
          x={30}
          y={212}
          w={580}
          h={46}
          title="Linux kernel"
          sub="one kernel, shared by every process and container"
          tone="focus"
        />
      </Diagram>
    );
  },

  "file-vs-running": ({ step }) => (
    <Diagram height={222} step={step}>
      <Label x={10} y={30} size="small" tone="muted" mono>
        app.conf on disk
      </Label>
      <Code
        x={10}
        y={40}
        w={180}
        spacing={26}
        lines={[{ text: "port = 9090", tone: "focus" }]}
      />
      <Reveal from={0} until={0}>
        <Arrow
          points={[
            [190, 60],
            [266, 60],
          ]}
          tone="muted"
          dashed
          label="not reread"
          labelAt={[228, 50]}
        />
        <Box
          x={270}
          y={36}
          w={170}
          h={56}
          title="running service"
          sub="listening on 8080"
          tone="warn"
        />
        <Box
          x={490}
          y={36}
          w={140}
          h={56}
          title="curl :9090"
          sub="✗ refused"
          tone="bad"
          mono
        />
        <Arrow
          points={[
            [490, 64],
            [444, 64],
          ]}
          tone="bad"
          dashed
        />
        <Label x={320} y={190} anchor="middle" tone="warn">
          The file and the running process disagree.
        </Label>
      </Reveal>
      <Reveal from={1}>
        <Arrow
          points={[
            [190, 60],
            [266, 60],
          ]}
          tone="good"
          label="read again"
          labelAt={[228, 50]}
        />
        <Box
          x={270}
          y={36}
          w={170}
          h={56}
          title="running service"
          sub="listening on 9090"
          tone="good"
        />
        <Box
          x={490}
          y={36}
          w={140}
          h={56}
          title="curl :9090"
          sub="✓ answers"
          tone="good"
          mono
        />
        <Arrow
          points={[
            [490, 64],
            [444, 64],
          ]}
          tone="good"
        />
        <Label x={320} y={180} anchor="middle" tone="good">
          After a restart, the process read the file again.
        </Label>
        <Label x={320} y={204} anchor="middle" mono tone="muted">
          sudo systemctl restart app
        </Label>
      </Reveal>
      <Tag x={355} y={118} text="active (running)" tone="good" />
      <Label x={355} y={148} anchor="middle" size="small" tone="muted">
        says the process runs, not which settings it uses
      </Label>
    </Diagram>
  ),

  "exam-task-loop": () => {
    const top: [string, string][] = [
      ["1. Read the task", "context, namespace, names"],
      ["2. Switch", "context and namespace"],
      ["3. Generate YAML", "--dry-run=client -o yaml"],
    ];
    const bottom: [string, string][] = [
      ["6. Next task", "or a flagged one"],
      ["5. Check the result", "Ready, endpoints, can-i"],
      ["4. Edit and apply", "kubectl apply -f"],
    ];
    return (
      <Diagram height={226}>
        {top.map(([title, sub], index) => (
          <Box
            key={title}
            x={10 + index * 220}
            y={20}
            w={180}
            h={60}
            title={title}
            sub={sub}
            tone={index === 1 ? "focus" : "default"}
          />
        ))}
        {bottom.map(([title, sub], index) => (
          <Box
            key={title}
            x={10 + index * 220}
            y={150}
            w={180}
            h={60}
            title={title}
            sub={sub}
            tone={index === 1 ? "good" : "default"}
          />
        ))}
        <Arrow
          points={[
            [190, 50],
            [226, 50],
          ]}
        />
        <Arrow
          points={[
            [410, 50],
            [446, 50],
          ]}
        />
        <Arrow
          points={[
            [540, 80],
            [540, 146],
          ]}
        />
        <Arrow
          points={[
            [450, 180],
            [414, 180],
          ]}
        />
        <Arrow
          points={[
            [230, 180],
            [194, 180],
          ]}
        />
        <Arrow
          points={[
            [100, 150],
            [100, 84],
          ]}
        />
        <Tag
          x={320}
          y={115}
          text="too slow? flag it and return at the end"
          tone="warn"
        />
      </Diagram>
    );
  },
} satisfies Drawings;
