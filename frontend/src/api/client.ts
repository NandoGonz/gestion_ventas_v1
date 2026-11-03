export type ApiError = Error & { status?: number }

export type User = {
  id: number
  full_name: string
  email: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export type Client = {
  documento: number
  nombre: string
  apellido: string
  direccion: string
  email: string | null
  saldo: string | number
  estado: 'activo' | 'inactivo' | 'moroso' | 'suspendido'
  fecha_creacion: string
  fecha_actualizacion: string
}

export type Product = {
  id: number
  nombre: string
  descripcion: string
  precio: string | number
  stock: number
  estado: 'disponible' | 'agotado' | 'descontinuado' | 'preventa'
  fecha_registro: string
  fecha_actualizacion: string
}

export type SaleDetail = {
  id: number
  venta_id: number
  producto_id: number
  producto_nombre: string
  cantidad: number
  precio_unitario: string | number
  subtotal: string | number
}

export type Sale = {
  id: number
  fecha: string
  forma_pago: 'decontado' | 'credito' | 'transferencia'
  cliente_documento: number
  usuario_id: number
  total: string | number
  estado: string
  fecha_creacion: string
  detalle_ventas: SaleDetail[]
}

export type InventoryMovement = {
  id: number
  producto_id: number
  producto_nombre: string
  tipo_movimiento: 'entrada' | 'salida' | 'venta'
  cantidad: number
  motivo: string
  venta_id: number | null
  fecha_creacion: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/$/, '')

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.body && !(options.body instanceof URLSearchParams) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (options.body instanceof URLSearchParams) headers.set('Content-Type', 'application/x-www-form-urlencoded')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/api/v1${path}`, { ...options, headers })
  } catch {
    throw new Error('No se pudo conectar con la API. Comprueba que el backend esté activo.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail
    let message = typeof detail === 'string' ? detail : 'No se pudo completar la solicitud.'
    if (response.status === 401) message = 'Tu sesión no es válida. Inicia sesión de nuevo.'
    if (response.status === 403) message = 'No tienes permisos para esta operación.'
    if (response.status === 409 && typeof detail !== 'string') message = 'La operación entra en conflicto con los datos existentes.'
    if (response.status === 422 && Array.isArray(detail)) message = detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(' ')
    const error = new Error(message) as ApiError
    error.status = response.status
    throw error
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function login(email: string, password: string) {
  return request<{ access_token: string; token_type: string }>(
    '/auth/login',
    { method: 'POST', body: new URLSearchParams({ username: email, password }) },
  )
}

export const getMe = (token: string) => request<User>('/auth/me', {}, token)
export const getClients = (token: string) => request<Client[]>('/clientes/?limit=200', {}, token)
export const createClient = (payload: unknown, token: string) => request<Client>('/clientes/', { method: 'POST', body: JSON.stringify(payload) }, token)
export const updateClient = (documento: number, payload: unknown, token: string) => request<Client>(`/clientes/${documento}`, { method: 'PATCH', body: JSON.stringify(payload) }, token)
export const deactivateClient = (documento: number, token: string) => request<Client>(`/clientes/${documento}`, { method: 'DELETE' }, token)
export const getProducts = (token: string) => request<Product[]>('/productos/?limit=200', {}, token)
export const createProduct = (payload: unknown, token: string) => request<Product>('/productos/', { method: 'POST', body: JSON.stringify(payload) }, token)
export const updateProduct = (id: number, payload: unknown, token: string) => request<Product>(`/productos/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }, token)
export const getSales = (token: string) => request<Sale[]>('/ventas/?limit=100', {}, token)
export const createSale = (payload: unknown, token: string) => request<Sale>('/ventas/', { method: 'POST', body: JSON.stringify(payload) }, token)
export const getInventory = (token: string) => request<Product[]>('/inventario/?limit=200', {}, token)
export const getInventoryMovements = (token: string) => request<InventoryMovement[]>('/inventario/movimientos?limit=200', {}, token)
export const registerInventoryEntry = (payload: unknown, token: string) => request<InventoryMovement>('/inventario/entradas', { method: 'POST', body: JSON.stringify(payload) }, token)
export const registerInventoryExit = (payload: unknown, token: string) => request<InventoryMovement>('/inventario/salidas', { method: 'POST', body: JSON.stringify(payload) }, token)

export function formatMoney(value: string | number): string {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 2 }).format(Number(value))
}
