# 🏥 Automação NTISS - Vínculo e Cadastro Massivo

Este projeto é uma solução de automação RPA (Robotic Process Automation) desenvolvida em **Python** com **Selenium WebDriver** para o sistema **NTISS** (Unimed/Neki IT).

A ferramenta funciona como um "Canivete Suíço" para o setor de TI/Faturamento, oferecendo um menu interativo para automatizar tarefas repetitivas.

## 🚀 Funcionalidades

### 1. Modo de Vínculo (Opção 1)
* **Múltiplos Logins:** Lê o arquivo `logins.txt` e vincula automaticamente uma lista de usuários (ex: `77.hu`, `faturista2`) a cada médico.
* **Inteligência de Tabela:** Verifica se o login já está marcado. Se faltar algum, ele marca e salva. Se todos já estiverem ok, ele apenas cancela para ganhar tempo.
* **Detector de Inativos:** Pula automaticamente médicos inativos na lista.

### 2. Modo de Cadastro (Opção 2)
* **Cadastro em Massa:** Lê nomes do arquivo `medicos.txt` e realiza o cadastro de serviço completo.
* **Preenchimento Automático:** Seleciona o prestador (com busca exata), aguarda a tabela carregar e marca as permissões ("Visualiza", "Cancela", "Todas").
* **Sincronia Perfeita:** Sistema de espera inteligente que aguarda o carregamento do AJAX (Tabelas e Modais) para evitar erros de clique.

### ⚙️ Funcionalidades Globais
* **🔄 Ciclo Infinito com Hot-Reload:** Ao terminar uma lista, o robô pausa e permite que você edite os arquivos `.txt` (bloco de notas) e troque a página no navegador. Ao dar `ENTER`, ele recarrega os novos dados sem precisar reiniciar o programa.
* **⏸️ Sistema de Pausa:** Pressione a tecla `p` no terminal a qualquer momento para pausar o robô com segurança entre as ações.

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

## 📝 Configuração dos Arquivos de Dados

Crie os seguintes arquivos de texto na mesma pasta do script (um item por linha):

**`medicos.txt`** (Para o Modo 2 - Cadastro)
```text
JOAO DA SILVA
MARIA SOUZA
...