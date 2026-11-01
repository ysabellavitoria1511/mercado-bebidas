import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

st.set_page_config(page_title="Controle - Mercado de Bebidas", layout="wide")

# Conexão com o Supabase usando os Secrets
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Funções de busca de dados do Supabase
def carregar_produtos():
    response = supabase.table("produtos").select("*").execute()
    df = pd.DataFrame(response.data)
    if df.empty:
        return pd.DataFrame(columns=["id", "nome", "preco_custo", "preco_venda", "estoque"])
    return df

def carregar_vendas():
    response = supabase.table("vendas").select("*").execute()
    df = pd.DataFrame(response.data)
    if df.empty:
        return pd.DataFrame(columns=["id", "data", "produto", "quantidade", "valor_total"])
    return df

df_produtos = carregar_produtos()
df_vendas = carregar_vendas()

st.title("🍻 Controle de Estoque e Vendas - Mercado")

menu = st.sidebar.selectbox("Menu", ["💳 Registrar Venda", "📦 Cadastrar / Estoque", "📊 Relatórios e Faturamento"])

# 1. REGISTRAR VENDA
if menu == "💳 Registrar Venda":
    st.header("Registrar Nova Venda")
    
    if df_produtos.empty:
        st.warning("Nenhum produto cadastrado ainda.")
    else:
        lista_produtos = df_produtos["nome"].tolist()
        produto_escolhido = st.selectbox("Selecione o Produto", lista_produtos)
        
        info_prod = df_produtos[df_produtos["nome"] == produto_escolhido].iloc[0]
        preco_venda = float(info_prod["preco_venda"])
        estoque_atual = int(info_prod["estoque"])
        prod_id = info_prod["id"]
        
        st.write(f"Preço Unitário: **R$ {preco_venda:.2f}** | Estoque Disponível: **{estoque_atual}**")
        
        qtd_vendida = st.number_input("Quantidade", min_value=1, value=1, step=1)
        
        if st.button("Confirmar Venda"):
            if qtd_vendida > estoque_atual:
                st.error("Estoque insuficiente!")
            else:
                novo_estoque = estoque_atual - qtd_vendida
                supabase.table("produtos").update({"estoque": novo_estoque}).eq("id", prod_id).execute()
                
                nova_venda = {
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "produto": produto_escolhido,
                    "quantidade": qtd_vendida,
                    "valor_total": qtd_vendida * preco_venda
                }
                supabase.table("vendas").insert(nova_venda).execute()
                
                st.success(f"Venda de {qtd_vendida}x {produto_escolhido} registrada com sucesso!")
                st.rerun()

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
            if not df_produtos.empty and novo_produto in df_produtos["nome"].values:
                st.error("Esse produto já está cadastrado!")
            else:
                dados_prod = {
                    "nome": novo_produto,
                    "preco_custo": preco_custo,
                    "preco_venda": preco_venda,
                    "estoque": estoque_inicial
                }
                supabase.table("produtos").insert(dados_prod).execute()
                st.success(f"Produto '{novo_produto}' cadastrado com sucesso!")
                st.rerun()

    st.subheader("Estoque Atual e Exclusão")
    if not df_produtos.empty:
        st.dataframe(df_produtos[["nome", "preco_custo", "preco_venda", "estoque"]], use_container_width=True)
        
        st.write("---")
        st.subheader("Apagar Produto Incorreto")
        produto_para_apagar = st.selectbox("Selecione o produto que deseja apagar", df_produtos["nome"].tolist(), key="apagar_prod")
        
        if st.button("🗑️ Apagar Produto Selecionado"):
            prod_id_apagar = df_produtos[df_produtos["nome"] == produto_para_apagar].iloc[0]["id"]
            supabase.table("produtos").delete().eq("id", prod_id_apagar).execute()
            st.success(f"Produto '{produto_para_apagar}' apagado com sucesso!")
            st.rerun()

# 3. RELATÓRIOS
elif menu == "📊 Relatórios e Faturamento":
    st.header("Relatórios de Vendas e Faturamento")
    
    if df_vendas.empty:
        st.info("Nenhuma venda registrada ainda.")
    else:
        faturamento_total = df_vendas["valor_total"].sum()
        st.metric(label="Faturamento Total Registrado", value=f"R$ {faturamento_total:.2f}")
        
        st.subheader("Histórico de Vendas")
        st.dataframe(df_vendas[["data", "produto", "quantidade", "valor_total"]], use_container_width=True)
        
        st.subheader("Produtos Mais Vendidos")
        mais_vendidos = df_vendas.groupby("produto")["quantidade"].sum().reset_index()
        st.bar_chart(mais_vendidos.set_index("produto"))
        
