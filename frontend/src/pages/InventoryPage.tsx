import { useCallback, useEffect, useState, type FormEvent } from 'react'
import {
  getInventory,
  getInventoryMovements,
  registerInventoryEntry,
  registerInventoryExit,
  type InventoryMovement,
  type Product,
} from '../api/client'
import { useAuth } from '../context/AuthContext'

type MovementForm = { producto_id: string; cantidad: string; motivo: string }

const emptyForm = (): MovementForm => ({ producto_id: '', cantidad: '1', motivo: '' })

export function InventoryPage() {
  const { token } = useAuth()
  const [products, setProducts] = useState<Product[]>([])
  const [movements, setMovements] = useState<InventoryMovement[]>([])
  const [entry, setEntry] = useState(emptyForm)
  const [exit, setExit] = useState(emptyForm)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState<'entry' | 'exit' | null>(null)

  const reload = useCallback(async () => {
    if (!token) return
    const [productRows, movementRows] = await Promise.all([getInventory(token), getInventoryMovements(token)])
    setProducts(productRows)
    setMovements(movementRows)
  }, [token])

  useEffect(() => { reload().catch(reason => setError(reason.message)) }, [reload])

  const operableProducts = products.filter(product => !['descontinuado', 'preventa'].includes(product.estado))

  async function submit(
    event: FormEvent<HTMLFormElement>,
    type: 'entry' | 'exit',
    form: MovementForm,
  ) {
    event.preventDefault()
    setError('')
    setNotice('')
    setLoading(type)
    try {
      const payload = {
        producto_id: Number(form.producto_id),
        cantidad: Number(form.cantidad),
        motivo: form.motivo,
      }
      const movement = type === 'entry'
        ? await registerInventoryEntry(payload, token!)
        : await registerInventoryExit(payload, token!)
      if (type === 'entry') setEntry(emptyForm())
      else setExit(emptyForm())
      await reload()
      setNotice(`${type === 'entry' ? 'Entrada' : 'Salida'} registrada para ${movement.producto_nombre}.`)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo registrar el movimiento.')
    } finally {
      setLoading(null)
    }
  }

  return <div className="page-stack">
    <div className="page-heading"><div><p className="eyebrow">OPERACIÓN</p><h2>Inventario</h2><p className="muted">Administra entradas y salidas con historial inmutable.</p></div><span className="pill">{products.length} productos</span></div>
    {error && <div className="alert alert-error" role="alert">{error}</div>}{notice && <div className="alert alert-success" role="status">{notice}</div>}
    <section className="panel"><div className="panel-header"><div><h3>Existencias actuales</h3><p className="muted">El stock actual del producto es la fuente de verdad.</p></div></div>{products.length === 0 ? <p className="empty-state">No hay productos registrados.</p> : <div className="table-wrap"><table><thead><tr><th>Producto</th><th>Stock</th><th>Estado</th></tr></thead><tbody>{products.map(product => <tr key={product.id}><td><strong>{product.nombre}</strong><small className="cell-subtitle">{product.descripcion || 'Sin descripción'}</small></td><td><strong>{product.stock}</strong></td><td><span className={`status status-${product.estado}`}>{product.estado}</span></td></tr>)}</tbody></table></div>}</section>
    <div className="inventory-forms">
      <section className="panel"><div className="panel-header"><div><h3>Registrar entrada</h3><p className="muted">Incrementa existencias y conserva el motivo.</p></div></div><form className="form-grid" onSubmit={event => submit(event, 'entry', entry)}><label>Producto<select value={entry.producto_id} onChange={event => setEntry({ ...entry, producto_id: event.target.value })} required><option value="">Selecciona un producto</option>{operableProducts.map(product => <option key={product.id} value={product.id}>{product.nombre} · stock {product.stock}</option>)}</select></label><label>Cantidad<input type="number" min="1" max="1000000" value={entry.cantidad} onChange={event => setEntry({ ...entry, cantidad: event.target.value })} required /></label><label className="span-2">Motivo<input value={entry.motivo} minLength={1} maxLength={500} onChange={event => setEntry({ ...entry, motivo: event.target.value })} required /></label><div className="form-actions"><button className="button button-primary" disabled={loading !== null}>{loading === 'entry' ? 'Registrando…' : 'Registrar entrada'}</button></div></form></section>
      <section className="panel"><div className="panel-header"><div><h3>Registrar salida</h3><p className="muted">Requiere motivo y no permite exceder el stock disponible.</p></div></div><form className="form-grid" onSubmit={event => submit(event, 'exit', exit)}><label>Producto<select value={exit.producto_id} onChange={event => setExit({ ...exit, producto_id: event.target.value })} required><option value="">Selecciona un producto</option>{operableProducts.map(product => <option key={product.id} value={product.id}>{product.nombre} · stock {product.stock}</option>)}</select></label><label>Cantidad<input type="number" min="1" max="1000000" value={exit.cantidad} onChange={event => setExit({ ...exit, cantidad: event.target.value })} required /></label><label className="span-2">Motivo<input value={exit.motivo} minLength={1} maxLength={500} onChange={event => setExit({ ...exit, motivo: event.target.value })} required /></label><div className="form-actions"><button className="button button-danger" disabled={loading !== null}>{loading === 'exit' ? 'Registrando…' : 'Registrar salida'}</button></div></form></section>
    </div>
    <section className="panel"><div className="panel-header"><div><h3>Historial de movimientos</h3><p className="muted">Las ventas se registran automáticamente sin duplicar descuentos.</p></div><span className="pill pill-soft">{movements.length} movimientos</span></div>{movements.length === 0 ? <p className="empty-state">Todavía no hay movimientos de inventario.</p> : <div className="table-wrap"><table><thead><tr><th>Fecha</th><th>Producto</th><th>Tipo</th><th>Cantidad</th><th>Motivo</th><th>Venta</th></tr></thead><tbody>{movements.map(movement => <tr key={movement.id}><td>{new Date(movement.fecha_creacion).toLocaleString('es-CO')}</td><td><strong>{movement.producto_nombre}</strong></td><td><span className="pill">{movement.tipo_movimiento}</span></td><td>{movement.cantidad}</td><td>{movement.motivo}</td><td>{movement.venta_id ? `#${movement.venta_id}` : '—'}</td></tr>)}</tbody></table></div>}</section>
  </div>
}
