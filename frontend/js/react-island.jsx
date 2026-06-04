/*
 * EduAI — React Island: Akademik Özet Kartı
 * ------------------------------------------------------
 * Bu bileşen vanilla app.js'ten BAĞIMSIZ çalışır.
 * app.js analizi bitirince `eduai:analiz` custom event'i yayar,
 * bu bileşen onu dinleyip kendi animasyonlu görselini render eder.
 * Build adımı yok — React + Babel CDN üzerinden tarayıcıda derlenir.
 */
const { useState, useEffect, useRef } = React;

// Sayıyı 0'dan hedefe animasyonla artıran küçük hook
function useCountUp(target, active, duration = 700) {
  const [val, setVal] = useState(0);
  const rafRef = useRef(null);
  useEffect(() => {
    if (!active || target == null) { setVal(0); return; }
    const start = performance.now();
    const from = 0;
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
      setVal(Math.round(from + (target - from) * eased));
      if (p < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, active, duration]);
  return val;
}

// Dairesel ilerleme halkası (SVG)
function ProgressRing({ value, color }) {
  const r = 42, c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value));
  const offset = c - (pct / 100) * c;
  return (
    <svg width="110" height="110" viewBox="0 0 110 110" style={{ flexShrink: 0 }}>
      <circle cx="55" cy="55" r={r} fill="none" stroke="var(--color-border-tertiary)" strokeWidth="9" />
      <circle
        cx="55" cy="55" r={r} fill="none" stroke={color} strokeWidth="9"
        strokeLinecap="round" strokeDasharray={c} strokeDashoffset={offset}
        transform="rotate(-90 55 55)"
        style={{ transition: "stroke-dashoffset .7s cubic-bezier(.4,0,.2,1)" }}
      />
      <text x="55" y="52" textAnchor="middle" fontSize="26" fontWeight="700" fill="var(--color-text-primary)">{value}</text>
      <text x="55" y="70" textAnchor="middle" fontSize="10" fill="var(--color-text-tertiary)">/ 100</text>
    </svg>
  );
}

function Chip({ label, isim, ort, color }) {
  return (
    <div style={{
      flex: 1, background: "var(--color-background-primary)", border: "1px solid var(--color-border-tertiary)",
      borderRadius: 10, padding: "10px 12px", display: "flex", flexDirection: "column", gap: 2
    }}>
      <span style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-tertiary)", textTransform: "uppercase", letterSpacing: ".04em" }}>{label}</span>
      <span style={{ fontSize: 16, fontWeight: 700, color }}>{isim}</span>
      <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>Ort. {ort} / 100</span>
    </div>
  );
}

function OzetKart() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const handler = (e) => setData(e.detail);
    window.addEventListener("eduai:analiz", handler);
    return () => window.removeEventListener("eduai:analiz", handler);
  }, []);

  const active = !!data;
  const ortalama = useCountUp(active ? data.genelOrt : 0, active);
  const ringColor = ortalama >= 75 ? "#1D9E75" : ortalama >= 50 ? "#F59E0B" : "#E24B4A";

  return (
    <div style={{
      padding: 16, borderRadius: 14,
      background: "var(--ozet-bg)",
      border: "1px solid var(--ozet-border)"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: "var(--color-text-success)" }}>Akademik Özet</span>
      </div>

      {!active ? (
        <div style={{ fontSize: 13, color: "var(--color-text-tertiary)", padding: "18px 4px" }}>
          Analiz yapıldığında genel ortalaman, en güçlü ve gelişime açık dersin burada anlık olarak görünecek.
        </div>
      ) : (
        <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          <ProgressRing value={ortalama} color={ringColor} />
          <div style={{ display: "flex", gap: 10, flex: 1, minWidth: 220 }}>
            <Chip label="En güçlü" isim={data.guclu.isim} ort={data.guclu.ort} color={data.guclu.color} />
            <Chip label="Gelişmeli" isim={data.zayif.isim} ort={data.zayif.ort} color={data.zayif.color} />
          </div>
        </div>
      )}
    </div>
  );
}

const _root = document.getElementById("react-ozet-root");
if (_root) ReactDOM.createRoot(_root).render(<OzetKart />);
