import React from "react";

interface DissoundLogoProps {
  className?: string;
  size?: number;
}

export default function DissoundLogo({ className = "w-10 h-10", size }: DissoundLogoProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 512 512"
      width={size}
      height={size}
      className={className}
      fill="none"
    >
      <rect width="512" height="512" rx="128" fill="#0E1017" />
      <rect x="8" y="8" width="496" height="496" rx="120" stroke="#1A1E29" strokeWidth="6" />
      <g transform="translate(48, 48)">
        <path
          d="M 104 80 H 232 C 310 80, 368 138, 368 208 C 368 278, 310 336, 232 336 H 104 Z"
          stroke="#FFFFFF"
          strokeWidth="38"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        <rect x="194" y="158" width="28" height="100" rx="14" fill="#5865F2" />
        <rect x="238" y="128" width="28" height="160" rx="14" fill="#5865F2" />
        <rect x="282" y="158" width="28" height="100" rx="14" fill="#5865F2" />
      </g>
    </svg>
  );
}
