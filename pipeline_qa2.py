import itertools
from typing import Dict, Union

from nltk import sent_tokenize
import nltk

nltk.download('punkt')
import torch
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer
)
from transformers import AutoModelForSequenceClassification, AutoTokenizer

class QAPipeline:
    def __init__(self):
        self.model = AutoModelForSeq2SeqLM.from_pretrained("muchad/idt5-qa-qg")
        self.tokenizer = AutoTokenizer.from_pretrained("muchad/idt5-qa-qg")
        self.qg_format = "highlight"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        assert self.model.__class__.__name__ in ["T5ForConditionalGeneration"]
        self.model_type = "t5"

    def __call__(self, inputs: str):
        inputs = " ".join(inputs.split())
        answers = self._extract_answers(inputs)
        flat_answers = list(itertools.chain(*answers))

        if len(flat_answers) == 0:
            return []

    def _tokenize(self,
                  inputs,
                  padding=True,
                  truncation=True,
                  add_special_tokens=True,
                  max_length=512
                  ):
        inputs = self.tokenizer.batch_encode_plus(
            inputs,
            max_length=max_length,
            add_special_tokens=add_special_tokens,
            truncation=truncation,
            padding="max_length" if padding else False,
            pad_to_max_length=padding,
            return_tensors="pt"
        )
        return inputs


class TaskPipeline(QAPipeline):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.classification_model = AutoModelForSequenceClassification.from_pretrained("your-classification-model")
        self.classification_tokenizer = AutoTokenizer.from_pretrained("your-classification-model")

    def __call__(self, inputs: Union[Dict, str]):
        question = inputs["question"]
        context = inputs["context"]
        intent = self._classify_intent(question)  # Classify the intent of the question

        if intent == "Masjid Nabawi":
            return self._extract_answer(question, context, intent)
        elif intent == "Makam Al-Baqi":
            return self._extract_answer(question, context, intent)
        else:
            return []

    def _classify_intent(self, question):

        inputs = self.classification_tokenizer.encode_plus(
            question,
            add_special_tokens=True,
            return_tensors="pt"
        )
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)

        with torch.no_grad():
            outputs = self.classification_model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            logits = outputs.logits

        predicted_class_idx = torch.argmax(logits, dim=1).item()
        intent = self.classification_model.config.id2label[predicted_class_idx]

        return intent

    def _prepare_inputs(self, question, context):
        source_text = f"question: {question}  context: {context}"
        source_text = source_text + " </s>"
        return source_text

    def _extract_answer(self, question, context, intent):
        source_text = self._prepare_inputs(question, context)
        inputs = self._tokenize([source_text], padding=False)

        outs = self.model.generate(
            input_ids=inputs['input_ids'].to(self.device),
            attention_mask=inputs['attention_mask'].to(self.device),
            max_length=80,
        )
        answer = self.tokenizer.decode(outs[0], skip_special_tokens=True)

        # Add intent information to the answer
        answer_with_intent = f"{intent}: {answer}"
        return answer_with_intent


def pipeline():
    task = TaskPipeline
    return task()