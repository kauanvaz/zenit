import logging
import os
from decimal import Decimal
from typing import Any, Protocol

from django.db.models import Sum
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from ai.models import FinancialAnalysis
from transactions.models import Transaction
from .tools import build_tools

logger = logging.getLogger(__name__)

# Configurações da LLM
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-5-mini')
MAX_TOKENS = 1500
TEMPERATURE = 0.3

_SYSTEM_PROMPT = """Você é um analista financeiro pessoal experiente, focado em ajudar usuários a entenderem melhor sua saúde financeira.
Seu papel é analisar os dados financeiros do usuário para o período solicitado e produzir um relatório claro, objetivo e útil em Português Brasileiro.

## Instruções obrigatórias
- Use APENAS os dados retornados pelas ferramentas disponíveis. Nunca invente ou assuma números que não foram fornecidos.
- Responda SEMPRE em Português Brasileiro.
- Seja direto e conciso. Evite jargões técnicos desnecessários.
- Se não houver dados suficientes para uma seção, informe que não há registros suficientes.

## Ordem sugerida de análise
1. Obtenha o resumo geral do período (get_transactions_summary).
2. Verifique o saldo atual das contas (get_accounts_summary).
3. Identifique as maiores despesas (get_top_expenses).
4. Analise a tendência dos últimos meses (get_monthly_trend) para contexto.

## Formato da resposta final
Estrutura o seu relatório da seguinte forma:

### Resumo do Período
[Resumo de 2-3 frases sobre receitas, despesas e saldo líquido do mês analisado.]

### Principais Insights
- [Insight 1 baseado nos dados]
- [Insight 2 baseado nos dados]
- [Insight 3 baseado nos dados]

### Pontos de Atenção
[Relate gastos elevados em categorias específicas ou mudanças abruptas em relação aos meses anteriores. Se não houver alertas, omita esta seção.]

### Recomendações
- [Sugestão prática de economia ou investimento baseada na análise.]
- [Dica de controle financeiro personalizada.]

### Situação Patrimonial
[Breve comentário sobre a liquidez e saldo das contas bancárias.]
"""


class AgentExecutor(Protocol):
    """Contrato mínimo usado por run_analysis para invocar o agente."""

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...


def _message_content_to_text(content: Any) -> str:
    """Normaliza o conteúdo de mensagens do LangChain para texto simples."""
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                block_text = block.strip()
                if block_text:
                    parts.append(block_text)
                continue

            if not isinstance(block, dict):
                continue

            text = block.get('text')
            if text:
                parts.append(str(text).strip())

        return '\n'.join(part for part in parts if part).strip()

    return str(content).strip()


def _extract_ai_output(result: dict[str, Any]) -> str:
    """Extrai a última resposta do assistente do resultado retornado pelo agent graph."""
    output = result.get('output')
    if isinstance(output, str) and output.strip():
        return output

    messages = result.get('messages', [])
    if not isinstance(messages, list):
        return ''

    for message in reversed(messages):
        if isinstance(message, AIMessage):
            text = _message_content_to_text(message.content)
            if text:
                return text
            continue

        if isinstance(message, dict) and message.get('role') == 'assistant':
            text = _message_content_to_text(message.get('content', ''))
            if text:
                return text

    return ''


class _GraphAgentExecutor:
    """
    Adapter para manter a interface invoke({'input': ...}) esperada no código atual.
    """

    def __init__(self, agent_graph: Any):
        self._agent_graph = agent_graph

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        input_text = str(payload.get('input', '')).strip()

        graph_result = self._agent_graph.invoke({
            'messages': [
                {'role': 'user', 'content': input_text},
            ]
        })

        if not isinstance(graph_result, dict):
            return {'output': ''}

        return {
            'output': _extract_ai_output(graph_result),
            'messages': graph_result.get('messages', []),
        }


def _get_agent_executor(user_id: int) -> AgentExecutor:
    """
    Configura o executor do agente usando a API v1 do LangChain.
    """
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        api_key=os.getenv('OPENAI_API_KEY'),
    )

    tools = build_tools(user_id=user_id)
    agent_graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=_SYSTEM_PROMPT,
    )

    return _GraphAgentExecutor(agent_graph)


def run_analysis(user_id: int, period: str) -> FinancialAnalysis:
    """
    Executa a análise financeira para um usuário e período específicos,
    persistindo os resultados no modelo FinancialAnalysis.
    """
    # Busca ou cria FinancialAnalysis com status 'pending'
    # Se a view desejar evitar re-execução, ela deve checar antes.
    analysis = FinancialAnalysis.objects.create(
        user_id=user_id,
        period=period,
        status=FinancialAnalysis.Status.PENDING,
    )

    try:
        # Atualiza status para processing
        analysis.status = FinancialAnalysis.Status.PROCESSING
        analysis.save(update_fields=['status', 'updated_at'])

        # Executa o agente
        executor = _get_agent_executor(user_id=user_id)
        input_text = f'Analise minhas finanças do período {period}.'
        
        # Invoca o agente e retorna o output
        result = executor.invoke({'input': input_text})
        analysis_text = result.get('output', '')

        # Coleta snapshots financeiros para o período
        try:
            year, month = int(period[:4]), int(period[5:7])
            transactions = Transaction.objects.filter(
                user_id=user_id,
                date__year=year,
                date__month=month,
            )
            
            income = transactions.filter(type='income').aggregate(t=Sum('amount'))['t'] or Decimal('0')
            expenses = transactions.filter(type='expense').aggregate(t=Sum('amount'))['t'] or Decimal('0')
            
            analysis.total_income = income
            analysis.total_expenses = expenses
            analysis.net_balance = income - expenses
        except (ValueError, IndexError):
            logger.warning('Formato de período inválido ao coletar snapshots: %s', period)

        # Salva
        analysis.analysis_text = analysis_text
        analysis.status = FinancialAnalysis.Status.COMPLETED
        analysis.save(update_fields=[
            'analysis_text', 'total_income', 'total_expenses', 
            'net_balance', 'status', 'updated_at'
        ])

    except Exception as exc:
        logger.exception('Falha ao executar análise financeira para user_id=%s', user_id)
        analysis.status = FinancialAnalysis.Status.FAILED
        analysis.error_message = str(exc)
        analysis.save(update_fields=['status', 'error_message', 'updated_at'])

    return analysis
