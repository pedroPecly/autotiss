"""
🏥 AUTOMATION TOOLKIT - NTISS (V29 - AUTO LOGIN)
------------------------------------------------
Descrição: V28 com Login Automático adicionado.
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

# --- VARIÁVEIS DE CONTROLE ---
solicitar_finalizacao = False
medicos_cadastrados_sessao = {}  # {secretaria: [medico1, medico2, ...]}

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
USUARIO_LOGIN = CONF.get("usuario", "")
SENHA_LOGIN = CONF.get("senha", "")

# --- HELPERS ---

def log(mensagem):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {mensagem}")

def checar_pausa():
    """Verifica se há tecla pressionada para pausar (P) ou finalizar (F)"""
    global solicitar_finalizacao
    if msvcrt.kbhit():
        tecla = msvcrt.getch()
        if tecla.lower() == b'p':
            print("\n" + "="*60)
            print(">>> ⏸️  PAUSA SOLICITADA! <<<")
            print("    Pressione ENTER para continuar...")
            print("    Ou pressione F + ENTER para finalizar")
            print("="*60)
            resposta = input().strip().lower()
            if resposta == 'f':
                solicitar_finalizacao = True
                log("🛑 Finalização solicitada pelo usuário!")
            else:
                log("▶️  Retomando execução...")
        elif tecla.lower() == b'f':
            print("\n" + "="*60)
            print(">>> 🛑 FINALIZAÇÃO SOLICITADA! <<<")
            print("="*60)
            solicitar_finalizacao = True
            log("Encerrando processo...")

def esperar_aguarde_sumir(driver):
    time.sleep(0.2)
    try:
        WebDriverWait(driver, TIMEOUT_AGUARDE).until(
            EC.invisibility_of_element_located((By.ID, "aguarde"))
        )
    except: pass

def clicar_js(driver, elemento, nome="Elemento"):
    try: driver.execute_script("arguments[0].click();", elemento)
    except Exception as e: log(f"   [ERRO] Falha ao clicar {nome}: {e}")

def fechar_janelas_travadas(driver):
    try: webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    except: pass

# --- FUNÇÃO DE LOGIN AUTOMÁTICO (NOVA) ---

def realizar_login_automatico(driver):
    log("🔑 Iniciando Login Automático...")
    try:
        # Preenche Usuário
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "login")))
        driver.find_element(By.ID, "login").clear()
        driver.find_element(By.ID, "login").send_keys(USUARIO_LOGIN)
        
        # Preenche Senha
        driver.find_element(By.ID, "senha").clear()
        driver.find_element(By.ID, "senha").send_keys(SENHA_LOGIN)
        
        # Clica em Entrar
        # Tenta pelo ID do botão 'botaoEntrar' (pai do span)
        try:
            btn = driver.find_element(By.ID, "botaoEntrar")
            clicar_js(driver, btn, "Botão Entrar")
        except:
            # Fallback para o Span com texto
            btn = driver.find_element(By.XPATH, "//span[contains(text(),'Entrar')]")
            clicar_js(driver, btn, "Botão Entrar (Span)")
            
        esperar_aguarde_sumir(driver)
        log("✅ Login enviado!")
        
    except Exception as e:
        log(f"❌ Erro no login automático: {e}")
        print("   -> Faça o login manualmente.")

# --- FUNÇÕES DE NAVEGAÇÃO ---

def navegar_para_lista_funcionarios(driver):
    """Navega automaticamente até a tela de Consulta de Funcionários.
    Usa JS para clicar no link, sem depender do mouse físico (evita fechar o submenu acidentalmente).
    """
    log("🗂️  [NAVEGAÇÃO] Indo para a lista de Funcionários...")
    try:
        # Passo 1: Aguarda o link de 'Funcionário' existir no DOM (mesmo que oculto no submenu)
        # JS click funciona em elementos ocultos — não precisa de hover nem mover o mouse
        link_funcionario = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//a[contains(@href,'/ntiss/cadastros/funcionario/lista.jsf')]"
            ))
        )
        driver.execute_script("arguments[0].click();", link_funcionario)
        log("   -> Clique em 'Funcionário' realizado via JS.")

        # Passo 2: Aguarda a página carregar completamente
        esperar_aguarde_sumir(driver)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//button[span[text()='Pesquisar']]"))
        )

        # Passo 3: Move o mouse para o centro do conteúdo principal (longe da área do menu)
        # Evita que o submenu 'Cadastros' reabra por hover acidental após o carregamento
        try:
            corpo = driver.find_element(By.TAG_NAME, "body")
            webdriver.ActionChains(driver).move_to_element_with_offset(corpo, 100, 400).perform()
        except:
            pass

        log("✅ Tela de Consulta de Funcionários carregada!")
        return True
    except Exception as e:
        log(f"❌ Erro ao navegar para Funcionários: {e}")
        return False

def navegar_pesquisar_secretaria(driver, login_secretaria):
    log(f"🔍 [NAVEGAÇÃO] Pesquisando: {login_secretaria}")
    esperar_aguarde_sumir(driver)
    try:
        try: campo = driver.find_element(By.ID, "j_idt129")
        except: campo = driver.find_element(By.XPATH, "//label[contains(text(),'Login')]/following::input[1]")
        campo.clear()
        campo.send_keys(login_secretaria)
        time.sleep(0.5)
        
        try: btn = driver.find_element(By.XPATH, "//button[span[text()='Pesquisar']]")
        except: btn = driver.find_element(By.CSS_SELECTOR, "button[title='Pesquisar']")
        clicar_js(driver, btn, "Pesquisar")
        
        esperar_aguarde_sumir(driver)
        time.sleep(0.8)
        
        btn_lapis = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "img[title='Alterar']")))
        clicar_js(driver, btn_lapis, "Editar")
        esperar_aguarde_sumir(driver)
        return True
    except:
        log(f"   [AVISO] '{login_secretaria}' não encontrado/erro.")
        return False

def voltar_para_pesquisa(driver):
    log("🔙 [NAVEGAÇÃO] Voltando...")
    try:
        fechar_janelas_travadas(driver)
        esperar_aguarde_sumir(driver)
        xpath_cancelar = "//button[span[text()='Cancelar']][not(ancestor::div[contains(@class,'ui-dialog')])]"
        try:
            btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath_cancelar)))
            clicar_js(driver, btn, "Cancelar Voltar")
        except:
            try: driver.find_element(By.ID, "j_idt221").click()
            except: pass
        esperar_aguarde_sumir(driver)
    except: pass

# ==============================================================================
# MODO 1: VINCULAR (Mantido V28)
# ==============================================================================

def verificar_status_medico(driver, botao_lapis):
    try:
        linha = botao_lapis.find_element(By.XPATH, "./ancestor::tr")
        if any(img.is_displayed() for img in linha.find_elements(By.CSS_SELECTOR, "img[src*='inativar.png']")): return True 
        if any(img.is_displayed() for img in linha.find_elements(By.CSS_SELECTOR, "img[src*='ativar.png']")): return False 
        if "Sim" in linha.text: return True 
        return False
    except: return True 

def executar_logica_vincular_logins(driver, lista_logins, filtro_medicos=None):
    global solicitar_finalizacao
    if filtro_medicos is not None:
        log(f"   [VINCULAR] Modo filtrado: {len(filtro_medicos)} médico(s) alvo.")
    try:
        botoes = driver.find_elements(By.CSS_SELECTOR, "img[title='Alterar']")
        if not botoes: return
        total_proc = len(botoes) - 1 if len(botoes) > 1 else len(botoes)
        log(f"   [VINCULAR] Processando {total_proc} médicos...")

        for i in range(total_proc):
            if solicitar_finalizacao:
                log("🛑 Processo interrompido pelo usuário")
                return
            log(f"   --- Médico {i+1}/{total_proc} ---")
            checar_pausa()
            try:
                botoes = driver.find_elements(By.CSS_SELECTOR, "img[title='Alterar']")
                if i >= len(botoes): break
                botao = botoes[i]

                # Filtra por nome se filtro_medicos foi fornecido
                if filtro_medicos is not None:
                    try:
                        linha = botao.find_element(By.XPATH, "./ancestor::tr")
                        texto_linha = linha.text.upper()
                        if not any(m.upper() in texto_linha for m in filtro_medicos):
                            log("   -> Pulando (não cadastrado nesta sessão).")
                            continue
                    except: pass

                if not verificar_status_medico(driver, botao):
                    log("   -> Inativo.")
                    continue
                
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
                time.sleep(0.3)
                try: botao.click()
                except: clicar_js(driver, botao, "Lapis")
                esperar_aguarde_sumir(driver)
                
                try:
                    div = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id$=':escolherLogins']")))
                    try: div.find_element(By.CSS_SELECTOR, ".ui-selectcheckboxmenu-trigger").click()
                    except: driver.execute_script("arguments[0].click();", div)
                    time.sleep(1.0)
                    
                    campo = driver.find_element(By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-filter-container input")
                    houve_alt = False
                    for login in lista_logins:
                        campo.clear()
                        campo.send_keys(login)
                        time.sleep(1.0)
                        try:
                            chk = driver.find_element(By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-header .ui-chkbox-box")
                            if "ui-state-active" not in chk.get_attribute("class"):
                                chk.click()
                                houve_alt = True
                                log(f"      + Vinculado: {login}")
                        except: pass
                    
                    try: driver.find_element(By.CSS_SELECTOR, "a.ui-selectcheckboxmenu-close").click()
                    except: pass
                    time.sleep(0.5)

                    if houve_alt: clicar_js(driver, driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Salvar']"), "Salvar")
                    else: clicar_js(driver, driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Cancelar']"), "Cancelar")
                    esperar_aguarde_sumir(driver)
                except: fechar_janelas_travadas(driver)
            except: fechar_janelas_travadas(driver)
    except: pass

# ==============================================================================
# MODO 2: CADASTRAR SERVIÇOS (Mantido V28)
# ==============================================================================

def selecionar_item_otimizado(driver, nome_medico, timeout=3):
    xpath = f"//div[contains(@id, 'prestadorFuncionario_panel')]//li[contains(., '{nome_medico}')]"
    try:
        item = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, xpath)))
        item.click()
        return True
    except: return False

def garantir_checkbox(driver, texto_label):
    listas = [
        f"//tr[.//label[contains(text(), '{texto_label}')]]//div[contains(@class, 'ui-chkbox-box')]",
        f"//label[contains(text(), '{texto_label}')]/..//div[contains(@class, 'ui-chkbox-box')]"
    ]
    for xpath in listas:
        try:
            chk = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, xpath)))
            if "ui-state-active" not in chk.get_attribute("class"):
                clicar_js(driver, chk, texto_label)
                time.sleep(0.2)
        except: continue

def executar_logica_cadastrar_servicos(driver, medicos):
    global solicitar_finalizacao
    log(f"   [CADASTRAR] Iniciando lista de {len(medicos)} médicos...")
    modal_aberto = False
    cadastrados_agora = []
    
    for index, nome_medico in enumerate(medicos):
        if solicitar_finalizacao:
            log("🛑 Processo interrompido pelo usuário")
            if modal_aberto:
                try:
                    btn_cancelar = driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Cancelar']")
                    clicar_js(driver, btn_cancelar, "Cancelar Modal")
                    esperar_aguarde_sumir(driver)
                except: fechar_janelas_travadas(driver)
            return
        log(f"   --- [{index+1}/{len(medicos)}] {nome_medico} ---")
        checar_pausa()
        try:
            if not modal_aberto:
                try:
                    btn_criar = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Criar Serviço']]")))
                    clicar_js(driver, btn_criar, "Criar Serviço")
                    esperar_aguarde_sumir(driver)
                    modal_aberto = True
                except:
                    log("      [ERRO] Não consegui abrir o modal 'Criar Serviço'.")
                    continue

            try:
                driver.find_element(By.CSS_SELECTOR, "div[id$=':prestadorFuncionario'] .ui-selectonemenu-trigger").click()
                campo_filtro = WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[id$=':prestadorFuncionario_panel'] input")))
                campo_filtro.clear()
                campo_filtro.send_keys(nome_medico)
                time.sleep(1.0)
                
                encontrou = selecionar_item_otimizado(driver, nome_medico, timeout=3)
                if not encontrou:
                    log("      [JÁ CADASTRADO] Médico não apareceu na lista.")
                    try: driver.find_element(By.TAG_NAME, 'body').click() 
                    except: pass
                    continue 

                try: WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.ui-datatable")))
                except: pass

                garantir_checkbox(driver, "Visualiza transações")
                garantir_checkbox(driver, "Cancela/Exclui")
                
                try:
                    chk_todas = driver.find_element(By.XPATH, "//div[contains(@class, 'ui-datatable-scrollable-header')]//div[contains(@class, 'ui-chkbox-box')]")
                    if "ui-state-active" not in chk_todas.get_attribute("class"):
                        clicar_js(driver, chk_todas, "Check Todas")
                except: pass
                
                btn_salvar = driver.find_element(By.XPATH, "//span[text()='Salvar']")
                clicar_js(driver, btn_salvar, "Salvar")
                esperar_aguarde_sumir(driver)
                log("      -> Sucesso (Cadastrado).")
                cadastrados_agora.append(nome_medico)
                modal_aberto = False
                
            except Exception as e:
                log(f"      [ERRO INTERNO] {e}")
                fechar_janelas_travadas(driver)
                modal_aberto = False

        except Exception as e:
            log(f"      [ERRO CRÍTICO] {e}")
            fechar_janelas_travadas(driver)
            modal_aberto = False

    if modal_aberto:
        log("   Finalizando lista, fechando modal restante...")
        try:
            btn_cancelar = driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Cancelar']")
            clicar_js(driver, btn_cancelar, "Cancelar Modal Final")
            esperar_aguarde_sumir(driver)
        except: fechar_janelas_travadas(driver)
    return cadastrados_agora

# ==============================================================================
# MAIN
# ==============================================================================

def executar_robo_completo(driver):
    global solicitar_finalizacao, medicos_cadastrados_sessao
    while True:
        print("\n" + "="*60)
        print("--- MENU V29 (AUTO LOGIN) ---")
        print(" 1 - Vincular Logins")
        print(" 2 - Cadastrar Serviços (Otimizado)")
        print(" 0 - Sair")
        print("\n💡 Durante a execução:")
        print("   • Pressione [P] para PAUSAR")
        print("   • Pressione [F] para FINALIZAR")
        print("="*60)
        op = input(">>> Escolha: ").strip()
        if op == '0': break
        if op not in ('1', '2'):
            log("[AVISO] Opção inválida. Digite 1, 2 ou 0.")
            continue

        medicos_cadastrados_sessao = {}  # reseta a cada nova execução
        dados = carregar_json(ARQUIVO_DADOS)
        secretarias = dados.get("secretarias_para_pesquisar", [])
        if not secretarias:
            log("[ERRO] Lista de secretarias vazia!")
            continue

        for idx, sec in enumerate(secretarias):
            if solicitar_finalizacao:
                log("\n🛑 Execução finalizada pelo usuário!")
                solicitar_finalizacao = False
                break
            log(f"\n=== SECRETARIA [{idx+1}/{len(secretarias)}]: {sec} ===")
            if navegar_pesquisar_secretaria(driver, sec):
                if op == '1':
                    executar_logica_vincular_logins(driver, dados.get("logins_para_vincular", []))
                elif op == '2':
                    cadastrados = executar_logica_cadastrar_servicos(driver, dados.get("medicos_para_cadastrar", []))
                    if cadastrados:
                        medicos_cadastrados_sessao[sec] = cadastrados
                voltar_para_pesquisa(driver)
                if solicitar_finalizacao:
                    break

        if not solicitar_finalizacao:
            print("\n✅ CICLO FINALIZADO! Voltando ao menu...")
        else:
            print("\n🛑 Processo encerrado. Voltando ao menu...")
            solicitar_finalizacao = False

        # Após modo 2, oferece vincular logins apenas nos médicos cadastrados
        if op == '2' and medicos_cadastrados_sessao:
            total_cadastrados = sum(len(v) for v in medicos_cadastrados_sessao.values())
            print(f"\n🔗 {total_cadastrados} médico(s) cadastrado(s) em {len(medicos_cadastrados_sessao)} secretaria(s) nesta sessão.")
            print("   Deseja executar Vincular Logins apenas neles? (S/N): ", end="")
            resp = input().strip().lower()
            if resp == 's':
                solicitar_finalizacao = False
                log(f"[VINCULAR PÓS-CADASTRO] {len(medicos_cadastrados_sessao)} secretaria(s) com novos cadastros.")
                secs_com_cadastro = list(medicos_cadastrados_sessao.keys())
                for idx, sec in enumerate(secs_com_cadastro):
                    if solicitar_finalizacao:
                        log("\n🛑 Execução finalizada pelo usuário!")
                        solicitar_finalizacao = False
                        break
                    filtro = medicos_cadastrados_sessao[sec]
                    log(f"\n=== SECRETARIA [{idx+1}/{len(secs_com_cadastro)}]: {sec} ({len(filtro)} médico(s)) ===")
                    if navegar_pesquisar_secretaria(driver, sec):
                        executar_logica_vincular_logins(driver, dados.get("logins_para_vincular", []), filtro_medicos=filtro)
                        voltar_para_pesquisa(driver)
                        if solicitar_finalizacao:
                            break
                print("\n✅ VINCULAR PÓS-CADASTRO FINALIZADO! Voltando ao menu...")

if __name__ == "__main__":
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    driver.get(URL_SISTEMA)
    
    # --- NOVO BLOCO DE LOGIN AUTOMÁTICO ---
    if USUARIO_LOGIN and SENHA_LOGIN:
        realizar_login_automatico(driver)
    else:
        print(">>> [AVISO] Usuário/Senha não configurados no JSON. Faça login manual.")

    navegar_para_lista_funcionarios(driver)

    executar_robo_completo(driver)
    driver.quit()