import time
import msvcrt
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
TEMPO_ESPERA_AGUARDE = 40 

# --- FUNÇÕES ---

def log(mensagem):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {mensagem}")

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
    try:
        WebDriverWait(driver, TEMPO_ESPERA_AGUARDE).until(
            EC.invisibility_of_element_located((By.ID, "aguarde"))
        )
        time.sleep(1.0)
    except:
        pass

def clicar_js(driver, elemento, nome="Elemento"):
    try:
        driver.execute_script("arguments[0].click();", elemento)
        log(f"   -> Clique JS em: {nome}")
    except Exception as e:
        log(f"   [ERRO] Falha ao clicar em {nome}: {e}")

def verificar_status_medico(driver, botao_lapis):
    """Retorna TRUE se Ativo, FALSE se Inativo"""
    try:
        linha = botao_lapis.find_element(By.XPATH, "./ancestor::tr")
        
        # 1. Procura botão vermelho (Inativar) -> Indica que está ATIVO
        icones_inativar = linha.find_elements(By.CSS_SELECTOR, "img[src*='inativar.png']")
        for img in icones_inativar:
            if img.is_displayed():
                return True 

        # 2. Procura botão verde (Ativar) -> Indica que está INATIVO
        icones_ativar = linha.find_elements(By.CSS_SELECTOR, "img[src*='ativar.png']")
        for img in icones_ativar:
            if img.is_displayed():
                return False 

        # 3. Fallback: Texto
        texto = linha.text
        if "Sim" in texto: return True 
        if "Não" in texto: return False 
            
        return True 
    except:
        return True 

def tentar_clicar_lapis(driver, index):
    for tentativa in range(3):
        try:
            botoes = driver.find_elements(By.CSS_SELECTOR, "img[title='Alterar']")
            if index >= len(botoes): return "ERRO" # Proteção caso a lista mude
            botao = botoes[index]
            
            deve_processar = verificar_status_medico(driver, botao)
            if not deve_processar:
                return "INATIVO"

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
            time.sleep(0.5)
            botao.click()
            return "CLICADO"
        except StaleElementReferenceException:
            time.sleep(1)
        except Exception:
            try:
                clicar_js(driver, botao, f"Lápis {index}")
                return "CLICADO"
            except: pass
    raise Exception("Falha ao interagir com o lápis.")

def tentar_abrir_dropdown(driver):
    dropdown_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[id$=':escolherLogins']"))
    )
    for tentativa in range(1, 4):
        try:
            if tentativa == 1:
                dropdown_container.find_element(By.CSS_SELECTOR, ".ui-selectcheckboxmenu-trigger").click()
            elif tentativa == 2:
                dropdown_container.find_element(By.CSS_SELECTOR, ".ui-selectcheckboxmenu-label").click()
            elif tentativa == 3:
                driver.execute_script("arguments[0].click();", dropdown_container)

            time.sleep(1.5)
            try:
                campo_filtro = driver.find_element(By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-filter-container input")
                if campo_filtro.is_displayed():
                    return campo_filtro
            except: pass
        except: pass
    raise Exception("Dropdown não abriu.")

def fechar_janelas_travadas(driver):
    try:
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    except: pass

def processar_medico(driver, index):
    try:
        checar_pausa()
        resultado = tentar_clicar_lapis(driver, index)
        
        if resultado == "INATIVO":
            log("   -> [PULANDO] Inativo.")
            return True 
        if resultado == "ERRO":
            return False

        esperar_aguarde_sumir(driver)
        
        try:
            campo_filtro = tentar_abrir_dropdown(driver)
        except:
            log(f"   [AVISO] Sem campo de login.")
            fechar_janelas_travadas(driver)
            return False
            
        campo_filtro.clear()
        campo_filtro.send_keys("77.hu")
        time.sleep(2.5)

        chk_todos = driver.find_element(By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-header .ui-chkbox-box")
        ja_feito = "ui-state-active" in chk_todos.get_attribute("class")
        
        log(f"Status: {'[JÁ FEITO]' if ja_feito else '[PENDENTE]'}")

        if ja_feito:
            log("Ação: Cancelando...")
            driver.find_element(By.CSS_SELECTOR, "a.ui-selectcheckboxmenu-close").click()
            time.sleep(0.5)
            btn = driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Cancelar']")
            clicar_js(driver, btn, "Cancelar")
        else:
            log("Ação: Salvando...")
            chk_todos.click()
            time.sleep(0.5)
            driver.find_element(By.CSS_SELECTOR, "a.ui-selectcheckboxmenu-close").click()
            time.sleep(0.5)
            btn = driver.find_element(By.XPATH, "//form[@id='formServico']//span[text()='Salvar']")
            clicar_js(driver, btn, "Salvar")

        esperar_aguarde_sumir(driver)
        return True

    except Exception as e:
        log(f"[ERRO INDEX {index}]: {e}")
        fechar_janelas_travadas(driver)
        time.sleep(1)
        esperar_aguarde_sumir(driver)
        return False

# --- INÍCIO ---

log("--- ROBÔ NTISS V7 (MODO CICLO INFINITO) ---")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
driver.get(URL_SISTEMA)

input(">>> FAÇA LOGIN E APERTE ENTER PARA COMEÇAR O PRIMEIRO CICLO...")

ciclo_atual = 1

while True: # LOOP INFINITO ENTRE SECRETÁRIOS
    print("\n" + "="*50)
    log(f"INICIANDO CICLO {ciclo_atual}")
    print("="*50)
    
    lista_erros = []
    
    try:
        log("Lendo lista de médicos...")
        # Recarrega a lista do zero (importante pois mudou a tela)
        botoes_lapis = driver.find_elements(By.CSS_SELECTOR, "img[title='Alterar']")
        total = len(botoes_lapis)
        
        if total == 0:
            log("[AVISO] Nenhum médico encontrado. Verifique se a lista carregou.")
        else:
            # Garante que não tenta acessar índice negativo se tiver só 1 médico (o usuário)
            total_processar = total - 1 if total > 1 else 0
            
            log(f"Total na tela: {total}. Processar: {total_processar}.")

            for i in range(total_processar):
                log(f"\n--- MÉDICO {i+1} de {total_processar} ---")
                checar_pausa()
                sucesso = processar_medico(driver, i)
                if not sucesso:
                    log(f"-> Falha. Adicionado à repescagem (Index {i})")
                    lista_erros.append(i)

            # REPESCAGEM DO CICLO ATUAL
            if len(lista_erros) > 0:
                log(f"\n>>> REPESCAGEM ({len(lista_erros)} itens)...")
                for i_erro in lista_erros:
                    log(f"\n--- RE-TENTANDO INDEX {i_erro} ---")
                    processar_medico(driver, i_erro)

            log(f"\n[SUCESSO] Ciclo {ciclo_atual} finalizado!")
            ciclo_atual += 1

    except Exception as e_geral:
        log(f"ERRO FATAL NESTE CICLO: {e_geral}")

    # --- PONTO DE ESPERA ---
    print("\n" + "#"*60)
    print("   LISTA FINALIZADA!")
    print("   1. Vá no navegador e TROQUE O SECRETÁRIO/LISTA.")
    print("   2. Volte aqui e aperte ENTER para rodar na nova lista.")
    print("   (Ou digite 'sair' e Enter para fechar)")
    print("#"*60 + "\n")
    
    comando = input(">>> AGUARDANDO COMANDO: ")
    if comando.lower().strip() == 'sair':
        break

print("Fechando...")
driver.quit()