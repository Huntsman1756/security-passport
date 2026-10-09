import { useId, useState } from "react";
import { useNavigate } from "react-router-dom";
import { checkIsin, normalizeIsin } from "../lib/isin";

/** ISIN input with instant structure/check-digit feedback. */
export function IsinSearch({ size = "lg" }: { size?: "sm" | "lg" }) {
  const [q, setQ] = useState("");
  const [touched, setTouched] = useState(false);
  const nav = useNavigate();
  const hintId = useId();
  const res = checkIsin(q);
  const showError = touched && q.length > 0 && !res.ok;

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (!res.ok) return;
    setQ("");
    setTouched(false);
    nav(`/isin/${res.isin}`);
  };

  const sm = size === "sm";
  return (
    <form onSubmit={submit} className={`relative ${sm ? "w-full" : "w-full max-w-xl"}`} noValidate>
      <div className="flex gap-2">
        <input
          value={q}
          onChange={(e) => {
            setQ(normalizeIsin(e.target.value).slice(0, 12));
            if (normalizeIsin(e.target.value).length >= 12) setTouched(true);
          }}
          onBlur={() => setTouched(true)}
          placeholder={sm ? "Search ISIN" : "Enter an ISIN, e.g. DE000A3LJCB4"}
          maxLength={14}
          autoFocus={!sm}
          spellCheck={false}
          autoComplete="off"
          aria-label={sm ? "Search ISIN" : "ISIN"}
          aria-invalid={showError}
          aria-describedby={showError ? hintId : undefined}
          className={`mono min-w-0 flex-1 rounded-md border bg-[var(--surface-2)] tracking-wider outline-none placeholder:tracking-normal placeholder:text-[var(--ink-3)] focus:border-[var(--accent)] ${
            showError ? "border-rose-500/60" : "border-[var(--line)]"
          } ${sm ? "h-8 px-2.5 text-[12.5px]" : "h-12 px-4 text-[15px]"}`}
        />
        {sm ? null : (
          <button
            type="submit"
            className="h-12 shrink-0 whitespace-nowrap rounded-md bg-[var(--accent)] px-6 text-[14px] font-medium text-white transition hover:brightness-110"
          >
            Build passport
          </button>
        )}
      </div>
      {showError && !res.ok ? (
        <p id={hintId} role="alert" className={`mt-1.5 text-rose-600 dark:text-rose-400 ${sm ? "absolute text-[11px]" : "text-[12.5px]"}`}>
          {res.reason}
        </p>
      ) : null}
    </form>
  );
}
