import csv
import json
import os
import openai
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion_with_backoff(**kwargs):
    return openai.Completion.create(**kwargs)

load_dotenv()

openai.api_key = os.getenv("OPEN.AI_API_KEY")

def process_csv(file_name):
    monthly_data = defaultdict(lambda: {'products_purchased': 0, 'total_amount': 0})
    with open(file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            invoice_date = datetime.strptime(row['invoice_date'], '%d/%m/%Y')
            month = invoice_date.strftime('%B')
            qty = int(row['qty'])
            amount = float(row['amount'])

            monthly_data[month]['products_purchased'] += qty
            monthly_data[month]['total_amount'] += amount

    return monthly_data

def generate_json_output(monthly_data):
    output = []

    for month, data in monthly_data.items():
        output.append({
            'month': month,
            'products_purchased': data['products_purchased'],
            'total_amount': data['total_amount'],
        })

    return json.dumps(output, indent=2)

def generate_insights(monthly_data):
    
    prompt = "Generate insights for the following monthly sales data:\n\n"

    for month, data in monthly_data.items():
        prompt += f"{month}: Products purchased: {data['products_purchased']}, Total amount: ${data['total_amount']}\n"

    prompt += "\nInsights:"

    response = completion_with_backoff(
        engine="gpt-3.5-turbo",
        prompt=prompt,
        temperature=0.5,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    generated_text = response.choices[0].text.strip()
    return generated_text




csv_file = "invoices.csv"
monthly_data = process_csv(csv_file)
json_output = generate_json_output(monthly_data)
print(json_output)

# Add this line after generating the JSON output
insights = generate_insights(monthly_data)
print("\nGenerated Insights:")
print(insights)


