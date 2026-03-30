import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="Consolidador NFP - Precisão Total", layout="wide")

def limpar_id(txt):
    """Remove pontuação e zeros à esquerda para garantir o match"""
    if pd.isna(txt): return ""
    s = re.sub(r'\D', '', str(txt))
    return s.lstrip('0') # Remove zeros à esquerda

def para_numero(v):
    """Converte valores brasileiros (13,34) para float com segurança"""
    if pd.isna(v) or v == "": return 0.0
    try:
        s = str(v).replace("R$", "").strip()
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        return float(s)
    except:
        return 0.0

st.title("📊 Consolidador NFP (Ajuste de Precisão)")
st.info("Esta versão remove zeros à esquerda e padroniza textos para garantir que nenhuma nota seja ignorada.")

col1, col2 = st.columns(2)

with col1:
    file_cpf = st.file_uploader("1. Planilha de CPFs", type=["xlsx", "csv"])
with col2:
    file_cnpj = st.file_uploader("2. Planilha de CRÉDITOS", type=["xlsx", "csv"])

if file_cpf and file_cnpj:
    try:
        # Lendo arquivos
        df_cpf = pd.read_excel(file_cpf) if file_cpf.name.endswith('xlsx') else pd.read_csv(file_cpf)
        df_cnpj = pd.read_excel(file_cnpj) if file_cnpj.name.endswith('xlsx') else pd.read_csv(file_cnpj)

        with st.spinner('Cruzando dados...'):
            # --- PADRONIZAÇÃO AGRESSIVA ---
            # Limpamos CNPJ e NF removendo zeros à esquerda e caracteres
            df_cpf['key'] = df_cpf['CNPJ Estabelecimento'].apply(limpar_id) + "_" + df_cpf['NF'].apply(limpar_id)
            df_cpf['cpf_clean'] = df_cpf['CPF'].astype(str).str.strip()
            
            df_cnpj['key'] = df_cnpj['CNPJ'].apply(limpar_id) + "_" + df_cnpj['NF'].apply(limpar_id)
            df_cnpj['valor_clean'] = df_cnpj['Créditos'].apply(para_numero)

            # --- CRUZAMENTO ---
            # Usamos o merge baseado na chave única criada
            df_merged = pd.merge(
                df_cpf, 
                df_cnpj[['key', 'valor_clean']], 
                on='key', 
                how='left'
            )

            # Agrupamento
            resumo = df_merged.groupby('cpf_clean').agg({
                'key': 'count',
                'valor_clean': 'sum'
            }).reset_index()

            resumo.columns = ['CPF DOADOR', 'QTD NOTAS', 'TOTAL CRÉDITOS']
            resumo = resumo.sort_values(by='CPF DOADOR')

            # --- EXIBIÇÃO ---
            total_geral = resumo['TOTAL CRÉDITOS'].sum()
            st.success(f"✅ Processamento Concluído!")
            
            st.metric("Total Geral Calculado", f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            if total_geral < 29000:
                st.warning("⚠️ O valor ainda está abaixo do esperado pelo Java. Verifique se os nomes das colunas 'CNPJ' e 'NF' estão idênticos nos arquivos brutos.")

            st.dataframe(resumo, use_container_width=True)

            # Download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                resumo.to_excel(writer, index=False)
            
            st.download_button("📥 Baixar Resultado", output.getvalue(), "Resultado_NFP_Final.xlsx")

    except Exception as e:
        st.error(f"Erro inesperado: {e}")
