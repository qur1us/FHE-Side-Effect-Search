import json
import numpy as np
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

        self.random_dataset = []
        self.optimized_dataset = []


    def generate_random(self):
        # Parameters
        NUM_MEDICINES = 200
        NUM_SIDE_EFFECTS = 20
        NUM_ENTRIES = 10000
        MAX_PATIENT_MEDICINES = 10
        MAX_PATIENT_SIDE_EFFECTS = 5

        # List of side effects
        medicines_list = list(range(1, NUM_MEDICINES + 1))

        # List of side effects
        side_effect_list = list(range(1, NUM_SIDE_EFFECTS + 1))

        # List of genders
        genders = ['male', 'female']

        # List of actions
        actions = ['Stop', 'Drink', 'Double']

        # Random names generator
        fake = Faker()

        # Create a matrix representing the probability of each medicine causing each side effect
        correlation_matrix = np.random.rand(NUM_MEDICINES + 1, NUM_SIDE_EFFECTS + 1)
        
        # Generate random dataset
        for _ in range(NUM_ENTRIES):
            name = fake.name()
            age = random.randint(1, 99)
            gender = random.choice(genders)
            
            ######### IMPORTANT #########
            # Here we apply the above matrix for probability distribution of one medicine to cause a specific side effect

            # Generate random medicines
            medicine = random.sample(medicines_list, k=random.randint(1, MAX_PATIENT_MEDICINES))

            # Generate random number of side effects
            side_effect_count = random.randint(1, MAX_PATIENT_SIDE_EFFECTS)

            # Sum correlations of the generated medicines' side effects based on the correlation matrix
            side_effect_probs = np.sum(correlation_matrix[medicine], axis=0)

            # Normalize probabilities to ensure they sum to 1
            side_effect_probs /= side_effect_probs.sum()
            
            # Use multinomial calculations to produce indexes of side effects based on probabilities calculated in "side_effect_probs"
            side_effect_indices = np.random.multinomial(side_effect_count, side_effect_probs[:len(side_effect_list)], size=1).nonzero()[1]
            
            side_effect = [side_effect_list[i] for i in side_effect_indices]
            
            action = f"{random.choice(actions)} {random.choice(medicine)}"

            entry = {
                'name': name,
                'age': age,
                'gender': gender,
                'medicine': medicine,
                'side_effects': side_effect,
                'treatment' : action
            }
            
            self.random_dataset.append(entry)


    def optimize_dataset(self, query):
        search_medicines = query.medicine
        search_side_effects = query.side_effects

        # Check if there is at least on medicine and side effect in the optimized dataset
        for entry in self.random_dataset:
            if any(medicine in entry['medicine'] for medicine in search_medicines):
                if any(effect in entry['side_effects'] for effect in search_side_effects):
                    self.optimized_dataset.append(entry)

    
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

        self.optimize_dataset(query)

        results = []

        for entry in self.optimized_dataset:
            result: seal.Ciphertext = self.PIR_check(query, entry)
            results.append(result.to_string().hex())

        return results


    def get_data(self, indexes: list) -> str:
        result: list[dict] = []
        
        # Filter keys so no personal info is disclosed
        for index in indexes:
            filtered_entry = {key: value for key, value in self.optimized_dataset[index].items() if key not in ['name', 'age', 'gender']}
            result.append(filtered_entry)

        # Clear the optimized dataset, next query has to have a fresh instance
        self.optimized_dataset.clear()

        return json.dumps(result)
