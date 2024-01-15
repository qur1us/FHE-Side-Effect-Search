import numpy as np
import random
import matplotlib.pyplot as plt

# Function to generate a random dataset
def generate_random_dataset(medicines, side_effects, correlation_matrix, num_entries=100):
    MAX_PATIENT_MEDICINES = 3
    MAX_PATIENT_SIDE_EFFECTS = 3

    dataset = []

    for _ in range(num_entries):
        # Generate medicines
        medicine = random.sample(medicines, k=random.randint(1, MAX_PATIENT_MEDICINES))

        # Determine (calculate) side effects based on the correlation matrix
        side_effect_probs = np.sum(correlation_matrix[medicine], axis=0)

        # Normalize probabilities to ensure they sum to 1
        side_effect_probs /= side_effect_probs.sum()

        # Ensure that side_effects and side_effect_probs have the same size
        num_side_effects_to_choose = min(random.randint(1, MAX_PATIENT_SIDE_EFFECTS), len(side_effects))
        side_effect_indices = np.random.multinomial(num_side_effects_to_choose, side_effect_probs[:len(side_effects)], size=1).nonzero()[1]
        side_effect = [side_effects[i] for i in side_effect_indices]

        entry = {
            'Medicine': medicine,
            'SideEffects': side_effect
        }

        dataset.append(entry)

    return dataset

# Example usage
medicines = ["MedicineA", "MedicineB", "MedicineC"]
side_effects = ["SideEffect1", "SideEffect2", "SideEffect3", "SideEffect4"]

# Generate a random correlation matrix for visualization purposes
correlation_matrix = np.random.rand(len(medicines), len(side_effects))

# Visualize the correlation matrix
plt.imshow(correlation_matrix, cmap='viridis', interpolation='none', aspect='auto')
plt.colorbar()
plt.title('Correlation Matrix')
plt.xticks(range(len(side_effects)), side_effects, rotation='vertical')
plt.yticks(range(len(medicines)), medicines)
plt.show()

# Visualize normalized side effect probabilities
normalized_probs = np.sum(correlation_matrix, axis=0) / np.sum(np.sum(correlation_matrix, axis=0))
plt.bar(side_effects, normalized_probs)
plt.title('Normalized Side Effect Probabilities')
plt.show()

# Generate a random dataset
random_dataset = generate_random_dataset(medicines, side_effects, correlation_matrix, num_entries=10)

# Visualize the generated dataset
for entry in random_dataset:
    print(f"Medicine: {entry['Medicine']}, Side Effects: {entry['SideEffects']}")
