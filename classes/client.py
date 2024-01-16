import seal
import json
import urllib3
import requests

from classes.query import Query

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Client():
    def __init__(self) -> None:
        # initialize BFV scheme parameters
        params = seal.EncryptionParameters(seal.scheme_type.bfv)

        poly_modulus_degree = 4096
        params.set_poly_modulus_degree(poly_modulus_degree)
        params.set_coeff_modulus(seal.CoeffModulus.BFVDefault(poly_modulus_degree))
        params.set_plain_modulus(seal.PlainModulus.Batching(poly_modulus_degree, 20))

        self.context = seal.SEALContext(params)

        # initilize encoder that is used for encoding list of ints to `seal.Plaintext` and then decoding vice versa
        self.encoder = seal.BatchEncoder(self.context)

        # initialize encryptor and decryptors with keys
        keygen = seal.KeyGenerator(self.context)

        self.encryptor = seal.Encryptor(self.context, keygen.create_public_key())
        self.decryptor = seal.Decryptor(self.context, keygen.secret_key())


    def prepare_query(self, medicine: list, side_effects: list, age: int, gender: str) -> Query:
        """
        This function merges age and gender to a sigle parameter based on the reserach paper.
        Then the function encrypts this parameter using FHE, combines it with lists of
        medicines and side effects and returns a object representing the user query.
        """

        m = 0
        R = 5

        if gender == 'male':
            m = age + R
        elif gender == 'female':
            m = age + 128 + R

        plain_m: seal.Plaintext = seal.Plaintext(hex(m)[2::])
        
        # Encrypt m
        encrypted_m: seal.Ciphertext = self.encryptor.encrypt(plain_m)

        return Query(medicine, side_effects, encrypted_m.to_string().hex())
        

    def search(self, endpoint: str, data: str) -> str:
        """
        This is the main search function for the client. This function communicates with
        the query endpoint and sends the query. After getting a response from the server
        functions iterates over the array representing the results of FHE subtraction on
        server side and checks which entry is 0.

        If the entry in the restul array is equal to zero, that means that there is
        a match in the database data on the zero element's index.

        Then function requests data from the query endpoint based on the indexes found
        in the previous steps.
        """

        response: requests.Response = requests.post(endpoint, data=data, verify=False)
        
        results: list = json.loads(response.text)

        hit: bool = False
        indexes: list = []

        for result in results:
            # Deserialize ciphertext
            entry = self.context.from_cipher_str(bytes.fromhex(result))
            
            # decrypt and decode ciphertext
            decoded = self.encoder.decode(self.decryptor.decrypt(entry))[0]
            
            if decoded == 0:
                index: int = results.index(result)

                print(f"[+] Entry found on index {index}")
                
                indexes.append(index)
                hit = True
                
        if not hit:
            print("[x] Entry not found")
            exit(1)

        data: str = json.dumps(indexes)
        response: requests.Response = requests.get(endpoint +  '?indexes=' + data, verify=False)

        # Load the response as dicitonary, then prepare for pretty print to the console
        result = json.loads(response.text)
        result_pretty = json.dumps(result, indent=4)
        
        return result_pretty
