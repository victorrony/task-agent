const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005';

// --- TYPES ---
export interface DashboardStats {
  balance: string;
  profit: string;
  reserve: string;
  goals: string;
  status: string;
  raw_balance: number;
}

export interface Goal {
  name: string;
  target: number;
  current: number;
  percent: number;
  priority: string;
}

export interface Transaction {
  Data: string;
  'Descrição': string;
  Valor: number;
  Tipo: 'entrada' | 'saida';
  Categoria: string;
}

export interface DashboardResponse {
  stats: DashboardStats;
  goals: Goal[];
  recent_transactions: Transaction[];
}

export interface UserProfile {
  id: number;
  name: string;
}

// --- HELPERS ---

/**
 * Clean agent response from Gemini 2.5 metadata artifacts
 */
function cleanAgentResponse(text: string): string {
  if (!text) return '';

  // Remove Gemini 2.5 metadata patterns
  let cleaned = text.replace(/['"]extras['"]\s*:\s*\{[^}]*\}/g, '');
  cleaned = cleaned.replace(/['"]signature['"]\s*:\s*['"][^'"]*['"]/g, '');
  cleaned = cleaned.replace(/['"]type['"]\s*:\s*['"]text['"]/g, '');

  // Remove object notation leftovers like [{type:, {type:
  cleaned = cleaned.replace(/\[\s*\{\s*type\s*:/g, '');
  cleaned = cleaned.replace(/\{\s*type\s*:/g, '');

  // Clean up empty objects and loose commas
  cleaned = cleaned.replace(/,\s*\}/g, '}');
  cleaned = cleaned.replace(/\{\s*,/g, '{');
  cleaned = cleaned.replace(/\{\s*\}/g, '');

  // Convert literal \n to actual newlines
  cleaned = cleaned.replace(/\\n/g, '\n');

  // Clean up multiple spaces
  cleaned = cleaned.replace(/ {2,}/g, ' ').trim();

  return cleaned;
}

/**
 * Normalize response content from various formats to clean string
 */
function normalizeResponse(content: string | Array<string | { text?: string }> | { text?: string; content?: string } | null | undefined): string {
  if (typeof content === 'string') {
    return cleanAgentResponse(content);
  }

  if (Array.isArray(content)) {
    const text = content.map((item: any) =>
      typeof item === 'string' ? item : (item?.text ?? '')
    ).join('');
    return cleanAgentResponse(text);
  }

  if (typeof content === 'object' && content !== null) {
    const text = content.text ?? content.content ?? JSON.stringify(content);
    return cleanAgentResponse(text);
  }

  return cleanAgentResponse(String(content ?? ''));
}

export interface ExpenseCategory {
  name: string;
  value: number;
}

// --- API CALLS ---
export async function fetchExpenseCategories(userId: number): Promise<ExpenseCategory[]> {
  const res = await fetch(`${API_URL}/expenses/categories/${userId}`);
  if (!res.ok) throw new Error('Falha ao carregar categorias');
  return res.json();
}

export async function fetchDashboard(userId: number): Promise<DashboardResponse> {
  const res = await fetch(`${API_URL}/dashboard/${userId}`);
  if (!res.ok) throw new Error('Falha ao carregar dashboard');
  return res.json();
}

export async function fetchTransactions(userId: number): Promise<Transaction[]> {
  const res = await fetch(`${API_URL}/transactions/${userId}`);
  if (!res.ok) throw new Error('Falha ao carregar transações');
  return res.json();
}

export async function fetchChatHistory(userId: number): Promise<{role: string; content: string}[]> {
    const res = await fetch(`${API_URL}/chat/history/${userId}`);
    if (!res.ok) throw new Error('Falha ao carregar histórico');
    return res.json();
}

export async function fetchUsers(): Promise<UserProfile[]> {
  const res = await fetch(`${API_URL}/users`);
  if (!res.ok) throw new Error('Falha ao carregar utilizadores');
  return res.json();
}

export async function sendChatMessage(userId: number, message: string, mode: string = 'assistant', file?: File, signal?: AbortSignal) {
  let res;

  if (file) {
    const formData = new FormData();
    formData.append('user_id', userId.toString());
    formData.append('message', message);
    formData.append('mode', mode);
    formData.append('file', file);

    res = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      body: formData,
      signal,
    });
  } else {
    res = await fetch(`${API_URL}/chat/json`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, message, mode }),
      signal,
    });
  }

  if (!res.ok) throw new Error('Falha ao enviar mensagem');
  const data = await res.json();
  return { response: normalizeResponse(data.response) };
}
