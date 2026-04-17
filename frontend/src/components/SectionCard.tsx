import type { PropsWithChildren, ReactNode } from "react";

type Props = PropsWithChildren<{
  title: string;
  description?: string;
  aside?: ReactNode;
  className?: string;
}>;

export function SectionCard({ title, description, aside, className, children }: Props) {
  return (
    <section className={`panel ${className ?? ""}`.trim()}>
      <header className="panel-header">
        <div>
          <h2>{title}</h2>
          {description ? <p className="muted">{description}</p> : null}
        </div>
        {aside ? <div>{aside}</div> : null}
      </header>
      {children}
    </section>
  );
}
