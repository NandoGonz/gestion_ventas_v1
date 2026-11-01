import { useEffect, useState } from 'react'
import { getClients, getProducts, getSales, formatMoney, type Client, type Product, type Sale } from '../api/client'
import { useAuth } from '../context/AuthContext'

export function DashboardPage() {
  const { token } = useAuth()
  const [clients, setClients] = useState<Client[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [sales, setSales] = useState<Sale[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    Promise.all([getClients(token), getProducts(token), getSales(token)])
      .then(([clientRows, productRows, saleRows]) => { setClients(clientRows); setProducts(productRows); setSales(saleRows); setError('') })
      .catch(reason => setError(reason instanceof Error ? reason.message : 'No se pudo cargar el resumen.'))
  }, [token])

  const activeClients = clients.filter(client => client.estado === 'activo').length
  const availableProducts = products.filter(product => product.estado === 'disponible').length
  const stockLow = products.filter(product => product.stock > 0 && product.stock <= 5).length
  const totalSales = sales.reduce((sum, sale) => sum + Number(sale.total), 0)

  return <div className="page-stack">
    <div className="page-heading"><div><p className="eyebrow">RESUMEN</p><h2>Panel general</h2><p className="muted">Una vista rápida del estado de tu operación.</p></div><span className="pill pill-soft">V1 · MVP</span></div>
    {error && <div className="alert alert-error" role="alert">{error}</div>}
    <div className="metric-grid">
      <article className="metric-card"><span className="metric-icon metric-blue">♙</span><span className="metric-label">Clientes activos</span><strong>{activeClients}</strong><small>De {clients.length} registrados</small></article>
      <article className="metric-card"><span className="metric-icon metric-green">▤</span><span className="metric-label">Productos disponibles</span><strong>{availableProducts}</strong><small>{products.length} referencias registradas</small></article>
      <article className="metric-card"><span className="metric-icon metric-orange">↗</span><span className="metric-label">Ventas registradas</span><strong>{sales.length}</strong><small>Hasta 100 ventas recientes</small></article>
      <article className="metric-card"><span className="metric-icon metric-purple">$</span><span className="metric-label">Valor de ventas recientes</span><strong>{formatMoney(totalSales)}</strong><small>Suma del listado cargado</small></article>
    </div>
    <div className="dashboard-columns">
      <section className="panel"><div className="panel-header"><div><h3>Ventas recientes</h3><p className="muted">Últimos movimientos registrados</p></div><span className="pill">{sales.length}</span></div>{sales.length === 0 ? <p className="empty-state">Todavía no hay ventas registradas.</p> : <div className="table-wrap"><table><thead><tr><th>Venta</th><th>Fecha</th><th>Cliente</th><th>Total</th></tr></thead><tbody>{sales.slice(0, 6).map(sale => <tr key={sale.id}><td><strong>#{sale.id}</strong></td><td>{sale.fecha}</td><td>{sale.cliente_documento}</td><td>{formatMoney(sale.total)}</td></tr>)}</tbody></table></div>}</section>
      <section className="panel"><div className="panel-header"><div><h3>Atención de inventario</h3><p className="muted">Productos que requieren revisión</p></div></div><div className="inventory-alert"><span className="alert-icon">!</span><div><strong>{stockLow} productos con stock bajo</strong><p className="muted">Revisa los productos con cinco unidades o menos.</p></div></div><div className="inventory-alert"><span className="alert-icon alert-icon-muted">↗</span><div><strong>{products.filter(product => product.estado === 'agotado').length} agotados</strong><p className="muted">No se pueden incluir en nuevas ventas.</p></div></div></section>
    </div>
  </div>
}
