import time
import msvcrt
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException

# --- CONFIGURAÇÕES ---
URL_SISTEMA = "https://ntiss.neki-it.com.br/ntiss/login.jsf"
ARQUIVO_MEDICOS = "medicos.txt"
ARQUIVO_LOGINS = "logins.txt"
TIMEOUT_AGUARDE = 40 

# --- FUNÇÕES GERAIS ---

def log(mensagem):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {mensagem}")

def carregar_arquivo(nome_arquivo):
    """Lê um arquivo txt e retorna uma lista limpa"""
    if not os.path.exists(nome_arquivo):
        log(f"[ERRO] Arquivo '{nome_arquivo}' não encontrado!")
        return []
    with open(nome_arquivo, "r", encoding="utf-8") as arquivo:
        lista = [linha.strip() for linha in arquivo if linha.strip()]
    return lista

def checar_pausa():
    if msvcrt.kbhit():
        tecla = msvcrt.getch()
        if tecla.lower() == b'p':
            print("\n" + "="*40)
            print(">>> PAUSA SOLICITADA! <<<")
            input(">>> Pressione ENTER para CONTINUAR...")
            print("="*40 + "\n")
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
    try:
        driver.execute_script("arguments[0].click();", elemento)
    except Exception as e:
        log(f"   [ERRO] Falha ao clicar em {nome}: {e}")

def fechar_janelas_travadas(driver):
    try:
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    except: pass

def selecionar_item_combo(driver, nome_medico):
    xpath_item = f"//div[contains(@id, 'prestadorFuncionario_panel')]//li[contains(., '{nome_medico}')]"
    try:
        item_especifico = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, xpath_item))
        )
        item_especifico.click()
        return True
    except Exception:
        try:
            item_especifico = driver.find_element(By.XPATH, xpath_item)
            driver.execute_script("arguments[0].click();", item_especifico)
            return True
        except:
            return False

def garantir_checkbox(driver, texto_label):
    xpath_tr = f"//tr[.//label[contains(text(), '{texto_label}')]]//div[contains(@class, 'ui-chkbox-box')]"
    xpath_parent = f"//label[contains(text(), '{texto_label}')]/..//div[contains(@class, 'ui-chkbox-box')]"
    xpath_sibling = f"//label[contains(text(), '{texto_label}')]/preceding-sibling::div[contains(@class, 'ui-chkbox-box')]"
    lista_tentativas = [xpath_tr, xpath_parent, xpath_sibling]
    
    for xpath in lista_tentativas:
        try:
            chk = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, xpath)))
            if "ui-state-active" in chk.get_attribute("class"): return True 
            clicar_js(driver, chk, f"Checkbox '{texto_label}'")
            time.sleep(0.3)
            if "ui-state-active" in chk.get_attribute("class"): return True
        except: continue
    log(f"   [AVISO] Não consegui marcar '{texto_label}'.")
    return False

# ==============================================================================
# MODO 1: VINCULAR MÚLTIPLOS LOGINS (Recarregamento Automático)
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
    raise Exception("Falha ao interagir com o lápis.")

