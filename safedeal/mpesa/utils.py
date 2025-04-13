import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime

def get_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    r = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    access_token = r.json().get('access_token')
    return access_token

def format_phone(phone):
    """
    Converts 07XXXXXXXX to 2547XXXXXXXX
    """
    if phone.startswith("07"):
        return "254" + phone[1:]
    elif phone.startswith("01"):
        return "254" + phone[1:]
    elif phone.startswith("254") and len(phone) == 12:
        return phone
    else:
        raise ValueError("Invalid phone number format")



def lipa_na_mpesa(phone_number, amount, account_reference="SafeDeal", transaction_desc="SafeDeal Payment"):
    
    access_token = get_access_token()
    formatted_phone = format_phone(phone_number)
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    business_short_code = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    password = base64.b64encode((business_short_code + passkey + timestamp).encode()).decode()

    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "AccountReference": account_reference,
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": 1,#int(float(amount)),  # ensures compatibility just in case,
        "PartyA": '0748823384',#phone_number,
        "PartyB": business_short_code,
        "PhoneNumber": formatted_phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc,
    }

    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()
