import json
import argparse
import sys

def normalize_std(std_string):
    return str(std_string).replace(" ", "").lower()

def evaluate_results(results_file):
    try:
        with open(results_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading results file: {e}"); sys.exit(1)

    total_queries = len(data)
    if total_queries == 0:
        print("No queries found."); return

    hits_at_3 = 0; mrr_sum_at_5 = 0.0; total_latency = 0.0

    for item in data:
        expected = set(normalize_std(s) for s in item.get("expected_standards", []))
        retrieved = [normalize_std(s) for s in item.get("retrieved_standards", [])]
        total_latency += item.get("latency_seconds", 0.0)
        if any(s in expected for s in retrieved[:3]):
            hits_at_3 += 1
        for rank, s in enumerate(retrieved[:5], 1):
            if s in expected:
                mrr_sum_at_5 += 1.0/rank; break

    print("=" * 40)
    print("   BIS HACKATHON EVALUATION RESULTS")
    print("=" * 40)
    print(f"Total Queries Evaluated : {total_queries}")
    print(f"Hit Rate @3             : {hits_at_3/total_queries*100:.2f}% \t(Target: >80%)")
    print(f"MRR @5                  : {mrr_sum_at_5/total_queries:.4f} \t(Target: >0.7)")
    print(f"Avg Latency             : {total_latency/total_queries:.2f} sec \t(Target: <5 seconds)")
    print("=" * 40)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--results", required=True)
    evaluate_results(p.parse_args().results)
