from typing import Sequence
import requests

from edenai_apis.features import Text

from edenai_apis.features.text import (
    SummarizeDataClass,
    SyntaxAnalysisDataClass,
    AnonymizationDataClass,
    KeywordExtractionDataClass,
    InfosSyntaxAnalysisDataClass,
    InfosKeywordExtractionDataClass,
    SentimentAnalysisDataClass
)
from edenai_apis.features.base_provider.provider_api import ProviderApi
from edenai_apis.features.text.sentiment_analysis.sentiment_analysis_dataclass import Items
from edenai_apis.loaders.data_loader import ProviderDataEnum
from edenai_apis.loaders.loaders import load_provider
from edenai_apis.utils.exception import ProviderException
from edenai_apis.utils.types import ResponseType
from .emvista_tags import tags


class EmvistaApi(ProviderApi, Text):

    provider_name = "emvista"

    def __init__(self):
        self.api_settings = load_provider(ProviderDataEnum.KEY, self.provider_name)
        self.api_key = self.api_settings["api_key"]
        self.base_url = self.api_settings["base_url"]

    def text__summarize(
        self, text: str, output_sentences: int, language: str, model: str = None
    ) -> ResponseType[SummarizeDataClass]:
        # Prepare request
        files = {"text": text, "parameters": [{"name": "lang", "value": language}]}
        headers = {
            "Poa-Token": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        url = f"{self.base_url}summarizer"

        # Send request to API
        response = requests.post(url, headers=headers, json=files)
        original_response = response.json()

        # Check errors from API
        if response.status_code != 200:
            raise ProviderException(original_response["message"])

        # Return standarized response
        standarized_response_list = original_response["result"].get("sentences", [])
        level_items = [
            element for element in standarized_response_list if element["level"] == 10
        ]
        result = "".join([element["value"] for element in level_items])

        standarized_response = SummarizeDataClass(result=result)

        result = ResponseType[SummarizeDataClass](
            original_response=original_response,
            standarized_response=standarized_response,
        )
        return result

    def text__syntax_analysis(
        self, language: str, text: str
    ) -> ResponseType[SyntaxAnalysisDataClass]:
        # Prepare request
        files = {"text": text, "parameters": [{"name": "lang", "value": language}]}
        headers = {
            "Poa-Token": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        url = f"{self.base_url}parser"

        # Send request to API
        response = requests.post(url, headers=headers, json=files)
        original_response = response.json()

        items: Sequence[InfosSyntaxAnalysisDataClass] = []
        for sentence in original_response["result"].get("sentences", []):
            for word in sentence["tokens"]:
                if word["pos"] in tags:
                    gender = word.get("gender")
                    plural = word.get("plural")

                    other = {
                        "gender": gender,
                        "plural": plural,
                        "mode": word.get("mode"),
                        "infinitive": None,
                    }
                    items.append(
                        InfosSyntaxAnalysisDataClass(
                            word=word["form"],
                            tag=tags[word["pos"]],
                            lemma=word["lemma"],
                            others=other,
                        )
                    )

        standarized_response = SyntaxAnalysisDataClass(items=items)

        result = ResponseType[SyntaxAnalysisDataClass](
            original_response=original_response,
            standarized_response=standarized_response,
        )
        return result

    def text__anonymization(
        self, text: str, language: str
    ) -> ResponseType[AnonymizationDataClass]:
        # Prepare request
        files = {"text": text, "parameters": [{"name": "lang", "value": language}]}
        headers = {
            "Poa-Token": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        url = f"{self.base_url}anonymizer"

        # Send request to API
        response = requests.post(url, headers=headers, json=files)
        original_response = response.json()

        # Check errors from API
        if response.status_code != 200:
            raise ProviderException(original_response["message"])

        # Return standarized response
        standarized_response = AnonymizationDataClass(
            result=original_response["result"]["annotatedValue"]
        )

        result = ResponseType[AnonymizationDataClass](
            original_response=original_response,
            standarized_response=standarized_response,
        )
        return result

    def text__sentiment_analysis(
        self,
        language: str,
        text: str
        ) -> ResponseType[SentimentAnalysisDataClass]:
        # Prepare request
        files = {
            "text": text,
            "parameters": [{
                "name": "lang",
                "value": language
            }]
        }
        headers = {
            "Poa-Token": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        url = f"{self.base_url}emotions"

        # Send request to API
        response = requests.post(url, headers=headers, json=files)
        original_response = response.json()

        opinions_response = requests.post(f"{self.base_url}opinions", headers=headers, json=files)

        items: Sequence[Items] = []
        for opinion in opinions_response.json()["result"].get("opinions", []):
           if opinion['value'] < 0:
               items.append(Items(
                   sentiment="negative",
                   sentiment_rate=abs(opinion['value'])
               ))
           elif opinion['value'] > 0:
               items.append(Items(
                   sentiment="positive",
                   sentiment_rate=opinion['value']
               ))
           else:
               items.append(Items(
                   sentiment="neutral",
                   sentiment_rate=opinion['value']
               ))
    
        standarized_response = SentimentAnalysisDataClass(items=items)
        result = ResponseType[SentimentAnalysisDataClass](
            original_response=original_response,
            standarized_response=standarized_response
        )
        return result

    def text__keyword_extraction(
        self, language: str, text: str
    ) -> ResponseType[KeywordExtractionDataClass]:
        """
        parameters:
          languages: string
          text: string

        return:
          ResponseType(
            original_response: {},
            standarized_response: Keyword_extraction(text: str)
          )
        """
        # Prepare request
        files = {"text": text, "parameters": [{"name": "lang", "value": language}]}
        headers = {
            "Poa-Token": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        url = f"{self.base_url}keywords"

        # Send request to API
        response = requests.post(url, headers=headers, json=files)
        original_response = response.json()

        # Check error from API
        if response.status_code != 200:
            raise ProviderException(original_response["message"])

        # Standardize response
        items: Sequence[InfosKeywordExtractionDataClass] = []
        for keyword in original_response["result"]["keywords"]:
            items.append(
                InfosKeywordExtractionDataClass(
                    keyword=keyword["value"], importance=float(keyword["score"])
                )
            )
        standarized_response = KeywordExtractionDataClass(items=items)

        # Return standardized response
        result = ResponseType[KeywordExtractionDataClass](
            original_response=original_response,
            standarized_response=standarized_response,
        )

        return result