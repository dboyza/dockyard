import { useEffect, useState } from "react";
import { Copy, Terminal } from "lucide-react";
import { api } from "./api";
import type { Workbench } from "./useWorkbench";

type TerminalInfo = {
  options: { id: string; label: string }[];
  selected: string;
  automatic: string | null;
  command: string;
  wsl: boolean;
};

export function TerminalLauncher({
  model,
  unitId,
}: {
  model: Workbench;
  unitId: string;
}) {
  const [info, setInfo] = useState<TerminalInfo | null>(null);
  const [selected, setSelected] = useState("auto");
  const [error, setError] = useState("");
  const { busy, perform, setNotice, setError: reportError } = model;
  useEffect(() => {
    let active = true;
    api<TerminalInfo>(`/units/${unitId}/terminal`)
      .then((result) => {
        if (active) {
          setInfo(result);
          setSelected(result.selected);
          setError("");
        }
      })
      .catch((reason) => {
        if (active) setError((reason as Error).message);
      });
    return () => {
      active = false;
    };
  }, [unitId]);
  return (
    <div className="terminal-launcher">
      {info && info.options.length > 0 && (
        <>
          <label className="terminal-choice">
            Terminal application
            <select
              value={selected}
              disabled={!!busy}
              onChange={(event) => setSelected(event.target.value)}
            >
              <option value="auto">Automatic · {info.automatic}</option>
              {info.options.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <button
            className="primary full"
            disabled={!!busy}
            onClick={() => void perform("terminal", false, unitId, selected)}
          >
            <Terminal size={16} /> Open terminal
          </button>
        </>
      )}
      {error && (
        <p className="diagnostic" role="status">
          {error}
        </p>
      )}
      {!info && !error && (
        <p className="small muted" role="status">
          Finding terminal applications…
        </p>
      )}
      {info && (
        <details className="terminal-command" open={info.options.length === 0}>
          <summary>Use an existing terminal</summary>
          <p className="small muted">
            {info.wsl
              ? "Run this in a WSL shell, including one opened in Windows Terminal or your editor."
              : "Run this in any terminal, including your editor, tmux, or an SSH session on this computer."}
          </p>
          <code>{info.command}</code>
          <button
            className="small-button"
            onClick={() =>
              navigator.clipboard
                .writeText(info.command)
                .then(() => setNotice("Lab command copied."))
                .catch(() =>
                  reportError(
                    "Clipboard unavailable. Select and copy the displayed command.",
                  ),
                )
            }
          >
            <Copy size={13} /> Copy lab command
          </button>
        </details>
      )}
    </div>
  );
}
