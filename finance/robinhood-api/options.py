import requests
import json
import os

from collections import defaultdict
from datetime import datetime

# Environment Variables
auth_header = os.environ.get('AUTH_HEADER')
account_number = os.environ.get('ACCOUNT_NUMBER')

# Robinhood API endpoints
account_url = "https://api.robinhood.com/accounts/"
history_url = "https://api.robinhood.com/options/orders/?account_numbers=" + account_number

# Set authorization header
headers = {
    "Authorization": auth_header
}

def display_response(response):
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON data
        data = response.json()

        # Pretty print the JSON data
        formatted_json = json.dumps(data, indent=4)
        print(formatted_json)
    else:
        print(f"Request failed with status code: {response.status_code}")

# Uncomment following to get account details
# print("\nGet account details:\n")
# response = requests.get(account_url, headers=headers)
# display_response(response)

# Get Transaction History
print("\nGet account transaction history:\n")
history_response = requests.get(history_url, headers=headers)

# Uncomment following to display transaction history as JSON on console
# display_response(history_response)

# Group by chain id and display as a table

# Assuming the API response is stored in the variable 'history_response'
data = history_response.json()

all_results = []

# Check if the response contains the 'results' key
if 'results' in data:
    all_results.extend(data['results'])

    # Loop until the 'next' item is null
    while 'next' in data and data['next']:
        # Fetch the next page of results
        next_url = data['next']
        response = requests.get(next_url, headers=headers)
        data = response.json()

        # Append the new results to the existing data
        if 'results' in data:
            all_results.extend(data['results'])

    # Filter by state == "filled"
    filled_results = [result for result in all_results if result.get('state') == 'filled' and datetime.strptime(result.get('updated_at', '2023-09-01T00:00:00'), '%Y-%m-%dT%H:%M:%S.%fZ').date() >= datetime(2023, 9, 1).date()]

    # Group by chain_id
    grouped_results = defaultdict(list)
    for result in filled_results:
        chain_id = result.get('chain_id')
        grouped_results[chain_id].append(result)

    total_diff = 0

    # Create a table for each chain_id
    for chain_id, chain_results in grouped_results.items():
        print(f"Chain ID: {chain_id}")
        print("-" * 20)
        print("{:<20} {:<20} {:<20} {:<20} {:<20} {:<20}".format("Chain Symbol", "Opening Strategy", "Closing Strategy", "Net Amount Direction", "Net Amount", "Updated At"))
        print("-" * 120)

        # Sort the results within the group by reversed updated_at
        chain_results.sort(key=lambda x: x.get('updated_at'), reverse=True)

        total_credit = 0
        total_debit = 0

        for result in chain_results:
            chain_symbol = result.get('chain_symbol') or ''
            opening_strategy = result.get('opening_strategy') or ''
            closing_strategy = result.get('closing_strategy') or ''
            net_amount_direction = result.get('net_amount_direction') or ''
            net_amount = round(float(result.get('net_amount') or 0), 2)
            updated_at = result.get('updated_at') or ''

            print("{:<20} {:<20} {:<20} {:<20} {:<20} {:<20}".format(chain_symbol, opening_strategy, closing_strategy, net_amount_direction, net_amount, updated_at))

            if net_amount_direction.lower() == 'credit':
                total_credit += net_amount
            elif net_amount_direction.lower() == 'debit':
                total_debit += net_amount
        
        print("-" * 120)
        print(f"Total Credit: ${total_credit:.2f}")
        print(f"Total Debit: ${total_debit:.2f}")
        group_diff = total_credit - total_debit
        print(f"Gain/Loss: ${group_diff:.2f}")
        total_diff += group_diff
        print("\n")

    print(f"Total Gain/Loss: ${total_diff:.2f}")

    print("\n")

else:
    print("No 'results' key found in the response.")