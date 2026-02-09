export async function fetchDashboard(userId: number) {
    const res = await fetch(`http://localhost:8005/dashboard/${userId}`);
    if (!res.ok) throw new Error('Falha ao carregar dashboard');
    return res.json();
}

function normalizeResponse(content: any): string {
    if (typeof content === 'string') return content;
    if (Array.isArray(content)) {
        return content.map((item: any) =>
            typeof item === 'string' ? item : (item?.text ?? JSON.stringify(item))
        ).join('');
    }
    if (typeof content === 'object' && content !== null) {
        return content.text ?? content.content ?? JSON.stringify(content);
    }
    return String(content ?? '');
}

export async function sendChatMessage(userId: number, message: string) {
    const res = await fetch(`http://localhost:8005/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, message, mode: 'assistant' })
    });
    if (!res.ok) throw new Error('Falha ao enviar mensagem');
    const data = await res.json();
    return { response: normalizeResponse(data.response) };
}

export async function fetchTransactions(userId: number) {
  const res = await fetch(`http://localhost:8005/transactions/${userId}`);
  if (!res.ok) throw new Error('Falha ao carregar transações');
  return res.json();
}
