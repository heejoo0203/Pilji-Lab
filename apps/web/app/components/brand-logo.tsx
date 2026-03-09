import Link from "next/link";

type BrandLogoProps = {
  href?: string;
  className?: string;
  withTagline?: boolean;
  size?: "sm" | "md" | "lg";
};

function BrandMark({ size }: { size: "sm" | "md" | "lg" }) {
  const dimension = size === "lg" ? 68 : size === "md" ? 54 : 42;

  return (
    <svg viewBox="0 0 64 64" width={dimension} height={dimension} aria-hidden className="brand-mark-svg">
      <defs>
        <linearGradient id="pinGradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#67c336" />
          <stop offset="100%" stopColor="#1c69c8" />
        </linearGradient>
        <linearGradient id="fieldGradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#7ed13f" />
          <stop offset="100%" stopColor="#329d4c" />
        </linearGradient>
      </defs>
      <path d="M32 60c-3.8-5.6-7.4-10-10.8-13.5C14.7 39.6 10 33.4 10 24.8 10 12.8 19.4 4 32 4s22 8.8 22 20.8c0 8.7-4.7 14.9-11.2 21.7C39.4 50 35.8 54.4 32 60Z" fill="url(#pinGradient)" />
      <circle cx="32" cy="25" r="16.5" fill="#f8fffb" />
      <path d="M18 31.5 32 21l14 10.5V41H18Z" fill="#1f63be" />
      <path d="M21 30.5 32 22.3l11 8.2V40H21Z" fill="#fff" />
      <path d="M22 38.5V31l10-7.1 10 7.1v7.5Z" fill="#eef7eb" />
      <path d="M18 41h28l-4 6H22Z" fill="url(#fieldGradient)" />
      <path d="M22 41h8l-3 6h-7Z" fill="#6acc34" />
      <path d="M30 41h8l-2 6h-9Z" fill="#3c8dd8" />
      <path d="M38 41h8l-4 6h-6Z" fill="#2e7f3f" />
      <path d="M31 31.8h4.8v8.2H31Z" fill="#ffd85a" />
      <path d="M25.4 31.8H31V36h-5.6Zm10.4 0H41V36h-5.2Z" fill="#ffcf33" />
      <circle cx="44.5" cy="16.5" r="3.4" fill="#ffd85a" />
    </svg>
  );
}

export function BrandLogo({ href, className = "", withTagline = false, size = "md" }: BrandLogoProps) {
  const content = (
    <>
      <span className={`brand-mark brand-mark-${size}`}>
        <BrandMark size={size} />
      </span>
      <span className="brand-wordmark-wrap">
        <span className={`brand-wordmark brand-wordmark-${size}`}>
          <span className="brand-wordmark-primary">필지</span>
          <span className="brand-wordmark-accent">Lab</span>
        </span>
        {withTagline ? <span className="brand-tagline">필지 경계 기반 토지 분석 플랫폼</span> : null}
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
