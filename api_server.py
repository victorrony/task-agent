"""
API SERVER - FinanceAgent Pro REST API
=====================================
Backend industrial para o frontend Next.js.
Exclui: Gradio (substituído por esta API)
Inclui: Endpoints RESTful, CORS, Pydantic Models.
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from agent import TaskAgent, init_db
from agent.data_service import get_quick_stats, get_transactions_df, get_goals_progress, get_users
from agent.tools import set_user_id

# Inicialização
init_db()
app = FastAPI(title="FinanceAgent Pro API", version="3.1.0")

# CORS (Permitir Frontend Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restringir para o domínio do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DADOS (Schemas) ---

class ChatRequest(BaseModel):
    user_id: int
    message: str
    mode: str = "assistant"

class Transaction(BaseModel):
    date: str
    description: str
    amount: float
    type: str
    category: str

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "online", "system": "FinanceAgent Pro v3.1"}

@app.get("/users")
def list_users():
    """Listar utilizadores disponíveis para login."""
    return get_users()

@app.get("/dashboard/{user_id}")
def get_dashboard_data(user_id: int):
    """Retorna estatísticas consolidadas para o dashboard."""
    set_user_id(user_id)
    stats = get_quick_stats(user_id)
    goals = get_goals_progress(user_id)
    # Transactions (últimas 5 para preview)
    df = get_transactions_df(user_id)
    recent_tx = df.head(5).to_dict(orient="records") if not df.empty else []
    
    return {
        "stats": stats,
        "goals": goals,
        "recent_transactions": recent_tx
    }

@app.post("/chat", status_code=200)
def chat_agent(req: ChatRequest):
    """Endpoint principal de conversa com o Agente."""
    try:
        # Instancia agente efêmero (ou recupera de cache se implementado)
        agent = TaskAgent(user_id=req.user_id, mode=req.mode)
        response = agent.run(req.message)
        # Garante que a resposta é sempre string (Gemini 2.5 pode retornar lista)
        if isinstance(response, list):
            response = "".join(
                item.get("text", str(item)) if isinstance(item, dict) else str(item)
                for item in response
            )
        elif not isinstance(response, str):
            response = str(response) if response else ""
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/transactions/{user_id}")
def get_transactions(user_id: int):
    """Histórico completo de transações."""
    df = get_transactions_df(user_id)
    return df.to_dict(orient="records") if not df.empty else []

if __name__ == "__main__":
    import uvicorn
    # Usa porta 8005 (menos conflito)
    uvicorn.run(app, host="0.0.0.0", port=8005)
