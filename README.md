# solana-how3

**Context**: The chatbot targets TradFi users with zero crypto knowledge, using a simple website (houseofweb3.io) built with Together AI and a frontend. It leverages MoonPay’s sandbox for fiat-to-crypto quotes (no real transactions) and operates on Solana testnet for a free trial. 

The goal is to fully automate wallet creation, fiat onramp, token purchase, and portfolio tracking with minimal user input (one confirmation), ensuring an intuitive experience on houseofweb3.io. Development must be completed in 2 days.

**Target Audience**: TradFi users who:
- Lack crypto/wallet knowledge.
- Expect a familiar, bank-like experience.
- Use houseofweb3.io to research and buy crypto via chat (e.g., “Buy 5 SOL”).
- Need hand-holding with clear, non-technical prompts.

**APIs**:
1. **Solana Testnet RPC** (`https://api.testnet.solana.com`):
   - Purpose: Create wallets, mint testnet tokens (e.g., USDC, SOL), and execute transactions.
   - Usage: Fund wallets with testnet SOL, simulate swaps, and track balances.
2. **MoonPay Sandbox API** (`https://api.moonpay.com`):
   - Purpose: Provide fiat-to-crypto price quotes (e.g., $100 = 1000 USDC).
   - Usage: Fetch quotes; mock execution to fund testnet tokens (sandbox is quote-only).
3. **Jupiter Swap API** (Mocked for testnet, `https://quote-api.jup.ag/v6/quote`):
   - Purpose: Simulate swap quotes for token purchases (e.g., USDC to SOL).
   - Usage: Mock mainnet API responses with testnet rates (e.g., 1 USDC = 0.99 SOL).
4. **Phantom Wallet Provider** (JavaScript, `window.solana`):
   - Purpose: Automate transaction signing in the browser.
   - Usage: Pre-configure Phantom in testnet mode for seamless signing.

**Features**:
1. **Automatic Wallet Creation**:
   - Generate a Solana wallet using the user’s email (simplified seed).
   - Auto-import into Phantom (testnet) without user interaction.
   - Display: “Your wallet is ready!” (hide public/private keys).
2. **Seamless Fiat Onramp**:
   - Use MoonPay sandbox to show quote (e.g., “$100 = 1000 USDC”).
   - Mock onramp by minting testnet USDC to the wallet.
   - One confirmation: “Pay $100 for 1000 USDC? [Confirm]”.
3. **Best Purchase Options**:
   - Mock Jupiter API to show three simple options (e.g., “100 USDC → 5 SOL”).
   - Non-technical display: “Best ways to buy 5 SOL with USDC”.
4. **One-Click Purchase**:
   - Execute swap with a mock `spl-token` transfer.
   - One confirmation: “Buy 5 SOL for 100 USDC? [Confirm]”.
   - Add tokens to wallet; show: “5 SOL added to your wallet!”.
5. **Portfolio Tracking**:
   - Display wallet balance (e.g., “You own: 5 SOL, 900 USDC”).
   - Simple UI on houseofweb3.io, like a bank account summary.
6. **Chatbot UX**:
   - Handle inputs like “Buy 5 SOL” via Together AI.
   - Friendly prompts: “Let’s get you 5 SOL! Confirm payment?”.
   - Avoid crypto jargon (e.g., no “sign transaction”, “public key”).

**Integration Steps**:
1. **Setup** (1 hour):
   - Install: `pip install flask solana aiohttp solders`.
   - Use Solana testnet RPC: `https://api.testnet.solana.com`.
   - Pre-install Phantom (testnet mode) on development browser.
   - Leverage existing Together AI chatbot and houseofweb3.io frontend.

2. **Wallet Creation** (2 hours):
   - Generate Solana keypair:
     ```python
     from solders.keypair import Keypair
     keypair = Keypair()
     public_key = str(keypair.pubkey())
     private_key = keypair.secret().hex()
     ```
   - Mock Phantom auto-import by storing keypair in-memory; assume Phantom is pre-configured.
   - Return public key to backend; show user: “Wallet created!”.

3. **Mock Onramp** (3 hours):
   - Fetch MoonPay sandbox quote:
     ```python
     import aiohttp
     async def get_moonpay_quote(amount_usd):
         async with aiohttp.ClientSession() as session:
             async with session.get("https://api.moonpay.com/v3/currencies/usdc_sol/quote", params={"baseCurrencyAmount": amount_usd}) as resp:
                 return await resp.json()
     ```
   - Mock onramp execution:
     ```python
     async def mock_onramp(public_key, usdc_amount=1000):
         # Simulate: spl-token mint 8FRFC6MoGGkMFQwngccyu69VnNu9pMoQjiX4D6darAAc 1000 <public_key>
         return {"status": "success", "usdc_amount": usdc_amount}
     ```
   - Frontend prompt: `<button onclick="confirmOnramp()">Pay $100 for 1000 USDC</button>`.

