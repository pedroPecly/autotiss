````markdown
# 🏥 Automação NTISS - Vínculo e Cadastro Massivo (JSON Edition)

Solução de automação RPA (Robotic Process Automation) desenvolvida em **Python** com **Selenium WebDriver** para otimizar processos no sistema **NTISS**.

Esta versão (**V24**) utiliza uma arquitetura profissional baseada em **arquivos JSON**, separando configurações, dados e código.

## 🚀 Funcionalidades

### 1. Modo de Vínculo (Opção 1)
* **Multi-Login:** Lê a lista `logins_para_vincular` do arquivo `dados.json`.
* **Fluxo Inteligente:** Itera sobre cada login, verifica se já está vinculado ao médico e salva apenas se houver alterações.
* **Detecção de Inativos:** Pula automaticamente médicos inativos na listagem visual.

### 2. Modo de Cadastro (Opção 2)
* **Cadastro Estruturado:** Lê a lista `medicos_para_cadastrar` do arquivo `dados.json`.
* **Seleção Precisa:** Utiliza busca exata no dropdown do PrimeFaces.
* **Sincronia Total:** Aguarda o carregamento da tabela de transações via AJAX antes de tentar marcar opções.
* **Marcação Obsessiva:** Garante que as checkboxes ("Visualiza", "Cancela") foram marcadas verificando a classe CSS `ui-state-active`.

### ⚙️ Funcionalidades Globais
* **Configuração Centralizada:** URL do sistema e Timeouts configuráveis via `config.json`.
* **Hot-Reload:** Ao terminar um ciclo, você pode editar o `dados.json`, salvar e pressionar ENTER para o robô processar os novos dados sem reiniciar.
* **Tratamento de Erros:** Validação de sintaxe JSON para evitar crashes por formatação incorreta.

## 🛠️ Instalação

1.  Clone o repositório.
2.  Instale as dependências:
    ```bash
    pip install selenium webdriver-manager
    ```

## 📝 Configuração (Arquivos JSON)

Para o robô funcionar, você precisa criar dois arquivos na raiz do projeto:

### 1. `config.json` (Configurações do Sistema)
```json
{
  "url_sistema": "[https://ntiss.neki-it.com.br/ntiss/login.jsf](https://ntiss.neki-it.com.br/ntiss/login.jsf)",
  "timeout_aguarde": 40
}
```

### 3. `dados.json` (exemplo)

O arquivo `dados.json` contém os dados que o robô irá processar: logins a vincular e a lista de médicos a cadastrar. Exemplo de estrutura válida:

```json
{
  "logins_para_vincular": [
    "77.usuario"
  ],
  "medicos_para_cadastrar": [
    "JOAO DA SILVA",
    "MARIA SOUZA",
    "JOSE PEREIRA"
  ]
}
```

Salve o arquivo na raiz do projeto como `dados.json`. Lembre-se: JSON puro não aceita comentários — use campos como `_comment` se precisar anotar algo no próprio arquivo.
