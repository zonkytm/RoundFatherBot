import { Link, useLocation } from 'react-router-dom';

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/mailings', label: 'Mailings' },
  { to: '/revenue', label: 'Revenue' },
  { to: '/settings', label: 'Settings' },
];

export default function Nav() {
  const location = useLocation();

  return (
    <nav className="bg-gray-800 px-6 py-3 flex gap-6">
      {links.map((link) => (
        <Link
          key={link.to}
          to={link.to}
          className={
            location.pathname === link.to
              ? 'text-white font-bold'
              : 'text-gray-400 hover:text-white'
          }
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
