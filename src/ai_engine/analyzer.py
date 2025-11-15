from llm_reasoner import llm_reason
# Example ML outputs
prediction_text = predict_empty(level_data)
anomaly_list = detect_anomalies(level_data)   # we will add this later
stats = {
    "avg_level": np.mean([x[1] for x in level_data]),
    "min_level": min([x[1] for x in level_data]),
    "max_level": max([x[1] for x in level_data]),
    "sample_count": len(level_data)
}

# LLM reasoning
final_ai_report = llm_reason(
    prediction_text,
    anomaly_list,
    stats,
    last24h_data
)

print("=== AI Report ===")
print(final_ai_report)
