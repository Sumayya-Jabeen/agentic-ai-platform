"use client";

import { SkillType } from "@/lib/types";

type Props = { skill: SkillType };

const SKILL_CONFIG = {
  research: {
    label: "Research",
    icon: (
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    className: "bg-indigo-50 text-indigo-600 border-indigo-200",
  },
  plan: {
    label: "Task Plan",
    icon: (
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
    className: "bg-emerald-50 text-emerald-600 border-emerald-200",
  },
  both: {
    label: "Research + Plan",
    icon: (
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    className: "bg-purple-50 text-purple-600 border-purple-200",
  },
};

export default function SkillBadge({ skill }: Props) {
  if (!skill) return null;
  const config = SKILL_CONFIG[skill];

  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full border ${config.className}`}>
      {config.icon}
      {config.label}
    </span>
  );
}
