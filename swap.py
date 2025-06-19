import datetime
import sys
import random
import json
import os
from web3 import Web3
from eth_account import Account
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from pyfiglet import Figlet
import blessed

# توليد ساعة تشغيل عشوائية يومياً (مثلاً الساعة 10 أو 17)
random.seed(datetime.date.today().toordinal())
chosen_hour = random.randint(0, 23)
chosen_minute = random.randint(0, 59)
now = datetime.datetime.utcnow()

if now.hour != chosen_hour or now.minute != chosen_minute:
    print(f"[INFO] الآن: {now.hour}:{now.minute} UTC، وليس موعد التشغيل العشوائي اليوم {chosen_hour}:{chosen_minute}. الخروج.")
    sys.exit(0)

# تحديد مدة عشوائية للتشغيل (من 5 إلى 15 دقيقة)
end_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=random.randint(5, 15))
print(f"[INFO] التشغيل بدأ وسيستمر حتى {end_time.strftime('%H:%M:%S')} UTC")

def display_header():
    term = blessed.Terminal()
    os.system("cls" if os.name == "nt" else "clear")
    fig = Figlet(font="slant")
    print(term.bold_cyan(fig.renderText("CRYPTO ALERT")))
    print(term.yellow("✦ ✦ PHRS AUTO TRANSFER ✦ ✦\n"))

def generate_encryption_key():
    if not os.path.exists("secret.key"):
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)

def encrypt_private_key(private_key, key_file="secret.key"):
    with open(key_file, "rb") as file:
        encryption_key = file.read()
    encrypted = Fernet(encryption_key).encrypt(private_key.encode())
    with open("private_key.enc", "wb") as f:
        f.write(encrypted)

def decrypt_private_key(key_file="secret.key", enc_file="private_key.enc"):
    with open(key_file, "rb") as kf:
        encryption_key = kf.read()
    with open(enc_file, "rb") as ef:
        encrypted = ef.read()
    return Fernet(encryption_key).decrypt(encrypted).decode()

load_dotenv()
generate_encryption_key()

if not os.path.exists("private_key.enc"):
    pk = os.getenv("PRIVATE_KEY")
    if not pk:
        print("[ERROR] Add your PRIVATE_KEY to .env")
        exit()
    encrypt_private_key(pk)

private_key_main = decrypt_private_key()
rpc_url = "https://testnet.dplabs-internal.com"
web3 = Web3(Web3.HTTPProvider(rpc_url))

if not web3.is_connected():
    print("[ERROR] Cannot connect to Pharos RPC.")
    exit()
print("[SUCCESS] Connected to Pharos Testnet.")

main_wallet = web3.eth.account.from_key(private_key_main).address
print(f"[INFO] Using wallet: {main_wallet}")

def generate_wallets():
    wallets = []
    for _ in range(20):
        account = Account.create()
        wallets.append({"address": account.address, "private_key": account.key.hex()})
    with open("generated_wallets.json", "w") as f:
        json.dump(wallets, f, indent=4)
    print("[INFO] 20 wallets generated.")

def send_phrs(to_address):
    for _ in range(5):
        try:
            amount = round(random.uniform(0.0001, 0.001), 6)
            amount_wei = web3.to_wei(amount, "ether")
            print(f"[INFO] Sending {amount} PHRS → {to_address}")

            balance = web3.eth.get_balance(main_wallet)
            print(f"[INFO] Wallet balance: {web3.from_wei(balance, 'ether')} PHRS")

            nonce = web3.eth.get_transaction_count(main_wallet)
            gas_limit = 21000

            gas_price_phrs = round(random.uniform(0.000000001, 0.000000005), 18)
            gas_price = int(gas_price_phrs * (10**18))

            total_cost = amount_wei + gas_limit * gas_price
            print(f"[INFO] Total cost: {web3.from_wei(total_cost, 'ether')} PHRS")

            if balance < total_cost:
                print("[ERROR] Not enough PHRS for transfer.")
                return False

            tx = {
                "from": main_wallet,
                "to": to_address,
                "value": amount_wei,
                "gas": gas_limit,
                "gasPrice": gas_price,
                "nonce": nonce,
                "chainId": 688688
            }

            signed = web3.eth.account.sign_transaction(tx, private_key_main)
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)

            print(f"[SUCCESS] TX hash: {tx_hash.hex()}")
            print(f"[INFO] Gas used: {gas_price_phrs} PHRS\n")
            return True

        except Exception as e:
            print(f"[ERROR] Failed: {str(e)}\n")
            time.sleep(10)
    return False

if __name__ == "__main__":
    display_header()

    while datetime.datetime.utcnow() < end_time:
        generate_wallets()
        try:
            with open("generated_wallets.json", "r") as f:
                wallets = json.load(f)
        except:
            print("[ERROR] Wallet list missing.")
            break

        for wallet in wallets:
            if send_phrs(wallet["address"]):
                print(f"[SUCCESS] Sent to {wallet['address']}")
            wait = random.randint(60, 300)
            print(f"[INFO] Waiting {wait} seconds before next transfer...\n")
            time.sleep(wait)

        print("[INFO] Generating new batch of wallets...\n")
