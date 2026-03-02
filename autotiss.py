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
import threading
import queue
import tkinter as tk
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

# --- THREADING / UI ---
log_queue        = queue.Queue()
_menu_escolha    = None
_menu_event      = threading.Event()
_pause_event     = threading.Event()
_pause_event.set()          # inicia no estado "rodando"
_dialog_result   = None
_dialog_event    = threading.Event()
ui               = None     # instancia da FloatingUI (set no __main__)

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

def _nivel_log(msg):
    """Detecta o nivel visual do log para colorir na UI."""
    m = msg.strip()
    if any(x in m for x in ("✅", "-> Sucesso", "+ Vinculado", "carregada", "Login enviado")): return "ok"
    if any(x in m for x in ("❌", "[ERRO CRÍTICO]", "[ERRO INTERNO]")): return "erro"
    if "🛑" in m: return "erro"
    if any(x in m for x in ("[AVISO]", "[RETRY", "[JÁ CADASTRADO]", "não marcou")): return "aviso"
    if "[ERRO]" in m:       return "erro"
    if "=== SECRETARIA" in m: return "sec"
    if any(x in m for x in ("-> Inativo", "Pulando")): return "dim"
    return "info"

def log(mensagem):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {mensagem}")
    if ui:
        log_queue.put((mensagem, _nivel_log(mensagem)))


# =============================================================================
# FLOATING UI  (Tkinter — sempre no topo, tema escuro, arastável)
# =============================================================================

