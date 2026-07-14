import asyncio
import os
import random
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from typing import Iterable

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


URL_CONSULTA_BA = "https://portal.sefaz.ba.gov.br/scripts/cadastro/cadastroBa/consultaBa.asp"


def localizar_chromium_sistema() -> str | None:
    caminhos = [
        os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ]

    for caminho in caminhos:
        if caminho and os.path.exists(caminho):
            return caminho

    return None


def instalar_chromium_playwright(on_status=None) -> None:
    if on_status:
        on_status("Chromium nao encontrado. Instalando navegador do Playwright...")

    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
        timeout=180,
    )


def limpar_cnpj(cnpj: str) -> str:
    return re.sub(r"\D", "", str(cnpj or "")).zfill(14)


def classificar_status(status: str) -> str:
    status = (status or "").upper().strip()
    if status == "ATIVO":
        return "APTO"
    if status == "INAPTO":
        return "INAPTO"
    if status == "SUSPENSO":
        return "SUSPENSO"
    if status == "BAIXADO":
        return "BAIXADO"
    return "VERIFICAR"


def extrair_situacao(texto: str) -> str:
    texto = re.sub(r"\s+", " ", (texto or "").upper())
    padroes = [
        r"SITUA[ÇC][ÃA]O CADASTRAL VIGENTE\s*:?\s*([A-ZÇÃÕÁÉÍÓÚ ]+)",
        r"SITUA..O CADASTRAL VIGENTE\s*:?\s*([A-ZÇÃÕÁÉÍÓÚ ]+)",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto)
        if match:
            valor = match.group(1).strip()
            for status in ("ATIVO", "INAPTO", "SUSPENSO", "BAIXADO"):
                if status in valor:
                    return status
            return valor.split(" ")[0]

    if "NÃO ENCONTRADO" in texto or "NAO ENCONTRADO" in texto:
        return "NAO_ENCONTRADO"

    return "VERIFICAR"


class ConsultaSintegraBA:
    def __init__(
        self,
        delay_min: float = 1.5,
        delay_max: float = 3.0,
        timeout_ms: int = 30000,
        headless: bool = True,
        on_status=None,
    ):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.timeout_ms = timeout_ms
        self.headless = headless
        self.on_status = on_status
        self._playwright = None
        self._browser = None
        self._page = None

    def __enter__(self):
        self._status("Iniciando Playwright")
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            asyncio.set_event_loop(asyncio.new_event_loop())

        self._playwright = sync_playwright().start()
        self._status("Abrindo Chromium")

        launch_kwargs = {
            "headless": self.headless,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"],
        }

        if sys.platform != "win32":
            chromium_sistema = localizar_chromium_sistema()
            if chromium_sistema:
                self._status(f"Usando Chromium do sistema: {chromium_sistema}")
                launch_kwargs["executable_path"] = chromium_sistema

        try:
            self._browser = self._playwright.chromium.launch(**launch_kwargs)
        except Exception:
            if sys.platform == "win32" or "executable_path" in launch_kwargs:
                raise
            instalar_chromium_playwright(self.on_status)
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
        self._page = self._browser.new_page()
        self._page.set_default_timeout(self.timeout_ms)
        self._abrir_pagina("Abrindo portal da Sefaz-BA")
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def _status(self, mensagem: str):
        if self.on_status:
            self.on_status(mensagem)

    def _abrir_pagina(self, mensagem: str = "Carregando portal da Sefaz-BA"):
        self._status(mensagem)
        self._page.goto(URL_CONSULTA_BA, wait_until="domcontentloaded", timeout=self.timeout_ms)
        self._page.wait_for_selector('input[name="CGC"]', timeout=self.timeout_ms)

    def consultar(self, cnpj: str, tentativas: int = 2) -> dict:
        cnpj_limpo = limpar_cnpj(cnpj)
        consultado_em = datetime.now().isoformat(timespec="seconds")

        if len(cnpj_limpo) != 14:
            return self._resposta(cnpj_limpo, "INVALIDO", "VERIFICAR", consultado_em)

        ultimo_erro = None
        for tentativa in range(1, tentativas + 1):
            try:
                self._status(f"Consultando CNPJ {cnpj_limpo} - tentativa {tentativa}")
                texto = self._consultar_uma_vez(cnpj_limpo)
                situacao = extrair_situacao(texto)
                status_final = classificar_status(situacao)

                if situacao != "VERIFICAR" or tentativa == tentativas:
                    return self._resposta(
                        cnpj_limpo,
                        situacao,
                        status_final,
                        consultado_em,
                        tentativa=tentativa,
                    )
            except PlaywrightTimeoutError as erro:
                ultimo_erro = f"TIMEOUT: {erro}"
                self._abrir_pagina("Reabrindo portal apos timeout")
            except Exception as erro:
                ultimo_erro = f"ERRO: {erro}"
                self._abrir_pagina("Reabrindo portal apos erro")

            time.sleep(random.uniform(self.delay_min, self.delay_max))

        return self._resposta(
            cnpj_limpo,
            "VERIFICAR",
            "VERIFICAR",
            consultado_em,
            erro=ultimo_erro,
        )

    def consultar_lote(self, cnpjs: Iterable[str], tentativas: int = 2) -> list[dict]:
        resultados = []
        cache = {}

        for cnpj in cnpjs:
            cnpj_limpo = limpar_cnpj(cnpj)
            if cnpj_limpo not in cache:
                cache[cnpj_limpo] = self.consultar(cnpj_limpo, tentativas=tentativas)
                time.sleep(random.uniform(self.delay_min, self.delay_max))
            resultados.append(cache[cnpj_limpo])

        return resultados

    def _consultar_uma_vez(self, cnpj: str) -> str:
        self._abrir_pagina("Preparando formulario de consulta")
        self._page.fill('input[name="CGC"]', cnpj)
        time.sleep(random.uniform(self.delay_min, self.delay_max))
        self._page.click('input[name="B1"]')
        self._page.wait_for_load_state("domcontentloaded", timeout=self.timeout_ms)
        self._page.wait_for_timeout(1000)
        return self._page.locator("body").inner_text(timeout=self.timeout_ms)

    @staticmethod
    def _resposta(
        cnpj: str,
        situacao: str,
        status_final: str,
        consultado_em: str,
        tentativa: int | None = None,
        erro: str | None = None,
    ) -> dict:
        return {
            "cnpj": cnpj,
            "uf": "BA",
            "situacao_cadastral": situacao,
            "status_final": status_final,
            "fonte": URL_CONSULTA_BA,
            "consultado_em": consultado_em,
            "tentativa": tentativa,
            "erro": erro,
        }


def consultar_sintegra(cnpj: str) -> str:
    with ConsultaSintegraBA() as consulta:
        resultado = consulta.consultar(cnpj)
    return resultado["situacao_cadastral"]
