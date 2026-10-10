export function ShieldMark({ compact = false }: { compact?: boolean }) {
  return (
    <div
      className={[
        "flex shrink-0 items-center justify-center rounded-[20px] bg-gradient-to-br from-[#ff765f] via-[#ef4e91] to-[#9b64e8] shadow-[0_12px_30px_rgba(236,79,143,.28)]",
        compact ? "h-11 w-11" : "h-12 w-12",
      ].join(" ")}
      aria-label="AegisOps"
    >
      <svg
        viewBox="0 0 40 40"
        className={compact ? "h-7 w-7" : "h-8 w-8"}
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M20 4.5 31 8.6v8.8c0 7.9-4.6 14.2-11 17.1-6.4-2.9-11-9.2-11-17.1V8.6L20 4.5Z"
          fill="rgba(255,255,255,.12)"
          stroke="white"
          strokeWidth="2.2"
          strokeLinejoin="round"
        />
        <path
          d="M12.8 20h4.1l2.1-5.2 3.2 10.1 2.1-4.9h3"
          stroke="white"
          strokeWidth="2.25"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

/*
 * Decorative sidebar sculpture inspired by the reference dashboard.
 * It remains vector/CSS based, so it stays crisp at any screen density.
 */
export function BrandOrbit3D() {
  return (
    <div className="relative h-[126px] w-[126px]" aria-hidden="true">
      <svg
        viewBox="0 0 180 180"
        className="h-full w-full overflow-visible"
        fill="none"
      >
        <defs>
          <linearGradient id="outerTube" x1="24" y1="28" x2="157" y2="148" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="#ffcf63" />
            <stop offset="0.20" stopColor="#ff9b49" />
            <stop offset="0.48" stopColor="#f66a64" />
            <stop offset="0.72" stopColor="#e85896" />
            <stop offset="1" stopColor="#9d69e6" />
          </linearGradient>

          <linearGradient id="crossTube" x1="32" y1="145" x2="143" y2="27" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="#ff9a47" />
            <stop offset="0.30" stopColor="#f66b76" />
            <stop offset="0.58" stopColor="#e052a0" />
            <stop offset="0.82" stopColor="#b261de" />
            <stop offset="1" stopColor="#766fe6" />
          </linearGradient>

          <linearGradient id="shineA" x1="46" y1="40" x2="135" y2="110" gradientUnits="userSpaceOnUse">
            <stop stopColor="white" stopOpacity="0.72" />
            <stop offset="0.32" stopColor="white" stopOpacity="0.26" />
            <stop offset="1" stopColor="white" stopOpacity="0" />
          </linearGradient>

          <linearGradient id="shadeA" x1="42" y1="60" x2="142" y2="130" gradientUnits="userSpaceOnUse">
            <stop stopColor="#40152a" stopOpacity="0" />
            <stop offset="0.72" stopColor="#34133c" stopOpacity="0.22" />
            <stop offset="1" stopColor="#12091f" stopOpacity="0.46" />
          </linearGradient>

          <filter id="tubeShadow" x="-70%" y="-70%" width="240%" height="240%">
            <feDropShadow dx="0" dy="15" stdDeviation="9" floodColor="#020617" floodOpacity="0.42" />
          </filter>

          <filter id="floorBlur" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="6" />
          </filter>
        </defs>

        <ellipse
          cx="91"
          cy="92"
          rx="61"
          ry="27"
          transform="rotate(-26 91 92)"
          stroke="#050811"
          strokeOpacity="0.38"
          strokeWidth="25"
          filter="url(#tubeShadow)"
        />

        <ellipse
          cx="91"
          cy="92"
          rx="61"
          ry="27"
          transform="rotate(-26 91 92)"
          stroke="url(#outerTube)"
          strokeWidth="21"
          strokeLinecap="round"
        />

        <ellipse
          cx="92"
          cy="91"
          rx="55"
          ry="24"
          transform="rotate(49 92 91)"
          stroke="#050811"
          strokeOpacity="0.32"
          strokeWidth="24"
          filter="url(#tubeShadow)"
        />

        <ellipse
          cx="92"
          cy="91"
          rx="55"
          ry="24"
          transform="rotate(49 92 91)"
          stroke="url(#crossTube)"
          strokeWidth="20"
          strokeLinecap="round"
        />

        <path
          d="M43 75c19-20 46-29 71-24 10 2 19 6 27 12"
          stroke="url(#shineA)"
          strokeWidth="5.5"
          strokeLinecap="round"
          opacity="0.82"
        />

        <path
          d="M53 128c28 15 63 11 88-11"
          stroke="white"
          strokeOpacity="0.18"
          strokeWidth="4"
          strokeLinecap="round"
        />

        <path
          d="M112 48c22 17 31 39 28 61"
          stroke="url(#shadeA)"
          strokeWidth="7"
          strokeLinecap="round"
        />

        <ellipse
          cx="95"
          cy="145"
          rx="48"
          ry="8"
          fill="#050811"
          opacity="0.28"
          filter="url(#floorBlur)"
        />
      </svg>
    </div>
  );
}
