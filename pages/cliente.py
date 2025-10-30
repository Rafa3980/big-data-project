# pages/cliente.py
import datetime
import pandas as pd
import streamlit as st
import psycopg2
import altair as alt

# -------------------------------
# Configuração do Streamlit
# -------------------------------
st.set_page_config(page_title="Gerenciador de clientes", page_icon="🎫")

# -------------------------------
# Verifica se o usuário está logado
# -------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Você precisa fazer o login para acessar esta página!")
    st.stop()

# -------------------------------
# Conexão com o banco Neon
# -------------------------------
try:
    conn = psycopg2.connect(st.secrets["neon_db_url"])
    st.sidebar.success("Conexão com Neon OK!")
except Exception as e:
    st.sidebar.error(f"Erro ao conectar: {e}")
    st.stop()

# -------------------------------
# Função para carregar dados do Neon
# -------------------------------
def carregar_dados():
    query = """
        SELECT 
            id_cliente, cliente_ativo, nome_completo, cpf, cep, endereco, complemento, numero, email, criado_em
        FROM clientes
        ORDER BY id_cliente DESC
    """
    df = pd.read_sql(query, conn)
    return df

# Sempre atualizar os dados ao abrir a página
st.session_state.df = carregar_dados()

# -------------------------------
# Título e descrição
# -------------------------------
st.title("👤 Gerenciador de clientes")
st.write("""
Este aplicativo permite gerenciar perfis de clientes. 
É possível cadastrar novos clientes, ver todos os clientes e visualizar estatísticas.
""")

# -------------------------------
# Botão de logout
# -------------------------------
c1, c2 = st.columns([1, 6])
with c1:
    if st.button("Sair"):
        for k in ("auth", "user", "display_name"):
            st.session_state.pop(k, None)
        st.session_state.authenticated = False
        st.experimental_rerun()

# -------------------------------
# Botão para atualizar manualmente os dados
# -------------------------------
if st.button("Atualizar dados do Neon"):
    st.session_state.df = carregar_dados()
    st.success("Dados atualizados com sucesso!")

# -------------------------------
# Adicionar novo cliente
# -------------------------------
st.header("Adicionar um novo cliente")
with st.form("add_cliente"):
    nome = st.text_input("Nome completo")
    cpf = st.text_input("CPF")
    email = st.text_input("Email")
    cep = st.text_input("CEP")
    endereco = st.text_input("Endereço")
    complemento = st.text_input("Complemento")
    numero = st.text_input("Número")
    cliente_ativo = st.checkbox("Cliente ativo", value=True)
    submitted = st.form_submit_button("Cadastrar")

if submitted:
    try:
        cursor = conn.cursor()
        insert_query = """
            INSERT INTO clientes (cliente_ativo, nome_completo, cpf, cep, endereco, complemento, numero, email, criado_em)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_cliente;
        """
        cursor.execute(insert_query, (
            cliente_ativo, nome, cpf, cep, endereco, complemento, numero, email, datetime.datetime.now()
        ))
        conn.commit()
        new_id = cursor.fetchone()[0]
        st.success(f"Cliente cadastrado com sucesso! ID: {new_id}")

        # Atualiza o DataFrame após cadastro
        st.session_state.df = carregar_dados()
    except Exception as e:
        st.error(f"Erro ao cadastrar cliente: {e}")

# -------------------------------
# Exibir clientes cadastrados
# -------------------------------
st.header("Clientes cadastrados")
st.data_editor(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    disabled=["id_cliente", "criado_em"]  # impede edição de ID e data
)

# -------------------------------
# Gráficos e estatísticas
# -------------------------------
st.header("Análise de dados e gráficos")
st.write("* Quantidade de clientes por bairro:")
chart_bairro = (
    alt.Chart(st.session_state.df)
    .mark_bar()
    .encode(
        x="endereco:O",
        y="count():Q",
        color="endereco:N"
    )
)
st.altair_chart(chart_bairro, use_container_width=True)

st.write("* Quantidade de clientes ativos/inativos:")
chart_ativo = (
    alt.Chart(st.session_state.df)
    .mark_bar()
    .encode(
        x="cliente_ativo:N",
        y="count():Q",
        color="cliente_ativo:N"
    )
)
st.altair_chart(chart_ativo, use_container_width=True)
