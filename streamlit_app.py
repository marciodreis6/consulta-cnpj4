import base64
import io
from pathlib import Path
import time

import pandas as pd
import streamlit as st

from consulta_sintegra import ConsultaSintegraBA, limpar_cnpj


APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "assets" / "m-dias-branco-logo.png"
HERO_BG_PATH = APP_DIR / "assets" / "fundo-sem-logo.png"


def imagem_base64(caminho: Path) -> str:
    if not caminho.exists():
        return ""
    return base64.b64encode(caminho.read_bytes()).decode("utf-8")


LOGO_BASE64 = imagem_base64(LOGO_PATH)
HERO_BG_BASE64 = imagem_base64(HERO_BG_PATH)

st.set_page_config(page_title="Consulta CNPJ BA", layout="wide")

st.markdown(
    f"""
    <style>
    :root {{
        --mdb-bg: #07111d;
        --mdb-panel: #0b2f4f;
        --mdb-panel-strong: #073c68;
        --mdb-card: #0b2d4a;
        --mdb-card-soft: #0d2236;
        --mdb-border: #23577e;
        --mdb-text: #f7fbff;
        --mdb-muted: #b7c8da;
        --mdb-accent: #f3b51f;
        --mdb-blue: #0070bd;
        --mdb-red: #ff4b4b;
    }}

    .stApp {{
        background:
            linear-gradient(rgba(7, 17, 29, .48), rgba(7, 17, 29, .66)),
            url("data:image/png;base64,{HERO_BG_BASE64}"),
            repeating-linear-gradient(90deg, rgba(255,255,255,.035) 0, rgba(255,255,255,.035) 1px, transparent 1px, transparent 32px);
        background-size: cover, cover, auto;
        background-position: center, center bottom, top left;
        background-attachment: fixed, fixed, scroll;
        color: var(--mdb-text);
    }}

    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #064271 0%, #06365d 100%);
        border-right: 1px solid rgba(255,255,255,.08);
    }}

    section[data-testid="stSidebar"] * {{
        color: #ffffff;
    }}

    section[data-testid="stSidebar"] [data-testid="stInfo"] {{
        background: rgba(13, 101, 170, .55);
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 8px;
    }}

    .block-container {{
        max-width: 1280px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }}

    .mdb-hero {{
        min-height: 150px;
        background: linear-gradient(135deg, #0b2f4f 0%, #092844 62%, #082238 100%);
        border: 1px solid var(--mdb-border);
        border-radius: 8px;
        padding: 26px 30px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 28px;
        box-shadow: 0 22px 48px rgba(0, 0, 0, .25);
        margin-bottom: 26px;
    }}

    .mdb-kicker {{
        color: var(--mdb-accent);
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: .02em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }}

    .mdb-title {{
        color: #ffffff;
        font-size: clamp(2rem, 3vw, 3rem);
        font-weight: 850;
        line-height: 1.08;
        margin: 0;
    }}

    .mdb-subtitle {{
        color: #d6e4f2;
        font-size: 1.03rem;
        margin-top: 12px;
        max-width: 760px;
    }}

    .mdb-logo {{
        width: min(260px, 24vw);
        min-width: 190px;
        filter: brightness(0) invert(1);
        opacity: .96;
    }}

    .mdb-section-title {{
        color: #ffffff;
        font-size: 1.18rem;
        font-weight: 800;
        margin: 24px 0 8px;
    }}

    [data-testid="stMetric"] {{
        background: linear-gradient(180deg, rgba(11,47,79,.98), rgba(9,39,66,.98));
        border: 1px solid var(--mdb-border);
        border-left: 5px solid var(--mdb-accent);
        border-radius: 8px;
        padding: 18px 20px;
        min-height: 110px;
    }}

    [data-testid="stMetricLabel"] {{
        color: var(--mdb-accent);
        font-size: .76rem;
        font-weight: 850;
        text-transform: uppercase;
    }}

    [data-testid="stMetricValue"] {{
        color: #ffffff;
        font-size: 1.85rem;
        font-weight: 850;
    }}

    [data-testid="stFileUploader"] {{
        max-width: 560px;
    }}

    [data-testid="stFileUploader"] section {{
        background: rgba(255,255,255,.08);
        border: 1px dashed rgba(255,255,255,.18);
        border-radius: 8px;
        min-height: 62px;
        padding: 10px 12px;
    }}

    [data-testid="stFileUploader"] section > div {{
        padding: 0;
    }}

    .stAlert {{
        max-width: 560px;
        border-radius: 8px;
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid rgba(74, 111, 143, .75);
        border-radius: 8px;
        overflow: hidden;
    }}

    .mdb-preview-table {{
        border: 1px solid rgba(74, 111, 143, .75);
        border-radius: 8px;
        overflow: hidden;
        background: rgba(5, 11, 20, .76);
        box-shadow: 0 16px 36px rgba(0,0,0,.22);
    }}

    .mdb-preview-table table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        font-size: .9rem;
    }}

    .mdb-preview-table thead th {{
        background: rgba(28, 32, 42, .98);
        color: #b9c7d6;
        text-align: center;
        padding: 11px 16px;
        border-bottom: 1px solid rgba(255,255,255,.09);
        text-transform: uppercase;
        font-size: .76rem;
        letter-spacing: .02em;
    }}

    .mdb-preview-table tbody td {{
        color: #f7fbff;
        text-align: center;
        padding: 10px 16px;
        border-bottom: 1px solid rgba(255,255,255,.075);
        font-weight: 700;
    }}

    .mdb-preview-table tbody tr:nth-child(even) td {{
        background: rgba(255,255,255,.018);
    }}

    .mdb-preview-table tbody tr:last-child td {{
        border-bottom: 0;
    }}

    .stButton > button, .stDownloadButton > button {{
        background: var(--mdb-blue);
        color: white;
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 7px;
        font-weight: 800;
        padding: .72rem 1.05rem;
    }}

    .stButton > button[kind="primary"] {{
        background: var(--mdb-red);
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        border-bottom: 1px solid rgba(255,255,255,.12);
    }}

    .stTabs [data-baseweb="tab"] {{
        background: rgba(11, 47, 79, .75);
        border: 1px solid rgba(35, 87, 126, .8);
        border-bottom: 0;
        border-radius: 7px 7px 0 0;
        padding: 10px 16px;
        color: #dbe9f5;
        font-weight: 750;
    }}

    .stTabs [aria-selected="true"] {{
        color: #ffffff;
        background: #0d4778;
    }}

    hr {{
        border-color: rgba(255,255,255,.12);
    }}

    @media (max-width: 900px) {{
        .mdb-hero {{
            align-items: flex-start;
            flex-direction: column;
        }}
        .mdb-logo {{
            width: 210px;
            min-width: 0;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

logo_html = (
    f'<img class="mdb-logo" src="data:image/png;base64,{LOGO_BASE64}" alt="M. Dias Branco">'
    if LOGO_BASE64
    else ""
)

st.markdown(
    f"""
    <div class="mdb-hero">
        <div>
            <div class="mdb-kicker">M. Dias Branco</div>
            <h1 class="mdb-title">Consulta de CNPJs na Sefaz-BA</h1>
            <div class="mdb-subtitle">Consulta em lote da situação cadastral estadual para apoio à triagem fiscal.</div>
        </div>
        {logo_html}
    </div>
    """,
    unsafe_allow_html=True,
)

upload_col, _ = st.columns([0.42, 0.58])
with upload_col:
    uploaded_file = st.file_uploader("Envie sua planilha Excel", type=["xlsx"])
    if not uploaded_file:
        st.info("Envie uma planilha .xlsx com a coluna CNPJ. A coluna REMESSA e opcional.")

with st.sidebar:
    st.header("Velocidade")
    modo = st.radio("Modo de consulta", ["Seguro", "Rapido"], horizontal=True)
    tentativas = st.number_input("Tentativas por CNPJ", min_value=1, max_value=5, value=2)

    if modo == "Seguro":
        delay_min = st.slider("Delay minimo", 0.5, 10.0, 1.5, 0.5)
        delay_max = st.slider("Delay maximo", 0.5, 15.0, 3.0, 0.5)
    else:
        delay_min = st.slider("Delay minimo", 0.5, 10.0, 0.8, 0.5)
        delay_max = st.slider("Delay maximo", 0.5, 15.0, 1.5, 0.5)

    st.info("Use o modo rapido em testes menores. Para volume maior, o modo seguro costuma falhar menos.")
    st.divider()
    st.caption("Fiscal - Cadastro BA")
    st.caption("Horario: America/Sao_Paulo")


def preparar_planilha(arquivo) -> pd.DataFrame:
    df = pd.read_excel(arquivo)
    colunas = {col.upper().strip(): col for col in df.columns}

    if "CNPJ" not in colunas:
        raise ValueError("A planilha precisa ter uma coluna chamada CNPJ.")

    df = df.copy()
    df["CNPJ"] = df[colunas["CNPJ"]].apply(limpar_cnpj)

    if "REMESSA" not in colunas:
        df["REMESSA"] = ""
    else:
        df["REMESSA"] = df[colunas["REMESSA"]]

    return df


def gerar_excel(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultado")
    return buffer.getvalue()


def tabela_previa_html(df: pd.DataFrame) -> str:
    previa = df[["CNPJ", "REMESSA"]].head(12).copy()
    previa.index = range(1, len(previa) + 1)
    html = previa.to_html(escape=False)
    return f'<div class="mdb-preview-table">{html}</div>'


if uploaded_file:
    try:
        df = preparar_planilha(uploaded_file)
    except Exception as erro:
        st.error(str(erro))
        st.stop()

    cnpjs_unicos = list(dict.fromkeys(df["CNPJ"].tolist()))
    remessas_unicas = df["REMESSA"].nunique() if "REMESSA" in df.columns else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Linhas", len(df))
    col2.metric("CNPJs unicos", len(cnpjs_unicos))
    col3.metric("Remessas unicas", remessas_unicas)

    st.markdown('<div class="mdb-section-title">Previa da planilha</div>', unsafe_allow_html=True)
    st.markdown(tabela_previa_html(df), unsafe_allow_html=True)

    if st.button("Iniciar consulta", type="primary"):
        resultados_por_cnpj = {}
        inicio = time.time()
        barra = st.progress(0)
        status = st.empty()
        detalhe = st.empty()

        def mostrar_status(mensagem: str):
            detalhe.info(mensagem)

        status.text("Iniciando navegador de consulta...")

        try:
            with ConsultaSintegraBA(
                delay_min=delay_min,
                delay_max=delay_max,
                timeout_ms=20000,
                on_status=mostrar_status,
            ) as consulta:
                for indice, cnpj in enumerate(cnpjs_unicos, start=1):
                    status.text(f"Consultando {indice}/{len(cnpjs_unicos)}: {cnpj}")
                    resultado = consulta.consultar(cnpj, tentativas=tentativas)
                    resultados_por_cnpj[cnpj] = resultado

                    progresso = indice / len(cnpjs_unicos)
                    tempo_decorrido = time.time() - inicio
                    tempo_medio = tempo_decorrido / indice
                    tempo_restante = int((len(cnpjs_unicos) - indice) * tempo_medio)

                    barra.progress(progresso)
                    status.text(
                        f"{indice}/{len(cnpjs_unicos)} consultados "
                        f"({int(progresso * 100)}%) | ~{tempo_restante}s restantes"
                    )
        except Exception as erro:
            detalhe.empty()
            st.error(
                "Nao foi possivel abrir o navegador Chromium no ambiente do deploy. "
                "Confira se `packages.txt` e `runtime.txt` foram enviados junto com o app."
            )
            st.code(str(erro), language="text")
            st.stop()

        detalhe.empty()

        linhas = []
        for _, row in df.iterrows():
            resultado = resultados_por_cnpj[row["CNPJ"]]
            linhas.append(
                {
                    "CNPJ": row["CNPJ"],
                    "REMESSA": row["REMESSA"],
                    "SITUACAO_CADASTRAL": resultado["situacao_cadastral"],
                    "STATUS_FINAL": resultado["status_final"],
                    "CONSULTADO_EM": resultado["consultado_em"],
                    "TENTATIVA": resultado["tentativa"],
                    "ERRO": resultado["erro"],
                }
            )

        df_resultado = pd.DataFrame(linhas)

        st.success("Consulta finalizada.")

        aptos = df_resultado[df_resultado["STATUS_FINAL"] == "APTO"]
        inaptos = df_resultado[df_resultado["STATUS_FINAL"] == "INAPTO"]
        suspensos = df_resultado[df_resultado["STATUS_FINAL"] == "SUSPENSO"]
        baixados = df_resultado[df_resultado["STATUS_FINAL"] == "BAIXADO"]
        verificar = df_resultado[df_resultado["STATUS_FINAL"] == "VERIFICAR"]

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Aptos", len(aptos))
        col2.metric("Inaptos", len(inaptos))
        col3.metric("Suspensos", len(suspensos))
        col4.metric("Baixados", len(baixados))
        col5.metric("Verificar", len(verificar))

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            ["Inaptos", "Suspensos", "Baixados", "Aptos", "Verificar", "Todos"]
        )
        tab1.dataframe(inaptos, use_container_width=True)
        tab2.dataframe(suspensos, use_container_width=True)
        tab3.dataframe(baixados, use_container_width=True)
        tab4.dataframe(aptos, use_container_width=True)
        tab5.dataframe(verificar, use_container_width=True)
        tab6.dataframe(df_resultado, use_container_width=True)

        st.download_button(
            "Baixar XLSX",
            data=gerar_excel(df_resultado),
            file_name="resultado_consulta_cnpj_ba.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
