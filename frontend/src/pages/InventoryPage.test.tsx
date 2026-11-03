import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { InventoryPage } from './InventoryPage'

const api = vi.hoisted(() => ({
  getInventoryMock: vi.fn(),
  getInventoryMovementsMock: vi.fn(),
  registerInventoryEntryMock: vi.fn(),
  registerInventoryExitMock: vi.fn(),
}))

vi.mock('../api/client', () => ({
  getInventory: api.getInventoryMock,
  getInventoryMovements: api.getInventoryMovementsMock,
  registerInventoryEntry: api.registerInventoryEntryMock,
  registerInventoryExit: api.registerInventoryExitMock,
}))
vi.mock('../context/AuthContext', () => ({ useAuth: () => ({ token: 'test-token' }) }))

const products = [{
  id: 1,
  nombre: 'Teclado',
  descripcion: 'Teclado de prueba',
  precio: '100.00',
  stock: 5,
  estado: 'disponible',
  fecha_registro: '2026-01-01T00:00:00Z',
  fecha_actualizacion: '2026-01-01T00:00:00Z',
}]

describe('InventoryPage', () => {
  beforeEach(() => {
    api.getInventoryMock.mockReset()
    api.getInventoryMovementsMock.mockReset()
    api.registerInventoryEntryMock.mockReset()
    api.registerInventoryExitMock.mockReset()
    api.getInventoryMock.mockResolvedValue(products)
    api.getInventoryMovementsMock.mockResolvedValue([])
  })

  it('loads stock and submits an inventory entry', async () => {
    api.registerInventoryEntryMock.mockResolvedValue({
      id: 2,
      producto_id: 1,
      producto_nombre: 'Teclado',
      tipo_movimiento: 'entrada',
      cantidad: 3,
      motivo: 'Recepción',
      venta_id: null,
      fecha_creacion: '2026-01-01T00:00:00Z',
    })
    render(<InventoryPage />)

    expect(await screen.findByText('Teclado')).toBeInTheDocument()
    fireEvent.change(screen.getAllByLabelText('Producto')[0], { target: { value: '1' } })
    fireEvent.change(screen.getAllByLabelText('Cantidad')[0], { target: { value: '3' } })
    fireEvent.change(screen.getAllByLabelText('Motivo')[0], { target: { value: 'Recepción' } })
    fireEvent.click(screen.getByRole('button', { name: 'Registrar entrada' }))

    await waitFor(() => expect(api.registerInventoryEntryMock).toHaveBeenCalledWith(
      { producto_id: 1, cantidad: 3, motivo: 'Recepción' },
      'test-token',
    ))
    expect(await screen.findByText('Entrada registrada para Teclado.')).toBeInTheDocument()
  })
})
