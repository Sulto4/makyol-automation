import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { ShieldCheck, UserPlus, KeyRound, Power, RefreshCw, Copy } from 'lucide-react';
import apiClient from '../api/client';
import { AuthUser, useAuthStore } from '../store/authStore';

function generatePassword(length = 16): string {
  const alphabet = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%^&*';
  const bytes = new Uint32Array(length);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (v) => alphabet[v % alphabet.length]).join('');
}

async function copy(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    // non-secure contexts won't allow writeText — show-only fallback is fine
  }
}

export default function AdminUsersPage() {
  const currentUser = useAuthStore((s) => s.user);
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState(() => generatePassword());
  const [isAdmin, setIsAdmin] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [lastCreated, setLastCreated] = useState<{ email: string; password: string } | null>(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get<{ users: AuthUser[] }>('/auth/admin/users');
      setUsers(res.data.users);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Nu am putut încărca utilizatorii');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchUsers();
  }, [fetchUsers]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await apiClient.post('/auth/admin/users', {
        email: email.trim().toLowerCase(),
        password,
        isAdmin,
      });
      setLastCreated({ email: email.trim().toLowerCase(), password });
      setEmail('');
      setPassword(generatePassword());
      setIsAdmin(false);
      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Creare eșuată');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleActive = async (user: AuthUser) => {
    try {
      await apiClient.patch(`/auth/admin/users/${user.id}/active`, {
        is_active: !user.is_active,
      });
      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Actualizare eșuată');
    }
  };

  const handleResetPassword = async (user: AuthUser) => {
    const newPw = generatePassword();
    if (!confirm(`Resetezi parola pentru ${user.email}? Parola nouă va fi afișată o singură dată.`)) {
      return;
    }
    try {
      await apiClient.patch(`/auth/admin/users/${user.id}/password`, {
        password: newPw,
      });
      setLastCreated({ email: user.email, password: newPw });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Resetare eșuată');
    }
  };

  const sortedUsers = useMemo(
    () => [...users].sort((a, b) => a.email.localeCompare(b.email)),
    [users],
  );

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100 flex items-center gap-2">
            <ShieldCheck size={22} className="text-blue-600 dark:text-blue-400" />
            Administrare utilizatori
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Creează conturi pentru testeri. Parolele sunt afișate o singură dată — copiază-le înainte să pleci de pe pagină.
          </p>
        </div>
        <button
          onClick={() => void fetchUsers()}
          className="flex items-center gap-2 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <RefreshCw size={14} />
          Reîncarcă
        </button>
      </header>

      {error && (
        <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md px-3 py-2">
          {error}
        </div>
      )}

      {lastCreated && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-300 dark:border-amber-700 rounded-md p-4 text-sm">
          <div className="font-medium text-amber-800 dark:text-amber-200 mb-2">
            Credențiale pentru {lastCreated.email} (afișate o singură dată):
          </div>
          <div className="flex items-center gap-2">
            <code className="flex-1 px-2 py-1 bg-white dark:bg-gray-900 border border-amber-200 dark:border-amber-800 rounded text-xs">
              {lastCreated.password}
            </code>
            <button
              onClick={() => void copy(`${lastCreated.email} / ${lastCreated.password}`)}
              className="flex items-center gap-1 px-2 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded text-xs"
            >
              <Copy size={12} />
              Copiază
            </button>
            <button
              onClick={() => setLastCreated(null)}
              className="text-xs text-amber-700 dark:text-amber-300 hover:underline"
            >
              Închide
            </button>
          </div>
        </div>
      )}

      <section className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-800 dark:text-gray-100 flex items-center gap-2 mb-4">
          <UserPlus size={18} />
          Creează cont nou
        </h2>
        <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-[2fr_2fr_1fr_auto] gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Parolă (generată)</label>
            <div className="flex gap-1">
              <input
                type="text"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="flex-1 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-xs font-mono"
              />
              <button
                type="button"
                onClick={() => setPassword(generatePassword())}
                className="px-2 py-2 rounded-md border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700"
                title="Regenerează"
              >
                <RefreshCw size={14} />
              </button>
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
            <input
              type="checkbox"
              checked={isAdmin}
              onChange={(e) => setIsAdmin(e.target.checked)}
            />
            Admin
          </label>
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-medium rounded-md"
          >
            {submitting ? 'Se creează...' : 'Creează'}
          </button>
        </form>
      </section>

      <section className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-300">
            <tr>
              <th className="text-left px-4 py-2 font-medium">Email</th>
              <th className="text-left px-4 py-2 font-medium">Rol</th>
              <th className="text-left px-4 py-2 font-medium">Stare</th>
              <th className="text-left px-4 py-2 font-medium">Creat</th>
              <th className="text-left px-4 py-2 font-medium">Ultim login</th>
              <th className="text-right px-4 py-2 font-medium">Acțiuni</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-gray-500">Se încarcă...</td>
              </tr>
            ) : sortedUsers.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-gray-500">Niciun utilizator</td>
              </tr>
            ) : (
              sortedUsers.map((user) => (
                <tr key={user.id} className="text-gray-800 dark:text-gray-100">
                  <td className="px-4 py-2">
                    <span className="flex items-center gap-2">
                      {user.is_admin && <ShieldCheck size={14} className="text-blue-600 dark:text-blue-400" />}
                      {user.email}
                      {user.id === currentUser?.id && (
                        <span className="text-xs text-gray-500">(tu)</span>
                      )}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-600 dark:text-gray-300">
                    {user.is_admin ? 'Admin' : 'Tester'}
                  </td>
                  <td className="px-4 py-2">
                    <span
                      className={
                        user.is_active
                          ? 'text-green-700 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }
                    >
                      {user.is_active ? 'Activ' : 'Dezactivat'}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-500 text-xs">
                    {new Date(user.created_at).toLocaleDateString('ro-RO')}
                  </td>
                  <td className="px-4 py-2 text-gray-500 text-xs">
                    {user.last_login_at
                      ? new Date(user.last_login_at).toLocaleString('ro-RO')
                      : 'niciodată'}
                  </td>
                  <td className="px-4 py-2 text-right space-x-2">
                    <button
                      onClick={() => void handleResetPassword(user)}
                      className="inline-flex items-center gap-1 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-xs hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <KeyRound size={12} />
                      Resetează
                    </button>
                    {user.id !== currentUser?.id && (
                      <button
                        onClick={() => void handleToggleActive(user)}
                        className={`inline-flex items-center gap-1 px-2 py-1 border rounded text-xs ${
                          user.is_active
                            ? 'border-red-300 dark:border-red-700 text-red-700 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                            : 'border-green-300 dark:border-green-700 text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20'
                        }`}
                      >
                        <Power size={12} />
                        {user.is_active ? 'Dezactivează' : 'Activează'}
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
