from cobo_waas2.configuration import Configuration
from cobo_waas2.api_client import ApiClient
from cobo_waas2.api.wallets_api import WalletsApi
from cobo_waas2.api.transactions_api import TransactionsApi
from cobo_waas2.models.contract_call_params import ContractCallParams
from cobo_waas2.models.estimate_fee_params import EstimateFeeParams
from cobo_waas2.models.message_sign_params import MessageSignParams

from .wallet import Wallet

ENV_URLS = {
    "dev": "https://api.dev.cobo.com/v2",
    "sandbox": "https://api.sandbox.cobo.com/v2",
    "prod": "https://api.cobo.com/v2"
}

class PortalApi(object):

    def __init__(self, env: str, private_key: str) -> None:
        self.cfg = Configuration(
            api_private_key=private_key,
            host=ENV_URLS[env]
        )

        self.client = ApiClient(self.cfg)
        self.wallets = WalletsApi(self.client)
        self.transactions = TransactionsApi(self.client)

        self.requests = []

    def list_enabled_tokens(self):
        return self.wallets.list_enabled_tokens().data

    def list_enabled_chains(self):
        return self.wallets.list_enabled_chains().data

    def list_wallets(self):
        resp = self.wallets.list_wallets()
        return [Wallet(self, w) for w in resp.data]
    
    def get_wallet(self, wallet_id: str):
        resp = self.wallets.get_wallet_by_id(wallet_id)
        return Wallet(self, resp)
    
    def list_addresses(self, wallet_id: str):
        return self.wallets.list_addresses(wallet_id).data
    
    def list_token_balances_for_address(self, wallet_id: str, address: str):
        resp = self.wallets.list_token_balances_for_address(wallet_id, address)
        return resp.data
    
    def contract_call(self, params: dict):
        request = self.transactions.create_contract_call_transaction(ContractCallParams.from_dict(params))
        assert request.status == 'Submitted'
        self.requests.append(request)
        return request
    
    def estimate_fee(self, params: dict):
        return self.transactions.estimate_fee(EstimateFeeParams.from_dict(params))

    def get_transaction_info(self, request_id: str):
        return self.transactions.get_transaction_by_id(request_id)
    
    def sign_message(self, params: dict):
        return self.transactions.create_message_sign_transaction(MessageSignParams.from_dict(params))