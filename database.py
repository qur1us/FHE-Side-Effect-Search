import seal
import random

from query import Query

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
       # List of medicines (A to F)
        medicines = ['A', 'B', 'C', 'D', 'E', 'F']

        # List of side effects (1 to 15)
        side_effects = list(range(1, 11))

        # List of genders
        genders = ['male', 'female']

        # Create a list of 20 random entries
        random_entries = []

        for _ in range(20):
            num_side_effects = random.randint(1, 5)
            entry = {
                'medicine': random.choice(medicines),
                'side_effects': random.sample(side_effects, k=num_side_effects),
                'age': random.randint(1, 99),
                'gender': random.choice(genders)
            }
            self.random_entries.append(entry)


    def optimize_dataset(self, query) -> list:
        search_medicines = query.medicine
        search_side_effects = query.side_effects

        # Perform search
        matching_entries = []

        for entry in self.random_entries:
            for medicine in search_medicines:
                if medicine in entry['medicine']:
                    if any(effect in entry['side_effects'] for effect in search_side_effects):
                        matching_entries.append(entry)

        return matching_entries

    def search(self, query: Query):

        optimized_dataset = self.optimize_dataset(query)

        # Print the matching entries
        print("Matching Entries:")
        for i, entry in enumerate(optimized_dataset, start=1):
            print(f"Entry {i}: {entry}")