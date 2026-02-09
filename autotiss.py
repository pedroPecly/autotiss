"""
🏥 AUTOMATION TOOLKIT - NTISS (V24 - JSON Edition)
--------------------------------------------------
Descrição: Automação RPA para vínculo de logins e cadastro de serviços médicos.
Autor: Pedro Henrique
Tecnologias: Selenium WebDriver, Python, JSON.

Funcionalidades:
1. Leitura de configurações e dados via arquivos JSON.
2. Tratamento robusto de esperas (AJAX/Loading).
3. Verificação visual de status (Ativo/Inativo).
4. Sistema de pausa e recarregamento de arquivos em tempo real.
"""

import time
import msvcrt  # Biblioteca nativa do Windows para capturar teclas (usado na Pausa)
import os
import json
from datetime import datetime

# Importações do Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException

# --- CONSTANTES DE ARQUIVOS ---
ARQUIVO_CONFIG = "config.json"
ARQUIVO_DADOS = "dados.json"

# --- FUNÇÕES DE CARREGAMENTO E CONFIGURAÇÃO ---

def carregar_json(caminho):
    """
    Tenta ler um arquivo JSON e retorna os dados.
    Possui tratamento de erros para não quebrar o script se o arquivo estiver ruim.
    """
    if not os.path.exists(caminho):
        log(f"[ERRO] Arquivo '{caminho}' não encontrado.")
        return None
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log(f"[ERRO DE SINTAXE] O arquivo '{caminho}' está mal formatado (vírgula ou aspas erradas): {e}")
        return None
    except Exception as e:
        log(f"[ERRO CRÍTICO] Falha ao ler '{caminho}': {e}")
        return None

# Tenta carregar as configurações. Se falhar, usa valores padrão para não travar.
CONF = carregar_json(ARQUIVO_CONFIG)
if not CONF:
    CONF = {
        "url_sistema": "https://ntiss.neki-it.com.br/ntiss/login.jsf", 
        "timeout_aguarde": 40
    }

# Define variáveis globais a partir do JSON
URL_SISTEMA = CONF.get("url_sistema")
TIMEOUT_AGUARDE = CONF.get("timeout_aguarde", 40)

# --- FUNÇÕES UTILITÁRIAS (HELPERS) ---

def log(mensagem):
    """Imprime mensagens no terminal com o horário atual."""
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {mensagem}")

def checar_pausa():
    """
    Verifica se o usuário pressionou a tecla 'p'.
    Se sim, pausa a execução até que ENTER seja pressionado.
    Útil para quando o usuário precisa usar o mouse rapidinho.
    """
    if msvcrt.kbhit():  # Se alguma tecla foi pressionada
        tecla = msvcrt.getch()
        if tecla.lower() == b'p':
            print("\n" + "="*40)
            print(">>> PAUSA SOLICITADA! (Robô Parado) <<<")
            input(">>> Pressione ENTER para CONTINUAR...")
            print("="*40 + "\n")
            log("Retomando execução...")

def esperar_aguarde_sumir(driver):
    """
    Monitora o modal de carregamento 'Aguarde' do PrimeFaces.
    O script fica parado aqui até que o 'Aguarde' desapareça da tela.
    """
    time.sleep(0.3) # Pequeno delay inicial para dar tempo do modal aparecer
    try:
        WebDriverWait(driver, TIMEOUT_AGUARDE).until(
            EC.invisibility_of_element_located((By.ID, "aguarde"))
        )
        time.sleep(0.3) # Estabilização extra pós-carregamento
    except: pass

def clicar_js(driver, elemento, nome="Elemento"):
    """
    Força um clique usando JavaScript.
    Necessário quando o Selenium diz que o elemento está 'coberto' por outro.
    """
    try:
        driver.execute_script("arguments[0].click();", elemento)
    except Exception as e:
        log(f"   [ERRO] Falha ao clicar em {nome}: {e}")

def fechar_janelas_travadas(driver):
    """Pressiona ESC para tentar fechar modais ou menus que travaram."""
    try:
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    except: pass

# --- FUNÇÕES ESPECÍFICAS DO SISTEMA (PRIMEFACES) ---

def selecionar_item_combo(driver, nome_medico):
    """
    Lida com o Dropdown (SelectOneMenu) do PrimeFaces.
    Procura na lista suspensa (ul/li) pelo item que contém o texto EXATO do médico.
    """
    # XPath procura: Dentro do painel do dropdown -> Item de lista (li) -> Contendo o texto
    xpath_item = f"//div[contains(@id, 'prestadorFuncionario_panel')]//li[contains(., '{nome_medico}')]"
    try:
        item_especifico = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, xpath_item))
        )
        item_especifico.click()
        return True
    except Exception:
        # Tentativa de fallback via JS se o clique normal falhar
        try:
            item_especifico = driver.find_element(By.XPATH, xpath_item)
            driver.execute_script("arguments[0].click();", item_especifico)
            return True
        except:
            return False

