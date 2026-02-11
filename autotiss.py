"""
🏥 AUTOMATION TOOLKIT - NTISS (V27 - FULL INTEGRATION)
------------------------------------------------------
Descrição: Fusão completa da V24 (Lógica de Negócio) com a V25 (Navegação).
Autor: Pedro Henrique + Gemini
"""

import time
import msvcrt
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

# --- CONSTANTES ---
ARQUIVO_CONFIG = "config.json"
ARQUIVO_DADOS = "dados.json"

# --- CONFIGURAÇÃO ---
def carregar_json(caminho):
    if not os.path.exists(caminho): return None
    try:
        with open(caminho, "r", encoding="utf-8") as f: return json.load(f)
    except: return None

CONF = carregar_json(ARQUIVO_CONFIG)
if not CONF:
    CONF = {"url_sistema": "https://ntiss.neki-it.com.br/ntiss/login.jsf", "timeout_aguarde": 40}

URL_SISTEMA = CONF.get("url_sistema")
TIMEOUT_AGUARDE = CONF.get("timeout_aguarde", 40)

# --- HELPERS (DO SEU CÓDIGO ORIGINAL) ---

def log(mensagem):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {mensagem}")

def checar_pausa():
    if msvcrt.kbhit():
        tecla = msvcrt.getch()
        if tecla.lower() == b'p':
            print("\n>>> PAUSA SOLICITADA! ENTER para continuar... <<<")
            input()
            log("Retomando...")

def esperar_aguarde_sumir(driver):
    time.sleep(0.3)
    try:
        WebDriverWait(driver, TIMEOUT_AGUARDE).until(
            EC.invisibility_of_element_located((By.ID, "aguarde"))
        )
        time.sleep(0.3)
    except: pass

def clicar_js(driver, elemento, nome="Elemento"):
    try: driver.execute_script("arguments[0].click();", elemento)
    except Exception as e: log(f"   [ERRO] Falha ao clicar {nome}: {e}")

def fechar_janelas_travadas(driver):
    try: webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    except: pass

# --- FUNÇÕES DE NAVEGAÇÃO (NOVAS - O PASSO A PASSO QUE VOCÊ PEDIU) ---

def navegar_pesquisar_secretaria(driver, login_secretaria):
    """
    Passo 1: Pesquisa o login na tela principal e clica no lápis.
    """
    log(f"🔍 [NAVEGAÇÃO] Pesquisando: {login_secretaria}")
    esperar_aguarde_sumir(driver)
    
    try:
        # 1. Limpa e Digita o Login
        # Procura o input pelo ID (j_idt129) ou genericamente
        try:
            campo = driver.find_element(By.ID, "j_idt129")
        except:
            # Fallback: Input após o label 'Login'
            campo = driver.find_element(By.XPATH, "//label[contains(text(),'Login')]/following::input[1]")
            
        campo.clear()
        campo.send_keys(login_secretaria)
        time.sleep(0.5)
        
        # 2. Clica em Pesquisar
        try:
            btn_pesquisar = driver.find_element(By.XPATH, "//button[span[text()='Pesquisar']]")
        except:
            btn_pesquisar = driver.find_element(By.CSS_SELECTOR, "button[title='Pesquisar']")
            
        clicar_js(driver, btn_pesquisar, "Pesquisar")
        esperar_aguarde_sumir(driver)
        time.sleep(1.0)
        
        # 3. Clica no Lápis do resultado
        try:
            btn_lapis = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "img[title='Alterar']"))
            )
            clicar_js(driver, btn_lapis, "Editar Usuário")
            esperar_aguarde_sumir(driver)
            log("   -> Entrei no cadastro.")
            return True
        except:
            log(f"   [AVISO] Usuário '{login_secretaria}' não encontrado na pesquisa.")
            return False
            
    except Exception as e:
        log(f"   [ERRO NAVEGAÇÃO] {e}")
        return False

def voltar_para_pesquisa(driver):
    """
    Passo Final: Clica no Cancelar da página para voltar.
    """
    log("🔙 [NAVEGAÇÃO] Voltando para pesquisa...")
    try:
        fechar_janelas_travadas(driver)
        esperar_aguarde_sumir(driver)
        
        # Busca o botão Cancelar do rodapé (j_idt221 ou via texto)
        xpath_cancelar = "//button[span[text()='Cancelar']][not(ancestor::div[contains(@class,'ui-dialog')])]"
        
        try:
            btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath_cancelar)))
            clicar_js(driver, btn, "Cancelar (Voltar)")
        except:
            # Tenta pelo ID específico que você mandou
            btn = driver.find_element(By.ID, "j_idt221") 
            clicar_js(driver, btn, "Cancelar ID Fixo")

        esperar_aguarde_sumir(driver)
        
    except Exception as e:
        log(f"   [ERRO AO VOLTAR] {e}")

