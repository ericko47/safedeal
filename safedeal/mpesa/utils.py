import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime
import uuid

def get_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    r = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    access_token = r.json().get('access_token')
    return access_token

def format_phone(phone):
 
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
    api_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest" #"https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    business_short_code = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    password = base64.b64encode((business_short_code + passkey + timestamp).encode()).decode()

    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(float(amount)),  
        "PartyA": formatted_phone,
        "PartyB": business_short_code,
        "PhoneNumber": formatted_phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc,
    }

    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()


def initiate_b2c_payment(phone_number, amount, transaction_reference):
    access_token = get_access_token()
    formatted_phone = format_phone(phone_number)
    b2c_url = "https://api.safaricom.co.ke/mpesa/b2c/v3/paymentrequest"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    originator_id = str(uuid.uuid4())

    payload = {
        "InitiatorName": settings.MPESA_INITIATOR_NAME,
        "SecurityCredential": settings.MPESA_SECURITY_CREDENTIAL,
        "CommandID": "BusinessPayment",
        "Amount": int(amount),
        "PartyA": settings.MPESA_SHORTCODE,
        "PartyB": formatted_phone,
        "Remarks": "Seller Payout",
        "QueueTimeOutURL": settings.MPESA_TIMEOUT_CALLBACK,
        "ResultURL": settings.MPESA_RESULT_CALLBACK,
        "Occasion": transaction_reference,
        "OriginatorConversationID" : originator_id,
    }

    response = requests.post(b2c_url, json=payload, headers=headers)
    return response.json()

def query_stk_status(checkout_request_id):
    access_token = get_access_token()
    url = "https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query" #"https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(
        (settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp).encode()
    ).decode()

    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

