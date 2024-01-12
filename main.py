import seal
from client import Client

def main():
    client: Client = Client()

    # Test data
    medicine = [1, 2]
    side_effects = [2]
    age = 40
    gender = "male"

    query = client.prepare_query(medicine, side_effects, age, gender)

    print(f"Medicine IDs: {medicine}")
    print(f"Side effect IDs: {side_effects}")
    print(f"Age: {age}")
    print(f"Gender: {gender}")

    #client.test(query)


    client.search("http://127.0.0.1:8000/query", query.serialize())

if __name__ == '__main__':
    main()