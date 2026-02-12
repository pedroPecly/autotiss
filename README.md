# 🏥 Automação NTISS — Vínculo e Cadastro Massivo (JSON)

Descrição: automação RPA em Python (Selenium) para login automático, vínculo de logins e cadastro massivo de médicos no sistema NTISS.

---

## Sumário

- [Visão geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Execução](#execução)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Segurança e .gitignore](#segurança-e-gitignore)
- [Solução de problemas](#solução-de-problemas)
- [Contribuição](#contribuição)

---

## Visão geral

Este projeto (versões V24/V29) automatiza tarefas repetitivas no NTISS: autenticação, navegação entre telas, vínculo de logins a médicos e cadastro massivo. A configuração e os dados ficam separados em arquivos JSON (`config.json`, `dados.json`).

## Funcionalidades

- Login automático a partir de credenciais em `config.json`.
- Modo Vínculo: processa `logins_para_vincular` e evita regravações desnecessárias.
- Modo Cadastro: processa `medicos_para_cadastrar`, com busca/seleção precisa em componentes PrimeFaces e espera por carregamento AJAX.
- Navegação resiliente: detecta falhas de pesquisa, pula itens e continua o ciclo.
- Ações via JavaScript para contornar overlays e elementos inacessíveis.
- Hot-reload básico: editar `dados.json` e iniciar novo ciclo (quando o script suportar).
- Pausa manual segura (ex.: tecla para pausar no terminal).

## Requisitos

- Python 3.8+
- Navegador compatível (Chrome/Edge/Firefox) e driver correspondente
- Dependências Python (recomendado via `requirements.txt`)

## Instalação

1. Clone o repositório.
2. Crie e ative um ambiente virtual (opcional, recomendado).
3. Instale dependências:

```bash
pip install -r requirements.txt
# ou, instalar apenas os essenciais:
pip install selenium webdriver-manager
```

## Configuração

Crie `config.json` na raiz com as configurações mínimas e credenciais:

```json
{
  "url_sistema": "https://seu-ntiss",
  "timeout_aguarde": 40,
  "usuario": "SEU_USUARIO",
  "senha": "SUA_SENHA"
}
```

Crie `dados.json` com os arrays a processar (exemplo):

```json
{
  "secretarias_para_pesquisar": ["77.mrios", "77.joana"],
  "logins_para_vincular": ["77.usuario1", "77.usuario2"],
  "medicos_para_cadastrar": ["JOAO DA SILVA", "MARIA SOUZA"]
}
```

Observação: JSON não aceita comentários; use campos como `_comment` para anotações internas.

## Execução

Executar o script principal:

```bash
python autotiss.py
```

Comportamento esperado:
- O robô realiza login automático usando `config.json`.
- Navega para as telas necessárias e executa os módulos de vínculo ou cadastro.
- Pode pedir interação (pressionar Enter) para iniciar ciclos novos após edição de `dados.json`.

## Estrutura do projeto

- `autotiss.py` — script principal
- `config.json` — configurações do sistema e credenciais
- `dados.json` — dados de entrada (logins, médicos, secretarias)
- `requirements.txt` — dependências (opcional)

## Segurança e .gitignore

Por conter credenciais, inclua regras no seu `.gitignore`:

```
config.json
dados.json
*.log
__pycache__/
```

Nunca comite `config.json` com credenciais reais.

## Solução de problemas

- `JSONDecodeError`: valide `config.json` e `dados.json` com um validador JSON.
- Erros de WebDriver: atualize o driver ou use `webdriver-manager` para versão compatível com o navegador.
- Janela minimizada no Windows: não minimize a janela do navegador; o Windows pode suspender renderização.

## Contribuição

Contribuições são bem-vindas: abra uma issue descrevendo o problema ou envie um pull request com testes mínimos e instruções.

---

Se desejar, adiciono exemplos de execução (logs), badges, ou scripts de CI. Quer que eu abra o preview do `README.md` agora? 
