import React, { useState } from 'react';
import { login, register } from '../api';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      if (creating) await register(username, password);
      await login(username, password);
      onLogin();
    } catch (err) {
      setError('Invalid credentials or registration failed');
    }
  }

  return (
    <div className="login-container">
      <div className="login-logo">
        <img src="/logo.png" alt="CC Tracker logo" className="logo-img" />
        <h1>CC Tracker</h1>
      </div>

      <form onSubmit={handleSubmit} className="login-form">
        <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
        {error && <div className="error">{error}</div>}
        <button type="submit">{creating ? 'Create Account' : 'Login'}</button>
      </form>

      <div className="login-links">
        <a onClick={() => setCreating(!creating)}>
          {creating ? 'Already have an account? Login' : 'Create Account'}
        </a>
      </div>
    </div>
  );
}
