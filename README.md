# ✈️ Flight Hunter

Protótipo web familiar para pesquisar passagens de ida e volta, com datas flexíveis, até oito destinos por busca e filtro de orçamento.

## Publicar no Railway

1. Conecte a conta Railway e selecione **Deploy from GitHub Repo**.
2. Escolha `gabrielcd35/flight-hunter`.
3. Railway utilizará o `Dockerfile` na raiz do repositório.
4. Em **Settings > Networking**, gere um domínio público.
5. Confira o log de build e execute uma busca curta de teste.

**Atenção:** O motor FLI faz consultas não oficiais ao Google Flights. Buscas podem não funcionar em provedores de nuvem. Compare tarifas na página de reserva antes de comprar. Limites gratuitos e custos de hospedagem variam conforme o plano da Railway.

## Executar localmente

```bash
python3 -m pip install -r requirements.txt
streamlit run app.py
```

## Roadmap

* Armazenamento de histórico
* Alertas de promoções reais
* Comparação de fontes independentes
* Acesso familiar com controles para uso e custos
