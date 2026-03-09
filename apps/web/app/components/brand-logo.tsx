import Image from "next/image";
import Link from "next/link";

type BrandLogoProps = {
  href?: string;
  className?: string;
  priority?: boolean;
  withTagline?: boolean;
  size?: "sm" | "md" | "lg";
};

export function BrandLogo({
  href,
  className = "",
  priority = false,
  withTagline = false,
  size = "md",
}: BrandLogoProps) {
  const content = (
    <>
      <span className={`brand-logo-frame brand-logo-frame-${size}`}>
        <Image
          src="/brand/piljilab-logo.png"
          alt="필지랩"
          width={400}
          height={140}
          priority={priority}
          className="brand-logo-image"
        />
      </span>
      {withTagline ? <span className="brand-tagline">필지 경계 기반 토지 분석 플랫폼</span> : null}
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
