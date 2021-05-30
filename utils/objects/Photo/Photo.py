import pprint
from decimal import Decimal
from PIL import Image
import requests
import io
import hashlib as hl

class Photo:
    def __init__(self, photo_id=None, place_id=None, destination_id=None, src=None, mimeType=None, height=None, width=None, creation_timestamp=None, **kwargs):
        self.photo_id = photo_id if photo_id else kwargs.get('id', None)
        self.place_id = place_id
        self.destination_id = destination_id
        self.src = src if src else kwargs.get('productUrl', None)
        self.mimeType = mimeType
        self.height = height if height else kwargs.get('mediaMetadata', {}).get('height', None)
        self.width = width if width else kwargs.get('mediaMetadata', {}).get('width', None)
        self.creation_timestamp = creation_timestamp if creation_timestamp else kwargs.get('mediaMetadata', {}).get('creationTime', None)
        self._hash = None

        assert self._is_valid()

        self._buffer = io.BytesIO()
        self._s3_url = None

    def __repr__(self):
        return '{name}({raw})'.format(
            name=self.__class__.__name__,
            raw=pprint.pformat(self.__dict__, indent=4),
        )

    def _is_valid(self):
        if self.photo_id and self.place_id and self.destination_id:
            return True 
        return False

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

    def _hash_function(self, img):
        md5 = hl.md5()
        md5.update(img)
        return md5.hexdigest()

    def download(self, url, is_cover_image=False):
        r = requests.get(url + '=d')
        r.raw.decode_content = True # handle spurious Content-Encoding

        #Save the file contents to a variable
        content = r.content

        image = Image.open(io.BytesIO(content))
        image = self._rescale(image, max_size=(512 if is_cover_image else 2048))
        self.width, self.height = image.size
        self._hash = self._hash_function(content)

        #Save the image back out to a buffer and repoint the buffer back to the beginning
        image.save(self._buffer, 'PNG')
        self._buffer.seek(0)
    

    def write(self, s3, overwrite_if_exists=False):
        #TODO check that buffer isn't empty and hash has been compute
        file_name = self._hash + ".png"
        file_path = f"images/{self.destination_id}/{self.place_id}/{file_name}".replace(" ", "_")

        self._s3_url = f"{s3.base_url}/{file_path}" 
        if overwrite_if_exists or not s3.does_image_exist(file_path):
            s3.write_image_to_s3(file_path, self._buffer, ACL='public-read', ContentType='image/png')
        return self._s3_url

    def serialize(self):
        assert self._s3_url
        return {
            "place_id": self.place_id,
            "photo_id": self.photo_id,
            "src": self._s3_url,
            "type": self.mimeType,
            "height": Decimal(self.height),
            "width": Decimal(self.width),
            "creation_timestamp": self.creation_timestamp,
            "destination_id": self.destination_id
        }
