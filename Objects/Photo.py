import pprint
from decimal import Decimal
from PIL import Image
from DynamoDB import _put_item
import requests
import io

class Photo:
    def __init__(self, id, place_id, productUrl, mimeType, mediaMetadata, city_id, **kwargs):
        self.photo_id = id
        self.place_id = place_id
        self.url = productUrl
        self.type = mimeType
        self.height = mediaMetadata.get('height', None)
        self.width = mediaMetadata.get('width', None)
        self.creation_timestamp = mediaMetadata.get('creationTime', None)
        self.city_id = city_id

        self._buffer = io.BytesIO()
        self._s3_url = None

    def __repr__(self):
        return '{name}({raw})'.format(
            name=self.__class__.__name__,
            raw=pprint.pformat(self.__dict__, indent=4),
        )

    def _rescale(self, image, max_size=2048):
        width, height = image.size
        ratio = width / height

        if width <= max_size and height <= max_size:
            pass
        elif ratio > 1:
            image = image.resize((max_size, int(max_size / ratio)))
        elif ratio < 1:
            image = image.resize((int(max_size * ratio), max_size))

        return image

    def download(self):
        r = requests.get(self.url + '=d')
        r.raw.decode_content = True # handle spurious Content-Encoding

        #Save the file contents to a variable
        content = r.content

        image = Image.open(io.BytesIO(content))

        if not self.height or not self.width:

            #Not sure this is needed
            # image = self._rescale(image)
            self.width, self.height = image.size

            #Save the image back out to a buffer and repoint the buffer back to the beginning
        image.save(self._buffer, 'PNG')
        self._buffer.seek(0)
    

    def write(self, s3):
        file_name = self.photo_id + ".png"
        file_path = "{}/{}/{}".format('images', self.city_id, self.place_id).replace(" ", "_")

        # if not self.does_image_exist(file_path + file_name):
            #Write the image to S3
        resp = s3.write_image_to_s3(file_path + file_name, self._buffer, ACL='public-read', ContentType='image/png')
        self._s3_url = file_path + file_name


    def serialize(self):
        assert self._s3_url
        return {
            "place_id": self.place_id,
            "photo_id": self.photo_id,
            "url": self._s3_url,
            "type": self.type,
            "height": self.height,
            "width": self.width,
            "creation_timestamp": self.creation_timestamp,
            "city_id": self.city_id
        }

    def insert(self, table):
        _put_item(table, self.serialize())