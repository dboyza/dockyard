import type { ReactNode } from "react";

/**
 * A link to a place on the current page. It scrolls and moves focus without
 * changing the URL fragment, which holds the workbench route.
 */
export function InPageLink({
  target,
  className,
  children,
}: {
  target: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <a
      href={`#${target}`}
      className={className}
      onClick={(event) => {
        event.preventDefault();
        const element = document.getElementById(target);
        if (!element) return;
        if (!element.hasAttribute("tabindex"))
          element.setAttribute("tabindex", "-1");
        element.scrollIntoView({ block: "start" });
        element.focus({ preventScroll: true });
      }}
    >
      {children}
    </a>
  );
}
