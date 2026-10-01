import httpx
import msgspec
import asyncio

from datetime import datetime

from tqdm import tqdm

from urllib.parse import urlencode, quote


class XEMARecord(msgspec.Struct):
    odata_id: str = msgspec.field(name="@odata.id")
    codi_variable: str
    data_lectura: datetime
    valor_lectura: float


class ODataQueryResponse(msgspec.Struct):
    context: str = msgspec.field(name="@odata.context")
    value: list[XEMARecord]
    next_link: str | None = msgspec.field(name="@odata.nextLink", default=None)


class XEMAClient:
    """Requests-based client for the XEMA database. Query the server using
    an app token from Transparencia Catalunya.

    Totes les dades mesurades per una EMA passen un control de qualitat per
    determinar si el valor enregistrat és vàlid o no. Per tant, totes les
    lectures disposen d’un atribut estat que indica el resultat del procés de
    validació. Els valors possibles d’aquest atribut són:

    - espai en blanc: la dada no ha iniciat el procés de validació,
    - T: el procés de validació s’ha iniciat sobre la dada però està pendent
    d’un resultat,
    - V: la dada es considera vàlida,
    - N: la dada es considera invàlida.

    
    Info on the SoQL implementation and available functionality:
    https://dev.socrata.com/docs/queries/
    """

    DEFAULT_APP_TOKEN = "0XYFJLmsdqS3s6dLxQd9B3ink"
    dataset_id = "nzvn-apee"

    # Checkout OData API https://support.socrata.com/hc/en-us/articles/115005364207-Access-Data-Insights-Data-using-OData
    ENDPOINT = "https://analisi.transparenciacatalunya.cat/api/odata/v4/nzvn-apee"

    fields = ["id",
              "codi_estacio",
              "codi_variable",
              "data_lectura",
              "data_extrem",
              "valor_lectura",
              "codi_estat",
              "codi_base"]

    def __init__(self) -> None:
        # self.headers = {"X-App-Token": self.DEFAULT_APP_TOKEN}
        self.headers = {"User-Agent": "Fluxy/1.0 UAB"}
        self.client = httpx.AsyncClient(headers=self.headers,
                                        timeout=httpx.Timeout(30, read=1200,
                                                              connect=5),
                                        transport=httpx.AsyncHTTPTransport(
                                            retries=15),
                                        http2=True,
                                        limits=httpx.Limits(max_connections=20,
                                                            max_keepalive_connections=10,
                                                            keepalive_expiry=60.0))
        self.semaphone = asyncio.Semaphore(10)

    async def query(self,
                    select: str | None = None,
                    filters: tuple[str, ...] | None = None,
                    top: int = 500, *,
                    pbar: tqdm | None = None,
                    payload_buffer: list = []) -> list[XEMARecord]:
        """Query the Transparencia Catalunya database for XEMA data using their
        OData RESTapi.

        :returns: An array of XEMA records that satisfy the query.
        :rtype: `list[XEMARecord]`
        """
        params = {"$format": "json"}

        if select:
            params["$select"] = select
        if filters:
            params["$filter"] = " and ".join(filters)
        if top:
            params["$top"] = top # type: ignore

        param_string = urlencode(params, quote_via=quote)
        async with self.semaphone:
            response = await self.client.get(self.ENDPOINT + "?" + param_string)
        try:
            response.raise_for_status()
        except httpx.HTTPError:
            raise httpx.HTTPError(response.text)

        query = msgspec.json.decode(response.content, type=ODataQueryResponse)
        payload_buffer = await self._collect_data(query, pbar=pbar, payload_buffer=payload_buffer)
        return payload_buffer

    def _retry_get(self, *args, **kwargs):
        return

    async def _collect_data(self, query_response: ODataQueryResponse,
                            payload_buffer: list,
                            pbar: tqdm | None) -> list[XEMARecord]:
        """Collect query data in a shared payload container.
        """
        batch = query_response.value
        payload_buffer += batch

        if pbar:
            pbar.update(len(batch))
            pbar.total = max(pbar.total, pbar.n)

        if query_response.next_link is not None:
            response = await self.client.get(query_response.next_link)
            try:
                response.raise_for_status()
            except httpx.HTTPError:
                raise httpx.HTTPError(response.text)
            query_response = msgspec.json.decode(response.content,
                                                 type=ODataQueryResponse)
            payload_buffer = await self._collect_data(query_response,
                                                      payload_buffer,
                                                      pbar)

        return payload_buffer
