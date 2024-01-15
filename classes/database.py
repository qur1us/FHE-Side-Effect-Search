import json
import seal
import random
from faker import Faker

from classes.query import Query

class Database():
    def __init__(self):
        # initialize BFV scheme parameters
        params = seal.EncryptionParameters(seal.scheme_type.bfv)

        poly_modulus_degree = 4096
        params.set_poly_modulus_degree(poly_modulus_degree)
        params.set_coeff_modulus(seal.CoeffModulus.BFVDefault(poly_modulus_degree))
        params.set_plain_modulus(seal.PlainModulus.Batching(poly_modulus_degree, 20))

        self.context = seal.SEALContext(params)

        # initilize encoder that is used for encoding list of ints to `seal.Plaintext` and then decoding vice versa
        self.encoder = seal.BatchEncoder(self.context)

        # initialize evaluator that is used for evaluating operations on `seal.Ciphertext`
        self.evaluator = seal.Evaluator(self.context)

        self.random_entries = []


    def generate_random(self):
        # List of side effects (1 to 5)
        medicines = list(range(1, 6))

        # List of side effects (1 to 5)
        side_effects = list(range(1, 6))

        # List of genders
        genders = ['male', 'female']

        # List of actions
        actions = ['Stop', 'Drink', 'Double']

        # Random names generator
        fake = Faker()

        for _ in range(1000):

            name = fake.name()
            age = random.randint(1, 99)
            gender = random.choice(genders)
            medicine = random.sample(medicines, k=random.randint(1, 5))
            side_effect = random.sample(side_effects, k=random.randint(1, 5))
            action = f"{random.choice(actions)} {random.choice(medicine)}"

            entry = {
                'name': name,
                'age': age,
                'gender': gender,
                'medicine': medicine,
                'side_effects': side_effect,
                'treatment' : action
            }
            self.random_entries.append(entry)

        test = {
            'name': fake.name(),
            'age': 40,
            'gender': 'male',
            'medicine': [1,4,5],
            'side_effects': [2],
            'treatment' : 'Stop 4'
        }

        self.random_entries.append(test)


    def optimize_dataset(self, query) -> list:
        search_medicines = query.medicine
        search_side_effects = query.side_effects

        # Perform search
        matching_entries = []

        for entry in self.random_entries:
            # Check if any medicine matches the search criteria
            if any(medicine in entry['medicine'] for medicine in search_medicines):
                # Check if any side effect matches the search criteria
                if any(effect in entry['side_effects'] for effect in search_side_effects):
                    matching_entries.append(entry)

        return matching_entries
    

    def prepare_PIR_data(self, gender: str, age: int) -> int:
        m = 0
        R = 5

        if gender == 'male':
            m = age + R
        elif gender == 'female':
            m = age + 128 + R
        
        return m


    def PIR_check(self, query: Query, entry: dict) -> seal.Ciphertext:
        query_m = self.context.from_cipher_str(bytes.fromhex(query.encrypted_m))

        m = self.prepare_PIR_data(entry['gender'], int(entry['age']))

        entry_m = seal.Plaintext(hex(m)[2::])
    
        diff = self.evaluator.sub_plain(query_m, entry_m)

        # Multiply difference by random number
        r = self.encoder.encode([random.randint(1, 10000) for _ in range(m)])
        result = self.evaluator.multiply_plain(diff, r)

        return result


    def search(self, query: Query):

        optimized_dataset = self.optimize_dataset(query)

        results = []

        for entry in optimized_dataset:
            result: seal.Ciphertext = self.PIR_check(query, entry)
            results.append(result.to_string().hex())

        return results


    def get_data(self, indexes: list) -> str:
        result: list[dict] = []
        
        # Filter keys so no personal info is disclosed
        for index in indexes:
            filtered_entry = {key: value for key, value in self.random_entries[index].items() if key not in ['name', 'age', 'gender']}
            result.append(filtered_entry)

        return json.dumps(result)
