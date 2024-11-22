import sys, json, os
import http.client
from dotenv import load_dotenv
from langchain_community.llms.ollama import OllamaLLM
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# Set
DEBUG = True

# Logger
def log(context, message):
    if DEBUG:
        print(f"\n[LOG:{context}] {message}\n")

# Define the function schema
# Define the function schema
tools = [{
    "type": "function",
    "function": {
        "name": "search_flights",
        "description": "Search for flights between cities",
        "parameters": {
            "type": "object",
            "properties": {
                "fromEntityId": {
                    "type": "string",
                    "enum": ["BOM", "DEL", "PNQ", "BLR", "MAA"],
                    "description": "Airport code for departure city"
                },
                "toEntityId": {
                    "type": "string",
                    "enum": ["BOM", "DEL", "PNQ", "BLR", "MAA"],
                    "description": "Airport code for arrival city"
                },
                "departDate": {
                    "type": "string",
                    "format": "date",
                    "description": "Departure date in YYYY-MM-DD format"
                },
                "wholeMonthDepart": {
                    "type": "string",
                    "format": "yyyy-mm",
                    "description": "Month for departure in YYYY-MM format"
                }
            },
            "required": ["fromEntityId", "toEntityId"]
        }
    }
}]

# Initialize Ollama with proper configuration
llm = OllamaLLM(
    model="llama3.2:3b",
    temperature=0,
    repeat_penalty=1.03, format="json", stop=["</tool_calls>", "</invoke>"],
)

def get_completion(messages):
    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    response = llm.invoke(
        prompt,
    )
    return response

# Function to print the introductory message and read user's input
def intro():
    user_input = input(">> ")
    if user_input.lower() == "exit":
        os.system("cls")
        sys.exit()
    return user_input

# Function to query the Skyscanner API
def query(
    fromEntityId,
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
        "toEntityId": toEntityId, "departDate": departDate,
        "wholeMonthDepart": wholeMonthDepart, "market": market,
        "locale": locale, "currency": currency,
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
    # Use tool calling to extract parameters
    messages = [
        {"role": "system", "content": "You are a helpful travel planning assistant. Use the search_flights function to help users find flights. Always respond with a tool call."},
        {"role": "user", "content": task}
    ]

    response = get_completion(messages)

    log("MODEL_OUT", response) # response = { "search_flights": "mumbai,IN,DEL,IN,27-Nov-2024" }

    try:
        tool_call = response
        if "search_flights" in tool_call:
            params = tool_call["search_flights"]
            params_dict = dict([param.split(",") for param in params.split(",")])
        tool_calls = response_dict.get('tool_calls', [])

        if tool_calls and tool_calls[0]['function']['name'] == 'search_flights':
            params_dict = json.loads(tool_calls[0]['function']['arguments'])
            params_dict.update({"locale": "", "currency": "INR"})
            log("FUNCTION_CALL", params_dict)
        else:
            raise ValueError("No valid tool call found")
    except Exception as e:
        print("|> Sorry, I couldn't understand your request. Please provide more details.")
        log("ERROR", str(e))
        return
# Call the Skyscanner API with extracted parameters
    # Call the Skyscanner API with extracted parameters
    result = query(**params_dict)
    log("API_OUT", result[:800])

    # Summarize the JSON output
    summary_messages = [
        {"role": "system", "content": "You are a helpful travel planning assistant."},
        {"role": "user", "content": f"Summarize the following JSON output and present the flights to the user in a conversational format in 3 to 4 lines: \n{result}"}
    ]

    summary_response = get_completion(summary_messages)
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
