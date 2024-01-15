import seal
import json
import urllib3
import requests

from query import Query

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

        result = json.dumps(json.loads(response.text), indent=4)
        
        return result


    def test(self, query):
        # Deserialize ciphertext
        entry = self.context.from_cipher_str(bytes.fromhex(query.encrypted_m))
        
        # decrypt and decode ciphertext
        decoded = self.encoder.decode(self.decryptor.decrypt(entry))[0]
        
        print(f"\n{decoded}\n")
