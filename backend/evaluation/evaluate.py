import json
import os
import sys
import collections

# Add parent directory to path to allow importing backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.rag import RAGPipeline

def normalize_text(text):
    """Lower text and remove punctuation, articles and extra whitespace."""
    import string
    import re

    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(text))))

def f1_score(prediction, ground_truth):
    prediction_tokens = normalize_text(prediction).split()
    ground_truth_tokens = normalize_text(ground_truth).split()
    common = collections.Counter(prediction_tokens) & collections.Counter(ground_truth_tokens)
    num_same = sum(common.values())
    
    if num_same == 0:
        return 0
    
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1

def evaluate_metrics():
    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    if not os.path.exists(dataset_path):
        print(f"❌ Error: Dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    print("🚀 Initializing RAG pipeline...")
    rag = RAGPipeline()
    rag.load_vector_store()

    print(f"\n📊 Starting Evaluation on {len(dataset)} examples...\n")
    
    total_f1 = 0
    total_source_match = 0
    
    for i, example in enumerate(dataset):
        query = example["query"]
        ground_truth = example["ground_truth"]
        expected_url = example.get("expected_source_url")
        
        print(f"🔹 Test {i+1}: {query}")
        
        # Run Inference
        result = rag.answer_query(query)
        prediction = result["response"]
        sources = result["sources"]
        
        # Calculate F1
        score = f1_score(prediction, ground_truth)
        total_f1 += score
        
        # Check Source
        retrieved_urls = [s["url"] for s in sources]
        source_hit = expected_url in retrieved_urls if expected_url else False
        if source_hit:
            total_source_match += 1
            
        print(f"   Prediction: {prediction[:100]}...")
        print(f"   F1 Score: {score:.4f}")
        print(f"   Source Match: {'✅' if source_hit else '❌'}")
        print("-" * 30)

    avg_f1 = total_f1 / len(dataset)
    avg_source_acc = (total_source_match / len(dataset)) * 100
    
    print("\n📈 Final Results:")
    print(f"   Average F1 Score: {avg_f1:.4f}")
    print(f"   Retrieval Accuracy: {avg_source_acc:.2f}%")

if __name__ == "__main__":
    evaluate_metrics()