def garantir_checkbox(driver, texto_label):
    """
    Tenta marcar uma checkbox de forma 'obsessiva'.
    Verifica se a classe 'ui-state-active' (verde) foi aplicada.
    Se não, tenta clicar de novo usando 3 estratégias de busca diferentes.
    """
    # Estratégia 1: Busca na mesma LINHA (tr) da tabela
    xpath_tr = f"//tr[.//label[contains(text(), '{texto_label}')]]//div[contains(@class, 'ui-chkbox-box')]"
    # Estratégia 2: Busca no elemento PAI
    xpath_parent = f"//label[contains(text(), '{texto_label}')]/..//div[contains(@class, 'ui-chkbox-box')]"
    # Estratégia 3: Busca no elemento IRMÃO ANTERIOR
    xpath_sibling = f"//label[contains(text(), '{texto_label}')]/preceding-sibling::div[contains(@class, 'ui-chkbox-box')]"
    
    lista_tentativas = [xpath_tr, xpath_parent, xpath_sibling]
    
    for xpath in lista_tentativas:
        try:
            # Verifica se o elemento existe
            chk = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, xpath)))
            
            # Se já estiver marcado (tem a classe active), não faz nada
            if "ui-state-active" in chk.get_attribute("class"): return True 
            
            # Tenta clicar
            clicar_js(driver, chk, f"Checkbox '{texto_label}'")
            time.sleep(0.3) # Espera a animação do check
            
            # Verifica se funcionou
            if "ui-state-active" in chk.get_attribute("class"): return True
        except: continue
        
    log(f"   [AVISO] Não consegui marcar '{texto_label}' após todas as tentativas.")
    return False

# ==============================================================================
# MODO 1: VINCULAR MÚLTIPLOS LOGINS (Lê dados.json)
# ==============================================================================

def verificar_status_medico(driver, botao_lapis):
    """Analisa visualmente (ícones) se o médico está ativo ou inativo."""
    try:
        linha = botao_lapis.find_element(By.XPATH, "./ancestor::tr")
        # Se tem botão vermelho 'inativar', ele está ATIVO
        if any(img.is_displayed() for img in linha.find_elements(By.CSS_SELECTOR, "img[src*='inativar.png']")): return True 
        # Se tem botão verde 'ativar', ele está INATIVO
        if any(img.is_displayed() for img in linha.find_elements(By.CSS_SELECTOR, "img[src*='ativar.png']")): return False 
        
        # Fallback: Verifica texto Sim/Não na linha
        texto = linha.text
        if "Sim" in texto: return True 
        if "Não" in texto: return False 
        return True 
    except: return True 

def tentar_clicar_lapis(driver, index):
    """
    Tenta clicar no botão de editar (lápis) do médico X da lista.
    Possui lógica de 'Retry' caso o elemento fique obsoleto (Stale) durante o loop.
    """
    for tentativa in range(3):
        try:
            botoes = driver.find_elements(By.CSS_SELECTOR, "img[title='Alterar']")
            if index >= len(botoes): return "ERRO"
            botao = botoes[index]
            
            if not verificar_status_medico(driver, botao): return "INATIVO"

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
            time.sleep(0.5)
            botao.click()
            return "CLICADO"
        except StaleElementReferenceException: time.sleep(1) # Elemento mudou, tenta de novo
        except: 
            try: clicar_js(driver, botao, f"Lápis {index}"); return "CLICADO"
            except: pass
    raise Exception("Falha ao interagir com o lápis.")

