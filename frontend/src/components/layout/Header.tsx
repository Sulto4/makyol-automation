interface HeaderProps {
  title: string;
  actions?: React.ReactNode;
}

export default function Header({ title, actions }: HeaderProps) {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{title}</h1>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  );
}
