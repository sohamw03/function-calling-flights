"""
Flight details API call
"""

import requests, json


def api_call():
    url = "https://sky-scanner3.p.rapidapi.com/flights/detail"

    querystring = {
        "token": "eyJhIjoxLCJjIjowLCJpIjowLCJjYyI6ImVjb25vbXkiLCJvIjoiQk9NIiwiZCI6IkRFTCIsImQxIjoiMjAyNC0wNy0xNyJ9",
        "itineraryId": "10075-2407172250--31435-0-10957-2407180100",
        "currency": "INR",
    }

    headers = {
        "x-rapidapi-key": "e48700ec66msh64ffb64e65d53a8p1d5a13jsn0f5339744b26",
        "x-rapidapi-host": "sky-scanner3.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring)
    json_str_response = json.dumps(response.json())

    return str(json_str_response)


if __name__ == "__main__":
    with open("flight_details_output.json", "w") as file:
        file.write(api_call())
