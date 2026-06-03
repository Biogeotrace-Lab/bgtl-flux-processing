import requests

from datetime import datetime

from pydantic.dataclasses import dataclass
from pydantic import TypeAdapter


@dataclass
class XEMARecord:
    codi_variable: int
    data_lectura: datetime
    valor_lectura: float


# For handling a naked JSON array of records.
XEMAPayloadAdapter = TypeAdapter(list[XEMARecord])


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
    data_id = "nzvn-apee"
    API_query_endpoint = ("https://analisi.transparenciacatalunya.cat"
                          "/api/v3/views/nzvn-apee/query.json")

    fields = ["id",
              "codi_estacio",
              "codi_variable",
              "data_lectura",
              "data_extrem",
              "valor_lectura",
              "codi_estat",
              "codi_base"]

    def __init__(self) -> None:
        self.headers = {"X-App-Token": self.DEFAULT_APP_TOKEN,
                        "Content-Type": "application/json"}

    def _query_json(self, select: str = "*",
                    where: str | None = None,
                    limit: int = 100000,
                    offset: int = 0) -> list[dict]:
        """Non-validated version of `XEMAClient.query`
        Kept for debugging and development reasons.
        """
        params = self._build_params(select=select,
                                    where=where,
                                    offset=offset,
                                    limit=limit)

        return requests.get(self.API_query_endpoint,
                            headers=self.headers,
                            params=params).json()
    
    def _build_params(self,
                      select: str = "*",
                      where: str | None = None,
                      offset: int = 0,
                      limit: int = 100000):
        
        query = f"""
        select {select} 
        {'where {where}' if where else ''} 
        offset {offset}
        limit {limit}
        """.format(select=select,
                   where=where,
                   limit=limit)

        params = {
            "query": query,
            "orderingSpecifier": "discard",
            "includeSystem": False,
            "includeSynthetic": False,
            "timeout": 1200
        }

        return params

    def query(self,
              select: str = "*",
              where: str | None = None,
              limit: int = 100000,
              offset: int = 0) ->\
                  list[XEMARecord]:
        """Query the Transparencia Catalunya database for XEMA data using an
        SQL-like statement.

        :param select: The columns (comma separated) to be returned, defaults
                        to *.
        :type select: `str`
        :param where: Filters the rows to be returned, defaults to limit.
        :type where: `str`
        :param limit: Max number of results to return, defaults to 100000.
        :type limit: `int`
        :param offset: Offset, used for paging. Defaults to 0.
        :type offset: `int`
        :returns: An array of XEMA records that satisfy the query.
        :rtype: `list[XEMARecord]`
        """
        params = self._build_params(select=select,
                                    where=where,
                                    offset=offset,
                                    limit=limit)
        request = requests.get(self.API_query_endpoint,
                                 headers=self.headers,
                                 params=params)
        request.raise_for_status()

        return XEMAPayloadAdapter.validate_json(
                    request.content,
                    strict=False)
