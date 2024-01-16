# FHE-Side-Effect-Search

This is a project for my Modern Cryptography course at Brno University of Technology. The main goal of the project is to demonstrate a privacy preserving database query system. The project utilizes homomorphic encryption to query data from a database based on sensitive patient information without revealing it to the server that holds the database.

## Table of contents

[Usage](#usage)<br>

1\. [Analysis](#analysis)<br>
&emsp;1\.1 [How does it work](#11-how-does-it-work)<br>
&emsp;1\.2 [Performance analysis](#12-performance-analysis)<br>
&emsp;&emsp;1\.2\.1 [Conclusion](#121-conclusion)<br>
2\. [Observations](#2-observations)<br>

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

# 1. Analysis

## 1.1 How does it work

Before we begin with analyzing and benchmarking, it's important to identify the parameters that enter the system. In this case we are dealing with these parameters:
- Number of entries in a database
- Number of medicines a patient takes
- Number of side effects that a patient suffers from
- Patient's age
- Patient's gender

The main goal of this analysis is to determine which parameters have direct or indirect impact on the FHE calculations. First, let's talk about what happens before we even start any cryptographic operations on the server side.

The very first thing that happens is that the client side application creates a query object from the user supplied data. This query consist of the aforementioned parameters except number of entries in the database. The patient's age and gender are combined into a single parameter $M$ as suggested by the article, which is then encrypted using FHE. This query is then transferred to the server using HTTPS. Please notice, that the only parameters that are encrypted are age and gender ($M$). The final query looks like the following.

```python
{
	"medicines": self.medicines,       # List
	"side_effects": self.side_effects, # List
	"encrypted_m": self.encrypted_m    # String
}
```

When the query arrives at the server side, the very first step is to optimize the dataset (randomly generated) using the non-FHE parameters. This step is very important since it will significantly speed up the whole process. Snippet of code responsible for dataset optimization can be seen below.

```python
for entry in self.random_dataset:
	if any(medicine in entry['medicine'] for medicine in query.medicine):
	    if any(effect in entry['side_effects'] for effect in query.side_effects):
	        self.optimized_dataset.append(entry)
```

Basically, what happens here is we take the lists of medicines and side effects and we try to find at least one element from each list that corresponds with at least one element in the dataset. After this step we are left with only relevant dataset entries upon which we will perform some FHE calculations in later steps.

After the dataset optimization we can start to perform the some FHE calculations. First we have to prepare the age and gender parameters from dataset entries to a desired format. After the age and gender parameters are combined into a single parameter $M_{e}$, we can perform FHE subtraction from user supplied $M_q$. We do this operation on each entry in the optimized dataset and construct a list of these results. This list is then sent back to the client for decryption.

When the client receives the aforementioned list of subtraction results, the individual values are decrypted and plaintexts observed. If there is a match in the dataset, then a particular element in the list will be of a value zero. Client iterates over the list and looks for elements that yield zero after decryption. Each zero then provides an index on which the desired entry is stored. Client can then use these indexes to query specific entries from the database.

## 1.2 Performance analysis

To test the performance, we can play with the system parameters to determine which may or may not have an influence on the overall system's and FHE computation's performance. Let's introduce the stock parameters.

| Total entries | Number of medicines | Number of side effects |
| ---- | ---- | ---- |
| 10000 | 200 | 20 |

By running the program we can observe these results:

| FHE subtraction | FHE decryption | Total time of execution |
| ---- | ---- | ---- |
| 1.93s | 1.83s | 4.03s |

If we keep the number of total entries and adjust the number of possible medicines and side effects we can observe the following:

| Total entries | Number of medicines | Number of side effects |
| ---- | ---- | ---- |
| 10000 | 20 | 10 |

This results in significant **increase** of time required to perform the calculations.

| FHE subtraction | FHE decryption | Total time of execution |
| ---- | ---- | ---- |
| 23.34s | 21.70s | 50.24s |

If we do the opposite and increase both numbers of possible medicines and side effects we get get the following results:

| Total entries | Number of medicines | Number of side effects |
| ---- | ---- | ---- |
| 10000 | 2000 | 1000 |

This results in significant **decrease** of time required to perform the calculations.

| FHE subtraction | FHE decryption | Total time of execution |
| ---- | ---- | ---- |
| 0.12s | 0.16s | 0.34s |

### 1.2.1 Conclusion

What we did, is we changed a coupe of non-FHE parameters and observed how the system would perform. We did not change any parameters, that are encrypted using FHE. To conclude, parameters that contribute to dataset optimization (number of medicines, number of side effects) have **significant** impact on the overall system's performance, mainly on number of FHE operations the program has to perform.

# 2. Observations

From the above description of how the program works and performance analysis, a couple of things can be observed, mainly the parameters that have a *direct* and *indirect* influence on the performance of the FHE calculations. Please note, that we are talking about parameters with influence on the performance of the FHE calculations, not the performance of the whole program.

The main parameter that has a *direct* influence on the performance of the FHE calculations is the size of the optimized dataset. When there are a lost of matches for the lists of medicines and side effects during the optimization phase, this still may yield a large dataset upon which the FHE calculations will be performed.

For a *indirect* influence we have to consider the number of possible medicines and side effects. Let's consider that patients can take only up to 10 medicines and can suffer from up to 5 side effects. If there is a total of 200 medicines available there is a lesser chance that we will find a match during the dataset optimization phase than if there were only total of e.g. 50 medicines available. Another parameter with a *indirect* influence is the total number of entries in the dataset which also contributes to the overall probability that there will be a match during the optimization phase which will naturally increase size of the optimized dataset.