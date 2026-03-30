import streamlit as st
import pandas as pd
import re
import io

# Configuração da Página
st.set_page_config(
    page_title="ACAAD - Consolidador NFP",
    page_icon="📊",
    layout="wide"
)

# --- ESTILIZAÇÃO (CSS) ---
# Aqui definimos as cores da ACAAD (Azul e Amarelo)
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stButton>button {
        background-color: #002b5c;
        color: white;
        border-radius: 8px;
        width: 100%;
        font-weight: bold;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #ffcc00;
    }
    h1 { color: #002b5c; font-family: 'Arial'; }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO COM LOGO ---
col_logo, col_titulo = st.columns([1, 4])

with col_logo:
    # IMPORTANTE: Substitua o link abaixo pelo link da imagem no seu GitHub se preferir
    # Por enquanto, estou usando o link da imagem que você me enviou
    logo_url = "https://raw.githubusercontent.com/flavioacaad/NFP/main/logo_acaad.png" 
    st.image("https://acaad.org.br/wp-content/uploads/2021/04/logo-acaad.png", width=150)

with col_titulo:
    st.title("CONSOLIDADOR DE CRÉDITOS NFP - ACAAD")
    st.info("Sistema de Precisão Total para Consolidação de Notas Fiscais Paulistas.")

# --- FUNÇÕES DE LIMPEZA ---
def limpar_id(txt):
    if pd.isna(txt): return ""
    s = re.sub(r'\D', '', str(txt))
    return s.lstrip('0')

def para_numero(v):
    if pd.isna(v) or v == "": return 0.0
    try:
        s = str(v).replace("R$", "").strip()
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        return float(s)
    except:
        return 0.0

# --- INTERFACE DE UPLOAD ---
st.markdown("---")
c1, c2 = st.columns(2)

with c1:
    st.subheader("1. Planilha de CPFs")
    file_cpf = st.file_uploader("Arraste o arquivo de Pedidos/CPFs", type=["xlsx", "csv"])

with c2:
    st.subheader("2. Planilha de CRÉDITOS")
    file_cnpj = st.file_uploader("Arraste o arquivo de Créditos/Consultas", type=["xlsx", "csv"])

# --- PROCESSAMENTO ---
if file_cpf and file_cnpj:
    try:
        df_cpf = pd.read_excel(file_cpf) if file_cpf.name.endswith('xlsx') else pd.read_csv(file_cpf)
        df_cnpj = pd.read_excel(file_cnpj) if file_cnpj.name.endswith('xlsx') else pd.read_csv(file_cnpj)

        with st.spinner('Cruzando dados com precisão...'):
            # Padronização
            df_cpf['key'] = df_cpf['CNPJ Estabelecimento'].apply(limpar_id) + "_" + df_cpf['NF'].apply(limpar_id)
            df_cpf['cpf_clean'] = df_cpf['CPF'].astype(str).str.strip()
            
            df_cnpj['key'] = df_cnpj['CNPJ'].apply(limpar_id) + "_" + df_cnpj['NF'].apply(limpar_id)
            df_cnpj['valor_clean'] = df_cnpj['Créditos'].apply(para_numero)

            # Cruzamento
            df_merged = pd.merge(df_cpf, df_cnpj[['key', 'valor_clean']], on='key', how='left')

            # Resumo Final
            resumo = df_merged.groupby('cpf_clean').agg({
                'key': 'count',
                'valor_clean': 'sum'
            }).reset_index()

            resumo.columns = ['CPF DOADOR', 'QTD NOTAS', 'TOTAL CRÉDITOS (R$)']
            resumo = resumo.sort_values(by='CPF DOADOR')

            # --- RESULTADOS ---
            total_geral = resumo['TOTAL CRÉDITOS (R$)'].sum()
            
            st.markdown("---")
            st.metric("Total Geral Calculado", f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.dataframe(resumo, use_container_width=True)

            # Download personalizado
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                resumo.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 BAIXAR RESULTADO CONSOLIDADO (.xlsx)",
                data=output.getvalue(),
                file_name="Relatorio_ACAAD_NFP.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Erro ao processar: Verifique se as colunas 'CNPJ', 'NF' e 'CPF' existem nos arquivos.")

# Rodapé
st.markdown("---")
st.caption("© 2026 ACAAD - Soluções de Dados com Precisão | Link Oficial: nfp-acaad.streamlit.app")
