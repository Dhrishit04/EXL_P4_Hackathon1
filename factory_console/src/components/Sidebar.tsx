/* Renders the console's primary navigation. */
import { ClipboardList, Home, LayoutDashboard, ShieldCheck } from 'lucide-react'
import { NavLink } from 'react-router-dom'

/** Shows the brand and navigation links for the console. */
export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          <ShieldCheck size={20} />
        </span>
        <span className="brand-name">ModelPassport</span>
      </div>
      <nav className="navigation" aria-label="Main navigation">
        <NavLink to="/" end aria-label="Home">
          <Home size={17} aria-hidden="true" />
          <span className="navigation-label">Home</span>
        </NavLink>
        <NavLink to="/dashboard" end aria-label="Dashboard">
          <LayoutDashboard size={17} aria-hidden="true" />
          <span className="navigation-label">Dashboard</span>
        </NavLink>
        <NavLink to="/models" aria-label="Inventory">
          <ClipboardList size={17} aria-hidden="true" />
          <span className="navigation-label">Inventory</span>
        </NavLink>
      </nav>
      <p className="sidebar-footer">Model risk evidence workspace</p>
    </aside>
  )
}
