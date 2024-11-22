import requests
import sys, os, json
from langchain_core.tools import tool
from langchain_ollama.chat_models import ChatOllama
from langchain.globals import set_debug
from dotenv import load_dotenv
load_dotenv()

DEBUG = True

# Logger
def log(context, message):
    if DEBUG:
        print(f"\n[LOG:{context}] {message}\n")

# Function to query the anner API
@tool
def one_way_flight(
    fromEntityId, toEntityId=None, departDate=None, wholeMonthDepart=None
) -> str:
    """
    Queries the API for one-way flights.

    Parameters:
    - 'fromEntityId' Required : 'BOM'(mumbai) | 'DEL'(delhi) | 'PNQ'(pune) | 'BLR'(bengaluru) | 'MAA'(chennai) | 'CCU'(kolkata) | 'HYD'(hyderabad) | 'ATQ'(amritsar) | 'SLV'(shimla) | 'PAT'(patna),
    - 'toEntityId': 'BOM'(mumbai) | 'DEL'(delhi) | 'PNQ'(pune) | 'BLR'(bengaluru) | 'MAA'(chennai) | 'CCU'(kolkata) | 'HYD'(hyderabad) | 'ATQ'(amritsar) | 'SLV'(shimla) | 'PAT'(patna),
    - 'departDate': 'YYYY-MM-DD',
    - 'wholeMonthDepart': 'YYYY-MM'(Use this or 'departDate' not Both),

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

    # If the user wants to search for a specific date
    if (wholeMonthDepart is None) and (departDate is not None):
        for itinerary in response_dict["data"]["itineraries"]:
            for leg in itinerary["legs"]:
                flight_details = {
                    # "id": itinerary["id"],
                    "price": itinerary["price"]["formatted"],
                    "origin": leg["origin"]["name"],
                    "destination": leg["destination"]["name"],
                    "duration": leg["durationInMinutes"],
                    "departure": leg["departure"],
                    "arrival": leg["arrival"],
                    "carrier": leg["carriers"]["marketing"][0]["name"],
                    "flight_number": leg["segments"][0]["flightNumber"],
                }
                if leg["carriers"]["marketing"][0]["name"] == "IndiGo":
                    flight_info.append(flight_details)
        return str({"flight_info": flight_info[:], "isWholeMonthDepart": False})
    # If the user wants to search for the whole month
    else:
        for flight_quote in response_dict["data"]["flightQuotes"]["results"]:
            quote_info = {
                # "id": flight_quote["id"],
                "price": flight_quote["content"]["price"],
                # "rawPrice": flight_quote["content"]["rawPrice"],
                "direct": flight_quote["content"]["direct"],
                "originAirport": flight_quote["content"]["outboundLeg"][
                    "originAirport"
                ]["name"],
                "destinationAirport": flight_quote["content"]["outboundLeg"][
                    "destinationAirport"
                ]["name"],
                "departureDate": flight_quote["content"]["outboundLeg"][
                    "localDepartureDate"
                ],
                "departureDateLabel": flight_quote["content"]["outboundLeg"][
                    "localDepartureDateLabel"
                ],
            }
            flight_info.append(quote_info)
        return str({"flight_info": flight_info[:], "isWholeMonthDepart": True})
    return ""


tools = [one_way_flight]

# ---------------------------- Chat ----------------------------

set_debug(DEBUG)
llm = ChatOllama(model="llama3.1")
llm_with_tools = llm.bind_tools(tools)

from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage

messages = [
    SystemMessage(
        """You are IndiGo's friendly flight booking chatbot. Follow these rules strictly:

1. For greetings or general questions, respond naturally WITHOUT using any tools
2. Only use the one_way_flight tool when ALL these conditions are met:
   - User has specifically asked about booking/searching flights
   - You have collected: origin city, destination city, and either a specific date or month
   - You have confirmed these details with the user

Be casual and friendly in conversation. Start by greeting and asking how you can help with flight bookings.
DO NOT call tools for general conversation."""
    ),
]

if __name__ == "__main__":
    os.system("cls")
    while True:
        query = input(">> ")
        if query.lower() == "exit":
            break

        messages.append(HumanMessage(content=query))
        result = llm_with_tools.invoke(messages)
        messages.append(result)

        # Only process tool calls if they exist and are actually needed
        if hasattr(result, 'tool_calls') and result.tool_calls:
            for tool_call in result.tool_calls:
                selected_tool = {"one_way_flight": one_way_flight}[tool_call["name"].lower()]
                tool_msg = selected_tool.invoke(tool_call)

                if "'wholeMonthDepart': True" in tool_msg.content:
                    tool_msg.content = "Present the flight quotes in a friendly way and ask user to pick a date:\n" + tool_msg.content
                else:
                    tool_msg.content = "Present the flight details in a friendly way:\n" + tool_msg.content

                messages.append(tool_msg)
            result = llm_with_tools.invoke(messages)
            messages.append(result)

        print(f"|> {result.content}\n")