def tentar_abrir_dropdown_logins(driver):
    """Tenta abrir o menu de logins de várias formas até conseguir."""
    dropdown_container = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id$=':escolherLogins']")))
    for tentativa in range(1, 4):
        try:
            if tentativa == 1: dropdown_container.find_element(By.CSS_SELECTOR, ".ui-selectcheckboxmenu-trigger").click()
            elif tentativa == 2: dropdown_container.find_element(By.CSS_SELECTOR, ".ui-selectcheckboxmenu-label").click()
            elif tentativa == 3: driver.execute_script("arguments[0].click();", dropdown_container)
            time.sleep(1.5)
            # Verifica sucesso procurando o campo de filtro
            campo = driver.find_element(By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-filter-container input")
            if campo.is_displayed(): return campo
        except: pass
    raise Exception("Dropdown Logins não abriu.")

def executar_modo_vincular_logins(driver):
    log(">>> MODO 1: VINCULAR MÚLTIPLOS LOGINS <<<")
    ciclo = 1
    
    while True: # Loop infinito para permitir troca de página
        log(f"\n--- CICLO {ciclo} ---")
        
        # Lê os dados frescos do arquivo JSON
        dados = carregar_json(ARQUIVO_DADOS)
        lista_logins = dados.get("logins_para_vincular", []) if dados else []
        
        if not lista_logins:
            log(f"Lista 'logins_para_vincular' vazia em '{ARQUIVO_DADOS}'.")
        else:
            log(f"Logins carregados: {lista_logins}")
            try:
                botoes_lapis = driver.find_elements(By.CSS_SELECTOR, "img[title='Alterar']")
                total = len(botoes_lapis)
                
                if total == 0: log("Nenhum médico encontrado na tela.")
                else:
                    # Ignora o último usuário (logado) se houver mais de um na lista
                    total_processar = total - 1 if total > 1 else total
                    log(f"Total: {total}. Processando: {total_processar}.")
                    
                    for i in range(total_processar):
                        log(f"\n--- Médico {i+1} ---")
                        checar_pausa()
                        try:
                            # 1. Tenta abrir a edição do médico
                            res = tentar_clicar_lapis(driver, i)
                            if res == "INATIVO": 
                                log("   -> Inativo. Pulando.")
                                continue
                            elif res == "ERRO": continue
                            
                            esperar_aguarde_sumir(driver)
                            
                            try:
                                # 2. Abre o dropdown de logins
                                campo = tentar_abrir_dropdown_logins(driver)
                                houve_alteracao = False 
                                
                                # 3. Itera sobre cada login configurado no JSON
                                for login_alvo in lista_logins:
                                    campo.clear()
                                    campo.send_keys(login_alvo)
                                    time.sleep(1.5) 
                                    
                                    # Verifica o checkbox de "Selecionar Todos" no cabeçalho do filtro
                                    chk_header = driver.find_element(By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-header .ui-chkbox-box")
                                    if "ui-state-active" not in chk_header.get_attribute("class"):
                                        chk_header.click()
                                        time.sleep(0.5)
                                        log(f"   -> Marquei {login_alvo}")
                                        houve_alteracao = True
                                
                                # Fecha o dropdown
                                driver.find_element(By.CSS_SELECTOR, "a.ui-selectcheckboxmenu-close").click()
                                time.sleep(0.5)

                                # 4. Salva ou Cancela
                                if houve_alteracao:
                                    log("   [SALVANDO]")
                                    btn = driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Salvar']")
                                    clicar_js(driver, btn, "Salvar")
                                else:
                                    btn = driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Cancelar']")
                                    clicar_js(driver, btn, "Cancelar")
                                
                                esperar_aguarde_sumir(driver)
                            except Exception as e:
                                log(f"   Erro interno no modal: {e}")
                                fechar_janelas_travadas(driver)
                                esperar_aguarde_sumir(driver)
                        except Exception as e:
                            log(f"Erro no loop: {e}")
                            fechar_janelas_travadas(driver)
            except Exception as e_geral:
                log(f"Erro fatal: {e_geral}")
                break

        # Pausa final para edição do JSON
        ciclo += 1
        print("\n" + "#"*60)
        print(" CICLO FINALIZADO!")
        print(f" 1. Pode editar '{ARQUIVO_DADOS}' (campo 'logins_para_vincular').")
        print(" 2. Troque a página no navegador se necessário.")
        print(" 3. ENTER para recomeçar (ou '0' para sair).")
        print("#"*60)
        op = input(">>> ")
        if op == '0': break

# ==============================================================================
# MODO 2: CADASTRAR SERVIÇOS (Lê dados.json)
# ==============================================================================

def executar_modo_cadastrar_servicos(driver):
    log(">>> MODO 2: CADASTRAR NOVOS SERVIÇOS <<<")
    ciclo = 1
    
    while True: 
        log(f"\n--- CICLO {ciclo} ---")
        
        # Lê médicos do JSON
        dados = carregar_json(ARQUIVO_DADOS)
        medicos = dados.get("medicos_para_cadastrar", []) if dados else []
        
        if not medicos:
            log(f"Lista 'medicos_para_cadastrar' vazia em '{ARQUIVO_DADOS}'.")
        else:
            log(f"Médicos carregados: {len(medicos)}")
            erros = []

            for index, nome_medico in enumerate(medicos):
                log(f"\n--- [{index+1}/{len(medicos)}] {nome_medico} ---")
                checar_pausa()
                try:
                    # 1. Clicar no botão 'Criar Serviço'
                    try:
                        btn_criar = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Criar Serviço']]")))
                        clicar_js(driver, btn_criar, "Criar Serviço")
                        esperar_aguarde_sumir(driver)
                    except:
                        log("   [ERRO] Botão 'Criar Serviço' não achado.")
                        continue

                    # 2. Selecionar o Prestador na lista
                    log("   Selecionando Prestador...")
                    try:
                        driver.find_element(By.CSS_SELECTOR, "div[id$=':prestadorFuncionario'] .ui-selectonemenu-trigger").click()
                        time.sleep(1)
                        # Filtra pelo nome
                        campo_filtro = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[id$=':prestadorFuncionario_panel'] input")))
                        campo_filtro.clear()
                        campo_filtro.send_keys(nome_medico)
                        time.sleep(2.0)
                        
                        # Seleciona o item exato
                        sucesso = selecionar_item_combo(driver, nome_medico)
                        if not sucesso:
                            log(f"   [AVISO] Nome não encontrado na lista (Filtro falhou?).")
                            fechar_janelas_travadas(driver)
                            erros.append(nome_medico)
                            continue
                    except Exception as e:
                        log(f"   [ERRO] Dropdown falhou: {e}")
                        fechar_janelas_travadas(driver)
                        erros.append(nome_medico)
                        continue

                    # 3. PONTO DE SINCRONIA: Aguardar Tabela de Transações
                    # O sistema só termina de carregar o médico quando essa tabela aparece.
                    log("   Aguardando carregamento dos dados (Tabela)...")
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.ui-datatable"))
                        )
                        time.sleep(0.5) 
                    except:
                        log("   [ALERTA] Tabela de transações não apareceu. Tentando marcar mesmo assim...")

                    # 4. Marcar Opções (Checkboxes)
                    log("   Marcando caixas...")
                    garantir_checkbox(driver, "Visualiza transações")
                    garantir_checkbox(driver, "Cancela/Exclui")

                    # Marcar "Todas" na tabela de transações
                    try:
                        chk_todas = driver.find_element(By.XPATH, "//div[contains(@class, 'ui-datatable-scrollable-header')]//div[contains(@class, 'ui-chkbox-box')]")
                        if "ui-state-active" not in chk_todas.get_attribute("class"):
                            # CORREÇÃO IMPORTANTE APLICADA AQUI: Variável correta usada
                            clicar_js(driver, chk_todas, "Todas")
                            time.sleep(0.3)
                    except: pass

                    time.sleep(0.5)

                    # 5. Salvar
                    log("   Salvando...")
                    btn_salvar = driver.find_element(By.XPATH, "//span[text()='Salvar']")
                    clicar_js(driver, btn_salvar, "Salvar")
                    esperar_aguarde_sumir(driver)
                    log("   -> Sucesso.")

                except Exception as e:
                    log(f"   [ERRO CRÍTICO] {e}")
                    fechar_janelas_travadas(driver)
                    esperar_aguarde_sumir(driver)
                    erros.append(nome_medico)

            log(f"\nCICLO {ciclo} FINALIZADO!")
            if erros:
                log("Erros neste ciclo:")
                for err in erros: print(f" - {err}")

        # Pausa final para edição do JSON
        ciclo += 1
        print("\n" + "#"*60)
        print(" LISTA FINALIZADO!")
        print(f" 1. Pode editar '{ARQUIVO_DADOS}' (campo 'medicos_para_cadastrar').")
        print(" 2. ENTER para recomeçar (ou '0' para sair).")
        print("#"*60)
        op = input(">>> ")
        if op == '0': break

# ==============================================================================
# BLOCO PRINCIPAL (MAIN)
# ==============================================================================

if __name__ == "__main__":
    print("\n--- ROBÔ NTISS V24 (EDITION FINAL JSON) ---")
    
    # Inicializa o Chrome automaticamente usando WebDriver Manager
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    driver.get(URL_SISTEMA) # URL lida do config.json
    
    print("\n>>> FAÇA LOGIN E VÁ PARA A TELA CERTA.")
    input(">>> ENTER PARA COMEÇAR...")
    
    while True:
        print("\n--- MENU PRINCIPAL ---")
        print(" 1 - Vincular Logins (Lê 'logins_para_vincular' do JSON)")
        print(" 2 - Cadastrar Serviços (Lê 'medicos_para_cadastrar' do JSON)")
        print(" 0 - Sair")
        op = input(">>> Escolha: ").strip()
        
        if op == "1": executar_modo_vincular_logins(driver)
        elif op == "2": executar_modo_cadastrar_servicos(driver)
        elif op == "0": break
        
    driver.quit()
    print("Execução encerrada.")