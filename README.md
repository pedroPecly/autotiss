# 🏥 Automação NTISS - Vínculo Massivo de Logins

Este projeto é uma solução de automação desenvolvida em **Python** com **Selenium WebDriver** para otimizar o fluxo de trabalho no sistema **NTISS** (utilizado por operadoras Unimed).

O script automatiza a tarefa repetitiva de vincular logins específicos (ex: faturistas) a uma lista de prestadores médicos, reduzindo horas de trabalho manual para minutos.

## 🚀 Funcionalidades Principais

* **⚡ Modo Ciclo Infinito:** Permite processar múltiplas listas de secretários sequencialmente sem reiniciar o programa.
* **🧠 Detecção Inteligente de Inativos:** Analisa visualmente a tabela (ícones de status) para identificar e pular médicos inativos, evitando erros de interação.
* **🛡️ Verificação de Duplicidade:** Checa se o login já está vinculado antes de salvar. Se já estiver, cancela a ação para ganhar tempo.
* **⏸️ Sistema de Pausa (Hotkey):** Pressione a tecla `p` a qualquer momento para pausar o robô de forma segura (após terminar o item atual) e usar o computador.
* **🔄 Robustez (Anti-Stale):** Implementação de *retry logic* para lidar com atualizações assíncronas da tabela (AJAX) que normalmente quebrariam automações simples.
* **🎯 Estratégia de "Triplo Clique":** Método avançado para interagir com dropdowns do *PrimeFaces* que são difíceis de automatizar.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Automação:** Selenium WebDriver
* **Gerenciamento de Driver:** WebDriver Manager (Chrome)
* **Interface de Sistema:** Biblioteca `msvcrt` (Nativa do Windows para detecção de teclas)

## 📋 Pré-requisitos

Como o projeto utiliza a biblioteca `msvcrt` para o sistema de pausa via teclado, ele é compatível nativamente com **Windows**.

* Python 3 instalado.
* Google Chrome instalado.

## 📦 Instalação

1.  Clone este repositório:
    ```bash
    git clone [https://github.com/SEU_USUARIO/NOME_DO_REPO.git](https://github.com/SEU_USUARIO/NOME_DO_REPO.git)
    cd NOME_DO_REPO
    ```

2.  Crie um ambiente virtual (recomendado):
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  Instale as dependências:
    ```bash
    pip install selenium webdriver-manager
    ```

## ▶️ Como Usar

1.  Execute o script:
    ```bash
    python autontiss.py
    ```
2.  Uma janela do Chrome será aberta. **Faça o login manualmente** no sistema NTISS.
3.  Navegue até a tela **Manutenção de Prestador** e filtre a lista desejada.
4.  Volte ao terminal (tela preta) e pressione `ENTER` para iniciar.
5.  O robô processará a lista. Ao finalizar, ele aguardará você trocar para o próximo secretário e pressionar `ENTER` novamente.

### Comandos de Controle

| Tecla | Ação |
| :--- | :--- |
| **`p`** | **Pausar:** O robô termina o médico atual e aguarda um Enter para continuar. |
| **`Enter`** | **Retomar:** Continua a execução após uma pausa ou inicia um novo ciclo. |

## 🔍 Detalhes Técnicos da Lógica

O script possui uma lógica de decisão para identificar o status do médico baseada nos ícones do PrimeFaces:

* **Botão Vermelho (Inativar) visível:** Médico está **ATIVO** -> *Processar*.
* **Botão Verde (Ativar) visível:** Médico está **INATIVO** -> *Pular*.

Isso impede que o script tente abrir menus em linhas desabilitadas, o que causaria exceções no Selenium.

## ⚠️ Aviso Legal

Esta ferramenta foi desenvolvida para fins de produtividade interna e aprendizado. O uso de scripts de automação (RPA) deve estar em conformidade com as políticas da empresa e os termos de uso do sistema alvo.