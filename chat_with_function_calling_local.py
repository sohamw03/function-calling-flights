import sys, json, os
import http.client
from dotenv import load_dotenv
from langchain_community.llms import HuggingFaceEndpoint
from langchain_community.chat_models.huggingface import ChatHuggingFace
from langchain_core.messages import HumanMessage, SystemMessage
from transformers import BitsAndBytesConfig

load_dotenv()

DEBUG = True


# Logger
def log(context, message):
    if DEBUG:
        print(f"\n[LOG:{context}] {message}\n")


quantization_config = {
    "load_in_4bit": True,
    "bnb_4bit_quant_type": "nf4",
    "bnb_4bit_compute_dtype": "float16",
    "bnb_4bit_use_double_quant": True,
}
llm = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    task="text-generation",
    max_new_tokens=1024,
    do_sample=False,
    repetition_penalty=1.03,
    model_kwargs={"quantization_config": quantization_config},
)
json_llm = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    task="text-generation",
    max_new_tokens=1024,
    do_sample=False,
    repetition_penalty=1.03,
    model_kwargs={
        "quantization_config": quantization_config,
        "response_format": {"type": "json_object"},
    },
)

chat_model = ChatHuggingFace(llm=llm)
json_model = ChatHuggingFace(llm=json_llm)


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

    # Use local model to parse the user input and extract parameters
    response = json_model.invoke(
        [
            SystemMessage(
                content="You are a helpful travel planning assistant. Respond in strictly JSON format."
            ),
            HumanMessage(
                content="""Extract travel query parameters from the following input in this json format 
                {'fromEntityId': 'BOM'(mumbai) | 'DEL'(delhi) | 'PNQ'(pune) | 'BLR'(bengaluru) | 'MAA'(chennai), 'toEntityId': 'BOM'(mumbai) | 'DEL'(delhi) | 'PNQ'(pune) | 'BLR'(bengaluru) | 'MAA'(chennai), 'departDate': 'YYYY-MM-DD', 'wholeMonthDepart': 'YYYY-MM' #if departDate is absent, 'locale': '', 'currency': 'INR'}: 
                """
                + str(task)
            ),
        ]
    )

    params = response.content.strip()

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

    # Summarize the JSON output using local model
    summary_response = chat_model.invoke(
        [
            SystemMessage(content="You are a helpful travel planning assistant."),
            HumanMessage(
                content=f"Summarize the following JSON output and present the flights to the user in a conversational format in 3 to 4 lines: \n{result}"
            ),
        ]
    )

    summary = summary_response.content.strip()

    # Print the summarized output
    print("|> ", end="")
    print(summary)


if __name__ == "__main__":
    os.system("cls")
    print("|> ", end="")
    print("Hello. I am a travel planning assistant. How can I help you today?")
    while True:
        chat()
