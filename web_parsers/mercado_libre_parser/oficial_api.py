import json
import os
import time
from mercadolibre.client import Client
from web_parsers.mercado_libre_parser.settings import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, TOKEN_FILE, SELLERS_FILE



def save_token(data):
    data['created_at'] = int(time.time())

    with open(TOKEN_FILE, 'w') as f:
        json.dump(data, f, indent=4)

    print("💾 Token saved")


def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None

    with open(TOKEN_FILE, 'r') as f:
        return json.load(f)


def is_token_expired(token):
    now = int(time.time())
    return now > token['created_at'] + token['expires_in'] - 60


def get_valid_client():
    client = Client(CLIENT_ID, CLIENT_SECRET, site='MLA')
    token = load_token()

    if token:
        print("📂 Token loaded from file")
        client.set_token(token)

        if not is_token_expired(token):
            print("✅ Token is still valid")
            return client

        print("⚠️ Token expired → refreshing...")

        try:
            new_token = client.refresh_token()
            save_token(new_token)
            client.set_token(new_token)
            return client

        except Exception as e:
            print(f"❌ Refresh failed: {e}")

    url = client.authorization_url(REDIRECT_URI)
    print("\n👉 Get authorization code here:\n", url)
    code = input("\nPaste CODE: ")
    token = client.exchange_code(REDIRECT_URI, code)
    print(f'\n\n{token}')
    if 'access_token' not in token:
        raise Exception(f"❌ Token request failed: {token}")
    save_token(token)
    client.set_token(token)

    return client

def load_sellers():
    try:
        with open(SELLERS_FILE, 'r') as file:
            return json.loads(file.read())
    except FileNotFoundError:
        print('No saved sellers')
        return []

def save_seller_info(client, user_id):
    user_info_resp = client.get_user(user_id)

    print(user_info_resp)
    try:
        sellers_lst = load_sellers()
        if user_id not in sellers_lst: 
            sellers_lst.append(user_info_resp)
        else:
            print(f'Pass saved id: {user_id}')

        with open(SELLERS_FILE, 'w') as file:
            file.write(json.dumps(sellers_lst))

        
        
    except FileNotFoundError:
        with open(SELLERS_FILE, 'w') as file:
            file.write(json.dumps([]))


def run_ml_parser():
    print("\n🚀 Running Mercado Libre parser")

    client = get_valid_client()


    # users_id_lst = [82126280, 1002871133, 250174632]
    # [save_seller_info(client, us_id) for us_id in users_id_lst]
    

    sellers_dicts = load_sellers()
    for seller_dict in sellers_dicts[:1]:
        print(seller_dict.keys())
        seller_dict['brands'] = client.get_user_brands(seller_dict['id'])
        print(seller_dict)

if __name__ == "__main__":
    run_ml_parser()

    # load_sellers()