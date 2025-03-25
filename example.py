import os
from dotenv import load_dotenv

from coboweb3.api import PortalApi
from coboweb3.wallet import EvmWallet, SolanaWallet

load_dotenv()

api = PortalApi('dev', os.getenv('DEV_API_KEY'))

r = api.list_enabled_tokens()
print(r)

# print(api.list_wallets())

# w = api.get_wallet('d814bf80-9a13-4ce7-a7fc-db8f7bedf29f').address_wallets()
# print(w)

# evm: EvmWallet = w[1]
# solana: SolanaWallet = w[2]

# print(solana.get_balances())

# ixs = [{
#     "program_id": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",
#     "accounts": [{
#         "pubkey": "E4MhQWiqCLER3fFZNf8LyQFpLWW3BRxtsR5eps3c3vNS",
#         "is_signer": False,
#         "is_writable": False
#     }],
#     "data": "AQ=="
# }]
# r = solana.send_transaction(ixs)
# print(r)

# r = evm.get_balances()
# print(r)

# approve_tx = {
#     "to": "0xb16f35c0ae2912430dac15764477e179d9b9ebea",
#     "data": "0x095ea7b3000000000000000000000000b16f35c0ae2912430dac15764477e179d9b9ebea0000000000000000000000000000000000000000000000000000000000000064",
# }

# send_eth_tx = {
#      "to": "0x0000000000000000000000000000000000000064",
#      "value": "1"
# }

# r = evm.send_transaction(approve_tx)
# print(r)

# r = evm.send_transaction(send_eth_tx)
# print(r)

# r = api.get_transaction_info('97717a28-c68e-40e1-85e2-42506708fe61')
# print(r.to_json())

# r = evm.estimate_fee(approve_tx)
# print(r)

# r = evm.personal_sign('hello world')
# print(r)

# typed_message = {"types":{"EIP712Domain":[{"name":"name","type":"string"},{"name":"version","type":"string"},{"name":"chainId","type":"uint256"},{"name":"verifyingContract","type":"address"}],"Person":[{"name":"name","type":"string"},{"name":"wallet","type":"address"}],"Mail":[{"name":"from","type":"Person"},{"name":"to","type":"Person"},{"name":"contents","type":"string"}]},"primaryType":"Mail","domain":{"name":"Ether Mail","version":"1","chainId":1,"verifyingContract":"0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"},"message":{"from":{"name":"Cow","wallet":"0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826"},"to":{"name":"Bob","wallet":"0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"},"contents":"Hello, Bob!"}}     
# r = evm.sign_typed_message(typed_message)
# print(r)