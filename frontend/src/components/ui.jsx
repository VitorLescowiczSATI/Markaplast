export function Card({ children, className = "", ...props }) {
  return (
    <section className={`rounded-lg border border-slate-200 bg-white shadow-sm ${className}`} {...props}>
      {children}
    </section>
  );
}

export function Badge({ children, className = "" }) {
  return <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${className}`}>{children}</span>;
}

export function Field({ label, children }) {
  return (
    <label className="block space-y-1">
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span>
      {children}
    </label>
  );
}

export function Input({ className = "", ...props }) {
  return (
    <input
      {...props}
      className={`w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-100 ${className}`}
    />
  );
}

export function TextArea({ className = "", ...props }) {
  return (
    <textarea
      {...props}
      className={`min-h-20 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-100 ${className}`}
    />
  );
}

export function SelectBox({ value, onChange, children, className = "" }) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className={`w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-100 ${className}`}
    >
      {children}
    </select>
  );
}

export function Button({ children, className = "", type = "button", ...props }) {
  return (
    <button
      type={type}
      {...props}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-bold transition active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
    >
      {children}
    </button>
  );
}

export function IconButton({ label, children, className = "", ...props }) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      {...props}
      className={`inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition hover:border-red-200 hover:bg-red-50 hover:text-red-600 ${className}`}
    >
      {children}
    </button>
  );
}

export function StatCard({ label, value, detail, tone = "slate" }) {
  const tones = {
    slate: "text-slate-900",
    amber: "text-amber-700",
    sky: "text-sky-700",
    teal: "text-teal-700",
    green: "text-green-700",
  };

  return (
    <Card className="p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${tones[tone] || tones.slate}`}>{value}</p>
      {detail && <p className="mt-1 text-xs text-slate-500">{detail}</p>}
    </Card>
  );
}

export function EmptyState({ children }) {
  return <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">{children}</div>;
}
