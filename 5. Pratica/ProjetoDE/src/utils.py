import unicodedata
import logging
import pandas as pd
import requests
import utils as utils



from typing import Any, Dict, Optional

def ingestion(configs: Dict[str, Any]) -> pd.DataFrame:
    """
    Realiza a ingestão de dados a partir da API https://randomuser.me.

    Parâmetros:
        configs (dict): Dicionário de configurações contendo as chaves 'api' e 'ingestion'.

    Retorno:
        pd.DataFrame: DataFrame com os dados ingeridos da API.
    """

    url = f"{configs['api']['url']}/?results={configs['ingestion']['results_per_page']}"
    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        raise Exception(f"Erro ao acessar API: {response.status_code}")

    data = response.json()

    if "results" not in data:
        raise ValueError("Resposta da API não contém a chave 'results'")

    print(f"Dados ingeridos: {len(data['results'])} registros")
    return pd.DataFrame(data["results"])



def validation_inputs(df: pd.DataFrame, configs: Dict[str, Any]) -> bool:
    """
    Valida o DataFrame antes de salvar no banco de dados.

    Parâmetros:
        df (pd.DataFrame): DataFrame a ser validado.
        configs (dict): Dicionário de configurações contendo as colunas obrigatórias.

    Retorno:
        bool: True se os dados estiverem corretos, caso contrário levanta exceção.
    """

    if df is None or df.empty:
        logging.error("DataFrame vazio ou inexistente")
        raise ValueError("Erro de validação: DataFrame vazio")

    required_columns = configs["validation"]["required_columns"]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        logging.error(f"Colunas obrigatórias ausentes: {missing_columns}")
        raise ValueError("Erro de validação: schema inválido")

    logging.info("Dados corretos")
    return True



def remove_caracter_especial(texto: Any) -> Any:
    """
    Remove caracteres especiais de um texto.

    Parâmetros:
        texto (Any): Texto de entrada.

    Retorno:
        Any: Texto sem caracteres especiais ou valor original se for nulo.
    """
    if pd.isna(texto):
        return texto
    return (
        unicodedata.normalize("NFKD", str(texto))
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )



def preparation(df: pd.DataFrame, configs: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Realiza a preparação dos dados:
        - Renomeia colunas
        - Ajusta tipo dos dados
        - Remove caracteres especiais
        - Valida e salva em SQLite

    Parâmetros:
        df (pd.DataFrame): DataFrame original.
        configs (dict, opcional): Dicionário de configurações.

    Retorno:
        pd.DataFrame: DataFrame tratado.
    """

    import os
    import sqlite3
    # 1. Renomear colunas
    data = df.rename(columns={"name": "nome", "phone": "telefone"})

    # 2. Renomear para nomes finais
    expected_columns = {
        "gender": "sexo",
        "nome": "nome",
        "location": "endereco",
        "email": "email",
        "login": "login",
        "dob": "dob",
        "registered": "registro",
        "telefone": "telefone",
        "cell": "celular",
        "id": "id",
        "picture": "foto",
        "nat": "estado",
    }
    data = data.rename(columns=expected_columns)

    # 3. Remover caracteres especiais
    for col in data.select_dtypes(include="object").columns:
        data[col] = data[col].apply(remove_caracter_especial)

    # 4. Validar dados
    if configs:
        validation_inputs(data, configs)

    # 5. Salvar em SQLite
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    db_path = os.path.join(assets_dir, 'dados_tratados.db')
    conn = sqlite3.connect(db_path)
    data.to_sql('usuarios', conn, if_exists='replace', index=False)
    conn.close()
    logging.info(f"Dados preparados e salvos com sucesso em {db_path}")
    return data