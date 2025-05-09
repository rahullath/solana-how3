from flask import Flask, request, jsonify
import asyncio
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
import base64
from spl.token.instructions import transfer_checked, TransferCheckedParams

app = Flask(__name__)

RPC_ENDPOINT = "https://api.testnet.solana.com"
SOLANA_CLIENT = AsyncClient(RPC_ENDPOINT)
SOL_MINT = "So11111111111111111111111111111111111111112"
TESTNET_TOKENS = [
    {"address": "8FRFC6MoGGkMFQwngccyu69VnNu9pMoQjiX4D6darAAc", "symbol": "USDC", "decimals": 6},
    {"address": "<CUSTOM_MINT>", "symbol": "CUSTOM", "decimals": 9}
]

async def create_wallet(email):
    keypair = Keypair()
    return {"public_key": str(keypair.pubkey()), "private_key": keypair.secret().hex()}

async def mock_onramp(public_key, amount_usdc=1000):
    # Simulate minting 1000 USDC to wallet
    return {"status": "success", "usdc_amount": amount_usdc}

async def get_mock_quote(input_mint, output_mint, amount, decimals):
    mock_rates = {
        "8FRFC6MoGGkMFQwngccyu69VnNu9pMoQjiX4D6darAAc": 0.99,
        "<CUSTOM_MINT>": 0.95
    }
    rate = mock_rates.get(input_mint, 1.0)
    input_amount = amount / rate / (10 ** decimals)
    return {
        "inAmount": str(int(input_amount * (10 ** decimals))),
        "outAmount": str(amount),
        "routePlan": [{"swapInfo": {"mintA": input_mint, "mintB": output_mint}, "percent": 100}]
    }

async def get_best_swap_options(token, amount):
    amount_in_lamports = int(amount * 1_000_000_000)
    quotes = []
    for t in TESTNET_TOKENS:
        quote = await get_mock_quote(t["address"], SOL_MINT, amount_in_lamports, t["decimals"])
        quotes.append({
            "input_symbol": t["symbol"],
            "input_mint": t["address"],
            "output_amount": int(quote["outAmount"]) / 1_000_000_000,
            "quote": quote
        })
    quotes.sort(key=lambda x: x["output_amount"], reverse=True)
    return quotes[:3]

async def create_swap_transaction(user_public_key, quote_response):
    user_pubkey = PublicKey(user_public_key)
    input_mint = PublicKey(quote_response["routePlan"][0]["swapInfo"]["mintA"])
    in_amount = int(quote_response["inAmount"])
    tx = Transaction()
    tx.add(
        transfer_checked(
            TransferCheckedParams(
                program_id=PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
                source=user_pubkey,
                mint=input_mint,
                dest=user_pubkey,
                owner=user_pubkey,
                amount=in_amount,
                decimals=6
            )
        )
    )
    return tx

@app.route("/buy_crypto", methods=["POST"])
async def buy_crypto():
    data = request.json
    email = data.get("email")
    token = data.get("token", "SOL")
    amount = data.get("amount", 5)

    # Step 1: Create wallet
    wallet = await create_wallet(email)
    public_key = wallet["public_key"]

    # Step 2: Mock onramp
    onramp_result = await mock_onramp(public_key)
    if onramp_result["status"] != "success":
        return jsonify({"error": "Onramp failed"}), 500

    # Step 3: Get swap options
    options = await get_best_swap_options(token, amount)
    if not options:
        return jsonify({"error": "No swap options found"}), 500

    response = {
        "wallet": {"public_key": public_key, "private_key": wallet["private_key"]},
        "options": [
            {
                "input_token": opt["input_symbol"],
                "input_mint": opt["input_mint"],
                "output_sol": opt["output_amount"]
            } for opt in options
        ]
    }

    # Step 4: Execute swap if option selected
    selected_option = data.get("selectedOption", 0)
    if selected_option < len(options):
        quote = options[selected_option]["quote"]
        tx = await create_swap_transaction(public_key, quote)
        response["transaction"] = base64.b64encode(bytes(tx.serialize())).decode("utf-8")

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)
