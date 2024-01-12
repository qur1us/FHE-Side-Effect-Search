import seal
from client import Client

def main():
    client: Client = Client()

    medicine = ['A', 'D']

    side_effects = [10]

    query = client.prepare_query(medicine, side_effects, 40, "male")

    # print(query.serialize())

    client.search("http://127.0.0.1:8000/", query.serialize())

if __name__ == '__main__':
    main()