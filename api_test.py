import requests
import json
import time
import random

API_URL = "http://127.0.0.1:5000/api/transaction"

def send_transaction():
    """Sends a randomly generated transaction to the API."""
    transaction = {
        "amount": round(random.uniform(1, 20000), 2),
        "location": random.choice(["New York", "London", "Tokyo", "known_fraud_location_1"])
    }

    try:
        response = requests.post(API_URL, json=transaction)
        if response.status_code == 201:
            print(f"Successfully sent transaction: {transaction}")
        else:
            print(f"Error sending transaction: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    while True:
        send_transaction()
        time.sleep(random.uniform(1, 10))
