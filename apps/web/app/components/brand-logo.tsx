import Link from "next/link";

type BrandLogoProps = {
  href?: string;
  className?: string;
  withTagline?: boolean;
  size?: "sm" | "md" | "lg";
};

function ParcelMark({ size }: { size: "sm" | "md" | "lg" }) {
  const dimension = size === "lg" ? 72 : size === "md" ? 56 : 44;

  return (
    <svg viewBox="0 0 92 92" width={dimension} height={dimension} aria-hidden className="brand-mark-svg">
      <defs>
        <linearGradient id="parcelLabPinBlue" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#1687d9" />
          <stop offset="100%" stopColor="#1250a8" />
        </linearGradient>
        <linearGradient id="parcelLabFieldGreen" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#88d53f" />
          <stop offset="100%" stopColor="#3baa3d" />
        </linearGradient>
        <linearGradient id="parcelLabFieldDark" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#4cb245" />
          <stop offset="100%" stopColor="#24884a" />
        </linearGradient>
      </defs>
      <ellipse cx="46" cy="82" rx="16" ry="4.8" fill="rgba(21, 32, 43, 0.12)" />
      <path
        d="M46 10C27.8 10 13 24.8 13 43c0 7.8 2.8 15.3 8 21.2L46 90l25-25.8c5.2-5.9 8-13.4 8-21.2C79 24.8 64.2 10 46 10Z"
        fill="url(#parcelLabPinBlue)"
      />
      <circle cx="46" cy="41" r="27.5" fill="#f5fff0" />
      <path d="M20 38c6-8 16.2-12.6 26-12.6 10.6 0 19.4 3.5 26.4 10.6v3.8H20Z" fill="url(#parcelLabFieldGreen)" />
      <path d="M20 41h52.4v11.2c-8.2 2.4-17.2 3.8-26.4 3.8-9.6 0-18.2-1.4-26-3.8Z" fill="url(#parcelLabFieldDark)" />
      <path d="M20 52.2c7.4 2.8 16.4 4.4 26 4.4 9.2 0 18.2-1.4 26.4-4.2v4.7L46 81.6 20 57.1Z" fill="#1f8c3f" />
      <path d="M15.8 50.2 33.6 38.8M26 63.2 52 48.5M43.5 77.2 69.2 56.4M14.8 42.8 38 56.6M30 27.5 58.2 42.8" stroke="#ffffff" strokeWidth="4" strokeLinecap="round" />
      <path d="M36.6 24.8 46 18.2l9.4 6.6v10.8H36.6Z" fill="#ffcb2f" />
      <path d="M33.2 27.2 46 18.2l12.8 9H33.2Z" fill="#f8bf1b" />
      <rect x="37.8" y="28" width="16.4" height="10.4" rx="1.8" fill="#ffffff" />
      <rect x="43.3" y="31.1" width="5.8" height="7.3" rx="1.2" fill="#8fc83d" />
      <rect x="50.4" y="31.1" width="3.6" height="7.3" rx="1.1" fill="#d9ec8a" />
      <rect x="19.6" y="28.6" width="3.8" height="8.8" rx="1.4" fill="#0c7b45" />
      <circle cx="21.5" cy="26.4" r="4.6" fill="#148b4f" />
      <circle cx="18.5" cy="27.4" r="3.2" fill="#1ea85d" />
      <rect x="68.2" y="28.6" width="3.8" height="8.8" rx="1.4" fill="#0c7b45" />
      <circle cx="70.1" cy="26.4" r="4.6" fill="#148b4f" />
      <circle cx="67.1" cy="27.4" r="3.2" fill="#1ea85d" />
    </svg>
  );
}

export function BrandLogo({ href, className = "", withTagline = false, size = "md" }: BrandLogoProps) {
  const content = (
    <>
      <span className={`brand-mark brand-mark-${size}`}>
        <ParcelMark size={size} />
      </span>
      <span className="brand-wordmark-wrap">
        <span className={`brand-wordmark brand-wordmark-${size}`}>
          <span className="brand-wordmark-primary">필지</span>
          <span className="brand-wordmark-accent">Lab</span>
        </span>
        {withTagline ? <span className="brand-tagline">필지와 구역을 읽는 토지 분석 도구</span> : null}
      </span>
    </>
  );

  if (href) {
    return (
      <Link href={href} className={`brand-lockup ${className}`.trim()}>
        {content}
      </Link>
    );
  }

  return <div className={`brand-lockup ${className}`.trim()}>{content}</div>;
}