def tentar_abrir_dropdown_logins(driver):
    dropdown_container = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id$=':escolherLogins']")))
    for tentativa in range(1, 4):
        try:
            if tentativa == 1: dropdown_container.find_element(By.CSS_SELECTOR, ".ui-selectcheckboxmenu-trigger").click()
            elif tentativa == 2: dropdown_container.find_element(By.CSS_SELECTOR, ".ui-selectcheckboxmenu-label").click()
            elif tentativa == 3: driver.execute_script("arguments[0].click();", dropdown_container)
            time.sleep(1.5)
            campo = driver.find_element(By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-filter-container input")
            if campo.is_displayed(): return campo
        except: pass
    raise Exception("Dropdown Logins não abriu.")

def executar_modo_vincular_logins(driver):
    log(">>> MODO 1: VINCULAR MÚLTIPLOS LOGINS <<<")
    ciclo = 1
    
    while True: # LOOP DO CICLO
        log(f"\n--- CICLO {ciclo} ---")
        
        # --- RECARREGA A LISTA DE LOGINS A CADA CICLO ---
        lista_logins = carregar_arquivo(ARQUIVO_LOGINS)
        if not lista_logins:
            log(f"Arquivo '{ARQUIVO_LOGINS}' vazio ou não encontrado.")
        else:
            log(f"Logins carregados: {lista_logins}")
            
            try:
                botoes_lapis = driver.find_elements(By.CSS_SELECTOR, "img[title='Alterar']")
                total = len(botoes_lapis)
                if total == 0: log("Nenhum médico encontrado.")
                else:
                    total_processar = total - 1 if total > 1 else total
                    log(f"Total: {total}. Processando: {total_processar}.")
                    
                    for i in range(total_processar):
                        log(f"\n--- Médico {i+1} ---")
                        checar_pausa()
                        try:
                            res = tentar_clicar_lapis(driver, i)
                            if res == "INATIVO": 
                                log("   -> Inativo. Pulando.")
                                continue
                            elif res == "ERRO": continue
                            
                            esperar_aguarde_sumir(driver)
                            
                            try:
                                campo = tentar_abrir_dropdown_logins(driver)
                                houve_alteracao = False 
                                
                                for login_alvo in lista_logins:
                                    # log(f"   Verificando: {login_alvo}") # Opcional: descomentar se quiser ver detalhes
                                    campo.clear()
                                    campo.send_keys(login_alvo)
                                    time.sleep(1.5) 
                                    
                                    chk_header = driver.find_element(By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-header .ui-chkbox-box")
                                    
                                    if "ui-state-active" not in chk_header.get_attribute("class"):
                                        chk_header.click()
                                        time.sleep(0.5)
                                        log(f"   -> Marquei {login_alvo}")
                                        houve_alteracao = True
                                    # else: log(f"   -> Já possui {login_alvo}")

                                driver.find_element(By.CSS_SELECTOR, "a.ui-selectcheckboxmenu-close").click()
                                time.sleep(0.5)

                                if houve_alteracao:
                                    log("   [SALVANDO]")
                                    btn = driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Salvar']")
                                    clicar_js(driver, btn, "Salvar")
                                else:
                                    # log("   [CANCELANDO]")
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

        # --- PAUSA ENTRE CICLOS ---
        ciclo += 1
        print("\n" + "#"*60)
        print(" CICLO FINALIZADO!")
        print(f" 1. Se quiser, edite '{ARQUIVO_LOGINS}' agora e salve.")
        print(" 2. Troque a página no navegador.")
        print(" 3. Pressione ENTER para rodar de novo com os novos valores.")
        print("#"*60)
        op = input(">>> ")
        if op == '0': break

# ==============================================================================
# MODO 2: CADASTRAR SERVIÇOS (Recarregamento Automático)
# ==============================================================================

def executar_modo_cadastrar_servicos(driver):
    log(">>> MODO 2: CADASTRAR NOVOS SERVIÇOS <<<")
    ciclo = 1
    
    while True: 
        log(f"\n--- CICLO {ciclo} ---")
        
        # --- RECARREGA A LISTA DE MÉDICOS A CADA CICLO ---
        medicos = carregar_arquivo(ARQUIVO_MEDICOS)
        
        if not medicos:
            log(f"Arquivo '{ARQUIVO_MEDICOS}' vazio ou não encontrado.")
        else:
            log(f"Médicos carregados: {len(medicos)}")
            erros = []

            for index, nome_medico in enumerate(medicos):
                log(f"\n--- [{index+1}/{len(medicos)}] {nome_medico} ---")
                checar_pausa()
                try:
                    try:
                        btn_criar = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Criar Serviço']]")))
                        clicar_js(driver, btn_criar, "Criar Serviço")
                        esperar_aguarde_sumir(driver)
                    except:
                        log("   [ERRO] Botão 'Criar Serviço' não achado.")
                        continue

                    log("   Selecionando Prestador...")
                    try:
                        driver.find_element(By.CSS_SELECTOR, "div[id$=':prestadorFuncionario'] .ui-selectonemenu-trigger").click()
                        time.sleep(1)
                        campo_filtro = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[id$=':prestadorFuncionario_panel'] input")))
                        campo_filtro.clear()
                        campo_filtro.send_keys(nome_medico)
                        time.sleep(2.0)
                        
                        sucesso = selecionar_item_combo(driver, nome_medico)
                        if not sucesso:
                            log(f"   [AVISO] Nome não encontrado na lista.")
                            fechar_janelas_travadas(driver)
                            erros.append(nome_medico)
                            continue
                    except Exception as e:
                        log(f"   [ERRO] Dropdown falhou: {e}")
                        fechar_janelas_travadas(driver)
                        erros.append(nome_medico)
                        continue

                    log("   Aguardando carregamento dos dados (Tabela)...")
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.ui-datatable"))
                        )
                        time.sleep(0.5) 
                    except:
                        log("   [ALERTA] Tabela de transações não apareceu. Tentando marcar mesmo assim...")

                    log("   Marcando caixas...")
                    garantir_checkbox(driver, "Visualiza transações")
                    garantir_checkbox(driver, "Cancela/Exclui")

                    try:
                        chk_todas = driver.find_element(By.XPATH, "//div[contains(@class, 'ui-datatable-scrollable-header')]//div[contains(@class, 'ui-chkbox-box')]")
                        if "ui-state-active" not in chk_todas.get_attribute("class"):
                            clicar_js(driver, chk_todas, "Todas")
                            time.sleep(0.3)
                    except: pass

                    time.sleep(0.5)

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

        ciclo += 1
        print("\n" + "#"*60)
        print(" LISTA FINALIZADO!")
        print(f" 1. Se quiser, edite '{ARQUIVO_MEDICOS}' agora e salve.")
        print(" 2. ENTER para recomeçar (ou '0' para sair).")
        print("#"*60)
        op = input(">>> ")
        if op == '0': break

if __name__ == "__main__":
    print("\n--- ROBÔ NTISS V21 (RECARREGAMENTO LIVE) ---")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    driver.get(URL_SISTEMA)
    print("\n>>> FAÇA LOGIN E VÁ PARA A TELA CERTA.")
    input(">>> ENTER PARA COMEÇAR...")
    while True:
        print("\n 1 - Vincular Logins (Lê 'logins.txt')\n 2 - Cadastrar Serviços (Lê 'medicos.txt')\n 0 - Sair")
        op = input(">>> ").strip()
        if op == "1": executar_modo_vincular_logins(driver)
        elif op == "2": executar_modo_cadastrar_servicos(driver)
        elif op == "0": break
    driver.quit()