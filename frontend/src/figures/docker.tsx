import {
  Arrow,
  Box,
  Code,
  Cylinder,
  Diagram,
  File,
  ImageStack,
  Label,
  Region,
  Reveal,
  Tag,
  Terminal,
  type Tone,
} from "./kit";
import type { Drawings } from "./registry";

export const docker = {
  "container-states": () => (
    <Diagram height={278}>
      <Box x={10} y={60} w={90} h={50} title="Image" tone="muted" />
      <Box x={150} y={60} w={110} h={50} title="Created" sub="not started" />
      <Box
        x={320}
        y={60}
        w={110}
        h={50}
        title="Running"
        sub="process running"
        tone="good"
      />
      <Box
        x={500}
        y={60}
        w={120}
        h={50}
        title="Exited"
        sub="process finished"
        tone="muted"
      />
      <Box x={500} y={204} w={120} h={40} title="Removed" tone="muted" dashed />
      <Arrow
        points={[
          [100, 85],
          [146, 85],
        ]}
        label="create"
        labelAt={[123, 77]}
      />
      <Arrow
        points={[
          [260, 85],
          [316, 85],
        ]}
        label="start"
        labelAt={[288, 77]}
      />
      <Arrow
        points={[
          [430, 85],
          [496, 85],
        ]}
        label="stop"
        labelAt={[463, 77]}
      />
      <Label x={465} y={128} anchor="middle" size="small" tone="muted">
        or the process ends
      </Label>
      <Arrow
        points={[
          [540, 110],
          [540, 170],
          [375, 170],
          [375, 114],
        ]}
        label="start again"
        labelAt={[458, 162]}
      />
      <Arrow
        points={[
          [604, 110],
          [604, 200],
        ]}
        label="rm"
        labelAt={[604, 190]}
      />
      <Arrow
        points={[
          [55, 60],
          [55, 32],
          [375, 32],
          [375, 56],
        ]}
        tone="focus"
        dashed
        label="docker run = create + start"
        labelAt={[215, 24]}
      />
      <Label x={10} y={232} size="small" tone="muted">
        docker ps lists running containers.
      </Label>
      <Label x={10} y={252} size="small" tone="muted">
        docker ps -a lists created and exited ones too.
      </Label>
    </Diagram>
  ),

  "container-identity": ({ step }) => (
    <Diagram height={236} step={step}>
      <Reveal from={0} until={1}>
        <Region x={20} y={20} w={270} h={170} label="Container" tone="focus" />
        <Box x={40} y={48} w={230} h={34} title="name: dispatch" mono />
        <Box x={40} y={92} w={230} h={34} title="ID: 3f2a9c…" mono />
        <Box x={40} y={136} w={230} h={34} title="its logs and files" />
      </Reveal>
      <Reveal from={1} until={1}>
        <Tag x={155} y={212} text="stopped and started: same ID" tone="good" />
      </Reveal>
      <Reveal from={2}>
        <Region x={20} y={20} w={270} h={170} label="Container" />
        <Label x={155} y={98} anchor="middle" tone="muted">
          Removed: its ID, logs,
        </Label>
        <Label x={155} y={118} anchor="middle" tone="muted">
          and files are gone.
        </Label>
        <Tag x={155} y={212} text="the name is free again" />
      </Reveal>
      <Reveal from={3}>
        <Arrow
          points={[
            [294, 105],
            [346, 105],
          ]}
          dashed
          tone="muted"
        />
        <Region
          x={350}
          y={20}
          w={270}
          h={170}
          label="New container"
          tone="warn"
        />
        <Box x={370} y={48} w={230} h={34} title="name: dispatch" mono />
        <Box
          x={370}
          y={92}
          w={230}
          h={34}
          title="ID: 9d41e7…"
          tone="warn"
          mono
        />
        <Box x={370} y={136} w={230} h={34} title="no logs or files yet" />
        <Tag x={485} y={212} text="same name, new container" tone="warn" />
      </Reveal>
    </Diagram>
  ),

  "log-streams": () => (
    <Diagram height={212}>
      <Region x={10} y={30} w={210} h={150} label="Container" tone="focus" />
      <Box
        x={28}
        y={78}
        w={174}
        h={56}
        title="python app.py"
        sub="the main process"
        mono
      />
      <Arrow
        points={[
          [202, 94],
          [300, 94],
        ]}
        label="standard output"
        labelAt={[251, 86]}
      />
      <Arrow
        points={[
          [202, 120],
          [300, 120],
        ]}
        tone="warn"
        label="standard error"
        labelAt={[251, 140]}
      />
      <Cylinder
        x={304}
        y={60}
        w={130}
        h={96}
        title="Logs"
        sub="kept by Docker"
      />
      <Arrow
        points={[
          [434, 108],
          [474, 108],
        ]}
      />
      <Terminal
        x={478}
        y={72}
        w={152}
        lines={["$ docker logs …", "GET /healthz 200"]}
      />
      <Label x={320} y={204} anchor="middle" size="small" tone="muted">
        Logs remain after the container stops, until it is removed.
      </Label>
    </Diagram>
  ),

  "stop-signals": ({ step }) => (
    <Diagram height={210} step={step}>
      <Box
        x={10}
        y={80}
        w={140}
        h={56}
        title="docker stop"
        sub="Docker Engine"
        mono
      />
      <Box
        x={250}
        y={80}
        w={170}
        h={56}
        title="process 1"
        sub="the main process"
      />
      <Arrow
        points={[
          [150, 96],
          [246, 96],
        ]}
        tone="focus"
        label="SIGTERM"
        labelAt={[198, 88]}
      />
      <Reveal from={1} until={1}>
        <Label x={335} y={160} anchor="middle" size="small">
          closes its connections, then exits
        </Label>
        <Arrow
          points={[
            [420, 108],
            [466, 108],
          ]}
          tone="good"
        />
        <Box
          x={470}
          y={80}
          w={150}
          h={56}
          title="Exited (0)"
          sub="stopped cleanly"
          tone="good"
        />
      </Reveal>
      <Reveal from={2}>
        <Box
          x={250}
          y={80}
          w={170}
          h={56}
          title="process 1"
          sub="ignores SIGTERM"
          tone="warn"
        />
        <Arrow
          points={[
            [150, 124],
            [246, 124],
          ]}
          tone="bad"
          label="SIGKILL"
          labelAt={[198, 146]}
        />
        <Label x={198} y={166} anchor="middle" size="small" tone="muted">
          after about 10 seconds
        </Label>
        <Arrow
          points={[
            [420, 108],
            [466, 108],
          ]}
          tone="bad"
        />
        <Box
          x={470}
          y={80}
          w={150}
          h={56}
          title="Exited (137)"
          sub="killed, no clean-up"
          tone="bad"
        />
      </Reveal>
    </Diagram>
  ),
  "dockerfile-layers": ({ step = 0 }) => {
    const lines = [
      "ARG BASE_IMAGE",
      "FROM ${BASE_IMAGE}",
      "WORKDIR /tool",
      "COPY report.py ./",
      'CMD ["python", "report.py"]',
    ];
    const active = [[0, 1], [2, 3], [4], []][step] ?? [];
    return (
      <Diagram height={292} step={step}>
        <Label x={10} y={20} size="small" tone="muted">
          Dockerfile
        </Label>
        <Code
          x={10}
          y={30}
          w={280}
          lines={lines.map((text, index) => ({
            text,
            tone: active.includes(index) ? "focus" : "default",
          }))}
        />
        <Label x={10} y={222} size="small" tone="muted">
          docker build follows it from top to bottom.
        </Label>
        <Label x={420} y={210} anchor="middle" size="small" tone="muted">
          the image
        </Label>
        <Reveal from={0}>
          <ImageStack
            x={320}
            y={160}
            w={200}
            layers={["Python 3.13", "Alpine Linux files"]}
            tone="muted"
          />
        </Reveal>
        <Reveal from={1}>
          <ImageStack
            x={320}
            y={130}
            w={200}
            layers={["/tool/report.py"]}
            tone="focus"
          />
        </Reveal>
        <Reveal from={2}>
          <Tag x={420} y={90} text="start: python report.py" tone="focus" />
          <Label x={420} y={66} anchor="middle" size="small" tone="muted">
            a setting, not files
          </Label>
        </Reveal>
        <Reveal from={3}>
          <Arrow
            points={[
              [380, 222],
              [380, 244],
            ]}
          />
          <Arrow
            points={[
              [460, 222],
              [460, 244],
            ]}
          />
          <Box x={326} y={248} w={100} h={34} title="container" tone="good" />
          <Box x={436} y={248} w={100} h={34} title="container" tone="good" />
        </Reveal>
      </Diagram>
    );
  },

  "build-context": () => (
    <Diagram height={236}>
      <Region
        x={10}
        y={14}
        w={290}
        h={196}
        label="Build context: your folder"
      />
      <File x={50} y={46} name="Dockerfile" />
      <File x={140} y={46} name="app.py" />
      <File x={230} y={46} name="VERSION" />
      <File x={50} y={126} name=".dockerignore" />
      <File x={140} y={126} name="secret.env" tone="bad" />
      <File x={230} y={126} name="cache/" tone="bad" />
      <Label x={198} y={196} anchor="middle" size="small" tone="bad">
        not sent
      </Label>
      <Arrow
        points={[
          [306, 98],
          [384, 98],
        ]}
        tone="focus"
        label="sent to Docker"
        labelAt={[345, 88]}
      />
      <Box
        x={388}
        y={60}
        w={232}
        h={76}
        title="docker build"
        sub="COPY can use only what it was sent"
        tone="focus"
      />
      <Label x={320} y={228} anchor="middle" size="small" tone="muted">
        .dockerignore lists secret.env and cache/, so they are never sent.
      </Label>
    </Diagram>
  ),

  "file-image-container": ({ step = 0 }) => (
    <Diagram height={250} step={step}>
      <Label x={100} y={24} anchor="middle" size="small" tone="muted">
        Your file
      </Label>
      <Label x={320} y={24} anchor="middle" size="small" tone="muted">
        Images
      </Label>
      <Label x={540} y={24} anchor="middle" size="small" tone="muted">
        Containers
      </Label>
      <Box
        x={10}
        y={48}
        w={180}
        h={56}
        title="VERSION"
        sub={step === 0 ? "dispatch-1" : "dispatch-2"}
        tone={step === 1 ? "focus" : "default"}
        mono
      />
      <Box
        x={230}
        y={48}
        w={180}
        h={56}
        title="image a1f3…"
        sub={step >= 2 ? "dispatch-1, no tag now" : "dispatch-1"}
        tone={step >= 2 ? "muted" : "default"}
        mono
      />
      <Tag x={320} y={136} text="tag: practice" tone="focus" />
      <Reveal from={0} until={1}>
        <Arrow
          points={[
            [320, 125],
            [320, 108],
          ]}
          tone="focus"
        />
      </Reveal>
      <Reveal from={2}>
        <Arrow
          points={[
            [190, 90],
            [226, 182],
          ]}
          tone="focus"
          label="docker build"
          labelAt={[186, 150]}
        />
        <Arrow
          points={[
            [320, 147],
            [320, 166],
          ]}
          tone="focus"
        />
        <Box
          x={230}
          y={170}
          w={180}
          h={56}
          title="image 7c90…"
          sub="dispatch-2"
          tone="focus"
          mono
        />
      </Reveal>
      <Reveal from={0} until={2}>
        <Arrow
          points={[
            [410, 76],
            [446, 76],
          ]}
        />
        <Box
          x={450}
          y={48}
          w={180}
          h={56}
          title="container"
          sub={step === 0 ? "serves dispatch-1" : "still serves dispatch-1"}
          tone={step === 2 ? "warn" : "good"}
        />
      </Reveal>
      <Reveal from={3}>
        <Box
          x={450}
          y={48}
          w={180}
          h={56}
          title="old container"
          sub="removed"
          tone="muted"
          dashed
        />
        <Arrow
          points={[
            [410, 198],
            [446, 198],
          ]}
          tone="good"
        />
        <Box
          x={450}
          y={170}
          w={180}
          h={56}
          title="new container"
          sub="serves dispatch-2"
          tone="good"
        />
      </Reveal>
    </Diagram>
  ),

  "build-cache": ({ step = 0 }) => {
    const lines = [
      "FROM ${BASE_IMAGE}",
      "WORKDIR /app",
      "COPY requirements.txt ./",
      "RUN python -m pip install …",
      "COPY service/ ./service/",
    ];
    const firstRebuilt = [0, 4, 2][step] ?? 0;
    const result = (index: number): [string, Tone] =>
      step === 0
        ? ["built", "default"]
        : index < firstRebuilt
          ? ["reused from cache", "good"]
          : ["runs again", "warn"];
    return (
      <Diagram height={236} step={step}>
        <Label x={10} y={20} size="small" tone="muted">
          Dockerfile
        </Label>
        <Label x={520} y={20} anchor="middle" size="small" tone="muted">
          On this build
        </Label>
        <Code
          x={10}
          y={30}
          w={320}
          lines={lines.map((text, index) => ({
            text,
            tone: step > 0 && index >= firstRebuilt ? "focus" : "default",
          }))}
        />
        {lines.map((line, index) => {
          const [text, tone] = result(index);
          return (
            <g key={line}>
              <Arrow
                points={[
                  [336, 52 + index * 28],
                  [436, 52 + index * 28],
                ]}
                tone="muted"
                dashed
              />
              <Tag x={520} y={52 + index * 28} text={text} tone={tone} />
            </g>
          );
        })}
        <Label x={10} y={208} size="small" tone="muted">
          When one step must run again, every step after it runs again too.
        </Label>
      </Diagram>
    );
  },

  "multi-stage-build": () => (
    <Diagram height={268}>
      <Region x={10} y={14} w={280} h={222} label="Stage 1: verify" />
      <Box x={30} y={44} w={240} h={32} title="FROM ${BASE_IMAGE}" mono />
      <Label x={30} y={116} mono>
        /source/
      </Label>
      <File x={44} y={128} name="__pycache__" tone="muted" />
      <File x={124} y={128} name="app.py" />
      <File x={194} y={128} name="VERSION" />
      <Box
        x={30}
        y={192}
        w={240}
        h={32}
        title="RUN py_compile app.py"
        tone="good"
        mono
      />

      <Region
        x={350}
        y={14}
        w={280}
        h={222}
        label="Stage 2: final image"
        tone="focus"
      />
      <Box x={370} y={44} w={240} h={32} title="FROM ${BASE_IMAGE}" mono />
      <Label x={370} y={116} mono>
        /app/
      </Label>
      <File x={384} y={128} name="app.py" tone="focus" />
      <File x={454} y={128} name="VERSION" tone="focus" />
      <Box
        x={370}
        y={192}
        w={240}
        h={32}
        title="USER 10001:10001"
        tone="good"
        mono
      />
      <Arrow
        points={[
          [224, 144],
          [380, 144],
        ]}
        tone="focus"
        label="COPY --from=verify"
        labelAt={[302, 134]}
      />
      <Label x={320} y={260} anchor="middle" size="small" tone="muted">
        Only the final stage becomes the image you run; the rest of verify is
        left behind.
      </Label>
    </Diagram>
  ),
  "port-mapping-mismatch": ({ step = 0 }) => {
    const y = step === 0 ? 168 : 128;
    return (
      <Diagram height={236} step={step}>
        <Region x={10} y={14} w={620} h={210} label="Your computer" />
        <Terminal
          x={26}
          y={48}
          w={180}
          title="Terminal"
          lines={[
            "$ curl …/healthz",
            step === 0 ? "connection reset" : '{"status": "ok"}',
          ]}
        />
        <Arrow
          points={[
            [116, 122],
            [116, y],
            [226, y],
          ]}
          tone="focus"
        />
        <Tag x={290} y={y} text="127.0.0.1:49152" tone="focus" />
        <Arrow
          points={[
            [352, y],
            [375, y],
          ]}
          tone="focus"
        />
        <Region x={400} y={40} w={216} h={168} label="Container" tone="focus" />
        <Box
          x={430}
          y={100}
          w={170}
          h={56}
          title="Dispatch"
          sub="listening on 8080"
          tone="good"
        />
        <Tag
          x={400}
          y={y}
          text={step === 0 ? "8081" : "8080"}
          tone={step === 0 ? "bad" : "good"}
        />
        <Reveal from={0} until={0}>
          <Label x={515} y={190} anchor="middle" size="small" tone="bad">
            nothing listens on 8081
          </Label>
        </Reveal>
      </Diagram>
    );
  },

  "localhost-perspective": () => (
    <Diagram height={222}>
      {[
        { x: 10, label: "Your computer", place: "this computer" },
        { x: 220, label: "API container", place: "the API container" },
        { x: 430, label: "Other container", place: "that container" },
      ].map((item) => (
        <g key={item.label}>
          <Region
            x={item.x}
            y={14}
            w={200}
            h={170}
            label={item.label}
            tone={item.x === 10 ? "default" : "focus"}
          />
          <Box
            x={item.x + 20}
            y={40}
            w={160}
            h={44}
            title="request"
            sub="to 127.0.0.1"
          />
          <Arrow
            points={[
              [item.x + 100, 84],
              [item.x + 100, 116],
            ]}
          />
          <Box
            x={item.x + 20}
            y={120}
            w={160}
            h={44}
            title="arrives in"
            sub={item.place}
            tone="good"
          />
        </g>
      ))}
      <Label x={320} y={210} anchor="middle" size="small" tone="muted">
        127.0.0.1 always means the place making the request, never a neighbor.
      </Label>
    </Diagram>
  ),

  "bridge-network": ({ step = 0 }) => (
    <Diagram height={262} step={step}>
      <Region x={10} y={14} w={620} h={236} label="Your computer" />
      <Reveal from={1}>
        <Region
          x={232}
          y={40}
          w={386}
          h={168}
          label="Lab network"
          tone="focus"
        />
        <Tag x={535} y={154} text="alias: dependency" tone="focus" />
      </Reveal>
      <Terminal
        x={26}
        y={64}
        w={164}
        title="Terminal"
        lines={["$ curl …/dependency"]}
      />
      <Arrow
        points={[
          [190, 98],
          [246, 98],
        ]}
        tone="focus"
      />
      <Box
        x={250}
        y={70}
        w={150}
        h={56}
        title="API"
        sub="published port"
        tone="focus"
      />
      <Box
        x={460}
        y={70}
        w={150}
        h={56}
        title="dependency"
        sub="no published port"
      />
      <Reveal from={0} until={0}>
        <Arrow
          points={[
            [400, 98],
            [456, 98],
          ]}
          tone="bad"
          dashed
          label="✗ unknown name"
          labelAt={[430, 62]}
        />
        <Label x={320} y={234} anchor="middle" size="small" tone="bad">
          No shared network, so the name dependency means nothing to the API.
        </Label>
      </Reveal>
      <Reveal from={1} until={1}>
        <Label x={320} y={234} anchor="middle" size="small" tone="focus">
          Both containers join one network; the dependency answers to its alias.
        </Label>
      </Reveal>
      <Reveal from={2}>
        <Arrow
          points={[
            [400, 98],
            [456, 98],
          ]}
          tone="good"
          label="dependency:8080"
          labelAt={[430, 62]}
        />
        <Label x={320} y={234} anchor="middle" size="small" tone="good">
          Docker’s DNS turns the name into the dependency’s current address.
        </Label>
      </Reveal>
    </Diagram>
  ),

  "wrong-upstream": ({ step = 0 }) => (
    <Diagram height={250} step={step}>
      <Region x={10} y={14} w={620} h={222} label="Lab network" />
      <Region
        x={30}
        y={44}
        w={270}
        h={170}
        label="API container"
        tone="focus"
      />
      <Region x={340} y={44} w={270} h={170} label="Dependency container" />
      <Box
        x={50}
        y={72}
        w={230}
        h={46}
        title="Dispatch API"
        sub={
          step === 2 ? "upstream: dependency:8080" : "upstream: 127.0.0.1:8081"
        }
        tone={step === 2 ? "good" : "focus"}
      />
      <Box
        x={360}
        y={72}
        w={230}
        h={46}
        title="dependency"
        sub="listening on 8080"
        tone="good"
      />
      <Reveal from={0} until={1}>
        <Arrow
          points={[
            [200, 118],
            [200, 160],
            [120, 160],
            [120, 122],
          ]}
          tone="bad"
          label="127.0.0.1:8081"
          labelAt={[250, 146]}
        />
        <Label x={165} y={194} anchor="middle" size="small" tone="bad">
          refused: nothing listens there
        </Label>
      </Reveal>
      <Reveal from={1} until={1}>
        <Arrow
          points={[
            [280, 96],
            [356, 96],
          ]}
          tone="focus"
          dashed
        />
        <Label x={475} y={160} anchor="middle" size="small" tone="focus">
          docker exec test of
        </Label>
        <Label x={475} y={178} anchor="middle" size="small" tone="focus">
          http://dependency:8080 works
        </Label>
      </Reveal>
      <Reveal from={2}>
        <Arrow
          points={[
            [280, 96],
            [356, 96],
          ]}
          tone="good"
        />
        <Label x={165} y={160} anchor="middle" size="small" tone="good">
          replaced with the corrected setting
        </Label>
      </Reveal>
    </Diagram>
  ),
} satisfies Drawings;
