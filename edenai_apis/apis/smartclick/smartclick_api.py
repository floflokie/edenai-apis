from io import BufferedReader
from typing import Sequence
import requests

from edenai_apis.features import ProviderApi, Image
from edenai_apis.features.image import (
    LogoDetectionDataClass,
    LogoBoundingPoly,
    LogoVertice,
    LogoItem,
)
from edenai_apis.loaders.data_loader import ProviderDataEnum
from edenai_apis.loaders.loaders import load_provider
from edenai_apis.utils.upload_s3 import upload_file_to_s3
from edenai_apis.utils.types import ResponseType
from edenai_apis.utils.exception import ProviderException


class SmartClickApi(ProviderApi, Image):
    provider_name = "smartclick"

    def __init__(self) -> None:
        self.api_settings = load_provider(ProviderDataEnum.KEY, self.provider_name)
        self.key = self.api_settings["key"]
        self.base_url = self.api_settings['base_url']
        self.headers = {
            "content-type": "application/json",
            "api-token": self.key,
        }

    def image__logo_detection(
        self, file: BufferedReader
    ) -> ResponseType[LogoDetectionDataClass]:
        url = f"{self.base_url}logo-detection"

        # Get URL for the image
        content_url = upload_file_to_s3(file, file.name)

        # Get response from the API
        payload = {"url": content_url}
        response = requests.request("POST", url, json=payload, headers=self.headers)

        # Handle error : if response is not 200, raise an exception
        if response.status_code != 200:
            raise ProviderException(message=response.content, code=response.status_code)

        # Standarized response : description/score/bounding_box
        items: Sequence[LogoItem] = []
        boxes = response.json()
        for box in boxes.get("bboxes"):
            vertices = []
            vertices.append(LogoVertice(x=box[0], y=box[1]))
            vertices.append(LogoVertice(x=box[2], y=box[1]))
            vertices.append(LogoVertice(x=box[2], y=box[3]))
            vertices.append(LogoVertice(x=box[0], y=box[3]))

            items.append(
                LogoItem(
                    bounding_poly=LogoBoundingPoly(vertices=vertices),
                )
            )
        standarized = LogoDetectionDataClass(items=items)
        return ResponseType[LogoDetectionDataClass](
            original_response=response.json(),
            standarized_response=standarized
        )