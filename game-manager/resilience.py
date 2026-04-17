import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


def create_resilient_session(
    retries=3,
    backoff_factor=0.5,
    status_forcelist=(500, 502, 503, 504)
):
    """
    Cria uma sessao HTTP com RETRY automatico.

    - retries: numero maximo de tentativas (padrao: 3)
    - backoff_factor: fator de espera exponencial entre tentativas
                      com 0.5, as esperas sao: 0.5s, 1s, 2s
    - status_forcelist: codigos HTTP que acionam retry automaticamente
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session