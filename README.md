# API CNPJ BA - Versao 4

Prototipo para testar a viabilidade de consulta de situacao cadastral de CNPJs no portal publico da Sefaz-BA.

## Instalar dependencias

```powershell
pip install -r requirements.txt
playwright install chromium
```

## Rodar a API

```powershell
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Depois abra:

```text
http://127.0.0.1:8000/docs
```

## Rodar a interface com upload de Excel

Essa e a tela mais parecida com a versao anterior:

```powershell
streamlit run streamlit_app.py
```

Depois envie uma planilha `.xlsx` com a coluna `CNPJ`. A coluna `REMESSA` e opcional.

## Consultar um CNPJ

Endpoint:

```text
POST /consultar
```

Exemplo:

```json
{
  "cnpj": "12345678000100",
  "tentativas": 2,
  "delay_min": 1.5,
  "delay_max": 3.0
}
```

## Consultar lote

Endpoint:

```text
POST /consultar-lote
```

Exemplo:

```json
{
  "cnpjs": ["12345678000100", "11111111000111"],
  "tentativas": 2,
  "delay_min": 1.5,
  "delay_max": 3.0,
  "modo": "seguro"
}
```

O modo `rapido` reduz o intervalo para uma faixa mais agressiva, mas ainda controlada. Use para teste pequeno.

## Teste por CSV

Crie um CSV com uma coluna chamada `CNPJ` e rode:

```powershell
python testar_lote.py caminho\para\arquivo.csv --delay-min 1.5 --delay-max 3 --tentativas 2
```

## Observacoes

- A consulta em lote abre o navegador apenas uma vez e reaproveita a sessao.
- CNPJs repetidos usam cache dentro da mesma chamada.
- O retorno `VERIFICAR` indica que o portal nao retornou um status reconhecido, houve instabilidade ou o layout mudou.
- Evite alto volume paralelo, porque o portal pode bloquear, falhar ou ficar instavel.
