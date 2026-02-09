# Correção: Bug Gemini 2.5 - response.content como lista

## Problema Identificado

O frontend Next.js (web/) apresentava o seguinte erro:

```
Objects are not valid as a React child (found: object with keys {type, text, extras}).
If you meant to render a collection of children, use an array instead.
```

### Causa Raiz

O **Gemini 2.5** retorna `response.content` em dois formatos diferentes:

1. **String simples** (comportamento esperado): `"Olá, tudo bem?"`
2. **Lista de objetos** (novo comportamento):
   ```python
   [
     {"type": "text", "text": "Olá, ", "extras": {...}},
     {"type": "text", "text": "tudo bem?", "extras": {...}}
   ]
   ```

O código não tratava o caso 2, causando:
- A API retornar uma lista em vez de string
- O frontend Next.js tentar renderizar objetos diretamente (erro React)

## Solução Implementada

### 1. Função de Normalização (`_normalize_content()`)

Criada função auxiliar no arquivo `/home/victor-rony/Documents/RONY/IA/task-agent/agent/task_agent.py`:

```python
def _normalize_content(content: Any) -> str:
    """
    Normaliza response.content do Gemini 2.5 para string.

    O Gemini 2.5 pode retornar:
    - String simples: "texto"
    - Lista de objetos: [{type: "text", text: "...", extras: ...}, ...]

    Esta função sempre retorna uma string.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        # Extrai o texto de cada objeto e concatena
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                # Tenta extrair do campo 'text' primeiro
                if 'text' in item:
                    text_parts.append(str(item['text']))
                # Fallback: pega qualquer campo de texto
                elif 'content' in item:
                    text_parts.append(str(item['content']))
                else:
                    # Se não encontrou campo de texto, converte o dict inteiro
                    text_parts.append(str(item))
            else:
                text_parts.append(str(item))
        return ''.join(text_parts)

    # Fallback: converte para string
    return str(content) if content else ""
```

### 2. Aplicação nos Pontos Críticos

A normalização foi aplicada em **3 métodos** da classe `TaskAgent`:

#### a) `run()` - Linha 238
**Antes:**
```python
return response.content
```

**Depois:**
```python
return _normalize_content(response.content)
```

#### b) `_classify_intent()` - Linha 155
**Antes:**
```python
content = response.content.replace("```json", "").replace("```", "").strip()
```

**Depois:**
```python
content = _normalize_content(response.content)
content = content.replace("```json", "").replace("```", "").strip()
```

#### c) `_generate_plan()` - Linha 166
**Antes:**
```python
return response.content
```

**Depois:**
```python
return _normalize_content(response.content)
```

## Testes de Validação

Criado arquivo de teste `/home/victor-rony/Documents/RONY/IA/task-agent/test_gemini_fix.py` que valida:

- ✅ String simples (compatibilidade com comportamento antigo)
- ✅ Lista de objetos Gemini 2.5 (novo comportamento)
- ✅ Lista com único objeto
- ✅ None (edge case)
- ✅ Lista vazia
- ✅ Fallback para campo 'content'
- ✅ Objeto dict direto (fallback)

**Resultado:** Todos os testes passaram ✅

## Arquivos Modificados

1. `/home/victor-rony/Documents/RONY/IA/task-agent/agent/task_agent.py`
   - Adicionada função `_normalize_content()`
   - Modificados métodos `run()`, `_classify_intent()`, `_generate_plan()`

## Impacto

- ✅ **Frontend React**: Não apresenta mais erro ao renderizar respostas
- ✅ **API**: Sempre retorna strings, garantindo compatibilidade
- ✅ **Retrocompatibilidade**: Suporta tanto formato antigo quanto novo do Gemini
- ✅ **Robustez**: Múltiplos fallbacks para edge cases

## Como Testar

1. Executar teste unitário:
   ```bash
   source venv/bin/activate
   python test_gemini_fix.py
   ```

2. Testar com API Server:
   ```bash
   source venv/bin/activate
   python api_server.py
   ```

3. Testar no frontend Next.js:
   - Enviar mensagem via chat
   - Verificar que não há mais erro React
   - Confirmar que resposta é renderizada como texto

## Notas Técnicas

- A função `_normalize_content()` é **defensiva** e sempre retorna string
- Suporta múltiplos formatos de resposta do LLM
- Mantém compatibilidade com versões antigas do Gemini
- Zero breaking changes no código existente

---

**Status:** ✅ Corrigido e testado
**Data:** 2026-02-09
**Versão:** 3.1.0+bugfix
