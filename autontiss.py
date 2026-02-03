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
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

# --- CONFIGURAÇÕES ---
URL_SISTEMA = "https://ntiss.neki-it.com.br/ntiss/login.jsf"
TEMPO_ESPERA_AGUARDE = 40 
ARQUIVO_MEDICOS = "medicos.txt"

# --- FUNÇÕES GERAIS ---

def log(mensagem):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {mensagem}")

def carregar_lista_medicos():
    if not os.path.exists(ARQUIVO_MEDICOS):
        log(f"[ERRO] Arquivo '{ARQUIVO_MEDICOS}' não encontrado!")
        return []
    with open(ARQUIVO_MEDICOS, "r", encoding="utf-8") as arquivo:
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
    """
    Espera o 'Aguarde' sumir.
    Pequeno delay inicial para dar tempo dele aparecer após o clique.
    """
    time.sleep(0.5) 
    try:
        WebDriverWait(driver, TEMPO_ESPERA_AGUARDE).until(
            EC.invisibility_of_element_located((By.ID, "aguarde"))
        )
        time.sleep(0.5) 
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

# ==============================================================================
# MODO 1: VINCULAR LOGINS (77.hu)
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
    dropdown_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[id$=':escolherLogins']"))
    )
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
    log(">>> MODO: VINCULAR 77.HU <<<")
    ciclo = 1
    while True:
        log(f"--- CICLO {ciclo} ---")
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
                            campo.clear()
                            campo.send_keys("77.hu")
                            time.sleep(2.5)

                            chk_todos = driver.find_element(By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-header .ui-chkbox-box")
                            ja_feito = "ui-state-active" in chk_todos.get_attribute("class")
                            log(f"   Status: {'[JÁ FEITO]' if ja_feito else '[PENDENTE]'}")

                            if ja_feito:
                                driver.find_element(By.CSS_SELECTOR, "a.ui-selectcheckboxmenu-close").click()
                                time.sleep(0.5)
                                btn = driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Cancelar']")
                                clicar_js(driver, btn, "Cancelar")
                            else:
                                chk_todos.click()
                                time.sleep(0.5)
                                driver.find_element(By.CSS_SELECTOR, "a.ui-selectcheckboxmenu-close").click()
                                time.sleep(0.5)
                                btn = driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Salvar']")
                                clicar_js(driver, btn, "Salvar")
                            
                            esperar_aguarde_sumir(driver)
                        except Exception as e:
                            log(f"   Erro interno: {e}")
                            fechar_janelas_travadas(driver)
                            esperar_aguarde_sumir(driver)
                    except Exception as e:
                        log(f"Erro no loop: {e}")
                        fechar_janelas_travadas(driver)
                
            ciclo += 1
            print("\nCICLO FINALIZADO! Troque o secretário e aperte ENTER.")
            input()
            
        except Exception as e_geral:
            log(f"Erro fatal: {e_geral}")
            break

# ==============================================================================
# MODO 2: CADASTRAR SERVIÇOS (Lê do Arquivo)
# ==============================================================================

def executar_modo_cadastrar_servicos(driver):
    log(">>> MODO: CADASTRAR NOVOS SERVIÇOS <<<")
    
    medicos_para_cadastrar = carregar_lista_medicos()
    
    if not medicos_para_cadastrar:
        log("Lista vazia ou arquivo não encontrado. Cancelando.")
        return

    log(f"Carregados {len(medicos_para_cadastrar)} nomes do arquivo '{ARQUIVO_MEDICOS}'.")
    erros = []

    for index, nome_medico in enumerate(medicos_para_cadastrar):
        log(f"\n--- [{index+1}/{len(medicos_para_cadastrar)}] Cadastrando: {nome_medico} ---")
        checar_pausa()
        
        try:
            # 1. Clicar em "Criar Serviço"
            try:
                # Espera botão estar clicável e clica
                btn_criar = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Criar Serviço']]"))
                )
                clicar_js(driver, btn_criar, "Criar Serviço")
                
                # --- CORREÇÃO AQUI: ESPERA O AGUARDE SUMIR ANTES DE PROSSEGUIR ---
                esperar_aguarde_sumir(driver) 
                # -----------------------------------------------------------------
            except:
                log("   [ERRO] Botão 'Criar Serviço' não achado.")
                continue

            # 2. Abrir Dropdown
            log("   Selecionando Prestador...")
            try:
                dropdown_trigger = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div[id$=':prestadorFuncionario'] .ui-selectonemenu-trigger"))
                )
                dropdown_trigger.click()
                time.sleep(1) 
            except:
                log("   [ERRO] Dropdown de prestador travado ou não encontrado.")
                fechar_janelas_travadas(driver)
                erros.append(nome_medico)
                continue

            # 3. Pesquisar Nome
            campo_filtro = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div[id$=':prestadorFuncionario_panel'] input"))
            )
            campo_filtro.clear()
            campo_filtro.send_keys(nome_medico)
            time.sleep(2.0) 

            # 4. Selecionar Item
            try:
                item_lista = driver.find_element(By.CSS_SELECTOR, "div[id$=':prestadorFuncionario_panel'] ul li:not(.ui-helper-hidden)")
                clicar_js(driver, item_lista, f"Selecionar {nome_medico}")
                
                # Espera carregar checkboxes (se houver AJAX no select)
                # Como você disse que não tem aguarde aqui, mantemos sleep simples
                # Se tiver aguarde aqui também, avise!
                time.sleep(1.5) 
            except:
                log(f"   [AVISO] Médico '{nome_medico}' não encontrado!")
                fechar_janelas_travadas(driver) 
                erros.append(nome_medico)
                continue

            # 5. Marcar Opções
            log("   Marcando opções...")
            
            try:
                chk_visualiza = driver.find_element(By.XPATH, "//label[contains(text(), 'Visualiza transações')]/preceding-sibling::div[contains(@class, 'ui-chkbox-box')]")
                if "ui-state-active" not in chk_visualiza.get_attribute("class"):
                    clicar_js(driver, chk_visualiza, "Visualiza Transações")
            except: pass

            try:
                chk_cancela = driver.find_element(By.XPATH, "//label[contains(text(), 'Cancela/Exclui')]/preceding-sibling::div[contains(@class, 'ui-chkbox-box')]")
                if "ui-state-active" not in chk_cancela.get_attribute("class"):
                    clicar_js(driver, chk_cancela, "Cancela/Exclui")
            except: pass

            try:
                chk_todas = driver.find_element(By.XPATH, "//div[contains(@class, 'ui-datatable-scrollable-header')]//div[contains(@class, 'ui-chkbox-box')]")
                if "ui-state-active" not in chk_todas.get_attribute("class"):
                    clicar_js(driver, chk_todas, "Todas as Transações")
            except:
                log("   [AVISO] Sem tabela de transações.")

            time.sleep(0.5)

            # 6. Salvar e ESPERAR O AGUARDE
            log("   Salvando...")
            btn_salvar = driver.find_element(By.XPATH, "//span[text()='Salvar']")
            clicar_js(driver, btn_salvar, "Botão Salvar")
            
            esperar_aguarde_sumir(driver) # Espera salvar
            log("   -> Sucesso.")

        except Exception as e:
            log(f"   [ERRO CRÍTICO] {nome_medico}: {e}")
            fechar_janelas_travadas(driver)
            esperar_aguarde_sumir(driver) # Garante que destrava se tiver modal
            erros.append(nome_medico)

    log("\n" + "="*50)
    log("CADASTRO FINALIZADO!")
    if erros:
        log(f"Erros ({len(erros)}):")
        for err in erros: print(f" - {err}")
    print("="*50)

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    print("\n--- ROBÔ NTISS V12 (FINAL) ---")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    driver.get(URL_SISTEMA)

    print("\n>>> FAÇA LOGIN E VÁ PARA A TELA CERTA.")
    input(">>> ENTER PARA COMEÇAR...")

    while True:
        print("\n" + "="*40)
        print(" 1 - Vincular Login '77.hu'")
        print(" 2 - Cadastrar Serviços (Lê 'medicos.txt')")
        print(" 0 - Sair")
        print("="*40)
        
        opcao = input(">>> Opção: ").strip()

        if opcao == "1": executar_modo_vincular_logins(driver)
        elif opcao == "2": executar_modo_cadastrar_servicos(driver)
        elif opcao == "0": break
        else: print("Inválido!")

    driver.quit()