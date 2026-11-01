import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('adminemiro@version1.com')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email.trim(), password)
      const from = (location.state as { from?: string } | null)?.from ?? '/dashboard'
      navigate(from, { replace: true })
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo iniciar sesión.')
    } finally {
      setLoading(false)
    }
  }

  return <main className="login-page">
    <section className="login-visual"><div className="login-visual-content"><span className="brand-mark brand-mark-large">V</span><p className="eyebrow eyebrow-light">GESTIÓN COMERCIAL</p><h1>Tu operación,<br />en una sola vista.</h1><p>Administra clientes, inventario y ventas con un flujo simple y trazable.</p></div><span className="visual-footer">Sistema de Gestión de Ventas · V1</span></section>
    <section className="login-panel"><div className="login-card"><span className="eyebrow">ACCESO ADMINISTRATIVO</span><h2>Bienvenido</h2><p className="muted">Ingresa tus credenciales para continuar.</p><form className="form-stack" onSubmit={submit}><label>Correo electrónico<input type="email" value={email} onChange={event => setEmail(event.target.value)} autoComplete="username" required /></label><label>Contraseña<input type="password" value={password} onChange={event => setPassword(event.target.value)} autoComplete="current-password" minLength={8} required /></label>{error && <div className="alert alert-error" role="alert">{error}</div>}<button className="button button-primary button-full" disabled={loading}>{loading ? 'Verificando…' : 'Iniciar sesión'} <span>→</span></button></form><p className="login-footnote">La sesión usa un token de acceso temporal. No se almacena la contraseña en el navegador.</p></div></section>
  </main>
}
