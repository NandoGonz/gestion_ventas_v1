import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { LoginPage } from './LoginPage'

const { loginMock } = vi.hoisted(() => ({ loginMock: vi.fn() }))
vi.mock('../context/AuthContext', () => ({ useAuth: () => ({ login: loginMock }) }))

describe('LoginPage', () => {
  beforeEach(() => { loginMock.mockReset(); loginMock.mockResolvedValue(undefined) })

  it('renders email and password fields', () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    expect(screen.getByLabelText('Correo electrónico')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
  })

  it('submits the credentials to the auth context', async () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    fireEvent.change(screen.getByLabelText('Correo electrónico'), { target: { value: 'admin@example.test' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'Password123!' } })
    fireEvent.submit(screen.getByRole('button', { name: /iniciar sesión/i }).closest('form')!)
    await waitFor(() => expect(loginMock).toHaveBeenCalledWith('admin@example.test', 'Password123!'))
  })

  it('shows an error when credentials are rejected', async () => {
    loginMock.mockRejectedValue(new Error('Correo o contraseña incorrectos.'))
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'wrongpassword' } })
    fireEvent.submit(screen.getByRole('button', { name: /iniciar sesión/i }).closest('form')!)
    expect(await screen.findByRole('alert')).toHaveTextContent('Correo o contraseña incorrectos.')
  })
})
