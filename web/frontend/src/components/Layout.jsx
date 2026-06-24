import Nav from './Nav';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Nav />
      <div className="container mx-auto px-4 py-8 overflow-hidden">
        {children}
      </div>
    </div>
  );
}
