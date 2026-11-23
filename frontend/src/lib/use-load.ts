"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type LoadState<T> = { key: string | null; data: T | undefined; error: unknown };

/**
 * Minimal data loader: { data, error, loading, reload }.
 * Re-fetches when `deps` change; optionally polls while `poll(data)` is true.
 * All state updates happen in async callbacks (never synchronously in an effect).
 */
export function useLoad<T>(
  fn: () => Promise<T>,
  deps: unknown[] = [],
  poll?: (d: T | undefined) => boolean,
  intervalMs = 3000,
) {
  const key = JSON.stringify(deps);
  const fnRef = useRef(fn);
  const keyRef = useRef(key);
  useEffect(() => {
    fnRef.current = fn;
    keyRef.current = key;
  });

  const [state, setState] = useState<LoadState<T>>({ key: null, data: undefined, error: null });

  // Fetch whenever the dependency key changes; ignore responses for stale keys.
  useEffect(() => {
    let cancelled = false;
    fnRef.current().then(
      (data) => {
        if (!cancelled) setState({ key, data, error: null });
      },
      (error) => {
        if (!cancelled) setState((s) => ({ key, data: s.data, error }));
      },
    );
    return () => {
      cancelled = true;
    };
  }, [key]);

  const reload = useCallback(async () => {
    const k = keyRef.current;
    try {
      const data = await fnRef.current();
      if (k === keyRef.current) setState({ key: k, data, error: null });
    } catch (error) {
      if (k === keyRef.current) setState((s) => ({ key: k, data: s.data, error }));
    }
  }, []);

  const shouldPoll = !!poll && poll(state.data) && state.key === key;
  useEffect(() => {
    if (!shouldPoll) return;
    const t = setTimeout(reload, intervalMs);
    return () => clearTimeout(t);
  }, [shouldPoll, state, reload, intervalMs]);

  return { data: state.data, error: state.error, loading: state.key !== key, reload };
}
