from dotenv import load_dotenv
import os

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator 
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.layout import LTTextBoxHorizontal

import spacy
import spacy_transformers

# NOT IN USE
from ollama import chat
from ollama import ChatResponse

from openai import OpenAI

import requests
import json

import re

load_dotenv()

# NOT IN USE
def call_ollama_api(pdf_to_text):
    api_endpoint = "http://localhost:11434/api/generate"
    entity_list = get_entities(pdf_to_text)
    user_message = f"Entities:\n{entity_list}\n\nText:\n{pdf_to_text}\n\nPlease return relationships in JSON format and never make up new entities"

    payload = {
    "model":'Datathon1:latest', 
    "prompt":user_message,
    "stream":False
    }

    response = requests.post(api_endpoint, json=payload)

    if response.status_code == 200:
        result = response.json()
        model_response = result.get('response')

        json_data = extract_json(model_response)
        print(type(json_data))
        return json_data

    else:
        print(f"Error {response.status_code}: {response.text}")
    return False

# Takes like 1 min
def call_openai(pdf_file):
    extracted_text = process_pdf(pdf_file)
    entity_list = get_entities(extracted_text)

    schema = {
        "type": "object",
        "properties": {
            "relationships": {
            "type": "array",
            "description": "A list of relationships between the provided entities.",
            "items": {
                "type": "object",
                "properties": {
                "entity1": {
                    "type": "string",
                    "description": "The first entity in the relationship."
                },
                "relationship": {
                    "type": "string",
                    "description": "A concise description of the relationship in two words or less."
                },
                "entity2": {
                    "type": "string",
                    "description": "The second entity in the relationship."
                }
                },
                "required": ["entity1", "relationship", "entity2"]
            }
            }
        },
        "required": ["relationships"]
    }

    system_prompts = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that identifies meaningful relationships between entities provided by the user. "
                "Only use the provided entities and do not invent or infer new entities. Focus on capturing meaningful and specific relationships."
            )
        },
        {
            "role": "system",
            "content": (
                "Focus on explicit and implied connections between entities. Avoid general or trivial relationships like 'attended meeting' unless they provide crucial information. "
                "Each relationship must be concise (two words or less) and meaningful."
            )
        },
        {
            "role": "system",
            "content": (
                "Include different types of relationships, such as actions, responsibilities, critiques, comparisons, and roles. Ensure the relationships are varied "
                "and reflect the richness of the interactions in the text."
            )
        },
        {
            "role": "system",
            "content": (
                "Explore all meaningful interactions between entities, including direct and indirect relationships. Ensure no meaningful interaction is overlooked."
            )
        },
        {
            "role": "system",
            "content": ("Ensure relationships are UNIQUE. Do not repeat the same relationship multiple times between different entities. Each relationship should provide new and meaningful information.")
        },
        {
            "role": "system",
            "content": (f"Here is the list of entities you are allowed to use: {entity_list}. You MUST NOT use any entities outside this list. If an entity is not in this list, exclude it entirely.")
        },
        {
            "role": "system",
            "content": ("Provide no more than 25 UNIQUE and MEANINGFUL relationships in total. Remove any duplicates, and ensure each relationship adds value.")
        },
        {
            "role": "system",
            "content": (f"Refer to {schema} when sending the results. Ensure all results conform to this schema for consistency and clarity.")
        }
    ]

    assistant_prompts = [
        {
            "role": "assistant",
            "content": (
                "Understood. I will identify as many meaningful relationships as possible from the provided text. I will focus on explicit and implied connections, ensuring no interaction is overlooked."
            )
        },
        {
            "role": "assistant",
            "content": (
                "I will explore both explicit and nuanced relationships, including actions, critiques, roles, and comparisons. Relationships will be detailed and varied, reflecting the richness of the text."
            )
        },
        {
            "role": "assistant",
            "content": (
                "I will ensure that all relationships are concise, no longer than three words, and provide significant meaning. "
                "I will avoid verbose or redundant descriptions."
            )
        },
    ]

    openai_key = os.getenv("OPENAPI_KEY")
    client = OpenAI(api_key=openai_key)

    user_message = f"Entities:\n{entity_list}\n\nText:\n{extracted_text}\n\nPlease return relationships in JSON format and never make up new entities"

    completion =  client.chat.completions.create(
        model="gpt-4o",
        response_format = {"type": "json_object"},
        messages = [
            {"role": "user", "content":user_message},
            *system_prompts,
            *assistant_prompts
        ],
        temperature = 0.1
    )
    if(completion is None):
        return False
    result = completion.choices[0].message.content
    result = json.loads(result)["relationships"]
    return result
    
def get_entities(extracted_text):
    nlp = spacy.load("en_core_web_trf")  # Transformer-based NER model
    doc = nlp(extracted_text)

    unique_entities = set()
    for ent in doc.ents:
        if (ent.label_ != "DATE" and ent.label_ != "CARDINAL" and ent.label_ != "LAW" and ent.label_ != "MONEY" and ent.label_ != "ORDINAL"):
            formatted_tuple = (ent.text,spacy.explain(ent.label_),ent.label_)
            unique_entities.add(formatted_tuple)
    return list(unique_entities)

def process_pdf(input_file):
    fp = open(input_file, 'rb')
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    pages = PDFPage.get_pages(fp)
    contentObjectList = []

    res = ""
    for pageNumber, page in enumerate(pages):
        if pageNumber != 0:
            interpreter.process_page(page)
            layout = device.get_result()
            for text_lines_obj in layout:
                if isinstance(text_lines_obj, LTTextBoxHorizontal) and text_lines_obj.get_text()!="\n":
                    # print(text_lines_obj.get_text())
                    res+=text_lines_obj.get_text()
    # print(res)
    return res.replace("\n"," ")

def extract_json(text):
    # Find content between ```json and ```
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    
    if json_match:
        json_str = json_match.group(1)
        try:
            json_data = json.loads(json_str)
            
            formatted_json = json.dumps(
                json_data,
                indent=4,
                ensure_ascii=False,
                sort_keys=False,
                separators=(',', ': ')
            )
            
            return formatted_json
        except json.JSONDecodeError:
            return None
    return None

