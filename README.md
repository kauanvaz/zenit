# Zenit

Aplicação web de controle financeiro pessoal construída com Django.  
O projeto centraliza cadastro de contas, categorias e transações, apresenta indicadores no dashboard, gera relatórios e oferece análise financeira assistida por IA.

## Funcionalidades

- Autenticação por e-mail (login, logout, registro).
- Dashboard com saldo total, receitas/despesas do mês e transações recentes.
- CRUD de contas, categorias e transações.
- Filtros de transações por mês, ano, tipo e categoria.
- Exportação de transações em CSV e PDF.
- Relatórios com gráficos (últimos 12 meses e despesas por categoria).
- Perfil do usuário (telefone e avatar).
- Análise financeira por IA para um período (`YYYY-MM`) com snapshot de receitas, despesas e saldo.

## Tecnologias utilizadas

- Python 3.14
- Django 6
- SQLite (padrão) com suporte a `DATABASE_URL` via `dj-database-url`
- LangChain + `langchain-openai` (módulo de IA)
- Pytest + pytest-django + pytest-cov
- `uv` para gestão de dependências

## Estrutura do projeto

```text
core/           # Configuração global (settings, urls, views base)
users/          # Usuário customizado e autenticação
accounts/       # Contas bancárias/carteira
categories/     # Categorias de receita e despesa
transactions/   # Transações, filtros e exportações
reports/        # Relatórios e gráficos
profiles/       # Perfil do usuário
ai/             # Análise financeira com agente LangChain/OpenAI
templates/      # Templates HTML por módulo
```

## Como executar localmente

1. Instale dependências:

```bash
uv sync --dev
```

2. Configure ambiente:

```bash
cp .env.example .env
```

3. Aplique migrações:

```bash
uv run python manage.py migrate
```

4. (Opcional) Popule categorias iniciais:

```bash
uv run python manage.py seed_categories
```

5. Suba o servidor:

```bash
uv run python manage.py runserver
```

Acesse:
- `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Variáveis de ambiente

Use o `.env.example` como base:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `OPENAI_API_KEY` (necessário para análise por IA)
- `OPENAI_MODEL` (padrão: `gpt-5-mini`)

## Testes

Execute todos os testes:

```bash
uv run pytest
```

Observações:
- A suíte exige cobertura mínima de **80%** (`--cov-fail-under=80`).
- Exemplo de execução pontual:

```bash
uv run pytest ai/tests/test_agent.py
```

## Notas sobre IA

- O endpoint `POST /ai/analyze/` exige usuário autenticado.
- A análise requer pelo menos 3 transações no período solicitado.
- Se já existir análise concluída nas últimas 24h para o mesmo período, o sistema reutiliza o resultado.
