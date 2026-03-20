# LIBRARY FOR API CALLS
# AUTHOR: MARTIN RUCHTI
# CONTACT: info@martin-ruchti.com

# IMPORTS
import requests
import json

class RestAPICalls:

    ## Class functions
    def __init__(self, api_url, legacy_anon_key, x_api_key) -> None:

        # store api url for use
        self.url = api_url

        # create key pairs for header building
        # first the outer security key, starting with 'sb_publishable'
        self.lv1_key = KeySecretPair('Authorization', f"Bearer {legacy_anon_key}")
        # second, the api key 
        self.lv2_key = KeySecretPair('x-api-key', x_api_key)

        # will later be used to store session token
        self.session_token = ''

    def GETTemperatureHistory(self, history_length) -> json:
        
        # build headers
        my_headers = {self.lv1_key.key:self.lv1_key.secret, self.lv2_key.key:self.lv2_key.secret, 'most-recent': str(history_length)}

        response = requests.get(url=self.url, headers=my_headers)
            
        # check for errors
        if(response.status_code == 200):
            responseJSON = response.json()
        else:
            # TODO: check if authentication needs to be updated
            # if so, do, else throw exception
            pass

        return responseJSON
    
    def POSTTemperature(self, timestamp, temperature) -> bool:
        
        # build headers
        my_headers = {self.lv1_key.key:self.lv1_key.secret, self.lv2_key.key:self.lv2_key.secret, "Content-Type": "application/json"}
        
        payload = {"temperature": temperature, "measured_at": timestamp}

        response = requests.post(url=self.url, headers=my_headers, json=payload)
            
        # check for errors
        if(response.status_code == 200 or response.status_code == 201):
            responseBool = True
        else:
            responseBool = False
            print("Error: " + str(response))

        return responseBool

# HELPER CLASSES
class KeySecretPair:

    def __init__(self, skey, ssecret) -> None:
        self.key = skey
        self.secret = ssecret
        self.token = ""
