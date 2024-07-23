from dotenv import load_dotenv
import requests
import sys, os
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.globals import set_debug

load_dotenv()
DEBUG = False


# Function to query the Skyscanner API
@tool
def one_way_flight(
    fromEntityId, toEntityId=None, departDate=None, wholeMonthDepart=None
) -> str:
    """
    Queries the API for one-way flights.

    Parameters:
    - 'fromEntityId'*: 'BOM'(mumbai) | 'DEL'(delhi) | 'PNQ'(pune) | 'BLR'(bengaluru) | 'MAA'(chennai) | 'CCU'(kolkata) | 'HYD'(hyderabad) | 'ATQ'(amritsar) | 'SLV'(shimla) | 'PAT'(patna),
    - 'toEntityId': 'BOM'(mumbai) | 'DEL'(delhi) | 'PNQ'(pune) | 'BLR'(bengaluru) | 'MAA'(chennai) | 'CCU'(kolkata) | 'HYD'(hyderabad) | 'ATQ'(amritsar) | 'SLV'(shimla) | 'PAT'(patna),
    - 'departDate': 'YYYY-MM-DD',
    - 'wholeMonthDepart': 'YYYY-MM'(Only if departDate is absent),

    Returns:
    str: A string of the flight search results.
    """
    url = "https://sky-scanner3.p.rapidapi.com/flights/search-one-way"
    headers = {
        "x-rapidapi-key": f"{os.getenv('SKY_SCANNER_API_KEY')}",
        "x-rapidapi-host": "sky-scanner3.p.rapidapi.com",
    }
    querystring = {
        "fromEntityId": fromEntityId,
        "toEntityId": toEntityId,
        "departDate": departDate,
        "wholeMonthDepart": wholeMonthDepart,
        "market": "IN",
        "locale": "en-GB",
        "currency": "INR",
    }
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code != 200:
        return f"Error: {response.json()}"
    response_dict = response.json()
    flight_info = []

    for itinerary in response_dict["data"]["itineraries"]:
        for leg in itinerary["legs"]:
            flight_details = {
                "id": itinerary["id"],
                "price": itinerary["price"]["formatted"],
                "origin": leg["origin"]["name"],
                "destination": leg["destination"]["name"],
                "duration": leg["durationInMinutes"],
                "departure": leg["departure"],
                "arrival": leg["arrival"],
                "carrier": leg["carriers"]["marketing"][0]["name"],
                "flight_number": leg["segments"][0]["flightNumber"],
            }
            flight_info.append(flight_details)
    return str(flight_info)


tools = [one_way_flight]

# ---------------------------- Chat ----------------------------

set_debug(DEBUG)
llm = ChatOpenAI(model="gpt-4-turbo")
llm_with_tools = llm.bind_tools(tools)

from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage

messages = [
    SystemMessage(
        """You are a helpful, cheerful, conversational flight booking chatbot. Conversationally collect the following information from the user:
        From location*, To location, Departure date, Which month the user wants (if departure date is absent).
        Before calling one_way_flight tool, confirm the search parameters with the user."""
    ),
]

if __name__ == "__main__":
    # Start chat loop
    os.system("cls")
    while True:
        query = input(">> ")
        if query.lower() == "exit":
            break

        messages.append(HumanMessage(content=query))
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)

        result = ai_msg
        if ai_msg.tool_calls and len(ai_msg.tool_calls) > 0:
            for tool_call in ai_msg.tool_calls:
                selected_tool = {"one_way_flight": one_way_flight}[
                    tool_call["name"].lower()
                ]
                tool_msg = selected_tool.invoke(tool_call)
                tool_msg.content = f"Summarize the following JSON output and present the flights to the user in a conversational format in 3 to 4 lines: \n{tool_msg.content}"
                messages.append(tool_msg)
            result = llm_with_tools.invoke(messages)

        print(f"|> {result.content}\n")
