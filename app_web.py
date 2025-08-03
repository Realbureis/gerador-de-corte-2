import streamlit as st
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from io import BytesIO


# --- Nossas funções de lógica do projeto antigo continuam aqui ---
# A única mudança é que a função de carregar config agora não encerra o programa,
# ela retorna None para que o Streamlit possa lidar com o erro.

@st.cache_data  # Cache para não recarregar o arquivo toda hora
def carregar_configuracoes(caminho_arquivo: str) -> dict:
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar o config.json: {e}")
        return None


def gerar_pdf_bytes(config: dict, grade: dict) -> bytes:
    """
    MODIFICADO: Gera o PDF e o retorna como um objeto de bytes na memória,
    em vez de salvar em um arquivo diretamente.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Lógica de desenho (exatamente a mesma de antes)
    pecas_a_desenhar = []
    for tamanho, quantidade_grade in sorted(grade.items()):
        if quantidade_grade == 0: continue
        for nome_peca, dados_peca in config['pecas'].items():
            # ... (toda a lógica de cálculo de medidas permanece idêntica) ...
            quantidade_total = quantidade_grade * dados_peca['quantidade_por_peca']
            altura_cm = dados_peca['altura_base']
            comprimento_base = dados_peca['comprimento_base']
            ajuste_gradacao = config['tabela_gradacao'][nome_peca][tamanho]
            comprimento_final = comprimento_base + ajuste_gradacao
            if dados_peca['regra_risco'] == "dividir_comprimento_por_2":
                largura_cm = comprimento_final / 2
            else:
                largura_cm = comprimento_final
            for i in range(quantidade_total):
                legenda = f"{nome_peca} ({tamanho}) - {i + 1}/{quantidade_total}"
                pecas_a_desenhar.append({'largura': largura_cm * cm, 'altura': altura_cm * cm, 'legenda': legenda})

    if not pecas_a_desenhar:
        return None

    largura_pagina, altura_pagina = A4
    margem = 1 * cm
    espacamento = 0.5 * cm
    x = margem
    y = altura_pagina - margem
    altura_max_linha = 0
    for peca in pecas_a_desenhar:
        if x + peca['largura'] > largura_pagina - margem:
            x = margem
            y -= (altura_max_linha + espacamento)
            altura_max_linha = 0
        if y - peca['altura'] < margem:
            c.showPage()
            x = margem
            y = altura_pagina - margem
            altura_max_linha = 0
        c.rect(x, y - peca['altura'], peca['largura'], peca['altura'])
        c.drawString(x + (0.2 * cm), y - (0.7 * cm), peca['legenda'])
        c.drawString(x + (0.2 * cm), y - (1.2 * cm), f"{peca['largura'] / cm:.1f} x {peca['altura'] / cm:.1f} cm")
        x += peca['largura'] + espacamento
        if peca['altura'] > altura_max_linha:
            altura_max_linha = peca['altura']

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# --- Interface da Aplicação Web com Streamlit ---

st.set_page_config(page_title="Gerador de Corte", layout="centered")
st.title("👕 Gerador de Lista de Corte")

config = carregar_configuracoes('config.json')

if config:
    tamanhos = sorted(list(next(iter(config['tabela_gradacao'].values())).keys()))

    # Usar a barra lateral para os inputs
    st.sidebar.header("1. Insira a Grade")
    grade_producao = {}
    for tam in tamanhos:
        # st.number_input cria um campo numérico
        grade_producao[tam] = st.sidebar.number_input(f'Quantidade {tam}', min_value=0, value=0, step=1)

    st.sidebar.header("2. Dê um nome ao Arquivo")
    nome_arquivo = st.sidebar.text_input("Nome do arquivo PDF", value="lista_de_corte")

    # Botão para gerar o PDF
    if st.sidebar.button("Gerar PDF para Download", type="primary"):
        # Verifica se pelo menos um item da grade foi preenchido
        if sum(grade_producao.values()) > 0:
            st.info("Gerando seu PDF... Por favor, aguarde.")

            pdf_bytes = gerar_pdf_bytes(config, grade_producao)

            if pdf_bytes:
                st.success("PDF gerado com sucesso!")

                # st.download_button cria um botão para o usuário baixar o arquivo
                st.download_button(
                    label="Clique aqui para baixar o PDF",
                    data=pdf_bytes,
                    file_name=f"{nome_arquivo}.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("A grade inserida não resultou em peças para o PDF.")
        else:
            st.error("Por favor, insira a quantidade para pelo menos um tamanho.")
else:
    st.header("Arquivo de configuração não encontrado. A aplicação não pode iniciar.")