# ==============================================================================
# LÓGICA V24 - MODO 1: VINCULAR LOGINS (RESTAURADA INTEGRALMENTE)
# ==============================================================================

def verificar_status_medico(driver, botao_lapis):
    try:
        linha = botao_lapis.find_element(By.XPATH, "./ancestor::tr")
        if any(img.is_displayed() for img in linha.find_elements(By.CSS_SELECTOR, "img[src*='inativar.png']")): return True 
        if any(img.is_displayed() for img in linha.find_elements(By.CSS_SELECTOR, "img[src*='ativar.png']")): return False 
        texto = linha.text
        if "Sim" in texto: return True 
        if "Não" in texto: return False 
        return True 
    except: return True 

def tentar_clicar_lapis(driver, index):
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
        except StaleElementReferenceException: time.sleep(1)
        except: 
            try: clicar_js(driver, botao, f"Lápis {index}"); return "CLICADO"
            except: pass
    return "ERRO"

def tentar_abrir_dropdown_logins(driver):
    div_dropdown = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id$=':escolherLogins']")))
    for tentativa in range(1, 4):
        try:
            if tentativa == 1: div_dropdown.find_element(By.CSS_SELECTOR, ".ui-selectcheckboxmenu-trigger").click()
            elif tentativa == 2: div_dropdown.find_element(By.CSS_SELECTOR, ".ui-selectcheckboxmenu-label").click()
            elif tentativa == 3: driver.execute_script("arguments[0].click();", div_dropdown)
            time.sleep(1.5)
            campo = driver.find_element(By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-filter-container input")
            if campo.is_displayed(): return campo
        except: pass
    raise Exception("Dropdown Logins não abriu.")

def executar_logica_vincular_logins(driver, lista_logins):
    """
    Lógica da V24 adaptada para rodar UMA VEZ na tela atual.
    """
    try:
        botoes_lapis = driver.find_elements(By.CSS_SELECTOR, "img[title='Alterar']")
        total = len(botoes_lapis)
        
        if total == 0:
            log("   [V24] Nenhum médico encontrado nesta tela.")
            return

        total_processar = total - 1 if total > 1 else total
        log(f"   [V24] Processando {total_processar} médicos...")

        for i in range(total_processar):
            log(f"   --- Médico {i+1} ---")
            checar_pausa()
            try:
                # 1. Abre modal
                res = tentar_clicar_lapis(driver, i)
                if res == "INATIVO": 
                    log("   -> Inativo. Pulando.")
                    continue
                elif res == "ERRO": continue
                
                esperar_aguarde_sumir(driver)
                
                # 2. Dropdown
                try:
                    campo = tentar_abrir_dropdown_logins(driver)
                    houve_alteracao = False 
                    
                    for login_alvo in lista_logins:
                        campo.clear()
                        campo.send_keys(login_alvo)
                        time.sleep(1.5)
                        
                        chk_header = driver.find_element(By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-header .ui-chkbox-box")
                        if "ui-state-active" not in chk_header.get_attribute("class"):
                            chk_header.click()
                            time.sleep(0.5)
                            log(f"      + Vinculado: {login_alvo}")
                            houve_alteracao = True
                        
                    driver.find_element(By.CSS_SELECTOR, "a.ui-selectcheckboxmenu-close").click()
                    time.sleep(0.5)

                    if houve_alteracao:
                        btn = driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Salvar']")
                        clicar_js(driver, btn, "Salvar")
                    else:
                        btn = driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Cancelar']")
                        clicar_js(driver, btn, "Cancelar")
                    
                    esperar_aguarde_sumir(driver)
                except Exception as e:
                    log(f"   Erro modal: {e}")
                    fechar_janelas_travadas(driver)
                    esperar_aguarde_sumir(driver)

            except Exception as e:
                log(f"   Erro loop: {e}")
                fechar_janelas_travadas(driver)
    except: pass

# ==============================================================================
# LÓGICA V24 - MODO 2: CADASTRAR SERVIÇOS (RESTAURADA INTEGRALMENTE)
# ==============================================================================

def selecionar_item_combo(driver, nome_medico):
    xpath_item = f"//div[contains(@id, 'prestadorFuncionario_panel')]//li[contains(., '{nome_medico}')]"
    try:
        item = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, xpath_item)))
        item.click()
        return True
    except:
        try:
            item = driver.find_element(By.XPATH, xpath_item)
            driver.execute_script("arguments[0].click();", item)
            return True
        except: return False

def garantir_checkbox(driver, texto_label):
    listas = [
        f"//tr[.//label[contains(text(), '{texto_label}')]]//div[contains(@class, 'ui-chkbox-box')]",
        f"//label[contains(text(), '{texto_label}')]/..//div[contains(@class, 'ui-chkbox-box')]",
        f"//label[contains(text(), '{texto_label}')]/preceding-sibling::div[contains(@class, 'ui-chkbox-box')]"
    ]
    for xpath in listas:
        try:
            chk = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, xpath)))
            if "ui-state-active" in chk.get_attribute("class"): return True 
            clicar_js(driver, chk, texto_label)
            time.sleep(0.3)
            if "ui-state-active" in chk.get_attribute("class"): return True
        except: continue
    return False

