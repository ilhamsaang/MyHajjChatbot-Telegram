import itertools
from typing import Dict, Union
import requests
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage

from nltk import sent_tokenize
import nltk

nltk.download('punkt')
import torch
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer
)


class QAPipeline:

    def __init__(
            self
    ):
        self.model = AutoModelForSeq2SeqLM.from_pretrained("muchad/idt5-qa-qg")
        self.tokenizer = AutoTokenizer.from_pretrained("muchad/idt5-qa-qg")
        self.qg_format = "highlight"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        assert self.model.__class__.__name__ in ["T5ForConditionalGeneration"]
        self.model_type = "t5"

        # Firebase Initialization
        cred = credentials.Certificate('path/to/serviceAccount.json')
        firebase_admin.initialize_app(cred, {
            'storageBucket': '<BUCKET_NAME>.appspot.com'
        })
        self.bucket = storage.bucket()

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

    def download_audio(self, url):
        blob = self.bucket.blob(url)
        audio = blob.download_as_string()
        return audio

class TaskPipeline(QAPipeline):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __call__(self, inputs: Union[Dict, str]):
        if 'url' in inputs:
            audio = self.download_audio(inputs['url'])
            return audio
        else:
            return self._extract_answer(inputs["question"], inputs["context"])

    def _prepare_inputs(self, question, context):
        source_text = f"question: {question}  context: {context}"
        source_text = source_text + " </s>"
        return source_text

     def _extract_answer(self, question, context):
        source_text = self._prepare_inputs(question, context)
        inputs = self._tokenize([source_text], padding=False)

        outs = self.model.generate(
            input_ids=inputs['input_ids'].to(self.device),
            attention_mask=inputs['attention_mask'].to(self.device),
            max_length=80,
            )
        answer = self.tokenizer.decode(outs[0], skip_special_tokens=True)
        return answer

def pipeline():
    task = TaskPipeline
    return task()