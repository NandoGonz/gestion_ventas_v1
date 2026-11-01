import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { createSale, getClients, getProducts, getSales, formatMoney, type Client, type Product, type Sale } from '../api/client'
import { useAuth } from '../context/AuthContext'

type DetailForm = { producto_id: string; cantidad: string }
const emptyLine = (): DetailForm => ({ producto_id: '', cantidad: '1' })

export function SalesPage() {
  const { token } = useAuth()
  const [clients, setClients] = useState<Client[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [sales, setSales] = useState<Sale[]>([])
  const [clientDocument, setClientDocument] = useState('')
  const [payment, setPayment] = useState<'decontado' | 'credito' | 'transferencia'>('decontado')
  const [lines, setLines] = useState<DetailForm[]>([emptyLine()])
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(false)

  const reload = useCallback(async () => {
    if (!token) return
    const [clientRows, productRows, saleRows] = await Promise.all([getClients(token), getProducts(token), getSales(token)])
    setClients(clientRows); setProducts(productRows); setSales(saleRows)
  }, [token])
  useEffect(() => { reload().catch(reason => setError(reason.message)) }, [reload])

  const activeClients = clients.filter(client => client.estado === 'activo')
  const availableProducts = products.filter(product => product.estado === 'disponible' && product.stock > 0)
  const estimatedTotal = lines.reduce((total, line) => {
    const product = products.find(item => item.id === Number(line.producto_id))
    return total + (product ? Number(product.precio) * Math.max(0, Number(line.cantidad) || 0) : 0)
  }, 0)

  function updateLine(index: number, key: keyof DetailForm, value: string) {
    setLines(current => current.map((line, row) => row === index ? { ...line, [key]: value } : line))
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setNotice(''); setLoading(true)
    try {
      const selectedIds = lines.map(line => Number(line.producto_id))
      if (new Set(selectedIds).size !== selectedIds.length) throw new Error('Cada producto debe aparecer una sola vez. Ajusta la cantidad en una sola línea.')
      const payload = { cliente_documento: Number(clientDocument), forma_pago: payment, detalles: lines.map(line => ({ producto_id: Number(line.producto_id), cantidad: Number(line.cantidad) })) }
      const sale = await createSale(payload, token!)
      setClientDocument(''); setPayment('decontado'); setLines([emptyLine()]); await reload()
      setNotice(`Venta #${sale.id} registrada por ${formatMoney(sale.total)}.`)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo registrar la venta.') }
    finally { setLoading(false) }
  }

  return <div className="page-stack">
    <div className="page-heading"><div><p className="eyebrow">OPERACIÓN</p><h2>Ventas</h2><p className="muted">Registra ventas con existencias verificadas por el backend.</p></div><span className="pill">{sales.length} recientes</span></div>
    {error && <div className="alert alert-error" role="alert">{error}</div>}{notice && <div className="alert alert-success" role="status">{notice}</div>}
    <section className="panel"><div className="panel-header"><div><h3>Nueva venta</h3><p className="muted">El total definitivo y el descuento de inventario los calcula la API.</p></div></div><form className="form-stack" onSubmit={submit}><div className="form-grid"><label>Cliente<select value={clientDocument} onChange={e => setClientDocument(e.target.value)} required><option value="">Selecciona un cliente</option>{activeClients.map(client => <option key={client.documento} value={client.documento}>{client.documento} · {client.nombre} {client.apellido}</option>)}</select></label><label>Forma de pago<select value={payment} onChange={e => setPayment(e.target.value as typeof payment)}><option value="decontado">De contado</option><option value="transferencia">Transferencia</option><option value="credito">Crédito</option></select></label></div><div className="lines-heading"><h4>Detalle de la venta</h4><button className="button button-small button-ghost" type="button" onClick={() => setLines(current => [...current, emptyLine()])} disabled={lines.length >= 100}>+ Añadir producto</button></div>{lines.map((line, index) => <div className="sale-line" key={index}><label>Producto<select value={line.producto_id} onChange={e => updateLine(index, 'producto_id', e.target.value)} required><option value="">Selecciona un producto</option>{availableProducts.map(product => <option key={product.id} value={product.id}>{product.nombre} · {formatMoney(product.precio)} · stock {product.stock}</option>)}</select></label><label>Cantidad<input type="number" min="1" max="1000000" value={line.cantidad} onChange={e => updateLine(index, 'cantidad', e.target.value)} required /></label>{lines.length > 1 && <button className="button button-small button-danger" type="button" aria-label={`Eliminar línea ${index + 1}`} onClick={() => setLines(current => current.filter((_, row) => row !== index))}>Quitar</button>}</div>)}<div className="sale-summary"><span>Total estimado</span><strong>{formatMoney(estimatedTotal)}</strong><small>El precio final se obtiene de la base de datos al registrar.</small></div><div><button className="button button-primary" disabled={loading || activeClients.length === 0 || availableProducts.length === 0}>{loading ? 'Registrando…' : 'Confirmar venta'}</button></div></form></section>
    <section className="panel"><div className="panel-header"><div><h3>Historial reciente</h3><p className="muted">Los detalles guardan el precio aplicado al momento de la venta.</p></div></div>{sales.length === 0 ? <p className="empty-state">Todavía no hay ventas registradas.</p> : <div className="sales-list">{sales.map(sale => <article className="sale-card" key={sale.id}><div className="sale-card-head"><div><strong>Venta #{sale.id}</strong><small>{sale.fecha} · Cliente {sale.cliente_documento} · {sale.forma_pago}</small></div><strong className="sale-total">{formatMoney(sale.total)}</strong></div><div className="sale-card-lines">{sale.detalle_ventas.map(line => <div key={line.id}><span>{line.producto_nombre} × {line.cantidad}</span><span>{formatMoney(line.subtotal)}</span></div>)}</div></article>)}</div>}</section>
  </div>
}
