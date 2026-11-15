import { useEffect, useState } from "react";
import { HardDrive, Trash2 } from "lucide-react";
import { api } from "./api";
import type { Workbench } from "./useWorkbench";

type Download = { name: string; label: string; bytes: number; needed: boolean };
type Storage = {
  docker_ready: boolean;
  host_images: Download[];
  archives: Download[];
  legacy_aliases: number;
  tools_bytes: number;
  keep_downloads: boolean;
  kept_scopes: string[];
  free_disk_gib: number;
};

function size(bytes: number) {
  return bytes >= 1024 ** 3
    ? `${(bytes / 1024 ** 3).toFixed(1)} GB`
    : `${Math.round(bytes / 1024 ** 2)} MB`;
}
const total = (items: Download[]) =>
  items.reduce((sum, item) => sum + item.bytes, 0);

/** What Dockyard has downloaded, where it lives, and how long it stays. */
export function StoragePanel({ model }: { model: Workbench }) {
  const { setError, setNotice, setDialog } = model;
  const [storage, setStorage] = useState<Storage | null>(null);
  const [working, setWorking] = useState(false);
  // Preparing, cleaning up, and prefetching all change what is downloaded.
  const activity = model.state.operations
    .map((item) => `${item.id}:${item.state}`)
    .join();
  useEffect(() => {
    let alive = true;
    api<Storage>("/storage")
      .then((result) => alive && setStorage(result))
      .catch((error) => alive && setError(error.message));
    return () => {
      alive = false;
    };
  }, [activity, setError]);
  const change = async (path: string, body: unknown, done?: string) => {
    setWorking(true);
    try {
      setStorage(await api<Storage>(path, body));
      if (done) setNotice(done);
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setWorking(false);
    }
  };
  const groups = storage
    ? [
        {
          title: "In Docker",
          hint: "Images Docker runs on this computer for your labs.",
          items: storage.host_images,
        },
        {
          title: "Private cluster images",
          hint: "Loaded straight into cluster nodes, so docker images never lists them.",
          items: storage.archives,
        },
      ]
    : [];
  const images = storage
    ? storage.host_images.length + storage.archives.length
    : 0;
  return (
    <section className="panel downloads-panel" aria-labelledby="storage-title">
      <div className="section-heading">
        <h2 id="storage-title">
          <HardDrive size={20} /> Downloads
        </h2>
        {storage && (
          <span className="small muted">
            {storage.free_disk_gib} GiB free on this disk
          </span>
        )}
      </div>
      <p className="muted">
        Dockyard downloads an image the first time a lab needs it. It removes
        the image again once no lab, the module you are studying, or a
        prefetched topic needs it.
      </p>
      {!storage ? (
        <p className="muted">Looking at what is downloaded…</p>
      ) : (
        <>
          {!storage.docker_ready && (
            <p className="diagnostic">
              Docker is not running, so images in Docker are not listed.
            </p>
          )}
          <div className="downloads-groups">
            {groups.map((group) => (
              <div key={group.title}>
                <h3>
                  {group.title}
                  <span>{size(total(group.items))}</span>
                </h3>
                <p className="small muted">{group.hint}</p>
                {group.items.length ? (
                  <ul>
                    {group.items.map((item) => (
                      <li key={item.name}>
                        <span>{item.label}</span>
                        {!item.needed && (
                          <span className="status-label">Not needed now</span>
                        )}
                        <span className="mono muted">{size(item.bytes)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="small muted">Nothing downloaded.</p>
                )}
              </div>
            ))}
          </div>
          <p className="small muted">
            Tools such as kubectl and VM images use another{" "}
            {size(storage.tools_bytes)} in Dockyard’s own folder.
            {storage.legacy_aliases > 0 &&
              ` ${storage.legacy_aliases} image names from an earlier version are removed the next time a lab is cleaned up.`}
          </p>
          <div className="downloads-actions">
            <label className="switch">
              <input
                type="checkbox"
                checked={storage.keep_downloads}
                disabled={working}
                onChange={(event) =>
                  void change("/storage", {
                    keep_downloads: event.target.checked,
                  })
                }
              />
              Keep every download until I free the space
            </label>
            <button
              disabled={working || images === 0}
              onClick={() =>
                setDialog({
                  title: "Remove Dockyard’s downloaded images?",
                  body: "This removes the images Dockyard downloaded, in Docker and in its own folder, and forgets prefetched topics. Images a container still uses stay. Labs download what they need again when you prepare them.",
                  confirmLabel: "Free the space",
                  danger: true,
                  action: () => {
                    setDialog(null);
                    void change(
                      "/storage/clean",
                      { confirmed: true },
                      "Downloaded images removed.",
                    );
                  },
                })
              }
            >
              <Trash2 size={15} /> Free space now
            </button>
          </div>
        </>
      )}
    </section>
  );
}
