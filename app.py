import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

st.set_page_config(page_title="Controle - Mercado de Bebidas", layout="wide", page_icon="🍻")

# Conexão com o Supabase usando os Secrets
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Funções de busca de dados
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

# Título Principal Estilizado
st.title("🍻 Mercado de Bebidas")
st.markdown("Gerenciamento rápido e seguro na nuvem.")
st.write("---")

# Abas Modernas (Substitui o menu lateral e fica ótimo no telemóvel)
aba1, aba2, aba3 = st.tabs(["💳 Vender", "📦 Estoque", "📊 Relatórios"])

# 1. ABA DE VENDAS
with aba1:
    st.header("Registrar Nova Venda")
    
    if df_produtos.empty:
        st.warning("⚠️ Nenhum produto cadastrado ainda. Vá na aba 'Estoque' para cadastrar.")
    else:
        lista_produtos = df_produtos["nome"].tolist()
        produto_escolhido = st.selectbox("Selecione o Produto", lista_produtos)
        
        info_prod = df_produtos[df_produtos["nome"] == produto_escolhido].iloc[0]
        preco_venda = float(info_prod["preco_venda"])
        estoque_atual = int(info_prod["estoque"])
        prod_id = info_prod["id"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Preço Unitário", f"R$ {preco_venda:.2f}")
        with col2:
            st.metric("Estoque Disponível", f"{estoque_atual} un.")
        
        qtd_vendida = st.number_input("Quantidade a vender", min_value=1, value=1, step=1)
        
        if st.button("Confirmar Venda", type="primary", use_container_width=True):
            if qtd_vendida > estoque_atual:
                st.error("❌ Estoque insuficiente!")
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
                
                st.success(f"✅ Venda de {qtd_vendida}x {produto_escolhido} registada com sucesso!")
                st.rerun()

# 2. ABA DE ESTOQUE E CADASTRO
with aba2:
    st.header("Gerenciamento de Estoque")
    
    with st.expander("➕ Cadastrar Novo Produto", expanded=False):
        with st.form("form_produto"):
            novo_produto = st.text_input("Nome do Produto (ex: Cerveja 600ml)")
            preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, format="%.2f")
            preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, format="%.2f")
            estoque_inicial = st.number_input("Quantidade em Estoque", min_value=0, step=1)
            
            cadastrar = st.form_submit_button("Salvar Produto no Sistema", use_container_width=True)
            
            if cadastrar and novo_produto:
                if not df_produtos.empty and novo_produto in df_produtos["nome"].values:
                    st.error("❌ Esse produto já está cadastrado!")
                else:
                    dados_prod = {
                        "nome": novo_produto,
                        "preco_custo": preco_custo,
                        "preco_venda": preco_venda,
                        "estoque": estoque_inicial
                    }
                    supabase.table("produtos").insert(dados_prod).execute()
                    st.success(f"✅ Produto '{novo_produto}' cadastrado com sucesso!")
                    st.rerun()

    st.subheader("📋 Produtos em Estoque")
    if not df_produtos.empty:
        st.dataframe(df_produtos[["nome", "preco_custo", "preco_venda", "estoque"]], use_container_width=True)
        
        st.markdown("### 🗑️ Apagar Produto")
        produto_para_apagar = st.selectbox("Selecione o produto para remover", df_produtos["nome"].tolist(), key="apagar_prod")
        if st.button("Apagar Produto Selecionado", type="secondary"):
            prod_id_apagar = df_produtos[df_produtos["nome"] == produto_para_apagar].iloc[0]["id"]
            supabase.table("produtos").delete().eq("id", prod_id_apagar).execute()
            st.success(f"🗑️ Produto '{produto_para_apagar}' apagado!")
            st.rerun()

# 3. ABA DE RELATÓRIOS
with aba3:
    st.header("📊 Faturamento e Vendas")
    
    if df_vendas.empty:
        st.info("ℹ️ Nenhuma venda registada ainda.")
    else:
        faturamento_total = df_vendas["valor_total"].sum()
        st.metric(label="💰 Faturamento Total", value=f"R$ {faturamento_total:.2f}")
        
        st.subheader("Histórico de Vendas")
        st.dataframe(df_vendas[["id", "data", "produto", "quantidade", "valor_total"]], use_container_width=True)
        
        with st.expander("🗑️ Corrigir / Apagar Venda"):
            df_vendas["descricao_venda"] = df_vendas.apply(
                lambda row: f"ID {row['id']} | {row['data']} - {row['produto']} ({row['quantidade']}x - R$ {row['valor_total']})", 
                axis=1
            )
            venda_escolhida = st.selectbox("Selecione a venda incorreta", df_vendas["descricao_venda"].tolist(), key="apagar_venda")
            
            if st.button("Apagar Venda Selecionada"):
                venda_id_apagar = df_vendas[df_vendas["descricao_venda"] == venda_escolhida].iloc[0]["id"]
                supabase.table("vendas").delete().eq("id", venda_id_apagar).execute()
                st.success("✅ Venda apagada com sucesso!")
                st.rerun()
        
        st.subheader("📈 Produtos Mais Vendidos")
        mais_vendidos = df_vendas.groupby("produto")["quantidade"].sum().reset_index()
        st.bar_chart(mais_vendidos.set_index("produto"))