class FloatingUI:
    C = {
        "bg":       "#1e1e2e",
        "card":     "#2a2a3e",
        "bar":      "#11111b",
        "texto":    "#cdd6f4",
        "dim":      "#585b70",
        "azul":     "#89b4fa",
        "ciano":    "#89dceb",
        "verde":    "#a6e3a1",
        "vermelho": "#f38ba8",
        "amarelo":  "#f9e2af",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("NTISS Auto")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.overrideredirect(True)
        self.root.configure(bg=self.C["bg"])
        w, h = 370, 540
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{sw - w - 20}+{sh - h - 60}")
        self.root.resizable(False, False)
        self._dx = self._dy = 0
        self._build()
        self.root.after(100, self._poll)

    # ------------------------------------------------------------------ build
    def _build(self):
        C = self.C
        # ---- barra de titulo arastável
        bar = tk.Frame(self.root, bg=C["bar"], height=34)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="🏥  AUTOTISS", fg=C["azul"], bg=C["bar"],
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)
        tk.Button(bar, text="✕", fg=C["vermelho"], bg=C["bar"], bd=0,
                  font=("Segoe UI", 11, "bold"), cursor="hand2",
                  activebackground=C["bar"], activeforeground=C["vermelho"],
                  command=self.root.destroy).pack(side="right", padx=8)
        bar.bind("<ButtonPress-1>",  self._drag_start)
        bar.bind("<B1-Motion>",      self._drag_move)
        for w in bar.winfo_children():
            w.bind("<ButtonPress-1>",  self._drag_start)
            w.bind("<B1-Motion>",      self._drag_move)

        # ---- card de status
        card = tk.Frame(self.root, bg=C["card"], padx=10, pady=8)
        card.pack(fill="x", padx=8, pady=(6, 0))
        self.lbl_modo = self._row(card, "MODO")
        self.lbl_sec  = self._row(card, "SECRETARIA")
        self.lbl_med  = self._row(card, "MÉDICO")
        self.lbl_prog = self._row(card, "PROGRESSO")

        # ---- botões (empacotado ANTES do log para reservar espaço no bottom)
        bf = tk.Frame(self.root, bg=C["bg"], height=40)
        bf.pack(side="bottom", fill="x", padx=8, pady=8)
        bf.pack_propagate(False)
        self.btn_v = self._btn(bf, "🔗 Vincular",  "#1e66f5", lambda: self._escolher(1))
        self.btn_c = self._btn(bf, "➕ Cadastrar", "#40a02b", lambda: self._escolher(2))
        self.btn_p = self._btn(bf, "⏸ Pausar",    "#df8e1d", self._toggle_pausa, state="disabled")
        self.btn_s = self._btn(bf, "🛑 Parar",     "#d20f39", self._parar,       state="disabled")

        # ---- area de log (expand=True agora só ocupa o espaço restante)
        lf = tk.Frame(self.root, bg=C["bg"])
        lf.pack(fill="both", expand=True, padx=8, pady=(6, 0))
        tk.Label(lf, text="LOG", fg=C["dim"], bg=C["bg"],
                 font=("Segoe UI", 7, "bold")).pack(anchor="w")
        border = tk.Frame(lf, bg=C["dim"], padx=1, pady=1)
        border.pack(fill="both", expand=True)
        self.txt = tk.Text(border, bg=C["bar"], fg=C["texto"], font=("Consolas", 8),
                           wrap="word", bd=0, state="disabled", spacing1=2,
                           selectbackground=C["card"])
        sb = tk.Scrollbar(border, command=self.txt.yview, bg=C["card"], width=8, troughcolor=C["bg"])
        self.txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt.pack(fill="both", expand=True)
        self.txt.tag_configure("ok",    foreground=C["verde"])
        self.txt.tag_configure("erro",  foreground=C["vermelho"])
        self.txt.tag_configure("aviso", foreground=C["amarelo"])
        self.txt.tag_configure("info",  foreground=C["ciano"])
        self.txt.tag_configure("dim",   foreground=C["dim"])
        self.txt.tag_configure("sec",   foreground=C["azul"], font=("Consolas", 8, "bold"))
        self.txt.tag_configure("hora",  foreground=C["dim"])

    def _row(self, parent, label):
        C = self.C
        f = tk.Frame(parent, bg=C["card"])
        f.pack(fill="x", pady=1)
        tk.Label(f, text=f"{label}:", fg=C["dim"], bg=C["card"],
                 font=("Segoe UI", 7, "bold"), width=12, anchor="w").pack(side="left")
        lbl = tk.Label(f, text="—", fg=C["texto"], bg=C["card"],
                       font=("Segoe UI", 8), anchor="w")
        lbl.pack(side="left", fill="x", expand=True)
        return lbl

    def _btn(self, parent, txt, cor, cmd, state="normal"):
        b = tk.Button(parent, text=txt, bg=cor, fg="white", bd=0, relief="flat",
                      font=("Segoe UI", 8, "bold"), cursor="hand2", command=cmd,
                      padx=6, pady=5, activebackground=cor, activeforeground="white",
                      state=state)
        b.pack(side="left", expand=True, fill="x", padx=2)
        return b

    def _drag_start(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    # ---------------------------------------------------------------- acoes
    def _escolher(self, op):
        global _menu_escolha
        _menu_escolha = str(op)
        self.btn_v.config(state="disabled")
        self.btn_c.config(state="disabled")
        self.btn_p.config(state="normal")
        self.btn_s.config(state="normal")
        modo = "Vincular Logins" if op == 1 else "Cadastrar Serviços"
        self.status(modo=modo)
        _menu_event.set()

    def _toggle_pausa(self):
        if _pause_event.is_set():
            _pause_event.clear()
            self.btn_p.config(text="▶ Retomar", bg="#40a02b")
            log("⏸ Pausado — clique em Retomar para continuar.")
        else:
            _pause_event.set()
            self.btn_p.config(text="⏸ Pausar", bg="#df8e1d")
            log("▶️  Retomando execução...")

    def _parar(self):
        global solicitar_finalizacao
        solicitar_finalizacao = True
        _pause_event.set()   # desbloqueia se estiver pausado
        _menu_event.set()    # desbloqueia se estiver no menu
        log("🛑 Parar solicitado pelo usuário.")

    # --------------------------------------------------------------- publicos
    def habilitar_menu(self):
        """Chama do thread do bot para re-habilitar os botões de menu."""
        def _do():
            self.btn_v.config(state="normal")
            self.btn_c.config(state="normal")
            self.btn_p.config(state="disabled", text="⏸ Pausar", bg="#df8e1d")
            self.btn_s.config(state="disabled")
            self.status(modo="—", secretaria="—", medico="—", progresso="—")
        self.root.after(0, _do)

    def status(self, modo=None, secretaria=None, medico=None, progresso=None):
        """Atualiza os rótulos de status de forma thread-safe."""
        def _do():
            _trunc = lambda s, n: (s[:n-1] + "…") if len(s) > n else s
            if modo is not None:        self.lbl_modo.config(text=_trunc(str(modo), 32))
            if secretaria is not None:  self.lbl_sec.config(text=_trunc(str(secretaria), 32))
            if medico is not None:      self.lbl_med.config(text=_trunc(str(medico), 32))
            if progresso is not None:   self.lbl_prog.config(text=str(progresso))
        self.root.after(0, _do)

    def perguntar(self, titulo, pergunta):
        """Mostra Sim/Não inline no painel flutuante (thread-safe via event)."""
        global _dialog_result
        C = self.C
        _dialog_event.clear()

        def _mostrar():
            # Esconde os botões normais
            for b in (self.btn_v, self.btn_c, self.btn_p, self.btn_s):
                b.pack_forget()

            # Frame temporário de confirmação
            self._confirm_frame = tk.Frame(self.btn_v.master, bg=C["card"], pady=6)
            self._confirm_frame.pack(fill="x")

            tk.Label(
                self._confirm_frame,
                text=pergunta,
                fg=C["amarelo"], bg=C["card"],
                font=("Segoe UI", 8, "bold"),
                wraplength=330, justify="center"
            ).pack(padx=8, pady=(4, 6))

            row = tk.Frame(self._confirm_frame, bg=C["card"])
            row.pack(fill="x", padx=8, pady=(0, 4))

            def _responder(resp):
                global _dialog_result
                _dialog_result = resp
                self._confirm_frame.destroy()
                for b in (self.btn_v, self.btn_c, self.btn_p, self.btn_s):
                    b.pack(side="left", expand=True, fill="x", padx=2)
                _dialog_event.set()

            tk.Button(
                row, text="✅  Sim, vincular agora",
                bg="#40a02b", fg="white", bd=0, relief="flat",
                font=("Segoe UI", 8, "bold"), cursor="hand2",
                padx=6, pady=6, activebackground="#40a02b",
                command=lambda: _responder(True)
            ).pack(side="left", expand=True, fill="x", padx=(0, 3))

            tk.Button(
                row, text="❌  Não",
                bg="#585b70", fg="white", bd=0, relief="flat",
                font=("Segoe UI", 8, "bold"), cursor="hand2",
                padx=6, pady=6, activebackground="#585b70",
                command=lambda: _responder(False)
            ).pack(side="left", expand=True, fill="x", padx=(3, 0))

            # Força o painel a ficar no topo e visível
            self.root.attributes("-topmost", True)
            self.root.lift()

        self.root.after(0, _mostrar)
        _dialog_event.wait()
        return _dialog_result


    # ----------------------------------------------------------- poll de logs
    def _poll(self):
        try:
            while True:
                msg, nivel = log_queue.get_nowait()
                self._write(msg, nivel)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _write(self, msg, nivel):
        self.txt.config(state="normal")
        hora = datetime.now().strftime("%H:%M")
        self.txt.insert("end", f"{hora} ", "hora")
        self.txt.insert("end", f"{msg}\n", nivel)
        lines = int(self.txt.index("end-1c").split(".")[0])
        if lines > 250:
            self.txt.delete("1.0", f"{lines - 250}.0")
        self.txt.see("end")
        self.txt.config(state="disabled")


def checar_pausa():
    """Bloqueia execução enquanto o botão Pausar estiver ativo."""
    if not _pause_event.is_set():
        _pause_event.wait()  # aguarda Retomar ser clicado


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
    if ui: ui.status(secretaria=login_secretaria, medico="—")
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
        if ui: ui.status(progresso=f"0 / {total_proc}")

        for i in range(total_proc):
            if solicitar_finalizacao:
                log("🛑 Processo interrompido pelo usuário")
                return
            log(f"   --- Médico {i+1}/{total_proc} ---")
            if ui: ui.status(progresso=f"{i+1} / {total_proc}")
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
                    houve_alt = False

                    # --- Garante "Visualiza transações de outros logins?" ativado ---
                    xpaths_viz = [
                        "//tr[.//label[contains(text(), 'Visualiza transa') and contains(text(), 'outros')]]//div[contains(@class, 'ui-chkbox-box')]",
                        "//label[contains(text(), 'Visualiza transa') and contains(text(), 'outros')]/..//div[contains(@class, 'ui-chkbox-box')]",
                    ]
                    for xp in xpaths_viz:
                        try:
                            chk_viz = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, xp)))
                            if "ui-state-active" not in (chk_viz.get_attribute("class") or ""):
                                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", chk_viz)
                                time.sleep(0.2)
                                clicar_js(driver, chk_viz, "Visualiza transações outros logins")
                                time.sleep(0.4)
                                chk_viz2 = driver.find_element(By.XPATH, xp)
                                if "ui-state-active" in (chk_viz2.get_attribute("class") or ""):
                                    log("      ✅ 'Visualiza transações de outros logins?' ativado.")
                                    houve_alt = True
                                else:
                                    log("      [AVISO] Não foi possível ativar 'Visualiza transações de outros logins?'.")
                            break
                        except:
                            continue

                    # --- Vincula logins ---
                    div = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id$=':escolherLogins']")))
                    try: div.find_element(By.CSS_SELECTOR, ".ui-selectcheckboxmenu-trigger").click()
                    except: driver.execute_script("arguments[0].click();", div)
                    time.sleep(1.0)

                    campo = driver.find_element(By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-filter-container input")
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
    nome_upper = nome_medico.upper()
    xpath = f"//div[contains(@id, 'prestadorFuncionario_panel')]//li[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{nome_upper}')]"
    try:
        item = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, xpath)))
        item.click()
        return True
    except: return False

