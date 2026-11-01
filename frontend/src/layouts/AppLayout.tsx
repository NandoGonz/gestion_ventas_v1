import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function AppLayout() {
  const { user, logout } = useAuth()
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">V</span><div><strong>Ventas</strong><small>Panel de gestión</small></div></div>
        <div className="nav-caption">OPERACIÓN</div>
        <nav className="main-nav">
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}><span>▦</span>Resumen</NavLink>
          <NavLink to="/clientes" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}><span>♙</span>Clientes</NavLink>
          <NavLink to="/productos" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}><span>▤</span>Productos</NavLink>
          <NavLink to="/ventas" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}><span>↗</span>Ventas</NavLink>
        </nav>
        <div className="sidebar-bottom"><span className="status-dot" /> API conectada por sesión autenticada</div>
      </aside>
      <section className="workspace">
        <header className="topbar"><div><span className="eyebrow">SISTEMA DE GESTIÓN</span><h1>Operaciones comerciales</h1></div><div className="account"><div className="avatar">{user?.full_name?.slice(0, 1).toUpperCase() ?? 'A'}</div><div className="account-meta"><strong>{user?.full_name}</strong><small>{user?.email}</small></div><button className="button button-ghost" onClick={logout}>Cerrar sesión</button></div></header>
        <main className="content"><Outlet /></main>
      </section>
    </div>
  )
}