4. **Swap Options** (3 hours):
   - Mock Jupiter quotes:
     ```python
     async def get_mock_quote(input_mint, output_mint, amount, decimals):
         mock_rates = {"8FRFC6MoGGkMFQwngccyu69VnNu9pMoQjiX4D6darAAc": 0.99}  # USDC
         rate = mock_rates.get(input_mint, 1.0)
         input_amount = amount / rate / (10 ** decimals)
         return {
             "inAmount": str(int(input_amount * (10 ** decimals))),
             "outAmount": str(amount),
             "routePlan": [{"swapInfo": {"mintA": input_mint, "mintB": output_mint}, "percent": 100}]
         }
     ```
   - Display on houseofweb3.io:
     ```html
     <div id="options">
         <p>Option 1: 100 USDC → 5 SOL <button onclick="buy(0)">Buy</button></p>
         <p>Option 2: 105 USDC → 4.75 SOL <button onclick="buy(1)">Buy</button></p>
     </div>
     ```

5. **Execute Swap** (3 hours):
   - Create mock swap transaction:
     ```python
     from spl.token.instructions import transfer_checked, TransferCheckedParams
     tx = Transaction()
     tx.add(transfer_checked(TransferCheckedParams(
         program_id=PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
         source=PublicKey(user_public_key),
         mint=PublicKey("8FRFC6MoGGkMFQwngccyu69VnNu9pMoQjiX4D6darAAc"),
         dest=PublicKey(user_public_key),
         owner=PublicKey(user_public_key),
         amount=in_amount,
         decimals=6
     )))
     serialized_tx = base64.b64encode(bytes(tx.serialize())).decode("utf-8")
     ```
   - Frontend Phantom signing:
     ```javascript
     async function buy(optionIndex) {
         const response = await fetch("/buy_crypto", {
             method: "POST",
             body: JSON.stringify({ email, amount: 5, selectedOption: optionIndex })
         });
         const data = await response.json();
         const txBuffer = Uint8Array.from(atob(data.transaction), c => c.charCodeAt(0));
         const signedTx = await window.solana.signTransaction(txBuffer);
         const txid = await window.solana.send(signedTx);
         document.getElementById("status").innerText = "Bought 5 SOL!";
     }
     ```

6. **Portfolio Tracking** (2 hours):
   - Query wallet balance:
     ```python
     async def get_balance(public_key):
         client = AsyncClient(RPC_ENDPOINT)
         sol_balance = await client.get_balance(PublicKey(public_key))
         usdc_balance = await client.get_token_account_balance(PublicKey("USDC_ATA_ADDRESS"))
         return {"sol": sol_balance.value / 1_000_000_000, "usdc": usdc_balance.value.ui_amount}
     ```
   - Display: `<p>Your wallet: 5 SOL, 900 USDC</p>`.

7. **Chatbot UX** (2 hours):
   - Extend Together AI to handle “Buy 5 SOL”:
     ```python
     @app.route("/buy_crypto", methods=["POST"])
     async def buy_crypto():
         data = request.json
         email = data["email"]
         amount = data.get("amount", 5)
         wallet = await create_wallet(email)
         await mock_onramp(wallet["public_key"])
         options = await get_mock_quote("8FRFC6MoGGkMFQwngccyu69VnNu9pMoQjiX4D6darAAc", SOL_MINT, amount * 1_000_000_000, 6)
         balance = await get_balance(wallet["public_key"])
         return jsonify({"wallet": wallet["public_key"], "options": options, "balance": balance})
     ```
   - Frontend: Friendly prompts like “Your 5 SOL is ready!”.

**Testing**:
- Fund wallet: `solana airdrop 10 <PUBLIC_KEY> --url https://api.testnet.solana.com`.
- Verify on `https://explorer.solana.com/?cluster=testnet`.
- Test flow: Enter email, confirm onramp, pick option, confirm purchase, check balance.

**Notes**:
- **TradFi UX**: Use bank-like terms (e.g., “Pay”, “Buy”, “Your Money”); avoid “sign”, “mint”, “lamports”.
- **Automation**: Pre-configure Phantom; hide wallet setup (show “Wallet ready!”).
- **MoonPay**: Use sandbox quotes; mock execution for testnet.
- **Trial**: Manual Phantom setup by developer; no real funds.
