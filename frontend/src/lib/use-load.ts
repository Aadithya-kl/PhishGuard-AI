"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/** Minimal data loader: { data, error, loading, reload }. Optionally polls while `poll(data)` is true. */
export function useLoad<T>(fn: () => Promise<T>, deps: unknown[] = [], poll?: (d: T | undefined) => boolean, intervalMs = 3000) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const fnRef = useRef(fn);
  useEffect(() => {
    fnRef.current = fn;
  });

  const reload = useCallback(async () => {
    try {
      const d = await fnRef.current();
      setData(d);
      setError(null);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    setLoading(true);
    reload();
  }, [reload]);

  useEffect(() => {
    if (!poll || !poll(data)) return;
    const t = setTimeout(reload, intervalMs);
    return () => clearTimeout(t);
  }, [data, poll, reload, intervalMs]);

  return { data, error, loading, reload, setData };
}
