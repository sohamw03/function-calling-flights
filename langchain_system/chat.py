from dotenv import load_dotenv
import requests
import sys, os, json
from langchain_core.tools import tool
# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.globals import set_debug

load_dotenv()
DEBUG = False


# Function to query the Skyscanner API
@tool
def one_way_flight(
    fromEntityId: str, toEntityId: str=None, departDate:str=None, wholeMonthDepart:str=None
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
    with open("response.json", "w") as f:
        json.dump(response_dict, f, indent=4)
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


tools = [one_way_flight]

# ---------------------------- Chat ----------------------------

set_debug(DEBUG)
llm = ChatGoogleGenerativeAI(
    api_key=f"{os.getenv('GEMINI_API_KEY')}",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    model="gemini-2.0-flash",
)
# llm = ChatOpenAI(
#     api_key=f"{os.getenv('OPENAI_API_KEY')}"  # Replace with your OpenAI API key
#     model="gpt-4-turbo",
# )
llm_with_tools = llm.bind_tools(tools)

from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage

messages = [
    SystemMessage(
        """You are a cheerful, conversational IndiGo flight booking chatbot. Conversationally collect the following information from the user:
        From location*, To location, Departure date, Which month the user wants (if user wants to search for the whole month).
        Before calling one_way_flight tool, confirm the search parameters with the user.
        Converse as if you are IndiGo's chatbot, user is only looking for IndiGo flights.
        Do not ask for any additional info."""
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
                selected_tool = {"one_way_flight": one_way_flight}[ tool_call["name"].lower() ]
                tool_msg = selected_tool.invoke(tool_call)
                if tool_msg.content.find("'wholeMonthDepart': True") != -1:
                    tool_msg.content = f"Summarize the following JSON output and present the flights quotes to the user in a conversational format in a concise way, ask the user to choose the date: \n{tool_msg.content}"
                else:
                    tool_msg.content = f"Summarize the following JSON output and present the flights to the user in a conversational format in a concise way: \n{tool_msg.content}"
                messages.append(tool_msg)
            result = llm_with_tools.invoke(messages)
            messages.append(result)

        print(f"|> {result.content}\n")
