# FHE-Side-Effect-Search
This is a project for my Modern Cryptography course at Brno University of Technology. The main goal of the project is to demonstrate a privacy preserving database query system. The project utilizes homomorphic encryption to query data from a database based on sensitive patient information without revealing it to the server that holds the database.


## Usage

```
$ python3 main.py --help 
usage: main.py [-h] --age AGE --gender {male,female} --medicine-ids MEDICINE_IDS --side-effect-ids SIDE_EFFECT_IDS
               [--outfile OUTFILE]
               endpoint

Medicine Side Effects Search

positional arguments:
  endpoint              Query system endpoint

options:
  -h, --help            show this help message and exit
  --age AGE             Patients's age
  --gender {male,female}
                        Patients's gender
  --medicine-ids MEDICINE_IDS
                        Comma-separated list of medicine IDs
  --side-effect-ids SIDE_EFFECT_IDS
                        Comma-separated list of side effect IDs
  --outfile OUTFILE     Enable output to file

```

Example:

```
$ python3 main.py https://127.0.0.1:8000/query --age 30 --gender male --medicine-ids 10,50,100,150 --side-effect-ids 10,15,18,4

[i] Supplied information:
	Age: 30
	Gender: male
	Medicine IDs: [10, 50, 100, 150]
	Side Effect IDs: [10, 15, 18, 4]
[*] Preparing query
[*] Querying the information...
[+] Entry found on index 114
[+] Entry found on index 318
[i] Query finished after 8.68 seconds
[+] Finished successfully
[*] Output:

[
    {
        "medicine": [
            100,
            53,
            4,
            10
        ],
        "side_effects": [
            1,
            4,
            9,
            20
        ],
        "treatment": "Double 100"
    },
    {
        "medicine": [
            147,
            140,
            10,
            28
        ],
        "side_effects": [
            1,
            4,
            5,
            9,
            20
        ],
        "treatment": "Stop 28"
    }
]
```