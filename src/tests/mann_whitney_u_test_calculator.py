from scipy.stats import mannwhitneyu

model1 = "EfficientNetB0"
model2 = "ResNet50"
performances1 = [0.9221,0.9286,0.9286,0.9221,0.9221,0.9156,0.9221,0.9221,0.9286,0.9286,0.9091,0.9286,0.9286,0.9221,0.9221]
performances2 = [0.9156,0.9156,0.9026,0.8896,0.8831,0.8961,0.8831,0.8896,0.8831,0.8831,0.8831,0.9156,0.8961,0.8896,0.8896]

performances_dict_1 = {f"{model1}_seed_{i+1}": performances1[i] for i in range(len(performances1))}
performances_dict_2 = {f"{model2}_seed_{i+1}": performances2[i] for i in range(len(performances2))}

combined_performances = {**performances_dict_1, **performances_dict_2}
print(combined_performances)

stat, p_value = mannwhitneyu(performances1, performances2, alternative='two-sided')
print(f"\nMann-Whitney U Test: {model1} vs {model2}")
print(f"U-statistic: {stat}")
print(f"p-value: {p_value}")
print(f"Significant difference (p < 0.05): {p_value < 0.05}")