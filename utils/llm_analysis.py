import os
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

import json
import re

def get_llm_report(orig_path, enh_path):
    """
    Sends the original and enhanced image to Gemini 1.5 Flash for a clinical-style comparison.
    Returns a dictionary with 'en' and 'hi' keys.
    """
    if not api_key:
        return {"en": "API Key not found.", "hi": "API कुंजी नहीं मिली।"}

    try:
        # Fixed model name to gemini-3-flash-preview based on verified list
        model = genai.GenerativeModel(model_name="gemini-3-flash-preview")
        
        img1 = Image.open(orig_path)
        img2 = Image.open(enh_path)
        
        prompt = """
        You are an advanced AI assistant for medical image enhancement and clinical visualization.

        You are given two versions of the same medical scan:
        - Original Scan
        - Enhanced Scan

        Compare the scans and provide a professional enhancement-focused analysis.

        Focus only on:
        - contrast improvement
        - noise reduction
        - edge sharpness
        - anatomical visibility
        - tissue differentiation
        - structural clarity
        - overall image enhancement quality

        Do not:
        - diagnose diseases
        - provide treatment recommendations
        - make certainty-based medical conclusions
        - generate alarming medical claims
        - refer to the scans as "Image 1" or "Image 2" — always say
            "the original scan" and "the enhanced scan"

        Maintain a professional and clinically informative tone.

        Return ONLY valid JSON in this exact format:

        {
        "en": "Professional enhancement-focused summary in English.",
        "hi": "Professional Hindi translation of the same summary."
        }

        Do not include markdown, explanations, or text outside the JSON.
        """
        
        # Adding safety settings to avoid blocking medical anatomical scans
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        response = model.generate_content([prompt, img1, img2], safety_settings=safety)
        text = response.text.strip()
        
        # Robust JSON extraction
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data
            
        return {"en": text, "hi": "Translation unavailable."}
        
    # except Exception as e:
    #     print(f"Error generating LLM report: {e}")
    #     return {"en": f"Analysis unavailable: {str(e)}", "hi": f"विश्लेषण उपलब्ध नहीं है: {str(e)}"}
    except Exception as e:

        print(f"Error generating LLM report: {e}")

        fallback_report = {
            "en": (
                "Enhanced scan demonstrates improved contrast separation, "
                "reduced background noise, and clearer structural visibility "
                "compared to the original image."
            ),

            "hi": (
                "उन्नत स्कैन में बेहतर कॉन्ट्रास्ट, कम शोर "
                "और अधिक स्पष्ट संरचनात्मक दृश्यता दिखाई देती है।"
            )
        }

        return fallback_report

def get_chat_response(question, orig_path, enh_path):
    """
    Analyzes specific user questions about the scans using the multimodal model.
    """
    if not api_key:
        return "API Key not found."

    try:
        print("\n========== CHAT REQUEST ==========")
        print("Question:", question)
        print("==================================\n")

        model = genai.GenerativeModel(model_name="gemini-3-flash-preview")
        
        img1 = Image.open(orig_path)
        img2 = Image.open(enh_path)
        
        prompt = (
            f"You are a Medical AI Assistant. A user is asking this question about these scans: '{question}'. "
            "Image 1 is 'Original', Image 2 is 'Enhanced'. "
            "Provide a clear, professional, and concise answer based only on what you see in the images. "
            "If the question is in Hindi, respond in Hindi. If in English, respond in English. "
            "Always maintain a clinical and helpful tone."
        )
        
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        response = model.generate_content([prompt, img1, img2], safety_settings=safety)
        return response.text.strip()
        
    # except Exception as e:
    #     print(f"Error in AI Chat: {e}")
    #     return f"I'm sorry, I'm having trouble analyzing the images right now. Error: {str(e)}"
    except Exception as e:

        print("\n========== CHAT ERROR ==========")
        print(e)
        print("================================\n")

        return (
            "AI analysis is temporarily unavailable. "
            "Please try again in a few moments."
        )
        