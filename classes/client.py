import os
import time
import seal
import json
import numpy as np
import random
import urllib3
import requests

from faker import Faker
from classes.query import Query
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Client:
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

        if not os.path.exists("public_key.bin") and not os.path.exists(
            "secret_key.bin"
        ):
            public_key = keygen.create_public_key()
            secret_key = keygen.secret_key()

            # Save keys to file
            public_key.save("public_key.bin")
            secret_key.save("secret_key.bin")
        else:
            # Load keys from file
            public_key = seal.PublicKey()
            secret_key = seal.SecretKey()
            public_key.load(self.context, "public_key.bin")
            secret_key.load(self.context, "secret_key.bin")

        self.encryptor = seal.Encryptor(self.context, public_key)
        self.decryptor = seal.Decryptor(self.context, secret_key)

        self.aes_key = b"4dd2498fcf9fd261614c9c608b8715c5"
        self.aes_nonce = b"x\x85\xa5\xd3\x19-\xd8CH\xb4Gck\x05\x99o"

        self.generate_random()

    def generate_random(self) -> None:
        """
        This function generates a random dataset. The dataset consist of the following:
        - Random name
        - Random age
        - Random gender
        - List of a random size consisting of random medicines
        - List of side effects that would most probably be caused by the medicines

        The list of side effects is generated based on randomly generated correlation
        matrix. This ensures that there is some order in the data.

        E.g. medicine 1 has a higher chance to cause side effect 3 than others, etc.

        This is achieved by aforementioined correlation matrix and multinomial distribution
        of the probabilities.
        """

        if not os.path.exists("dataset.json"):
            # Parameters
            NUM_MEDICINES = 200
            NUM_SIDE_EFFECTS = 20
            NUM_ENTRIES = 1000
            MAX_PATIENT_MEDICINES = 10
            MAX_PATIENT_SIDE_EFFECTS = 5

            # List of side effects
            medicines_list = list(range(1, NUM_MEDICINES + 1))

            # List of side effects
            side_effect_list = list(range(1, NUM_SIDE_EFFECTS + 1))

            # List of genders
            genders = ["male", "female"]

            # List of treatments
            treatments = ["Stop", "Drink", "Double"]

            # Random names generator
            fake = Faker()

            # Create a matrix representing the probability of each medicine causing each side effect
            correlation_matrix = np.random.rand(NUM_MEDICINES + 1, NUM_SIDE_EFFECTS + 1)

            # Create a random nonce (IV for CTR)
            # aes_nonce = os.urandom(16)

            # AES CTR initialization
            cipher = Cipher(
                algorithms.AES(self.aes_key),
                modes.CTR(self.aes_nonce),
                backend=default_backend(),
            )

            random_dataset = []

            # Generate random dataset
            for _ in range(NUM_ENTRIES):
                name = fake.name()

                # AES CTR encryption for 'name'
                encryptor = cipher.encryptor()
                name_encrypted = encryptor.update(name.encode()) + encryptor.finalize()

                age = random.randint(1, 99)
                gender = random.choice(genders)

                # FHE encryption for age and gender (m)
                encrypted_m = self.prepare_m(gender, age).to_string().hex()

                ######### IMPORTANT #########
                # Here we apply the above matrix for probability distribution of one medicine to cause a specific side effect

                # Generate random medicines
                medicines = random.sample(
                    medicines_list, k=random.randint(1, MAX_PATIENT_MEDICINES)
                )

                # Generate random number of side effects
                side_effect_count = random.randint(1, MAX_PATIENT_SIDE_EFFECTS)

                # Sum correlations of the generated medicines' side effects based on the correlation matrix
                side_effect_probs = np.sum(correlation_matrix[medicines], axis=0)

                # Normalize probabilities to ensure they sum to 1
                side_effect_probs /= side_effect_probs.sum()

                # Use multinomial calculations to produce indexes of side effects based on probabilities calculated in "side_effect_probs"
                side_effect_indices = np.random.multinomial(
                    side_effect_count,
                    side_effect_probs[: len(side_effect_list)],
                    size=1,
                ).nonzero()[1]

                side_effect = [side_effect_list[i] for i in side_effect_indices]

                # AES CTR encryption for 'treatment'
                encryptor_treatment = cipher.encryptor()
                treatment = f"{random.choice(treatments)} {random.choice(medicines)}"
                treatment_encrypted = (
                    encryptor_treatment.update(treatment.encode())
                    + encryptor_treatment.finalize()
                )

                entry = {
                    "name": name_encrypted.hex(),
                    "encrypted_m": encrypted_m,
                    "medicines": medicines,
                    "side_effects": side_effect,
                    "treatment": treatment_encrypted.hex(),
                }

                random_dataset.append(entry)

            test = {
                "name": "test",
                "encrypted_m": self.prepare_m("male", 40).to_string().hex(),
                "medicines": [1, 2],
                "side_effects": [1, 2],
                "treatment": treatment_encrypted.hex(),
            }

            random_dataset.append(test)

            # Save the dataset
            with open("dataset.json", "w") as f:
                f.write(json.dumps(random_dataset))
                print("[i] Wrote a fresh dataset to file: dataset.json")

    def AES_decrypt(self, encrypted_treatment_hex: str) -> str:
        """
        Simple function for AES CTR decryption.
        """

        encrypted_treatment = bytes.fromhex(encrypted_treatment_hex)

        cipher = Cipher(
            algorithms.AES(self.aes_key),
            modes.CTR(self.aes_nonce),
            backend=default_backend(),
        )

        decryptor = cipher.decryptor()
        decrypted_treatment = (
            decryptor.update(encrypted_treatment) + decryptor.finalize()
        )

        return decrypted_treatment

    def decrypt_response_result(self, result: dict) -> dict:
        """
        This function takes the result dictionary received from the server
        and decrypts the treatment information.
        """

        for res in result:
            # Decrypt AES encrypted treatment info
            res["treatment"] = self.AES_decrypt(res["treatment"]).decode()

        return result

    def prepare_m(self, gender: str, age: int) -> seal.Plaintext:
        """
        This function merges age and gender to a sigle parameter based on the reserach paper,
        then the function encrypts this parameter using FHE.
        """

        m = 0
        R = 5

        if gender == "male":
            m = age + R
        elif gender == "female":
            m = age + 128 + R

        plain_m: seal.Plaintext = seal.Plaintext(hex(m)[2::])

        # Encrypt m
        encrypted_m: seal.Ciphertext = self.encryptor.encrypt(plain_m)

        return encrypted_m

    def prepare_query(
        self, medicine: list, side_effects: list, age: int, gender: str
    ) -> Query:
        """
        This function combines encrypted m with lists of medicines and side effects
        and returns a object representing the user query.
        """

        # Encrypt m
        encrypted_m: seal.Ciphertext = self.prepare_m(gender, age)

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

        start_time = time.time()

        for result in results:
            # Deserialize ciphertext
            entry = self.context.from_cipher_str(bytes.fromhex(result))

            # Decrypt and decode ciphertext
            decoded = self.encoder.decode(self.decryptor.decrypt(entry))[0]

            if decoded == 0:
                index: int = results.index(result)

                print(f"[+] Entry found on index {index}")

                indexes.append(index)
                hit = True

        if not hit:
            print("[x] Entry not found")
            exit(1)

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"[i] FHE results decryption completed after: {elapsed_time:.2f} seconds")

        data: str = json.dumps(indexes)
        response: requests.Response = requests.get(
            endpoint + "?indexes=" + data, verify=False
        )

        # Load the response as dicitonary, decrypt, then prepare for pretty print to the console
        result = json.loads(response.text)
        result = self.decrypt_response_result(result)

        result_pretty = json.dumps(result, indent=4)

        return result_pretty
