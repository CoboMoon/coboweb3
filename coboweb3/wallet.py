import json
import uuid
import base64
import re
from decimal import Decimal

from cobo_waas2.models.wallet_info import WalletInfo
from cobo_waas2.models.address_info import AddressInfo

COBO_CHAIN_IDS = {
    1: 'ETH',
    42161: 'ARBITRUM_ETH',
    56: 'BSC_BNB',
    8453: "BASE_ETH",
    43114: "AVAXC",
    11155111: "SETH",
    137: "MATIC",
    10: "OPTIMISM_ETH",
}

class Wallet(object):

    def __init__(self, api, raw: WalletInfo) -> None:
        self.api = api
        self.raw = raw

        self.id = raw.actual_instance.wallet_id
        self.name = raw.actual_instance.name
        self.type = raw.actual_instance.wallet_type.value
        self.subtype = raw.actual_instance.wallet_subtype.value

    def __repr__(self) -> str:
        return f"<{self.name} ({self.type}, {self.subtype}, {self.id})>"
    
    def addresses(self) -> list[str]:
        return self.api.list_addresses(self.id)
    
    def address_wallets(self) -> list["AddressWallet"]:
        return [AddressWallet.create(self, a) for a in self.api.list_addresses(self.id)]

    def address_wallet(self, address: str) -> "AddressWallet":
        for wallet in self.address_wallets():
            if wallet.address == address:
                return wallet
            
        raise ValueError(f"Address {address} not found in wallet {self.id}")

class AddressWallet(object):

    def __init__(self, wallet: Wallet, raw: AddressInfo) -> None:
        self.wallet = wallet
        self.raw = raw

        self.address = raw.address
        self.cobo_chain_id = raw.chain_id

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.address}>"

    def _get_call_source(self) -> dict:
        return {
            "source_type": self.wallet.subtype,
            "wallet_id": self.wallet.id,
            "address": self.address
        }

    def transfer(self, token, to, amount):
        raise NotImplementedError


    def get_balances(self):
        return self.wallet.api.list_token_balances_for_address(self.wallet.id, self.address)
    
    @staticmethod
    def create(wallet: Wallet, raw: AddressInfo) -> "AddressWallet":
        if re.match(r'0x[0-9a-fA-F]{40}', raw.address):
            return EvmWallet(wallet, raw)
        if raw.chain_id in ['SOL', 'TSOL']:
            return SolanaWallet(wallet, raw)
        else:
            return AddressWallet(wallet, raw)

class EvmWallet(AddressWallet):

    def _get_cobo_chain_id(self, chain_id) -> str:
        if chain_id:
            return COBO_CHAIN_IDS[chain_id]
        return self.cobo_chain_id
    
    def _get_call_destination(self, tx: dict) -> dict:
        return {
            "destination_type": "EVM_Contract",
            "address": tx["to"],
            "calldata": tx.get("data") or "",
            "value": str(Decimal(tx.get("value"))/Decimal(10**18)) or "0"
        }

    def _get_fee(self, tx: dict) -> dict:
        
        cobo_chain_id = self._get_cobo_chain_id(tx.get("chainId"))

        if tx.get('type') == '0x2':
            assert 'maxFeePerGas' in tx
            assert 'maxPriorityFeePerGas' in tx
        
        fee = {}

        if 'maxFeePerGas' in tx and 'maxPriorityFeePerGas' in tx:
            fee = {
                "fee_type": "EVM_EIP_1559",
                "token_id": cobo_chain_id,
                "max_fee_per_gas": tx['maxFeePerGas'],
                "max_priority_fee_per_gas": tx['maxPriorityFeePerGas'],
            }
        elif 'gasPrice' in tx:
            fee = {
                "fee_type": "EVM_Legacy",
                "token_id": cobo_chain_id,
                "gas_price": tx['gasPrice'],
                "max_priority_fee_per_gas": tx['maxPriorityFeePerGas'],
            }

        if fee and 'gas' in tx:
            fee['gas_limit'] = tx['gas']
        
        return fee

    def send_transaction(self, tx: dict):
        """
        Send a transaction from this wallet.

        tx = {
            'to': '0xF0109fC8DF283027b6285cc889F5aA624EaC1F55',
            'value': 1000000000,
            'gas': 2000000,
            'maxFeePerGas': 2000000000,
            'maxPriorityFeePerGas': 1000000000,
            'nonce': 0,
            'chainId': 1,
            'type': '0x2',  # the type is optional and, if omitted, will be interpreted based on the provided transaction parameters
        }
        """

        assert self.wallet.type == 'MPC'

        cobo_chain_id = self._get_cobo_chain_id(tx.get("chainId"))
        
        params = {
            "request_id": f"coboweb3-{uuid.uuid4()}",
            "chain_id": cobo_chain_id,
            "source": self._get_call_source(),
            "destination": self._get_call_destination(tx),
        }

        fee = self._get_fee(tx)
        if fee: 
            params['fee'] = fee

        return self.wallet.api.contract_call(params)

    def sign_typed_message(self, msg: dict):
        destination = {
            "destination_type": "EVM_EIP_712_Signature",
            "structured_data": msg
        }

        params = {
            "request_id": f"coboweb3-{uuid.uuid4()}",
            "chain_id": self.cobo_chain_id,
            "source": self._get_call_source(),
            "destination": destination,
        }

        return self.wallet.api.sign_message(params)

    def personal_sign(self, msg: str | bytes):
        if isinstance(msg, str):
            msg = msg.encode('utf-8')
        
        destination = {
            "destination_type": "EVM_EIP_191_Signature",
            "message": base64.b64encode(msg).decode('utf-8')
        }

        params = {
            "request_id": f"coboweb3-{uuid.uuid4()}",
            "chain_id": self.cobo_chain_id,
            "source": self._get_call_source(),
            "destination": destination,
        }

        return self.wallet.api.sign_message(params)


    def estimate_fee(self, tx: dict):
        cobo_chain_id = self._get_cobo_chain_id(tx.get("chainId"))

        resp = self.wallet.api.estimate_fee({
            "request_type": "ContractCall",
            "source": self._get_call_source(),
            "chain_id": cobo_chain_id,
            "destination": {
                "destination_type": "EVM_Contract",
                "address": tx["to"],
                "calldata": tx.get("data") or "",
                "value": tx.get("value") or "0"
            }
        })
        return resp.to_json()

class SolanaWallet(AddressWallet):

    def _get_call_destination(self, ixs: list) -> dict:
        return {
            "destination_type": "SOL_Contract",
            "instructions": ixs,
        }

    def send_transaction(self, ixs: list):
        """
        Send a transaction from this wallet.

        ixs = [{
            "program_id": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",
            "accounts": [{
                "pubkey": "E4MhQWiqCLER3fFZNf8LyQFpLWW3BRxtsR5eps3c3vNS",
                "is_signer": True,
                "is_writable": True
            }],
            "data": "AQ=="
        }]
        """

        assert self.wallet.type == 'MPC'

        params = {
            "request_id": f"coboweb3-{uuid.uuid4()}",
            "chain_id": self.cobo_chain_id,
            "source": self._get_call_source(),
            "destination": self._get_call_destination(ixs),
        }
        return self.wallet.api.contract_call(params)