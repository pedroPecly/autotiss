#  Automação NTISS  Vínculo e Cadastro Massivo (JSON)

Automação RPA em Python + Selenium para login automático, vínculo de logins e cadastro massivo de serviços de médicos no sistema NTISS, com painel de controle flutuante em tempo real.

---

## Sumário

- [Visão geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Painel flutuante](#painel-flutuante)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Execução](#execução)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Segurança e .gitignore](#segurança-e-gitignore)

---

## Visão geral

O script (`autotiss.py`) automatiza tarefas repetitivas no NTISS: autenticação, navegação entre telas, vínculo de logins a médicos e cadastro massivo de serviços. A configuração e os dados de entrada ficam separados em arquivos JSON (`config.json`, `dados.json`).

Durante a execução, um painel flutuante com tema escuro é exibido sobre o navegador, mostrando status em tempo real e permitindo pausar, retomar ou parar o processo com um clique.

---

## Funcionalidades

###  Login automático
- Preenche usuário e senha a partir do `config.json` e clica em Entrar automaticamente.
- Fallback para login manual caso as credenciais não estejam configuradas.

###  Modo 1  Vincular Logins
- Itera sobre todos os médicos ativos de cada secretaria listada.
- Exibe o nome do médico em tempo real no campo **MÉDICO** do painel flutuante.
- Para cada médico, **verifica e ativa automaticamente** o checkbox *"Visualiza transações de outros logins?"*, garantindo que o acesso à pesquisa esteja liberado.
- Abre o campo *"Escolher Logins"* e executa o vínculo conforme o conteúdo de `logins_para_vincular`:
  - **Com logins configurados:** pesquisa cada login individualmente e marca seu checkbox.
  - **Com lista vazia:** marca o **select-all** do dropdown (vincula todos os logins disponíveis) sem precisar de nenhuma configuração extra.
- Salva apenas se houve alguma alteração; cancela caso contrário (evita gravações desnecessárias).
- Suporta modo filtrado: após o Modo 2, pode rodar apenas nos médicos recém-cadastrados na sessão.

###  Modo 2  Cadastrar Serviços
- Processa a lista `medicos_para_cadastrar` para cada secretaria.
- Busca o médico no dropdown do NTISS de forma **case-insensitive** (funciona independentemente de maiúsculas/minúsculas no JSON).
- Marca os checkboxes obrigatórios com **retry automático** (até 3 tentativas com scroll e verificação pós-clique):
  - *Visualiza transações*
  - *Cancela/Exclui*
  - *Todas as transações* (header da tabela)
- Detecta médicos já cadastrados e os pula sem interromper o ciclo.
- Ao final, oferece **inline no painel flutuante** a opção de executar o Modo 1 apenas nos médicos que foram cadastrados na sessão.

---

## Painel flutuante

Janela Tkinter com tema escuro, sempre visível sobre o navegador, arrastável pela barra de título.

```

   NTISS AUTOMATION                           

 MODO:        Cadastrar Serviços                 
 SECRETARIA:  77.hu_smoraes                      
 MÉDICO:      CRISTINA FACIOLI ROCHA             
 PROGRESSO:   12 / 76                            

 LOG                                             
 10:42  [NAVEGAÇÃO] Pesquisando: 77.hu_      
 10:43  Cadastrado com sucesso.                
 ...                                             

  Vincular   Cadastrar   Pausar   Parar

```

**Controles:**
| Botão | Função |
|---|---|
| Vincular | Inicia o Modo 1 |
| Cadastrar | Inicia o Modo 2 |
| Pausar / Retomar | Suspende e retoma o bot entre passos |
| Próximo usuário | (visível ao pausar) Pula a secretaria atual e avança para a próxima |
| Parar | Encerra o ciclo atual com segurança |

**Log colorido:**
| Cor | Significado |
|---|---|
| Verde | Sucesso, item cadastrado/vinculado |
| Vermelho | Erro crítico |
| Amarelo | Aviso, retry, já cadastrado |
| Ciano | Navegação, informação geral |
| Azul | Cabeçalho de secretaria |
| Cinza | Itens pulados / inativos |

---

## Requisitos

- Python 3.8+
- Google Chrome instalado
- Dependências Python listadas em `requirements.txt`

---

## Instalação

1. Clone o repositório.
2. Crie e ative um ambiente virtual (recomendado):

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## Configuração

### `config.json`

```json
{
  "url_sistema": "https://ntiss.neki-it.com.br/ntiss/login.jsf",
  "timeout_aguarde": 40,
  "usuario": "SEU_USUARIO",
  "senha": "SUA_SENHA"
}
```

### `dados.json`

```json
{
  "secretarias_para_pesquisar": [
    "77.hu_login1",
    "77.hu_login2"
  ],
  "logins_para_vincular": [
    "77.hu"
  ],
  "medicos_para_cadastrar": [
    "NOME DO MEDICO UM",
    "NOME DO MEDICO DOIS"
  ]
}
```

> **Dica:** os nomes em `medicos_para_cadastrar` podem estar em qualquer capitalização — o robô converte para maiúsculo automaticamente na busca.

> **Dica:** `logins_para_vincular` pode ser uma lista vazia `[]`. Nesse caso o Modo 1 abrirá o dropdown de logins de cada médico e marcará **todos** os logins disponíveis automaticamente (select-all).

---

## Execução

```bash
python autotiss.py
```

Fluxo ao iniciar:
1. O Chrome abre e o robô faz login automático.
2. Navega para a lista de Funcionários.
3. O painel flutuante aparece no canto inferior direito da tela.
4. Clique em **Vincular** ou **Cadastrar** para iniciar.

---

## Estrutura do projeto

```
autotiss.py         script principal (bot + UI flutuante)
config.json         credenciais e configurações do sistema
dados.json          dados de entrada (secretarias, logins, médicos)
requirements.txt    dependências Python
```

---

## Segurança e .gitignore

`config.json` contém credenciais reais  **nunca commite este arquivo**. Adicione ao `.gitignore`:

```
config.json
dados.json
*.log
__pycache__/
venv/
build/
*.spec
```
