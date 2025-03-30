from requests.exceptions import Timeout, RequestException
import requests
import logging


class ImageProviderError(Exception):
    pass

class ImageTimeoutError(ImageProviderError):
    pass

class ImageRequestError(ImageProviderError):
    pass


class ImageProviderClient:
    def __init__(self, host: str, timeout: int = 5):
        self.host = host
        self.timeout = timeout

    def get_image(self, image_id: int):
        try:
            res = requests.get(
                f'{self.host}/{image_id}',
                headers  = {'Accept': 'image/*'},
                timeout = self.timeout
            )

            res.raise_for_status()

            if 'image' not in res.headers['Content-Type']:
                logging.error('image not found')
                return {'error': 'image not found'}, 404

            return {'image_data': res.content}, 200

        except Timeout:
            logging.error(f'timeout {image_id}')
            return {'error': f'timeout {image_id}'}, 408
        except RequestException as reqerror:
            logging.error('image not found')
            return {'error': 'image not found'}, 404
    
    def get_images(self, images_ids: str):
        image_data = {}
        image_ids = images_ids.split(',')
        
        for image_id in image_ids:
            image_id = image_id.strip()

            image, status = self.get_image(image_id)
            
            if status == 200:
                image_data[image_id] = image['image_data']
            else:
                image_data[image_id] = f'image error {status}'

        return image_data


if __name__ == '__main__':
    client = ImageProviderClient(host='http://89.169.157.72:8080/images/')
    image_id = 10022
    res = client.get_image(image_id)
    print(res)
    ims = '10022,9965'
    res2 = client.get_images(ims)
    print(res2)