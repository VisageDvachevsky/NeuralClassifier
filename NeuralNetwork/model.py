import torch
from torch.utils.data import DataLoader, Dataset
from transformers import Trainer, TrainingArguments, XLMRobertaForSequenceClassification, XLMRobertaTokenizer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, roc_auc_score, matthews_corrcoef
from safetensors.torch import load_file as load_safetensors
import numpy as np
import os
import torch.nn.functional as F

class IntentDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels.iloc[idx], dtype=torch.long)
        return item

    def __len__(self):
        return len(self.labels)

class IntentRecognizer:
    def __init__(self, num_labels, model_name='xlm-roberta-base', temperature=1.0, num_mc_samples=10):
        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        self.model_name = model_name
        self.model = XLMRobertaForSequenceClassification.from_pretrained(model_name, num_labels=num_labels).to(self.device)
        self.tokenizer = XLMRobertaTokenizer.from_pretrained(model_name)
        self.temperature = temperature
        self.num_mc_samples = num_mc_samples

    def compute_metrics(self, pred):
        labels = pred.label_ids
        preds = pred.predictions.argmax(-1)
        probs = pred.predictions

        accuracy = accuracy_score(labels, preds)
        precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='weighted', zero_division=1)
        conf_matrix = confusion_matrix(labels, preds)
        mcc = matthews_corrcoef(labels, preds)

        if probs.ndim == 1:
            probs = np.expand_dims(probs, axis=1)

        if probs.shape[1] == len(set(labels)):
            try:
                roc_auc = roc_auc_score(labels, probs, multi_class='ovr')
            except ValueError:
                roc_auc = None
        else:
            roc_auc = None

        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'mcc': mcc,
            'confusion_matrix': conf_matrix.tolist()
        }
        
        if roc_auc is not None:
            metrics['roc_auc'] = roc_auc
        
        return metrics

    def train(self, train_dataset, val_dataset, resume_from_checkpoint=None):
        output_dir = 'results'
        os.makedirs(output_dir, exist_ok=True)
        
        training_args = TrainingArguments(
            output_dir='results',
            num_train_epochs=8,  
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='logs',
            logging_steps=10,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            save_steps=1000,
            save_total_limit=2,
            learning_rate=3e-5,  
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=self.compute_metrics,
        )

        if resume_from_checkpoint:
            trainer.train(resume_from_checkpoint=resume_from_checkpoint)
        else:
            trainer.train()
            
        self.save_model(self.model, self.tokenizer, output_dir)

    def evaluate_model(intent_recognizer, val_dataset):
        results = intent_recognizer.trainer.evaluate(eval_dataset=val_dataset)
        print("Evaluation results:", results)
        return results


    def load_model(self, checkpoint_path, tokenizer_name=None):
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"The specified checkpoint path '{checkpoint_path}' does not exist.")

        if tokenizer_name:
            tokenizer_path = os.path.join(checkpoint_path, tokenizer_name)
        else:
            tokenizer_path = checkpoint_path

        # self.tokenizer = XLMRobertaTokenizer.from_pretrained(tokenizer_path)

        model_safetensors_path = os.path.join(checkpoint_path, 'model.safetensors')
        if not os.path.exists(model_safetensors_path):
            raise FileNotFoundError(f"The specified model file '{model_safetensors_path}' does not exist.")

        self.model = XLMRobertaForSequenceClassification.from_pretrained(checkpoint_path)
        state_dict = load_safetensors(model_safetensors_path, device='cpu')
        self.model.load_state_dict(state_dict, strict=False)  
        self.model.to(self.device)
        self.model.eval()

    def recognize_intent(self, text, threshold=0.5):
        encodings = self.tokenizer(text, truncation=True, padding=True, return_tensors="pt").to(self.device)
        logits_list = []

        self.model.eval()  

        with torch.no_grad():
            for _ in range(self.num_mc_samples):
                outputs = self.model(**{k: v.to(self.device) for k, v in encodings.items()})
                logits_list.append(outputs.logits.unsqueeze(0))

        logits = torch.cat(logits_list, dim=0)
        logits_mean = logits.mean(dim=0) / self.temperature
        predicted_class_id = logits_mean.argmax().item()
        confidence = F.softmax(logits_mean, dim=1)[0, predicted_class_id].item()

        if confidence < threshold:
            return None, confidence
        return predicted_class_id, confidence

    def save_model(self, model, tokenizer, save_directory):
        model.save_pretrained(save_directory)
        tokenizer.save_pretrained(save_directory)
        print(f"Model and tokenizer saved to {save_directory}")
