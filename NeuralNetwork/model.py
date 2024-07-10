import torch
from torch.utils.data import DataLoader, Dataset
from transformers import BertForSequenceClassification, BertTokenizer, XLMRobertaForSequenceClassification, XLMRobertaTokenizer, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, roc_auc_score, matthews_corrcoef
import numpy as np
import os

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
    def __init__(self, num_labels, model_name='xlm-roberta-base'):
        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        self.model_name = model_name
        self.model = XLMRobertaForSequenceClassification.from_pretrained(model_name, num_labels=num_labels).to(self.device)
        self.tokenizer = XLMRobertaTokenizer.from_pretrained(model_name)

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
            output_dir=output_dir,
            num_train_epochs=4,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='logs',
            logging_steps=10,
            evaluation_strategy="epoch",
            dataloader_num_workers=4,
            fp16=False,
            save_strategy="steps",
            save_steps=1000,
            save_total_limit=25
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

        trainer.save_model(output_dir)
        self.trainer = trainer

    def evaluate(self, val_dataset):
        return self.trainer.evaluate(eval_dataset=val_dataset)

    def load_model(self, checkpoint_path, tokenizer_name=None):
        self.model = XLMRobertaForSequenceClassification.from_pretrained(checkpoint_path).to(self.device)
        if tokenizer_name:
            self.tokenizer = XLMRobertaTokenizer.from_pretrained(tokenizer_name)
        else:
            self.tokenizer = XLMRobertaTokenizer.from_pretrained(self.model_name)
        self.model.eval()

    def recognize_intent(self, text, threshold=0.5):
        encodings = self.tokenizer(text, truncation=True, padding=True, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model(**{k: v.to(self.device) for k, v in encodings.items()})
        logits = outputs.logits
        predicted_class_id = logits.argmax().item()
        confidence = torch.nn.functional.softmax(logits, dim=1)[0, predicted_class_id].item()
        
        if confidence < threshold:
            return None, confidence
        return predicted_class_id, confidence