def executar_logica_cadastrar_servicos(driver, medicos):
    """
    Lógica da V24 para Cadastrar Serviços (Vincular Médicos).
    """
    log(f"   [V24] Iniciando cadastro de {len(medicos)} médicos...")
    erros = []
    
    for index, nome_medico in enumerate(medicos):
        log(f"   --- [{index+1}/{len(medicos)}] {nome_medico} ---")
        checar_pausa()
        try:
            # 1. Clicar em Criar Serviço
            try:
                btn_criar = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Criar Serviço']]")))
                clicar_js(driver, btn_criar, "Criar Serviço")
                esperar_aguarde_sumir(driver)
            except:
                log("      [ERRO] Botão 'Criar Serviço' não encontrado.")
                continue

            # 2. Selecionar Prestador
            driver.find_element(By.CSS_SELECTOR, "div[id$=':prestadorFuncionario'] .ui-selectonemenu-trigger").click()
            time.sleep(1)
            campo_filtro = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[id$=':prestadorFuncionario_panel'] input")))
            campo_filtro.clear()
            campo_filtro.send_keys(nome_medico)
            time.sleep(2.0)
            
            if not selecionar_item_combo(driver, nome_medico):
                log("      [AVISO] Médico não encontrado no dropdown.")
                fechar_janelas_travadas(driver)
                erros.append(nome_medico)
                continue
            
            # 3. Esperar Tabela e Checkboxes
            try:
                WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.ui-datatable")))
            except: log("      [ALERTA] Tabela demorou.")

            garantir_checkbox(driver, "Visualiza transações")
            garantir_checkbox(driver, "Cancela/Exclui")
            
            try:
                chk_todas = driver.find_element(By.XPATH, "//div[contains(@class, 'ui-datatable-scrollable-header')]//div[contains(@class, 'ui-chkbox-box')]")
                if "ui-state-active" not in chk_todas.get_attribute("class"):
                    clicar_js(driver, chk_todas, "Check Todas")
            except: pass
            
            time.sleep(0.5)

            # 4. Salvar
            btn_salvar = driver.find_element(By.XPATH, "//span[text()='Salvar']")
            clicar_js(driver, btn_salvar, "Salvar")
            esperar_aguarde_sumir(driver)
            log("      -> Sucesso.")

        except Exception as e:
            log(f"      [ERRO CRÍTICO] {e}")
            fechar_janelas_travadas(driver)
            erros.append(nome_medico)
            
    if erros: log(f"   Erros no ciclo: {erros}")

# ==============================================================================
# LOOP PRINCIPAL (NAVIGATION WRAPPER)
# ==============================================================================

def executar_robo_completo(driver):
    while True:
        print("\n--- MENU V27 (NAVEGAÇÃO + V24 INTEGRAL) ---")
        print(" 1 - Vincular Logins (Pesquisa + Edita + Vincula)")
        print(" 2 - Cadastrar Serviços (Pesquisa + Cria + Cadastra)")
        print(" 0 - Sair")
        op = input(">>> Escolha: ").strip()
        
        if op == '0': break
        
        # Carrega dados
        dados = carregar_json(ARQUIVO_DADOS)
        secretarias = dados.get("secretarias_para_pesquisar", [])
        
        if not secretarias:
            log("[ERRO] Lista 'secretarias_para_pesquisar' vazia!")
            continue

        logins_vincular = dados.get("logins_para_vincular", [])
        medicos_cadastrar = dados.get("medicos_para_cadastrar", [])

        # LOOP DE NAVEGAÇÃO
        total = len(secretarias)
        for idx, sec in enumerate(secretarias):
            log(f"\n=========================================")
            log(f" SECRETARIA [{idx+1}/{total}]: {sec}")
            log(f"=========================================")
            
            # 1. NAVEGAR
            entrou = navegar_pesquisar_secretaria(driver, sec)
            if not entrou: continue
            
            # 2. EXECUTAR A TAREFA ESCOLHIDA
            if op == '1':
                executar_logica_vincular_logins(driver, logins_vincular)
            elif op == '2':
                executar_logica_cadastrar_servicos(driver, medicos_cadastrar)
            
            # 3. VOLTAR
            voltar_para_pesquisa(driver)

        print("\nCICLO FINALIZADO! ENTER para menu...")
        input()

if __name__ == "__main__":
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    driver.get(URL_SISTEMA)
    
    print("\n>>> FAÇA LOGIN E VÁ PARA A TELA DE PESQUISA.")
    input(">>> ENTER PARA COMEÇAR...")
    
    executar_robo_completo(driver)
    driver.quit()