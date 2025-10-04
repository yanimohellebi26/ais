import { useMemo, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8080'

const ROLE_OPTIONS = [
  { value: 'admin', label: 'Administrateur' },
  { value: 'owner', label: 'Propriétaire' },
  { value: 'captain', label: 'Capitaine' },
  { value: 'maritime_expert', label: 'Expert Maritime' },
  { value: 'financial_analyst', label: 'Analyste Financier' },
]

const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const initialFormState = {
  username: '',
  email: '',
  password: '',
  role: ROLE_OPTIONS[0].value,
}

function RegisterPage() {
  const [form, setForm] = useState(initialFormState)
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const passwordChecks = useMemo(
    () => ({
      length: form.password.length >= 8,
      upper: /[A-Z]/.test(form.password),
      lower: /[a-z]/.test(form.password),
      digit: /\d/.test(form.password),
      special: /[^A-Za-z0-9]/.test(form.password),
    }),
    [form.password],
  )

  const validate = (state = form) => {
    const validationErrors = {}
    const username = state.username.trim()
    const email = state.email.trim()

    if (!username) {
      validationErrors.username = 'Le nom d\'utilisateur est requis'
    } else if (username.length > 50) {
      validationErrors.username = 'Le nom d\'utilisateur doit contenir 50 caractères ou moins'
    }

    if (!email) {
      validationErrors.email = 'L\'adresse email est requise'
    } else if (!EMAIL_REGEX.test(email)) {
      validationErrors.email = 'Veuillez entrer une adresse email valide'
    }

    if (!state.password) {
      validationErrors.password = 'Le mot de passe est requis'
    } else if (!PASSWORD_REGEX.test(state.password)) {
      validationErrors.password =
        'Le mot de passe doit contenir au moins 8 caractères dont une majuscule, une minuscule, un chiffre et un caractère spécial'
    }

    if (!ROLE_OPTIONS.some((option) => option.value === state.role)) {
      validationErrors.role = 'Veuillez sélectionner un rôle'
    }

    return validationErrors
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))

    if (errors[name]) {
      const next = { ...errors }
      delete next[name]
      setErrors(next)
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    const validationErrors = validate()

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    setIsSubmitting(true)
    setServerError(null)

    const payload = {
      username: form.username.trim(),
      email: form.email.trim().toLowerCase(),
      password: form.password,
      role: form.role,
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      const data = await response
        .json()
        .catch(() => ({ message: 'Échec de l\'inscription' }))

      if (!response.ok) {
        setSuccess(null)
        setServerError(data?.message ?? 'Échec de l\'inscription')
        return
      }

      setSuccess(data)
      setErrors({})
      setForm((prev) => ({ ...initialFormState, role: prev.role }))
    } catch (error) {
      console.error('Registration error', error)
      setSuccess(null)
      setServerError('Impossible de joindre le serveur. Veuillez réessayer plus tard.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="register-wrapper">
      <div className="register-card" role="region" aria-labelledby="register-title">
        <header className="register-header">
          <h1 id="register-title">Créer votre compte SeaSight</h1>
          <p className="register-subtitle">
            Remplissez le formulaire pour créer un nouveau compte. Tous les champs sont requis.
          </p>
        </header>

        {success && (
          <div className="success-banner" role="status" aria-live="polite">
            <strong>Compte créé avec succès !</strong>
            <p>
              {success.username} peut maintenant se connecter avec {success.email} en tant que {success.role}.
            </p>
          </div>
        )}

        {serverError && (
          <div className="error-banner" role="alert" aria-live="assertive">
            {serverError}
          </div>
        )}

        <form className="register-form" onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="username">Nom d\'utilisateur</label>
            <input
              id="username"
              name="username"
              type="text"
              className={`form-control ${errors.username ? 'has-error' : ''}`}
              value={form.username}
              onChange={handleChange}
              autoComplete="username"
              maxLength={50}
              placeholder="Capitaine Nemo"
              required
            />
            {errors.username && <p className="input-error">{errors.username}</p>}
          </div>

          <div className="form-group">
            <label htmlFor="email">Adresse email</label>
            <input
              id="email"
              name="email"
              type="email"
              className={`form-control ${errors.email ? 'has-error' : ''}`}
              value={form.email}
              onChange={handleChange}
              autoComplete="email"
              placeholder="capitaine@seasight.com"
              required
            />
            {errors.email && <p className="input-error">{errors.email}</p>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              name="password"
              type="password"
              className={`form-control ${errors.password ? 'has-error' : ''}`}
              value={form.password}
              onChange={handleChange}
              autoComplete="new-password"
              placeholder="MotDePasse1!"
              required
            />
            {errors.password && <p className="input-error">{errors.password}</p>}
            <ul className="password-hints" aria-live="polite">
              <li className={passwordChecks.length ? 'valid' : ''}>Au moins 8 caractères</li>
              <li className={passwordChecks.upper ? 'valid' : ''}>Une lettre majuscule</li>
              <li className={passwordChecks.lower ? 'valid' : ''}>Une lettre minuscule</li>
              <li className={passwordChecks.digit ? 'valid' : ''}>Un chiffre</li>
              <li className={passwordChecks.special ? 'valid' : ''}>Un caractère spécial</li>
            </ul>
          </div>

          <div className="form-group">
            <label htmlFor="role">Rôle</label>
            <select
              id="role"
              name="role"
              className={`form-control ${errors.role ? 'has-error' : ''}`}
              value={form.role}
              onChange={handleChange}
              required
            >
              {ROLE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {errors.role && <p className="input-error">{errors.role}</p>}
          </div>

          <button type="submit" className="submit-button" disabled={isSubmitting}>
            {isSubmitting ? 'Création du compte…' : 'Créer le compte'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default RegisterPage
