import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Controle - Mercado de Bebidas", layout="wide")

# Arquivos locais para salvar os dados
ARQUIVO_PRODUTOS = "produtos.csv"
ARQUIVO_VENDAS = "vendas.csv"


# Funções para carregar e salvar dados
def carregar_dados(arquivo, colunas_padrao):
    if os.path.exists(arquivo):
        return pd.read_csv(arquivo)
    else:
        return pd.DataFrame(columns=colunas_padrao)


def salvar_dados(df, arquivo):
    df.to_csv(arquivo, index=False)


df_produtos = carregar_dados(ARQUIVO_PRODUTOS, ["Produto", "Preço Custo", "Preço Venda", "Estoque"])
df_vendas = carregar_dados(ARQUIVO_VENDAS, ["Data", "Produto", "Quantidade", "Valor Total"])

# Título principal
st.title("🍻 Controle de Estoque e Vendas - Mercado")

# Menu Lateral
menu = st.sidebar.selectbox("Menu", ["💳 Registrar Venda", "📦 Cadastrar / Estoque", "📊 Relatórios e Faturamento"])

# 1. REGISTRAR VENDA
if menu == "💳 Registrar Venda":
    st.header("Registrar Nova Venda")

    if df_produtos.empty:
        st.warning("Nenhum produto cadastrado ainda. Vá na aba 'Cadastrar / Estoque' primeiro.")
    else:
        lista_produtos = df_produtos["Produto"].tolist()
        produto_escolhido = st.selectbox("Selecione o Produto", lista_produtos)

        info_prod = df_produtos[df_produtos["Produto"] == produto_escolhido].iloc[0]
        preco_venda = info_prod["Preço Venda"]
        estoque_atual = info_prod["Estoque"]

        st.write(f"Preço Unitário: **R$ {preco_venda:.2f}** | Estoque Disponível: **{estoque_atual}**")

        qtd_vendida = st.number_input("Quantidade", min_value=1, value=1, step=1)

        if st.button("Confirmar Venda"):
            if qtd_vendida > estoque_atual:
                st.error("Estoque insuficiente para essa quantidade!")
            else:
                df_produtos.loc[df_produtos["Produto"] == produto_escolhido, "Estoque"] -= qtd_vendida
                salvar_dados(df_produtos, ARQUIVO_PRODUTOS)

                nova_venda = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Produto": produto_escolhido,
                    "Quantidade": qtd_vendida,
                    "Valor Total": qtd_vendida * preco_venda
                }])
                df_vendas = pd.concat([df_vendas, nova_venda], ignore_index=True)
                salvar_dados(df_vendas, ARQUIVO_VENDAS)

                st.success(f"Venda de {qtd_vendida}x {produto_escolhido} registrada com sucesso!")

# 2. CADASTRAR / ESTOQUE
elif menu == "📦 Cadastrar / Estoque":
    st.header("Gerenciamento de Estoque")

    with st.form("form_produto"):
        novo_produto = st.text_input("Nome do Produto (ex: Cerveja 600ml)")
        preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, format="%.2f")
        preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, format="%.2f")
        estoque_inicial = st.number_input("Quantidade em Estoque", min_value=0, step=1)

        cadastrar = st.form_submit_button("Salvar Produto")

        if cadastrar and novo_produto:
            if novo_produto in df_produtos["Produto"].values:
                st.error("Esse produto já está cadastrado!")
            else:
                novo_df = pd.DataFrame([{
                    "Produto": novo_produto,
                    "Preço Custo": preco_custo,
                    "Preço Venda": preco_venda,
                    "Estoque": estoque_inicial
                }])
                df_produtos = pd.concat([df_produtos, novo_df], ignore_index=True)
                salvar_dados(df_produtos, ARQUIVO_PRODUTOS)
                st.success(f"Produto '{novo_produto}' cadastrado com sucesso!")
                st.rerun()

    st.subheader("Estoque Atual")
    st.dataframe(df_produtos, use_container_width=True)

# 3. RELATÓRIOS
elif menu == "📊 Relatórios e Faturamento":
    st.header("Relatórios de Vendas e Faturamento")

    if df_vendas.empty:
        st.info("Nenhuma venda registrada ainda.")
    else:
        faturamento_total = df_vendas["Valor Total"].sum()
        st.metric(label="Faturamento Total Registrado", value=f"R$ {faturamento_total:.2f}")

        st.subheader("Histórico de Vendas")
        st.dataframe(df_vendas, use_container_width=True)

        st.subheader("Produtos Mais Vendidos")
        mais_vendidos = df_vendas.groupby("Produto")["Quantidade"].sum().reset_index()
        st.bar_chart(mais_vendidos.set_index("Produto"))