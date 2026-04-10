"use client";

import { useEffect, useRef } from "react";

interface UseProctoringLockdownOptions {
  isActive: boolean;
  onFullscreenExit?: () => void;
  /** Called when requestFullscreen() rejects (e.g. permission denied). */
  onFullscreenReenterFailed?: () => void;
  /** CSS selector — right-click is blocked only on matching elements.
   *  If omitted, right-click is blocked on the entire document. */
  contentSelector?: string;
  /** Called when a proctoring violation is detected (e.g. TAB_SWITCH). */
  onViolation?: (type: string) => void;
}

const BLOCKED_KEYS = ["F12", "F11", "Escape", "PrintScreen"] as const;
const BLOCKED_CTRL = ["c", "v", "p", "s", "a", "u"] as const;
const BLOCKED_CTRL_SHIFT = ["i", "j", "c"] as const;

/** @returns null — all work is side-effect only. */
export function useProctoringLockdown({
  isActive,
  onFullscreenExit,
  onFullscreenReenterFailed,
  contentSelector,
  onViolation,
}: UseProctoringLockdownOptions) {
  // Keep the latest callbacks in refs so the fullscreenchange listener
  // always calls the current versions without needing to rebuild the listener.
  const onFullscreenExitRef = useRef(onFullscreenExit);
  const onFullscreenReenterFailedRef = useRef(onFullscreenReenterFailed);
  const onViolationRef = useRef(onViolation);

  useEffect(() => {
    onFullscreenExitRef.current = onFullscreenExit;
    onFullscreenReenterFailedRef.current = onFullscreenReenterFailed;
    onViolationRef.current = onViolation;
  });

  useEffect(() => {
    if (!isActive) return;

    const handler = (e: KeyboardEvent) => {
      if (BLOCKED_KEYS.includes(e.key as (typeof BLOCKED_KEYS)[number])) {
        e.preventDefault();
        return;
      }

      if (e.ctrlKey || e.metaKey) {
        const key = e.key.toLowerCase();
        if (BLOCKED_CTRL.includes(key as (typeof BLOCKED_CTRL)[number])) {
          e.preventDefault();
          return;
        }
        if (e.shiftKey) {
          const shiftKey = e.key.toLowerCase();
          if (
            BLOCKED_CTRL_SHIFT.includes(
              shiftKey as (typeof BLOCKED_CTRL_SHIFT)[number]
            )
          ) {
            e.preventDefault();
            return;
          }
        }
        if (e.altKey && e.key === "F4") {
          e.preventDefault();
          return;
        }
      }
    };

    // Right-click blocked on the content area only when contentSelector is provided
    const contextHandler = (e: MouseEvent) => {
      if (!contentSelector) {
        e.preventDefault();
        return;
      }
      const target = e.target as HTMLElement;
      if (target.closest(contentSelector)) {
        e.preventDefault();
      }
    };

    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) {
        onFullscreenExitRef.current?.();
        const req = document.documentElement.requestFullscreen?.();
        if (req) {
          req.then(() => {
            // re-entered fullscreen automatically
          }).catch(() => {
            // Permission denied or not allowed — degrade gracefully
            onFullscreenReenterFailedRef.current?.();
          });
        }
      }
    };

    // Detect tab/window switch (visibilitychange fires when user switches tabs or minimizes)
    const handleVisibilityChange = () => {
      if (document.hidden) {
        onViolationRef.current?.("TAB_SWITCH");
      }
    };

    document.addEventListener("keydown", handler, true);
    document.addEventListener("contextmenu", contextHandler, true);
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      document.removeEventListener("keydown", handler, true);
      document.removeEventListener("contextmenu", contextHandler, true);
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [isActive, contentSelector]);
}

/** Non-rendering wrapper — drops into the tree to activate the hook. */
export default function ProctoringLockdown(props: UseProctoringLockdownOptions) {
  useProctoringLockdown(props);
  return null;
}
