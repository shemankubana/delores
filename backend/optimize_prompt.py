import sys
import os
from backend.evaluation.evaluate import evaluate_metrics, f1_score
from backend.rag import RAGPipeline
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CANDIDATE_PROMPTS = [
    """You are Delores, a helpful assistant for Irembo services.
Answer the question based ONLY on the context below.
If the answer is not in the context, say "I don't know."
Context: {context}
Question: {question}
Answer:""",

    """You are an expert Irembo support agent. 
Analyze the provided context carefully and answer the user's question accurately.
Use valid information from the context. Do not halluncinate.
Context:
{context}
Question: {question}
Answer:""",

    """Role: Irembo Assistant.
Task: Answer the query using the retrieved documents.
Verification: If the answer is not found, state "I cannot find this information".
Context:
{context}
Query: {question}
Response:"""
]

def optimize_prompt():
    print("🚀 Starting Prompt Optimization (RL-style)...")
    dataset_path = os.path.join(os.path.dirname(__file__), "evaluation", "golden_dataset.json")
    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    rag = RAGPipeline()
    rag.load_vector_store()
    
    best_score = -1
    best_prompt = None
    
    for i, prompt_template in enumerate(CANDIDATE_PROMPTS):
        print(f"\n🧪 Testing Prompt Candidate {i+1}...")
        total_f1 = 0
        
        # Monkey patch the prompt construction in RAG (conceptually)
        # Since we can't easily change the method code, we'll implement a custom answer loop here
        # or we would need to make RAGPipeline accept a prompt_template
        
        for example in dataset:
            query = example["query"]
            ground_truth = example["ground_truth"]
            
            # Retrieve
            docs = rag.retrieve(query)
            context = "\n\n".join([d.page_content for d in docs])[:6000]
            
            # Format Prompt
            full_prompt = prompt_template.format(context=context, question=query)
            
            # Generate
            from backend.local_model import local_models
            prediction = local_models.generate_response(full_prompt)
            
            score = f1_score(prediction, ground_truth)
            total_f1 += score
            
        avg_f1 = total_f1 / len(dataset)
        print(f"   📊 Average F1: {avg_f1:.4f}")
        
        if avg_f1 > best_score:
            best_score = avg_f1
            best_prompt = prompt_template
            
    print(f"\n🏆 Best Prompt Found (Score: {best_score:.4f}):")
    print(best_prompt)
    print("\n✅ You should update your RAGPipeline to use this prompt.")

if __name__ == "__main__":
    optimize_prompt()
