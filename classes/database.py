import time
import json
import seal
import random

from classes.query import Query


class Database:
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

    def load_dataset(self) -> None:
        print("[i] Loading dataset from a file: dataset.json")

        # Load dataset from file
        with open("dataset.json", "r") as f:
            content = "".join(f.readlines())
            self.random_dataset = json.loads(content)

    def optimize_dataset(self, query) -> None:
        """
        This function takes the user supplied query and uses non-FHE parameters
        (list of medicines and side effects) to filter the randomly generated dataset.
        This enusres that the exhaustive FHE operations are performed on a smaller
        sample lowering computing and memory complexity.
        """

        # Check if there is at least on medicine and side effect in the optimized dataset
        for entry in self.random_dataset:
            if any(medicine in entry["medicines"] for medicine in query.medicines):
                if any(
                    effect in entry["side_effects"] for effect in query.side_effects
                ):
                    self.optimized_dataset.append(entry)

    def FHE_difference(self, query: Query, entry: dict) -> seal.Ciphertext:
        """
        This function performs the FHE subtraction on the user supplied ciphertext in the query.
        More precisely, the function subtracts encrypted 'm' parameter from a database entry
        from the user supplied ciphertext effectively calculating difference between two
        ciphertexts.
        """

        query_m = self.context.from_cipher_str(bytes.fromhex(query.encrypted_m))
        entry_m = self.context.from_cipher_str(bytes.fromhex(entry["encrypted_m"]))

        diff = self.evaluator.sub(query_m, entry_m)

        # Multiply difference by random number
        r = self.encoder.encode([random.randint(1, 10000) for _ in range(256)])
        result = self.evaluator.multiply_plain(diff, r)

        return result

    def search(self, query: Query) -> list[str]:
        """
        This is the main search function. Function takes the user supplied query and returns
        an array of ouputs of FHE opereations. These outputs represent whether to query
        actually got a result back on a specific index (computed on the client side).
        """

        self.optimize_dataset(query)

        results = []

        start_time = time.time()

        for entry in self.optimized_dataset:
            result: seal.Ciphertext = self.FHE_difference(query, entry)
            results.append(result.to_string().hex())

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"[i] FHE subtraction completed after: {elapsed_time:.2f} seconds")

        return results

    def get_data(self, indexes: list) -> str:
        """
        This function serves to retrieve data from the optimized dataset based on
        user supplied indexes (results from FHE operations on client side).
        """

        result: list[dict] = []

        # Filter keys so no personal info is disclosed
        for index in indexes:
            filtered_entry = {
                key: value
                for key, value in self.optimized_dataset[index].items()
                if key not in ["name", "encrypted_m"]
            }
            result.append(filtered_entry)

        return json.dumps(result)
