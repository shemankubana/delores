import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class LocalModelManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        logger.info("loading Local Models... This may take a while on first run.")
        
        # 1. Vision Model (BLIP)
        logger.info("   Loading Vision Model (BLIP)...")
        self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        
        # 2. Text Embedding Model
        logger.info("   Loading Embedding Model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 3. LLM (TinyLlama - Small & Fast)
        logger.info("   Loading LLM (TinyLlama)...")
        model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.llm_model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            torch_dtype=torch.float32, 
            device_map="cpu" # Force CPU to avoid MPS autocast errors on Mac
        )
        
        self.text_pipeline = pipeline(
            "text-generation", 
            model=self.llm_model, 
            tokenizer=self.tokenizer,
            max_new_tokens=256,
            temperature=0.7
        )
        
        self._initialized = True
        logger.info("✅ All Local Models Loaded Successfully.")

    def caption_image(self, image: Image):
        """Generates a text caption for a PIL Image."""
        try:
            inputs = self.blip_processor(image, return_tensors="pt")
            out = self.blip_model.generate(**inputs, max_new_tokens=50)
            caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
            return caption
        except Exception as e:
            logger.error(f"Error captioning image: {e}")
            return "Image could not be processed."

    def embed_text(self, text):
        """Generates embedding vector for text."""
        return self.embedding_model.encode(text).tolist()
    
    def generate_response(self, prompt):
        """Generates text response from LLM."""
        formatted_prompt = f"<|system|>\nYou are Delores, a helpful assistant for Irembo.<|user|>\n{prompt}<|assistant|>\n"
        outputs = self.text_pipeline(formatted_prompt)
        return outputs[0]["generated_text"].split("<|assistant|>\n")[-1].strip()

# Global instance
local_models = LocalModelManager()
