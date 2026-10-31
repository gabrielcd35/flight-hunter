# ✈ Flight Hunter

Flight Hunter é uma experiência Streamlit para comparar passagens de ida e volta entre vários destinos, explorar datas flexíveis e conferir itinerários reais antes de abrir o Google Flights.

## Experiência de busca

- Catálogo pesquisável com aeroportos internacionais e grupos metropolitanos.
- Comparação de até oito destinos por busca.
- Flexibilidade independente para as datas de ida e volta.
- Volta por data exata ou duração fixa da viagem.
- Orçamento, voos diretos, número de conexões e duração máxima de conexão.
- Tarifa de calendário claramente separada de itinerário detalhado.
- Horários locais, companhias, duração, conexões e escalas somente quando fornecidos pelo FLI.
- Links de verificação restritos ao Google Flights.

## Arquitetura

```text
app.py                    Interface e fluxo Streamlit
flight_hunter/catalog.py  Catálogo internacional de aeroportos
flight_hunter/core.py     Regras e formatação sem dependência da UI
flight_hunter/search.py   Integração isolada com o CLI do FLI
flight_hunter/theme.py    Sistema visual responsivo
tests/                    Testes de regras, integração e UI
```

O fluxo mantém dois níveis de consulta:

1. `fli dates` encontra a menor tarifa para viagens com duração fixa. Esse resultado é apresentado como **tarifa de calendário**.
2. `fli flights` consulta uma combinação exata de ida e volta. Somente esse retorno pode preencher companhia, horários, duração e conexões.

Nenhum itinerário é preenchido com dados fictícios.

## Executar localmente

Requer Python 3.11.

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

Abra `http://localhost:8501`.

## Testes

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```

## Publicação

### Streamlit Community Cloud

Use `app.py` como arquivo principal. As dependências e o tema estão versionados no repositório.

### Railway ou outro provedor Docker

1. Conecte este repositório.
2. Use o `Dockerfile` da raiz.
3. Gere um domínio para a porta fornecida pela variável `PORT`.
4. Faça uma busca curta de verificação depois do deploy.

## Limitações conhecidas

O FLI consulta dados não oficiais do Google Flights. Restrições do provedor, mudanças de resposta ou bloqueios em infraestrutura compartilhada podem causar buscas lentas ou sem resultado. Preços e disponibilidade podem mudar; bagagem, tarifa final e condições devem ser confirmadas no Google Flights antes da compra.
