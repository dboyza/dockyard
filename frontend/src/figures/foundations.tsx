import {
  Arrow,
  Box,
  Code,
  Diagram,
  File,
  ImageStack,
  Label,
  Region,
  Reveal,
  Tag,
  Terminal,
} from "./kit";
import type { Drawings } from "./registry";

export const foundations = {
  "why-containers": () => (
    <Diagram height={258}>
      <Region x={10} y={10} w={300} h={238} label="Directly on your computer" />
      <Box
        x={40}
        y={62}
        w={240}
        h={44}
        title="A Python program"
        sub="written for Python 3.13"
      />
      <Arrow
        points={[
          [160, 106],
          [160, 128],
        ]}
      />
      <Box
        x={40}
        y={130}
        w={240}
        h={44}
        title="Python 3.9"
        sub="what this computer has installed"
        tone="bad"
      />
      <Label x={160} y={228} anchor="middle" tone="bad">
        ✗ Fails, or behaves differently
      </Label>

      <Region x={330} y={10} w={300} h={238} label="Inside a container" />
      <Region x={350} y={34} w={260} h={160} label="Container" tone="focus" />
      <Box
        x={370}
        y={62}
        w={220}
        h={44}
        title="A Python program"
        sub="written for Python 3.13"
      />
      <Arrow
        points={[
          [480, 106],
          [480, 128],
        ]}
      />
      <Box
        x={370}
        y={130}
        w={220}
        h={44}
        title="Python 3.13"
        sub="packaged with the program"
        tone="good"
      />
      <Label x={480} y={228} anchor="middle" tone="good">
        ✓ Runs the same wherever Docker runs
      </Label>
    </Diagram>
  ),

  "image-to-container": ({ step }) => (
    <Diagram height={262} step={step}>
      <ImageStack
        x={20}
        y={70}
        w={170}
        title="Image"
        layers={["Python 3.13", "Alpine Linux files"]}
      />
      <Label x={105} y={150} anchor="middle" size="small" tone="muted">
        a read-only template
      </Label>
      <Reveal from={1}>
        <Arrow
          points={[
            [198, 98],
            [262, 98],
          ]}
          label="docker run"
          labelAt={[230, 88]}
        />
        <Region x={266} y={20} w={354} h={228} label="Container" tone="focus" />
        <Box
          x={286}
          y={104}
          w={200}
          h={30}
          title="Writable layer"
          tone="focus"
        />
        <ImageStack
          x={286}
          y={142}
          w={200}
          layers={["Python 3.13", "Alpine Linux files"]}
          tone="muted"
        />
        <Label x={386} y={226} anchor="middle" size="small" tone="muted">
          the image’s files, shared and read-only
        </Label>
      </Reveal>
      <Reveal from={1} until={1}>
        <Tag x={555} y={71} text="Created" />
      </Reveal>
      <Reveal from={2} until={2}>
        <Box
          x={286}
          y={48}
          w={200}
          h={46}
          title="python"
          sub="main process: running"
          tone="good"
        />
        <Tag x={555} y={71} text="Running" tone="good" />
      </Reveal>
      <Reveal from={3}>
        <Box
          x={286}
          y={48}
          w={200}
          h={46}
          title="python"
          sub="finished with exit code 0"
          tone="muted"
          dashed
        />
        <Tag x={555} y={71} text="Exited (0)" tone="muted" />
        <Terminal
          x={20}
          y={168}
          w={236}
          title="docker logs"
          lines={["$ docker logs …", "Hello from inside a container"]}
        />
      </Reveal>
    </Diagram>
  ),

  "docker-client-engine": () => (
    <Diagram height={206}>
      <Terminal
        x={10}
        y={62}
        w={190}
        lines={["$ docker run …", "$ docker ps"]}
      />
      <Label x={105} y={158} anchor="middle" size="small" tone="muted">
        the docker command
      </Label>
      <Arrow
        points={[
          [202, 99],
          [256, 99],
        ]}
        label="request"
        labelAt={[229, 89]}
      />
      <Region
        x={260}
        y={14}
        w={370}
        h={182}
        label="Docker Engine"
        tone="focus"
      />
      <Label x={351} y={56} anchor="middle">
        Images
      </Label>
      <Box x={286} y={66} w={130} h={30} title="python" mono />
      <Box x={286} y={104} w={130} h={30} title="postgres" mono />
      <Box x={286} y={142} w={130} h={30} title="redis" mono />
      <Arrow
        points={[
          [422, 119],
          [464, 119],
        ]}
        label="creates"
        labelAt={[443, 109]}
      />
      <Label x={540} y={56} anchor="middle">
        Containers
      </Label>
      <Box x={470} y={66} w={140} h={30} title="running" tone="good" />
      <Box x={470} y={104} w={140} h={30} title="running" tone="good" />
      <Box x={470} y={142} w={140} h={30} title="exited" tone="muted" dashed />
    </Diagram>
  ),

  "image-layers": () => (
    <Diagram height={192}>
      <Terminal
        x={10}
        y={16}
        w={340}
        title="docker history, newest layer first"
        lines={[
          "$ docker history …",
          'CMD ["python3"]                0B',
          "RUN … install Python      44.1MB",
          "RUN … add packages        2.94MB",
          "ADD alpine-minirootfs …   9.31MB",
        ]}
      />
      <ImageStack
        x={390}
        y={46}
        w={230}
        title="The same layers, stacked"
        layers={[
          "Python 3.13 · 44 MB",
          "System packages · 3 MB",
          "Alpine Linux files · 9 MB",
        ]}
      />
      <Label x={505} y={150} anchor="middle" size="small" tone="muted">
        All read-only. Every container shares them.
      </Label>
      <Label x={12} y={176} size="small" tone="muted">
        Read from the bottom up to see the order the image was built in.
      </Label>
    </Diagram>
  ),

  "writable-layers": ({ step }) => (
    <Diagram height={284} step={step}>
      <ImageStack
        x={170}
        y={202}
        w={300}
        layers={["Python 3.13", "Alpine Linux files"]}
      />
      <Label x={320} y={276} anchor="middle" size="small" tone="muted">
        Image layers: read-only, stored once, shared
      </Label>

      <Reveal from={1} until={3}>
        <Region
          x={40}
          y={14}
          w={250}
          h={160}
          label="Container A"
          tone="focus"
        />
        <Arrow
          points={[
            [165, 158],
            [230, 198],
          ]}
          tone="muted"
          dashed
        />
      </Reveal>
      <Reveal from={1} until={1}>
        <Box x={60} y={104} w={210} h={54} title="Writable layer" sub="empty" />
      </Reveal>
      <Reveal from={2} until={3}>
        <Box
          x={60}
          y={42}
          w={210}
          h={46}
          title="echo … > /tmp/note.txt"
          sub="a process writes a file"
          mono
        />
        <Box
          x={60}
          y={104}
          w={210}
          h={54}
          title="Writable layer"
          sub="+ /tmp/note.txt"
          tone="focus"
        />
      </Reveal>
      <Reveal from={4}>
        <Region x={40} y={14} w={250} h={160} label="Container A" />
        <Label x={165} y={92} anchor="middle" tone="muted">
          Removed, along with
        </Label>
        <Label x={165} y={112} anchor="middle" tone="muted">
          its writable layer and note
        </Label>
      </Reveal>

      <Reveal from={1}>
        <Region
          x={350}
          y={14}
          w={250}
          h={160}
          label="Container B"
          tone="focus"
        />
        <Arrow
          points={[
            [475, 158],
            [410, 198],
          ]}
          tone="muted"
          dashed
        />
        <Box
          x={370}
          y={104}
          w={210}
          h={54}
          title="Writable layer"
          sub="empty"
        />
      </Reveal>
      <Reveal from={3}>
        <Box
          x={370}
          y={42}
          w={210}
          h={46}
          title="cat /tmp/note.txt"
          sub="No such file or directory"
          tone="bad"
          mono
        />
      </Reveal>
    </Diagram>
  ),

  "exec-process": () => (
    <Diagram height={258}>
      <Terminal
        x={10}
        y={40}
        w={250}
        lines={["$ docker run -d … sleep infinity", "$ docker exec … ps"]}
      />
      <Arrow
        points={[
          [262, 67],
          [356, 67],
        ]}
        label="starts"
        labelAt={[300, 58]}
      />
      <Arrow
        points={[
          [262, 96],
          [300, 96],
          [300, 129],
          [356, 129],
        ]}
        label="adds"
        labelAt={[281, 88]}
      />
      <Region x={340} y={16} w={290} h={196} label="Container" tone="focus" />
      <Box
        x={358}
        y={44}
        w={254}
        h={46}
        title="sleep infinity"
        sub="process 1, the main process"
        tone="good"
        mono
      />
      <Box
        x={358}
        y={106}
        w={254}
        h={46}
        title="ps"
        sub="an extra process from docker exec"
        tone="focus"
        mono
      />
      <Box x={358} y={166} w={254} h={32} title="Both see the same files" />
      <Label x={320} y={234} anchor="middle" size="small" tone="muted">
        An extra process can finish without stopping the container.
      </Label>
      <Label x={320} y={252} anchor="middle" size="small" tone="muted">
        When process 1 finishes, the container stops.
      </Label>
    </Diagram>
  ),

  "port-publishing": ({ step }) => (
    <Diagram height={236} step={step}>
      <Region x={150} y={14} w={480} h={210} label="Your computer" />
      <Terminal
        x={166}
        y={48}
        w={160}
        title="Terminal"
        lines={["$ curl 127.0.0.1:…"]}
      />
      <Region x={420} y={40} w={196} h={170} label="Container" tone="focus" />
      <Box
        x={456}
        y={112}
        w={146}
        h={56}
        title="web server"
        sub="listening on 8000"
        tone="good"
      />
      <Tag x={420} y={140} text="8000" tone="good" />
      <Reveal from={1} until={1}>
        <Arrow
          points={[
            [326, 76],
            [416, 76],
          ]}
          tone="bad"
          dashed
          label="✗ no way in"
          labelAt={[371, 66]}
        />
      </Reveal>
      <Reveal from={2}>
        <Arrow
          points={[
            [290, 103],
            [290, 127],
          ]}
          tone="focus"
        />
        <Tag x={310} y={140} text="127.0.0.1:54321" tone="focus" />
        <Arrow
          points={[
            [372, 140],
            [395, 140],
          ]}
          tone="focus"
        />
        <Label x={310} y={170} anchor="middle" size="small" tone="focus">
          published with -p
        </Label>
      </Reveal>
      <Reveal from={3}>
        <Box
          x={10}
          y={110}
          w={120}
          h={60}
          title="Another device"
          sub="on your network"
          tone="muted"
        />
        <Arrow
          points={[
            [130, 140],
            [245, 140],
          ]}
          tone="bad"
          dashed
          label="✗ refused"
          labelAt={[188, 130]}
        />
        <Label x={290} y={200} anchor="middle" size="small" tone="muted">
          127.0.0.1 means this computer only
        </Label>
      </Reveal>
    </Diagram>
  ),

  "bind-mount": () => (
    <Diagram height={222}>
      <Region x={10} y={14} w={280} h={196} label="Your computer" />
      <Label x={30} y={62} mono>
        $DOCKYARD_WORKSPACE/site/
      </Label>
      <File x={50} y={78} name="index.html" />
      <Label x={150} y={170} anchor="middle" size="small">
        Edit the file here…
      </Label>

      <Region x={350} y={14} w={280} h={196} label="Container" tone="focus" />
      <Label x={370} y={62} mono>
        /site/
      </Label>
      <File x={390} y={78} name="index.html" tone="focus" />
      <Label x={490} y={170} anchor="middle" size="small">
        …and the server sees it at once
      </Label>
      <Tag x={490} y={192} text="ro: cannot write" tone="warn" />

      <Arrow
        points={[
          [100, 94],
          [376, 94],
        ]}
        both
        tone="focus"
        label="the same files, not a copy"
        labelAt={[238, 84]}
      />
    </Diagram>
  ),

  "web-server-command": () => {
    const rows: { code: string; note: string; tone?: "focus" | "good" }[] = [
      { code: "docker run -d \\", note: "run in the background" },
      {
        code: '  --name "$DOCKYARD_CONTAINER" \\',
        note: "the name you use in later commands",
      },
      {
        code: '  --label "io.dockyard.lab=$DOCKYARD_LAB" \\',
        note: "marks it as this lab’s container",
      },
      {
        code: '  -p "127.0.0.1:$DOCKYARD_PORT:8000" \\',
        note: "your port on this computer → port 8000",
      },
      {
        code: '  -v "$DOCKYARD_WORKSPACE/site:/site:ro" \\',
        note: "your folder appears at /site, read-only",
      },
      { code: "  -w /site \\", note: "the process starts in /site" },
      {
        code: '  "$DOCKYARD_PYTHON_IMAGE" \\',
        note: "the image to start from",
        tone: "focus",
      },
      {
        code: "  python -m http.server 8000",
        note: "the main process",
        tone: "good",
      },
    ];
    return (
      <Diagram height={300}>
        <Code
          x={10}
          y={10}
          w={340}
          lines={rows.map((row) => ({ text: row.code, tone: row.tone }))}
        />
        {rows.map((row, index) => (
          <g key={row.code}>
            <Arrow
              points={[
                [354, 32 + index * 28],
                [372, 32 + index * 28],
              ]}
              tone={row.tone ?? "muted"}
            />
            <Label
              x={378}
              y={36 + index * 28}
              size="small"
              tone={row.tone ?? "default"}
            >
              {row.note}
            </Label>
          </g>
        ))}
        <Label x={10} y={272} size="small" tone="muted">
          Before the image: settings for the container.
        </Label>
        <Label x={10} y={290} size="small" tone="muted">
          After the image: the command that becomes the main process.
        </Label>
      </Diagram>
    );
  },
} satisfies Drawings;
