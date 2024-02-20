import time
import argparse
from classes.client import Client


def parse_args():
    parser = argparse.ArgumentParser(description="Medicine Side Effects Search")

    # Required arguments
    parser.add_argument("endpoint", help="Query system endpoint")
    parser.add_argument("--age", type=int, required=True, help="Patients's age")
    parser.add_argument(
        "--gender", choices=["male", "female"], required=True, help="Patients's gender"
    )

    # At least one value must be supplied for each list
    parser.add_argument(
        "--medicine-ids",
        required=True,
        type=lambda x: [int(i) for i in x.split(",")],
        help="Comma-separated list of medicine IDs",
    )
    parser.add_argument(
        "--side-effect-ids",
        required=True,
        type=lambda x: [int(i) for i in x.split(",")],
        help="Comma-separated list of side effect IDs",
    )
    parser.add_argument("--outfile", type=str, help="Enable output to file")

    return parser.parse_args()


def main():
    client: Client = Client()
    args = parse_args()

    endpoint = args.endpoint
    age = args.age
    gender = args.gender
    medicines = args.medicine_ids
    side_effects = args.side_effect_ids
    outfile = args.outfile

    print("\n[i] Supplied information:")
    print(f"\tAge: {age}")
    print(f"\tGender: {gender}")
    print(f"\tMedicine IDs: {medicines}")
    print(f"\tSide Effect IDs: {side_effects}")

    start_time = time.time()

    print("[*] Preparing query")
    query = client.prepare_query(medicines, side_effects, age, gender)

    print("[*] Querying the information...")
    result = client.search(endpoint, query.serialize())

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"[i] Query finished after a total of {elapsed_time:.2f} seconds")

    print("[+] Finished successfully")

    if outfile:
        with open(outfile, "w") as f:
            f.write(result)
            print(f"[*] Writing output to a file: {outfile}")
    else:
        print(f"[*] Output:\n\n{result}\n")


if __name__ == "__main__":
    main()
