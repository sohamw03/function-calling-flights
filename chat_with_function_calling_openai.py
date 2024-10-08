import sys, json, os
import http.client
import openai
from dotenv import load_dotenv

load_dotenv()

DEBUG = True


# Function to print the introductory message and read user's input
def intro():
    user_input = input(">> ")
    if user_input.lower() == "exit":
        os.system("cls")
        sys.exit()
    return user_input


# Logger
def log(context, message):
    if DEBUG:
        print(f"\n[LOG:{context}] {message}\n")


# Function to query the Skyscanner API
def query(
    fromEntityId=None,
    toEntityId=None,
    departDate=None,
    wholeMonthDepart=None,
    market=None,
    locale=None,
    currency=None,
):
    conn = http.client.HTTPSConnection("sky-scanner3.p.rapidapi.com")
    headers = {
        "x-rapidapi-key": f"{os.getenv('SKY_SCANNER_API_KEY')}",
        "x-rapidapi-host": "sky-scanner3.p.rapidapi.com",
    }
    req = "/flights/search-one-way?"
    d = {
        "fromEntityId": fromEntityId,
        "toEntityId": toEntityId,
        "departDate": departDate,
        "wholeMonthDepart": wholeMonthDepart,
        "market": market,
        "locale": locale,
        "currency": currency,
    }
    for i in d:
        if d[i] is not None:
            req += i + "=" + str(d[i]) + "&"
    req = req[:-1]
    conn.request("GET", req, headers=headers)
    res = conn.getresponse()
    data = res.read()
    return data.decode("utf-8")


# Main chat function
def chat():
    task = intro()

    # Initialize the OpenAI GPT-4 Turbo model
    openai.api_key = (
        f"{os.getenv('OPENAI_API_KEY')}"  # Replace with your OpenAI API key
    )

    # Use GPT-4 Turbo to parse the user input and extract parameters
    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful travel planning assistant.",
            },
            {
                "role": "user",
                "content": """Extract travel query parameters from the following input in this json format
                {'fromEntityId': 'BOM'(mumbai) | 'DEL'(delhi) | 'PNQ'(pune) | 'BLR'(bengaluru) | 'MAA'(chennai), 'toEntityId': 'BOM'(mumbai) | 'DEL'(delhi) | 'PNQ'(pune) | 'BLR'(bengaluru) | 'MAA'(chennai), 'departDate': 'YYYY-MM-DD', 'wholeMonthDepart': 'YYYY-MM' #if departDate is absent, 'locale': '', 'currency': 'INR'}:
                """
                + str(task),
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=100,
    )

    params = response.choices[0].message.content.strip()

    # Assuming the response text is a valid dictionary string, use eval (or safer parsing)
    try:
        params_dict = json.loads(params)
        log("JSON_IN", params_dict)
    except:
        print("|> ", end="")
        print("Sorry, I couldn't understand your request. Please provide more details.")
        return

    # Call the Skyscanner API with extracted parameters
    result = query(**params_dict)
    log("API_OUT", result[:800])

    # Summarize the JSON output using GPT-4 Turbo
    summary_response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful travel planning assistant.",
            },
            {
                "role": "user",
                "content": f"Summarize the following JSON output and present the flights to the user in a conversational format in 3 to 4 lines: \n{result}",
            },
        ],
        max_tokens=1024,
    )

    summary = summary_response.choices[0].message.content.strip()

    # Print the summarized output
    print("|> ", end="")
    print(summary)


if __name__ == "__main__":
    os.system("cls")
    print("|> ", end="")
    print("Hello. I am a travel planning assistant. How can I help you today?")
    while True:
        chat()
