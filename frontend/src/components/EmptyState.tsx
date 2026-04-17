type Props = {
  title: string;
  description: string;
};

export function EmptyState({ title, description }: Props) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}
