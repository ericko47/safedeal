from django.shortcuts import render
from django.http import JsonResponse
from .utils import lipa_na_mpesa
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from core.models import Transaction




def initiate_stk_push(request):
    phone_number = request.GET.get('phone')  # or from form
    amount = request.GET.get('amount')
    account_ref = "SafeDealTXN001"
    transaction_desc = "Payment for SafeDeal services"

    response = lipa_na_mpesa(phone_number, amount, account_ref, transaction_desc)
    return JsonResponse(response)



# @csrf_exempt
# def mpesa_callback(request):
#     data = json.loads(request.body)
#     print("Callback received:", data)
#     return JsonResponse({"message": "Callback received successfully"})

@csrf_exempt
def mpesa_callback(request):
    data = json.loads(request.body)
    try:
        result = data['Body']['stkCallback']
        metadata = result['CallbackMetadata']['Item']

        trans_ref = next((item['Value'] for item in metadata if item['Name'] == 'AccountReference'), None)
        amount = next((item['Value'] for item in metadata if item['Name'] == 'Amount'), None)

        transaction = Transaction.objects.get(transaction_reference=trans_ref)
        transaction.status = 'paid'
        transaction.save()

        # You can log more details or store M-PESA code

    except Exception as e:
        print("Callback processing error:", str(e))

    return JsonResponse({"message": "Callback processed"})

