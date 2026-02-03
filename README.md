# 🏥 Automação NTISS - Vínculo e Cadastro Massivo

Este projeto é uma solução de automação RPA (Robotic Process Automation) desenvolvida em **Python** com **Selenium WebDriver** para o sistema **NTISS** (Unimed/Neki IT).

O script foi evoluído para funcionar como um "Canivete Suíço", oferecendo um menu interativo para realizar duas tarefas críticas e repetitivas:
1.  **Vínculo de Logins:** Associa logins de faturistas (`77.hu`) a médicos ativos.
2.  **Cadastro de Serviços:** Cadastra novos médicos/prestadores em massa a partir de uma lista externa.

## 🚀 Funcionalidades

### 1. Modo de Vínculo (Opção 1)
* **Busca Inteligente:** Varre a lista de prestadores e ignora automaticamente médicos **Inativos** (baseado em ícones visuais).
* **Verificação de Duplicidade:** Se o login já estiver vinculado, cancela a ação.
* **Ciclo Infinito:** Permite trocar de secretário/lista sem fechar o robô.

### 2. Modo de Cadastro (Opção 2)
* **Leitura de Arquivo:** Lê uma lista de nomes do arquivo `medicos.txt` (um por linha).
* **Preenchimento Automático:** Seleciona o prestador, marca as permissões de transação ("Visualiza", "Cancela", "Todas") e salva.
* **Tratamento de AJAX:** Aguarda os carregamentos assíncronos (Modais de "Aguarde") para evitar cliques em falso.

### ⚙️ Funcionalidades Globais
* **⏸️ Sistema de Pausa:** Pressione a tecla `p` no terminal para pausar o robô após a tarefa atual (útil para liberar o mouse).
* **🛡️ Retry Logic:** Sistema anti-falha que tenta recuperar a interação caso o elemento expire (Stale Element) ou a internet oscile.

## 🛠️ Tecnologias

* Python 3.x
* Selenium WebDriver
* WebDriver Manager (Chrome)
* Biblioteca `msvcrt` (Interface de Teclado Windows)

## 📦 Instalação

1.  Clone o repositório.
2.  Crie um ambiente virtual e instale as dependências:
    ```bash
    pip install selenium webdriver-manager
    ```

## 📝 Configuração da Lista de Médicos

Para usar o **Modo de Cadastro (Opção 2)**, crie um arquivo chamado `medicos.txt` na mesma pasta do script. Insira um nome de médico por linha:

```text
JOAO DA SILVA
MARIA SOUZA
JOSE PEREIRA
...