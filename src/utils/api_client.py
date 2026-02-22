from niquests import Response, Session
from niquests.adapters import HTTPAdapter


class APIClient:
    def __init__(self) -> None:
        self.session: Session = self._create_session()
        self.timeout = (5, 10)

    def _create_session(self) -> Session:
        session = Session()
        session.headers.update(
            {
                "User-Agent": "weather-cli/0.1.0",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }
        )
        adapter = HTTPAdapter(
            pool_connections=5,
            pool_maxsize=5,
            max_retries=2,
            pool_block=False,
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def get(self, url: str, params: dict | None = None) -> dict:
        r: Response = self.session.get(url=url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
