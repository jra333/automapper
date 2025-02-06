import pandas as pd
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PlacementPredictor:
    def __init__(self, model_path, device=None):
        self.device = device if device else torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = model_path
        self.max_source_length = 200
        self.max_target_length = 128
        
        logger.info(f"Using device: {self.device}")
        logger.info(f"Loading model from: {self.model_path}")
        
        self.tokenizer = T5Tokenizer.from_pretrained(self.model_path)
        self.model = T5ForConditionalGeneration.from_pretrained(self.model_path).to(self.device)
        self.model.eval()

    def prepare_input(self, campaign, placement_name, dcm_name=''):
        """Prepare input text in the same format as training data"""
        if dcm_name:
            return f"Campaign: {campaign}, DCM Name: {dcm_name}, Placement Name: {placement_name}"
        return f"Campaign: {campaign}, Placement Name: {placement_name}"

    def parse_output(self, text):
        """Parse the model output into a dictionary"""
        parsed = {}
        try:
            for item in text.split(';'):
                key, value = item.strip().split(':', 1)
                parsed[key.strip()] = value.strip()
        except Exception as e:
            logger.error(f"Parsing error: {e}\nText: {text}")
        return parsed

    def predict(self, input_texts, batch_size=32):
        if isinstance(input_texts, str):
            input_texts = [input_texts]

        predictions = []

        for i in range(0, len(input_texts), batch_size):
            batch_texts = input_texts[i:i + batch_size]

            inputs = self.tokenizer(
                batch_texts,
                max_length=self.max_source_length,
                truncation=True,
                padding=True,
                return_tensors="pt"
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    max_length=self.max_target_length,
                    num_beams=2,
                    repetition_penalty=2.5,
                    length_penalty=0.8,
                    early_stopping=False
                )

            decoded_preds = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
            predictions.extend(decoded_preds)

        return [self.parse_output(pred) for pred in predictions]

def process_file(df, missing_columns=None):
    """Process the uploaded file with the T5 model predictions"""
    start_time = datetime.now()
    logger.info(f"Starting file processing at {start_time}")
    
    # Debug logging
    logger.info(f"Input DataFrame columns: {df.columns.tolist()}")
    logger.info(f"Input DataFrame shape: {df.shape}")
    
    

    processed_df = df.copy()

    # Standardize column names for processing
    temp_df = df.copy()
    temp_df.columns = temp_df.columns.str.upper().str.replace(' ', '_')
    
    # Clean PLACEMENT_NAME column: remove text occurring after ":D"
    #if 'PLACEMENT_NAME' in temp_df.columns:
    #    temp_df['PLACEMENT_NAME'] = temp_df['PLACEMENT_NAME'].apply(
    #        lambda x: x.split(":D")[0].strip() if isinstance(x, str) and ":D" in x else x
    #    )
    
 
    
    # Required input validation and prediction preparation 
    required_input_columns = ['CAMPAIGN', 'PLACEMENT_NAME']
    logger.info("Checking required columns...")
    missing_required = [col for col in required_input_columns if col not in temp_df.columns]
    if missing_required:
        raise ValueError(f"Missing required column(s): {missing_required}")
    
    # Initialize model and prepare input texts
    model_dir = os.getenv('MODEL_DIR', './model_outputs')
    predictor = PlacementPredictor(model_dir)
    
    # Prepare input texts
    input_texts = []
    for _, row in temp_df.iterrows():
        dcm_name = row.get('DCM_CAMPAIGN_NAME', '')
        input_texts.append(predictor.prepare_input(
            row['CAMPAIGN'],
            row['PLACEMENT_NAME'],
            dcm_name
        ))
    
    # Get predictions
    predictions = predictor.predict(input_texts)
    
    # Mapping of model output fields to DataFrame columns
    field_mapping = {
        'Placement Group': 'Placement Group',
        'Publisher': 'Publisher',
        'Tactic': 'Tactic',
        'Audience': 'Audience',
        'Ad Type': 'Ad Type'
    }
    
    # Update columns with predictions
    for model_field, df_column in field_mapping.items():
        # Add column if it doesn't exist
        if df_column not in processed_df.columns:
            processed_df[df_column] = ''
        # Update with predictions
        processed_df[df_column] = [pred.get(model_field, '') for pred in predictions]
    
    logger.info(f"File processing completed in {(datetime.now() - start_time).total_seconds():.2f} seconds")
    return processed_df