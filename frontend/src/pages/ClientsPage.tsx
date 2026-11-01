import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { createClient, deactivateClient, getClients, formatMoney, type Client } from '../api/client'
import { useAuth } from '../context/AuthContext'

const emptyForm = { documento: '', nombre: '', apellido: '', direccion: '', email: '' }

export function ClientsPage() {
  const { token } = useAuth()
  const [clients, setClients] = useState<Client[]>([])
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(false)

  const reload = useCallback(async () => { if (token) setClients(await getClients(token)) }, [token])
  useEffect(() => { reload().catch(reason => setError(reason.message)) }, [reload])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setNotice(''); setLoading(true)
    try {
      await createClient({ documento: Number(form.documento), nombre: form.nombre, apellido: form.apellido, direccion: form.direccion, email: form.email.trim() || null }, token!)
      setForm(emptyForm); await reload(); setNotice('Cliente registrado correctamente.')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo crear el cliente.') }
    finally { setLoading(false) }
  }

  async function deactivate(documento: number) {
    if (!token || !window.confirm(`¿Deseas desactivar al cliente ${documento}? Su historial se conservará.`)) return
    setError(''); setNotice('')
    try { await deactivateClient(documento, token); await reload(); setNotice('Cliente desactivado. El historial se conservó.') }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo desactivar el cliente.') }
  }

  return <div className="page-stack">
    <div className="page-heading"><div><p className="eyebrow">DIRECTORIO</p><h2>Clientes</h2><p className="muted">Registra y consulta clientes sin eliminar su historial comercial.</p></div><span className="pill">{clients.length} registros</span></div>
    {error && <div className="alert alert-error" role="alert">{error}</div>}{notice && <div className="alert alert-success" role="status">{notice}</div>}
    <section className="panel"><div className="panel-header"><div><h3>Registrar cliente</h3><p className="muted">El documento es el identificador único.</p></div></div><form className="form-grid" onSubmit={submit}><label>Documento<input type="number" min="1" value={form.documento} onChange={e => setForm({ ...form, documento: e.target.value })} required /></label><label>Nombre<input value={form.nombre} minLength={2} maxLength={60} onChange={e => setForm({ ...form, nombre: e.target.value })} required /></label><label>Apellido<input value={form.apellido} minLength={2} maxLength={60} onChange={e => setForm({ ...form, apellido: e.target.value })} required /></label><label>Correo (opcional)<input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></label><label className="span-2">Dirección<input value={form.direccion} minLength={3} maxLength={120} onChange={e => setForm({ ...form, direccion: e.target.value })} required /></label><div className="form-actions"><button className="button button-primary" disabled={loading}>{loading ? 'Guardando…' : 'Guardar cliente'}</button></div></form></section>
    <section className="panel"><div className="panel-header"><div><h3>Listado de clientes</h3><p className="muted">El saldo representa deuda asociada a ventas a crédito.</p></div></div>{clients.length === 0 ? <p className="empty-state">No hay clientes. Registra el primero en el formulario anterior.</p> : <div className="table-wrap"><table><thead><tr><th>Documento</th><th>Nombre</th><th>Correo</th><th>Saldo</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{clients.map(client => <tr key={client.documento}><td>{client.documento}</td><td><strong>{client.nombre} {client.apellido}</strong><small className="cell-subtitle">{client.direccion}</small></td><td>{client.email || '—'}</td><td>{formatMoney(client.saldo)}</td><td><span className={`status status-${client.estado}`}>{client.estado}</span></td><td>{client.estado === 'activo' ? <button className="button button-small button-ghost" onClick={() => deactivate(client.documento)}>Desactivar</button> : <span className="muted">—</span>}</td></tr>)}</tbody></table></div>}</section>
  </div>
}
