import type { ReactNode } from "react";

type FeedbackStateProps = {
  icon: ReactNode;
  title: string;
  description: string;
};

export function FeedbackState({ icon, title, description }: FeedbackStateProps) {
  return (
    <div className="feedback-state">
      <span className="feedback-state-icon" aria-hidden="true">{icon}</span>
      <strong>{title}</strong>
      <span>{description}</span>
    </div>
  );
}
