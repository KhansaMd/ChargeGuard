
import { NavLink } from 'react-router-dom';

function Sidebar() {
  const navigation = [
    { name: 'Overview', path: '/', icon: '▦' },
    { name: 'Disputes', path: '/disputes', icon: '▤' },
    { name: 'Transactions', path: '/transactions', icon: '⇄' },
    { name: 'Fraud Alerts', path: '/fraud-alerts', icon: '⚠' },
    { name: 'Audit Log', path: '/audit', icon: '◷' },
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">C</div>
        <span>
          Charge<span className="brand-highlight">Guard</span>
        </span>
      </div>

      <div className="sidebar-label">WORKSPACE</div>

      <nav className="navigation">
        {navigation.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : ''}`
            }
          >
            <span>{item.icon}</span>
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="sidebar-label">ACCOUNT</div>

        <NavLink to="/settings" className="nav-item">
          <span>⚙</span>
          Settings
        </NavLink>

        <div className="profile">
          <div className="avatar">JD</div>
          <div className="profile-info">
            <strong>John Doe</strong>
            <small>Merchant Account</small>
          </div>
          <span className="profile-menu">•••</span>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
