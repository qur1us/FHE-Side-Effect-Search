import seal
import requests

from query import Query

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

        plain_m: seal.Plaintext = seal.Plaintext(m)
        
        # Encrypt m
        encrypted_m: seal.Ciphertext = self.encryptor.encrypt(plain_m)

        return Query(medicine, side_effects, encrypted_m.to_string().hex())
        

    def search(self, endpoint: str, data: str):
        response: requests.Response = requests.post(endpoint, data=data)
        
        # Deserialize ciphertext
        #cipher = self.context.from_cipher_str(bytes.fromhex(response.decode()))

        # decrypt and decode ciphertext
        #decoded = self.encoder.decode(self.decryptor.decrypt(cipher))