def garantir_checkbox(driver, texto_label, tentativas=3):
    listas = [
        f"//tr[.//label[contains(text(), '{texto_label}')]]//div[contains(@class, 'ui-chkbox-box')]",
        f"//label[contains(text(), '{texto_label}')]/..//div[contains(@class, 'ui-chkbox-box')]"
    ]
    for xpath in listas:
        for tentativa in range(tentativas):
            try:
                chk = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                classes = chk.get_attribute("class") or ""
                if "ui-state-active" in classes:
                    return True  # já estava marcado
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chk)
                time.sleep(0.2)
                clicar_js(driver, chk, texto_label)
                time.sleep(0.4)
                # Verifica se foi realmente marcado
                chk_apos = driver.find_element(By.XPATH, xpath)
                if "ui-state-active" in (chk_apos.get_attribute("class") or ""):
                    return True
                log(f"   [RETRY {tentativa+1}/{tentativas}] Checkbox '{texto_label}' não marcou, tentando novamente...")
                time.sleep(0.3)
            except:
                time.sleep(0.3)
                continue
    log(f"   [AVISO] Não foi possível marcar checkbox '{texto_label}' após {tentativas} tentativas.")
    return False

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
        if ui: ui.status(medico=nome_medico, progresso=f"{index+1} / {len(medicos)}")
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
                campo_filtro.send_keys(nome_medico.upper())
                time.sleep(1.0)
                
                encontrou = selecionar_item_otimizado(driver, nome_medico, timeout=3)
                if not encontrou:
                    log("      [JÁ CADASTRADO] Médico não apareceu na lista.")
                    try: driver.find_element(By.TAG_NAME, 'body').click() 
                    except: pass
                    continue 

                try: WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.ui-datatable")))
                except: pass
                time.sleep(0.6)  # aguarda checkboxes renderizarem após o datatable

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
    global solicitar_finalizacao, medicos_cadastrados_sessao, _menu_escolha
    while True:
        solicitar_finalizacao = False
        _pause_event.set()
        if ui:
            ui.habilitar_menu()
            log("⏳ Aguardando escolha no painel flutuante...")
        else:
            print("\n" + "="*60)
            print(" 1 - Vincular Logins")
            print(" 2 - Cadastrar Serviços")
            print(" 0 - Sair")
            print("="*60)
            _menu_escolha = input(">>> Escolha: ").strip()

        _menu_event.clear()
        _menu_event.wait()
        op = _menu_escolha

        if solicitar_finalizacao or op == '0':
            log("🛑 Encerrando o robô.")
            break
        if op not in ('1', '2'):
            log("[AVISO] Opção inválida.")
            continue

        medicos_cadastrados_sessao = {}
        dados = carregar_json(ARQUIVO_DADOS)
        secretarias = dados.get("secretarias_para_pesquisar", [])
        if not secretarias:
            log("[ERRO] Lista de secretarias vazia!")
            continue

        total_secs = len(secretarias)
        log(f"🚀 Iniciando: {total_secs} secretaria(s) | {len(dados.get('medicos_para_cadastrar', []))} médico(s)")

        for idx, sec in enumerate(secretarias):
            if solicitar_finalizacao:
                log("🛑 Execução finalizada pelo usuário!")
                break
            log(f"\n=== SECRETARIA [{idx+1}/{total_secs}]: {sec} ===")
            if ui: ui.status(secretaria=sec)
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
            log("✅ CICLO FINALIZADO!")
        else:
            log("🛑 Processo encerrado.")

        # Após modo 2, oferece vincular logins apenas nos médicos cadastrados
        if op == '2' and medicos_cadastrados_sessao and not solicitar_finalizacao:
            total_cad = sum(len(v) for v in medicos_cadastrados_sessao.values())
            pergunta = (
                f"{total_cad} médico(s) cadastrado(s) em "
                f"{len(medicos_cadastrados_sessao)} secretaria(s).\n"
                "Vincular Logins neles agora?"
            )
            resp = ui.perguntar("NTISS Auto", pergunta) if ui else (
                input(f"\n🔗 {pergunta} (s/n): ").strip().lower() == 's'
            )
            if resp:
                solicitar_finalizacao = False
                log(f"[VINCULAR PÓS-CADASTRO] {len(medicos_cadastrados_sessao)} secretaria(s).")
                secs_com_cadastro = list(medicos_cadastrados_sessao.keys())
                for idx, sec in enumerate(secs_com_cadastro):
                    if solicitar_finalizacao:
                        log("🛑 Execução finalizada pelo usuário!")
                        break
                    filtro = medicos_cadastrados_sessao[sec]
                    log(f"\n=== SECRETARIA [{idx+1}/{len(secs_com_cadastro)}]: {sec} ({len(filtro)} médico(s)) ===")
                    if navegar_pesquisar_secretaria(driver, sec):
                        executar_logica_vincular_logins(driver, dados.get("logins_para_vincular", []), filtro_medicos=filtro)
                        voltar_para_pesquisa(driver)
                        if solicitar_finalizacao:
                            break
                log("✅ VINCULAR PÓS-CADASTRO FINALIZADO!")

if __name__ == "__main__":
    # Inicia o browser
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    driver.get(URL_SISTEMA)

    if USUARIO_LOGIN and SENHA_LOGIN:
        realizar_login_automatico(driver)
    else:
        print(">>> [AVISO] Usuário/Senha não configurados no JSON. Faça login manual.")

    navegar_para_lista_funcionarios(driver)

    # Cria a janela flutuante no thread principal (obrigatório para Tkinter)
    root = tk.Tk()
    ui = FloatingUI(root)
    log("🏥 Painel iniciado! Clique em Vincular ou Cadastrar para começar.")

    # Bot roda em thread separado
    bot_thread = threading.Thread(target=executar_robo_completo, args=(driver,), daemon=True)
    bot_thread.start()

    # Tkinter mainloop no thread principal
    root.mainloop()

    # Após fechar a janela, encerra tudo
    solicitar_finalizacao = True
    _pause_event.set()
    _menu_event.set()
    bot_thread.join(timeout=5)
    driver.quit()