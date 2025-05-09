# solana-how3

**Developer Brief: Simplified Crypto Purchase Chatbot Integration**

**Context**: The chatbot, built with Together AI and a frontend, uses MoonPay’s sandbox (quote-only, no real transactions) for fiat-to-crypto onramp. The current implementation assumes users manually connect wallets and confirm transactions. The goal is to automate the entire process—wallet creation, onramp, token purchase—on Solana testnet, requiring only one user confirmation, with no real money spent. The developer must integrate APIs and features to achieve this in a trial version.

**APIs**:
1. **Solana Testnet RPC** (`https://api.testnet.solana.com`):
   - Purpose: Interact with Solana testnet for wallet creation, token minting, and transactions.
   - Usage: Fund wallets with testnet SOL, mint testnet tokens (e.g., USDC), and send transactions.
2. **MoonPay Sandbox API** (`https://api.moonpay.com`):
   - Purpose: Simulate fiat-to-crypto quotes (e.g., USD to USDC).
   - Usage: Fetch price quotes for onramping; no real transactions (sandbox does nothing beyond quotes).
   - Note: Mock the onramp execution to fund testnet USDC.
3. **Jupiter Swap API** (Mocked for testnet, `https://quote-api.jup.ag/v6/quote`):
   - Purpose: Fetch swap quotes for token purchases (e.g., USDC to SOL).
   - Usage: Mainnet API is quote-only; mock responses for testnet with predefined rates (e.g., 1 USDC = 0.99 SOL).
4. **Phantom Wallet Provider** (JavaScript, `window.solana`):
   - Purpose: Sign and send transactions in the browser.
   - Usage: Automate wallet import and transaction signing on testnet.

**Features**:
1. **Automated Wallet Creation**:
   - Generate a Solana keypair using the user’s email as a seed (simplified for trial).
   - Output public/private key for import into Phantom (testnet mode).
2. **Mock Fiat Onramp**:
   - Use MoonPay sandbox to get a quote (e.g., $100 = 1000 USDC).
   - Simulate onramp by minting testnet USDC to the wallet (no real funds).
   - Require one user confirmation (e.g., “Confirm $100 to 1000 USDC”).
3. **Best Yield Options**:
   - Mock Jupiter API to list three swap options (e.g., USDC → 5 SOL, CUSTOM → 4.75 SOL).
   - Display options with input token, output amount, and a “Confirm” button.
4. **Automated Purchase**:
   - Execute swap using a simplified `spl-token` transfer (mocking a DEX swap).
   - Sign and send via Phantom with one user confirmation.
   - Add purchased tokens (e.g., 5 SOL) to the wallet.
5. **Chatbot Interface**:
   - Accept input (e.g., “Buy 5 SOL”) via Together AI’s existing chatbot.
   - Display wallet details, swap options, and confirmation prompts in the frontend.

**Integration Steps**:
1. **Setup** (1 hour):
   - Install Python libraries: `pip install flask solana aiohttp solders`.
   - Configure Solana testnet RPC: `https://api.testnet.solana.com`.
   - Ensure Phantom Wallet is in testnet mode.
   - Use existing Together AI chatbot and frontend.

2. **Wallet Creation** (2 hours):
   - Modify backend to generate a Solana keypair:
     ```python
     from solders.keypair import Keypair
     keypair = Keypair()
     public_key = str(keypair.pubkey())
     private_key = keypair.secret().hex()
     ```
   - Return keypair to frontend; instruct user to import private key into Phantom (manual step for trial).
   - Store public key for transactions.

