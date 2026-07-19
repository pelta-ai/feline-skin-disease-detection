from scipy.stats import wilcoxon

model1 = "MobileNetV3-Small Frozen"
model2 = "MobileNetV3-Small Partially Fine-Tuned"
performances1 = [0.9177,0.9209,0.9214,0.9146,0.9098,0.9074,0.9133,0.9125,0.9228,0.9202,0.8967,0.9233,0.9201,0.9148,0.9117]
performances2 = [0.9118,0.9024,0.9047,0.9062,0.8997,0.9055,0.9225,0.9225,0.9224,0.9119,0.9092,0.9063,0.9141,0.9080,0.8981]

performances_dict_1 = {f"{model1}_seed_{i+1}": performances1[i] for i in range(len(performances1))}
performances_dict_2 = {f"{model2}_seed_{i+1}": performances2[i] for i in range(len(performances2))}

combined_performances = {**performances_dict_1, **performances_dict_2}
print(combined_performances)

stat, p_value = wilcoxon(performances1, performances2, alternative='two-sided')
print(f"\nWilcoxon Signed-Rank Test: {model1} vs {model2}")
print(f"W-statistic: {stat}")
print(f"p-value: {p_value}")
print(f"Significant difference (p < 0.05): {p_value < 0.05}")
