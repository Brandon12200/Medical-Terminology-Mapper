import { Outlet } from 'react-router-dom';
import { Header } from './Header';

export const Layout = () => {
  return (
    <div>
      <Header />
      <main className="main-container">
        <Outlet />
      </main>
    </div>
  );
};