import os
import sqlite3
from datetime import datetime
import pluggy_sdk
from pluggy_sdk.api import AuthApi, ItemsApi, AccountApi, TransactionApi
from pluggy_sdk.models.auth_request import AuthRequest

DB_PATH = "agent_data.db"

class PluggyService:
    def __init__(self):
        self.client_id = os.getenv("PLUGGY_CLIENT_ID", "p_abc123")
        self.client_secret = os.getenv("PLUGGY_CLIENT_SECRET", "s_abc123")
        self.api_key = None
        self.configuration = pluggy_sdk.Configuration()
        
    def _authenticate(self):
        """Autentica na API do Pluggy e obtém o API Key."""
        if not self.api_key:
            with pluggy_sdk.ApiClient() as api_client:
                auth_instance = AuthApi(api_client)
                auth_req = AuthRequest(client_id=self.client_id, client_secret=self.client_secret)
                try:
                    auth_response = auth_instance.auth_create(auth_req)
                    self.api_key = auth_response.api_key
                    self.configuration.api_key['apiKey'] = self.api_key
                except Exception as e:
                    print(f"Erro de autenticação Pluggy: {e}")
                    raise e
        return self.api_key

    def sync_data(self):
        """
        Sincroniza contas e transações do Pluggy para o SQLite local.
        """
        try:
            self._authenticate()
            
            with pluggy_sdk.ApiClient(self.configuration) as api_client:
                # 1. Obter itens
                items_instance = ItemsApi(api_client)
                items_response = items_instance.items_list()
                
                # Verificando a estrutura provável baseada em dir()
                items = items_response.results if hasattr(items_response, 'results') else []
                
                if not items:
                    return "Nenhuma conexão bancária encontrada no Pluggy."

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                new_transactions_count = 0
                
                acc_instance = AccountApi(api_client)
                tx_instance = TransactionApi(api_client)

                for item in items:
                    item_id = item.id if hasattr(item, 'id') else item.get('id')
                    
                    # 2. Obter contas do item
                    acc_response = acc_instance.accounts_list(item_id)
                    accounts = acc_response.results if hasattr(acc_response, 'results') else []
                    
                    for acc in accounts:
                        acc_id = acc.id if hasattr(acc, 'id') else acc.get('id')
                        balance = acc.balance if hasattr(acc, 'balance') else acc.get('balance', 0)
                        currency = acc.currency_code if hasattr(acc, 'currency_code') else acc.get('currencyCode', 'BRL')
                        
                        cursor.execute(
                            "INSERT INTO account_balance (balance, currency) VALUES (?, ?)",
                            (balance, currency)
                        )

                        # 3. Obter transações da account
                        tx_response = tx_instance.transactions_list(acc_id)
                        transactions = tx_response.results if hasattr(tx_response, 'results') else []
                        
                        for tx in transactions:
                            tx_date = tx.date.strftime("%Y-%m-%d") if hasattr(tx.date, 'strftime') else str(tx.date)[:10]
                            desc = tx.description
                            amount = abs(tx.amount)
                            tx_type = 'entrada' if tx.amount > 0 else 'saida'
                            category = tx.category if tx.category else 'outros'

                            # Check if exists
                            cursor.execute("""
                                SELECT id FROM transactions 
                                WHERE date = ? AND description = ? AND amount = ? AND type = ?
                            """, (tx_date, desc, amount, tx_type))
                            
                            if not cursor.fetchone():
                                cursor.execute("""
                                    INSERT INTO transactions (date, description, amount, type, category, balance_after)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (tx_date, desc, amount, tx_type, category, balance))
                                new_transactions_count += 1

                conn.commit()
                conn.close()
                return f"Sincronização concluída! {new_transactions_count} novas transações importadas do Pluggy."

        except Exception as e:
            return f"Erro na sincronização com Pluggy: {str(e)}"
