"""
Get location codes for flight search
"""

import requests, json


def api_call():
    url = "https://sky-scanner3.p.rapidapi.com/flights/auto-complete"

    querystring = {"query":"Mumbai, Delhi"}

    headers = {
      "x-rapidapi-key": "e48700ec66msh64ffb64e65d53a8p1d5a13jsn0f5339744b26",
      "x-rapidapi-host": "sky-scanner3.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    json_str_response = json.dumps(response.json(), indent=2)

    return str(json_str_response)


if __name__ == "__main__":
    with open("autocomplete_loc_codes_output.json", "w") as file:
        file.write(api_call())
