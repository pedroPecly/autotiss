# 🏥 Automação NTISS - Navegação e Vínculo (V27)

Projeto de automação (RPA) em Python que utiliza Selenium WebDriver para automatizar cadastro, vínculo e criação de serviços no sistema NTISS.

## 🚀 Visão Geral

A versão V27 introduz Navegação Autônoma: o robô percorre uma lista de secretarias (logins), abre cada cadastro, executa a ação configurada (vínculo ou cadastro de serviços) e segue automaticamente para a próxima secretaria.

## ✨ Funcionalidades principais

- Navegação automática entre logins definidos em `dados.json` (`secretarias_para_pesquisar`).
- Modo Vínculo: vincula usuários da lista `logins_para_vincular` aos médicos da secretaria.
- Modo Cadastro de Serviços: cria serviços em massa usando os nomes em `medicos_para_cadastrar`.
- Detecção e espera por modais/overlays para evitar cliques incorretos.
- Cliques efetuados via injeção JavaScript quando necessário para driblar elementos invisíveis.
- Hot-reload de `dados.json`: alterações podem ser aplicadas entre ciclos sem reiniciar o script.
- Pausa manual: pressione `P` no terminal para pausar a execução de forma segura.

## 🛠️ Requisitos

- Python 3.8+
- Navegador Chrome ou Firefox (compatível com `webdriver-manager`)
- Dependências (instale via requirements ou manualmente):

```bash
pip install -r requirements.txt
```

ou

```bash
pip install selenium webdriver-manager
```

## ⚙️ Configuração

Coloque `config.json` e `dados.json` na raiz do projeto.

- Exemplo de `config.json`:

```json
{
  "url_sistema": "https://ntiss.neki-it.com.br/ntiss/login.jsf",
  "timeout_aguarde": 40
}
```

- Exemplo de `dados.json` (V27):

```json
{
  "secretarias_para_pesquisar": [
    "77.mrios",
    "77.joana",
    "77.toliveira"
  ],
  "logins_para_vincular": [
    "77.hu",
    "77.suporte"
  ],
  "medicos_para_cadastrar": [
    "JOAO DA SILVA",
    "MARIA SOUZA"
  ]
}
```

Descrição dos campos:

- `secretarias_para_pesquisar`: logins que o robô buscará na tela principal para navegar entre cadastros.
- `logins_para_vincular`: usuários que serão vinculados dentro do cadastro (Modo Vínculo).
- `medicos_para_cadastrar`: nomes que receberão serviços (Modo Cadastro de Serviços).

## ⚠️ Cuidados durante a execução

- Não minimize a janela do navegador — isso pode pausar a renderização e causar timeouts.
- Não bloqueie a sessão do Windows (Win+L) durante a execução.
- Evite usar o mouse/teclado quando o script estiver digitando ou clicando elementos críticos.

## 🔎 Como executar

```bash
python autotiss.py
```

Pressione `P` no terminal para pausar o robô.