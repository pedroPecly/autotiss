# 🏥 Automação NTISS - Navegação e Vínculo (V27 - Full Integration)

Solução de automação RPA (Robotic Process Automation) desenvolvida em **Python** com **Selenium WebDriver**. 

Esta versão (**V27**) introduz a **Navegação Autônoma**, permitindo que o robô pesquise secretarias, entre no cadastro, realize as tarefas e retorne para processar a próxima da lista automaticamente.

## 🚀 Funcionalidades

### 🔄 1. Navegação Automática (Novo)
- **Ciclo Completo:** O robô lê uma lista de secretarias, pesquisa o login na tela inicial, entra no modo de edição e, ao finalizar, clica em "Cancelar" para buscar a próxima.
- **Proteção de Modais:** Detecta janelas de carregamento ("Aguarde") e sobreposições (overlays) do PrimeFaces para evitar cliques falsos.

### 🔗 2. Modo de Vínculo (Opção 1)
- **Multi-Login:** Lê a lista `logins_para_vincular` e associa aos médicos da secretaria atual.
- **Filtro Inteligente:** Digita letra por letra no filtro do dropdown para garantir a renderização dos itens.
- **Verificação de Estado:** Só clica em "Salvar" se houver alterações reais; caso contrário, apenas cancela o modal.

### 📝 3. Modo de Cadastro de Serviços (Opção 2)
- **Criação em Massa:** Clica em "Criar Serviço", seleciona o médico da lista `medicos_para_cadastrar` e marca as permissões necessárias.
- **Marcação Garantida:** Verifica via classe CSS (`ui-state-active`) se as checkboxes ("Visualiza", "Cancela") foram realmente marcadas.

### ⚙️ Funcionalidades Globais
- **Cliques via JavaScript:** Todos os cliques utilizam injeção de JS para ignorar elementos invisíveis que bloqueiam a interface.
- **Pausa Manual:** Pressione a tecla **`P`** no terminal a qualquer momento para pausar o robô com segurança.
- **Hot-Reload:** É possível editar o `dados.json` entre os ciclos sem fechar o script.

## 🛠️ Instalação

1. Clone o repositório.
2. Instale as dependências:

```bash
pip install selenium webdriver-manager