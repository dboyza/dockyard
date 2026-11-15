import { useEffect, useRef, useState } from "react";

/** A small menu that closes on Escape or a click anywhere outside its anchor. */
export function usePopover<T extends HTMLElement>() {
  const [open, setOpen] = useState(false);
  const anchor = useRef<T>(null);
  useEffect(() => {
    if (!open) return;
    const dismiss = (event: Event) => {
      if (event instanceof KeyboardEvent && event.key !== "Escape") return;
      if (
        event instanceof PointerEvent &&
        anchor.current?.contains(event.target as Node)
      )
        return;
      setOpen(false);
    };
    window.addEventListener("pointerdown", dismiss);
    window.addEventListener("keydown", dismiss);
    return () => {
      window.removeEventListener("pointerdown", dismiss);
      window.removeEventListener("keydown", dismiss);
    };
  }, [open]);
  return { open, setOpen, anchor };
}