3. **Mock Onramp** (3 hours):
   - Use MoonPay sandbox to get a quote:
     ```python
     import aiohttp
     async def get_moonpay_quote(amount_usd):
         async with aiohttp.ClientSession() as session:
             async with session.get("https://api.moonpay.com/v3/currencies/usdc_sol/quote", params={"baseCurrencyAmount": amount_usd}) as resp:
                 return await resp.json()
     ```
   - Mock onramp execution by minting testnet USDC:
     ```python
     async def mock_onramp(public_key, usdc_amount=1000):
         # Simulate: spl-token mint 8FRFC6MoGGkMFQwngccyu69VnNu9pMoQjiX4D6darAAc <usdc_amount> <public_key>
         return {"status": "success", "usdc_amount": usdc_amount}
     ```
   - Add confirmation prompt in frontend (e.g., “Confirm $100 to 1000 USDC”).

4. **Swap Options** (3 hours):
   - Mock Jupiter quote API for testnet:
     ```python
     async def get_mock_quote(input_mint, output_mint, amount, decimals):
         mock_rates = {"8FRFC6MoGGkMFQwngccyu69VnNu9pMoQjiX4D6darAAc": 0.99}
         rate = mock_rates.get(input_mint, 1.0)
         input_amount = amount / rate / (10 ** decimals)
         return {
             "inAmount": str(int(input_amount * (10 ** decimals))),
             "outAmount": str(amount),
             "routePlan": [{"swapInfo": {"mintA": input_mint, "mintB": output_mint}, "percent": 100}]
         }
     ```
   - Fetch quotes for 5 SOL, sort, and return top three to frontend:
     ```python
     options = [{"input_token": "USDC", "input_mint": "8FRFC6MoGGkMFQwngccyu69VnNu9pMoQjiX4D6darAAc", "output_sol": 5.0}, ...]
     ```

5. **Execute Swap** (4 hours):
   - Create a mock swap transaction:
     ```python
     from spl.token.instructions import transfer_checked, TransferCheckedParams
     tx = Transaction()
     tx.add(transfer_checked(TransferCheckedParams(
         program_id=PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
         source=PublicKey(user_public_key),
         mint=PublicKey(input_mint),
         dest=PublicKey(user_public_key),
         owner=PublicKey(user_public_key),
         amount=in_amount,
         decimals=6
     )))
     serialized_tx = base64.b64encode(bytes(tx.serialize())).decode("utf-8")
     ```
   - Update frontend to sign and send via Phantom:
     ```javascript
     async function executeSwap(serializedTx) {
         const txBuffer = Uint8Array.from(atob(serializedTx), c => c.charCodeAt(0));
         const signedTx = await window.solana.signTransaction(txBuffer);
         const txid = await window.solana.send(signedTx);
         alert("Transaction sent: " + txid);
     }
     ```
   - Add one confirmation button (e.g., “Confirm USDC → 5 SOL”).

6. **Chatbot Integration** (2 hours):
   - Extend Together AI chatbot to send requests to Flask:
     ```python
     @app.route("/buy_crypto", methods=["POST"])
     async def buy_crypto():
         data = request.json
         email = data["email"]
         amount = data.get("amount", 5)
         wallet = await create_wallet(email)
         await mock_onramp(wallet["public_key"])
         options = await get_mock_quote(...)  # Simplified
         return jsonify({"wallet": wallet, "options": options})
     ```
   - Update frontend to display wallet details and options:
     ```html
     <input id="email" placeholder="Enter email" />
     <button onclick="buyCrypto()">Buy 5 SOL</button>
     <div id="options"></div>
     ```

**Testing**:
- Fund wallet with testnet SOL: `solana airdrop 10 <PUBLIC_KEY> --url https://api.testnet.solana.com`.
- Verify wallet creation, USDC funding, swap options, and transaction on `https://explorer.solana.com/?cluster=testnet`.
- Test flow: Enter email, confirm onramp, select swap, confirm purchase.

**Notes**:
- **Automation**: Eliminate manual wallet connection; assume Phantom is pre-installed and set to testnet.
- **MoonPay Sandbox**: Use for quotes only; mock execution to stay free.
- **Trial Limitations**: Manual private key import into Phantom; simplified UI.
- **Security**: Use testnet-only wallets; no real funds or KYC.
