# ------------------------------- 
# Importações
# -------------------------------
import hashlib
import streamlit as st
import psycopg2
import pandas as pd

# -------------------------------
# Configuração do Streamlit
# -------------------------------
st.set_page_config(page_title="Gerenciamento de clientes", page_icon="🎫", layout="centered")

# -------------------------------
# Teste de conexão com Neon
# -------------------------------
try:
    conn = psycopg2.connect(st.secrets["neon_db_url"])
    st.sidebar.success("Conexão com Neon OK!")
except Exception as e:
    st.sidebar.error(f"Erro ao conectar: {e}")

# -------------------------------
# Sistema de login
# -------------------------------
USERS = {
    "admin@exemplo.com": hashlib.sha256("123456".encode()).hexdigest(),
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def _sha256(tx: str) -> str:
    return hashlib.sha256(tx.encode()).hexdigest()

def _is_authed() -> bool:
    return bool(st.session_state.get("auth") and st.session_state.get("user"))

def _login(email: str):
    st.session_state["auth"] = True
    st.session_state["user"] = email
    st.session_state["display_name"] = email.split("@")[0].title()
    st.session_state.authenticated = True

def _logout():
    for k in ("auth", "user", "display_name"):
        st.session_state.pop(k, None)
    st.session_state.authenticated = False 

def _render_login():
    st.markdown(
        """
        <div style="max-width:420px;margin:8vh auto 0 auto;padding:2rem;border-radius:16px;
             background:var(--secondary-background-color,#1a2035);box-shadow:0 10px 30px rgba(0,0,0,.35)">
          <h2 style="text-align:center;margin-top:0">Bem-vindo!</h2>
          <p style="text-align:center;margin-bottom:1rem">Faça login para continuar</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        if email and password and USERS.get(email.strip().lower()) == _sha256(password):
            _login(email.strip().lower())
            st.success("Login realizado!")
            st.rerun()
        else:
            st.error("Credenciais inválidas. Verifique email e senha.")

# -------------------------------
# Mostrar login se não autenticado
# -------------------------------
if not _is_authed():
    _render_login()
    st.stop()

# -------------------------------
# Função para buscar clientes do Neon
# -------------------------------
def buscar_clientes():
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id_cliente, cliente_ativo, criado_em, cpf, cep, endereco, complemento,
                   numero, nome_completo, email
            FROM clientes;
        """)
        resultados = cur.fetchall()
        colunas = [desc[0] for desc in cur.description]
        df = pd.DataFrame(resultados, columns=colunas)
        cur.close()
        return df
    except Exception as e:
        st.error(f"Erro ao buscar clientes: {e}")
        return pd.DataFrame()

# -------------------------------
# Interface principal após login
# -------------------------------
st.title(f"Olá, {st.session_state['display_name']}! 🎫")
c1, c2 = st.columns([1, 6])

with c1:
    if st.button("Sair"):
        _logout()
        st.success("Sessão encerrada.")
        st.rerun()

with c2:
    st.header("Lista de Clientes")
    df_clientes = buscar_clientes()
    if not df_clientes.empty:
        # Criar coluna "Status" legível
        df_clientes['Status'] = df_clientes['cliente_ativo'].apply(lambda x: 'Ativo' if x else 'Inativo')
        st.dataframe(df_clientes[['id_cliente','nome_completo','email','Status','criado_em','cpf','cep','endereco','complemento','numero']])
    else:
        st.info("Nenhum cliente encontrado.")

