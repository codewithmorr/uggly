import os
import requests
import base64

from datetime import datetime
from requests.auth import HTTPBasicAuth


# -------------------- M-PESA CONFIG --------------------

consumer_key = "UVAtXJzDv7f5zNA9Q1LXdog9NAO7vrVQQU2y2X8qe5hMg2qE"
consumer_secret = "LBDFJLRbow5QV6xaukjtNy3Mm85qRoGxDODH0FGED9hZc2ZBTVC5H1SelRzSvEpG"

business_shortcode = "174379"

# sandbox passkey
passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"


# -------------------- ACCESS TOKEN --------------------

def get_access_token():

    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(
        url,
        auth=HTTPBasicAuth(
            consumer_key.strip(),
            consumer_secret.strip()
        )
    )

    print("STATUS:", response.status_code)
    print("RAW RESPONSE:", response.text)

    data = response.json()

    if "access_token" not in data:
        return None

    return data["access_token"]


# -------------------- STK PUSH --------------------

def lipa_na_mpesa(phone, amount):

    access_token = get_access_token()

    if not access_token:
        return {
            "error": "Failed to generate access token"
        }

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password = base64.b64encode(
        (
            business_shortcode +
            passkey +
            timestamp
        ).encode()
    ).decode()

    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": business_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": business_shortcode,
        "PhoneNumber": phone,

        # change this later when deployed
         "CallBackURL": "https://example.com/callback",

        "AccountReference":"HushandBlush",
        "TransactionDesc": "Payment"
    }

    response = requests.post(
        api_url,
        json=payload,
        headers=headers
    )

    print("STK STATUS:", response.status_code)
    print("STK RESPONSE:", response.text)

    data = response.json()

    print("FULL STK RESPONSE:")
    print(data)

    return data