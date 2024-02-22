import requests
from django.conf import settings
from helpers.baxi_helpers import posible_requey_statuses
from django.conf import settings

posible_requey_statuses = ["BX0001", "BX0019", "BX0021","BX0024", "EXC00103", "EXC00105", "EXC00109", "EXC00114", "EXC00124", "UNK0001", "EXC00001"]


class BaxiPayManager:
    def __init__(self):
        self.authorization_key = settings.BAXI_KEY
        self.base_url = settings.BAXI_BASE_URL_2
        self.agent_id = settings.BAXI_AGENT_ID
        self.mock = False

    def _make_request(self, endpoint, method, data=None, params=None, headers=None):
        print("XXXXXXX")
        # url = f"{self.base_url}{endpoint}"

        url = f"{self.base_url}{endpoint}"

        # url = "/transaction/requery"

        headers = headers or {}
        headers.update({
            "Authorization": "Api-key " + self.authorization_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

        response = requests.request(method, url, json=data, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def requery_transaction(self, agent_reference):
        print("trying to requery.........")
        if self.mock:
            return self.mock_requery_response()
        else:
            endpoint = 'superagent/transaction/requery'
            data = {"agentReference": agent_reference}
            response_data = self._make_request(endpoint, method='GET', data=data)
            print(response_data, 12345)

            if response_data["status"].lower() == "success" and str(response_data["code"]) == "200":
                return True, response_data["message"], False
            elif response_data["code"] in posible_requey_statuses:
                print(response_data, "MMMMMMMMM")
                return False, "should be requeried", True
            elif response_data["code"] == "error":
                return False, "should not be requeried", False
            else:
                return False, response_data["message"], False


    def mock_requery_response(self):

        print("in query mock reponse.........")

        import random
        from helpers.baxi_helpers import posible_requey_statuses
        possible_statuses = ["success"]
        # possible_requery_statuses = ["200", "400"] + posible_requey_statuses + ["500", "422"]
        # possible_requery_statuses = ["200", "400"] + ["500", "422"]
        possible_requery_statuses = ["200", "500", "BX0001"]


        # possible_requery_statuses = ["401", "403"]
        possible_failure_statuses = ["500", "422"]


        status = random.choice(possible_statuses)
        code = random.choice(possible_requery_statuses)

        response_data = {
            "status": status,
            "code": code,
            "data": "response data",
        }
        print(response_data)
        if status == "success" and code == "200":
            return True, response_data["data"], False
        elif code in posible_requey_statuses:
            return False, "should be requeried", False
        else:
            return False, posible_requey_statuses, True