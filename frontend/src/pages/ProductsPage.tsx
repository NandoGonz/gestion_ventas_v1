import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { createProduct, getProducts, updateProduct, formatMoney, type Product } from '../api/client'
import { useAuth } from '../context/AuthContext'

const emptyForm = { nombre: '', descripcion: '', precio: '', stock: '0' }

export function ProductsPage() {
  const { token } = useAuth()
  const [products, setProducts] = useState<Product[]>([])
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(false)
  const reload = useCallback(async () => { if (token) setProducts(await getProducts(token)) }, [token])
  useEffect(() => { reload().catch(reason => setError(reason.message)) }, [reload])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setNotice(''); setLoading(true)
    try {
      await createProduct({ nombre: form.nombre, descripcion: form.descripcion, precio: form.precio, stock: Number(form.stock) }, token!)
      setForm(emptyForm); await reload(); setNotice('Producto registrado correctamente.')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo crear el producto.') }
    finally { setLoading(false) }
  }

  async function discontinue(product: Product) {
    if (!token || !window.confirm(`¿Marcar ${product.nombre} como descontinuado?`)) return
    try { await updateProduct(product.id, { estado: 'descontinuado' }, token); await reload(); setNotice('Estado del producto actualizado.') }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo actualizar el producto.') }
  }

  return <div className="page-stack">
    <div className="page-heading"><div><p className="eyebrow">CATÁLOGO</p><h2>Productos e inventario</h2><p className="muted">Controla precios, disponibilidad y existencias.</p></div><span className="pill">{products.length} productos</span></div>
    {error && <div className="alert alert-error" role="alert">{error}</div>}{notice && <div className="alert alert-success" role="status">{notice}</div>}
    <section className="panel"><div className="panel-header"><div><h3>Registrar producto</h3><p className="muted">El precio debe ser mayor que cero y el stock no puede ser negativo.</p></div></div><form className="form-grid" onSubmit={submit}><label>Nombre<input value={form.nombre} minLength={2} maxLength={80} onChange={e => setForm({ ...form, nombre: e.target.value })} required /></label><label>Precio (COP)<input type="number" min="0.01" step="0.01" value={form.precio} onChange={e => setForm({ ...form, precio: e.target.value })} required /></label><label>Stock inicial<input type="number" min="0" max="1000000" value={form.stock} onChange={e => setForm({ ...form, stock: e.target.value })} required /></label><label className="span-2">Descripción<input value={form.descripcion} maxLength={500} onChange={e => setForm({ ...form, descripcion: e.target.value })} /></label><div className="form-actions"><button className="button button-primary" disabled={loading}>{loading ? 'Guardando…' : 'Guardar producto'}</button></div></form></section>
    <section className="panel"><div className="panel-header"><div><h3>Inventario actual</h3><p className="muted">El stock se descuenta al registrar una venta.</p></div></div>{products.length === 0 ? <p className="empty-state">No hay productos registrados.</p> : <div className="table-wrap"><table><thead><tr><th>Producto</th><th>Precio</th><th>Stock</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{products.map(product => <tr key={product.id}><td><strong>{product.nombre}</strong><small className="cell-subtitle">{product.descripcion || 'Sin descripción'}</small></td><td>{formatMoney(product.precio)}</td><td><strong>{product.stock}</strong></td><td><span className={`status status-${product.estado}`}>{product.estado}</span></td><td>{!['descontinuado', 'preventa'].includes(product.estado) ? <button className="button button-small button-ghost" onClick={() => discontinue(product)}>Descontinuar</button> : <span className="muted">—</span>}</td></tr>)}</tbody></table></div>}</section>
  </div>
}
