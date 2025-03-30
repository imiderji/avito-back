from flask import Flask, request
from models.plate_reader import PlateReader, InvalidImage
from image_provider_client import ImageProviderClient, ImageProviderError
from plate_reader_client import PlateReaderClient
import logging
import io

IMAGES_SERVICE_HOST = 'http://89.169.157.72:8080/images/'

app = Flask(__name__)
plate_reader = PlateReader.load_from_file('./model_weights/plate_reader_model.pth')
image_client = ImageProviderClient(host=IMAGES_SERVICE_HOST)
plate_reader_client = PlateReaderClient(host='http://127.0.0.1:8080')


@app.route('/')
def hello():
    user = request.args.get('user', 'Guest')
    return f'<h1 style="color:red;"><center>Hello {user}!</center></h1>'


# <url>:8080/greeting?user=me
# <url>:8080 : body: {"user": "me"}
# -> {"result": "Hello me"}
@app.route('/greeting', methods=['POST'])
def greeting():
    if 'user' not in request.json:
        return {'error': 'field "user" not found'}, 400

    user = request.json['user']
    return {
        'result': f'Hello {user}',
    }


# <url>:8080/readPlateNumber : body <image bytes>
# {"plate_number": "c180mv ..."}
@app.route('/readPlateNumber', methods=['POST'])
def read_plate_number():
    im = request.get_data()
    im = io.BytesIO(im)

    try:
        res = plate_reader.read_text(im)
    except InvalidImage:
        logging.error('invalid image')
        return {'error': 'invalid image'}, 400

    return {
        'plate_number': res,
    }


@app.route('/recognize_plate_number/<int:image_id>', methods=['GET'])
def recognize_plate_number(image_id: int):
    image_data, status = image_client.get_image(image_id)

    if status == 200:
        result = plate_reader_client.read_plate_number(image_data['image_data'])

        return {
            f'image{image_id}': result,
        }
    
    return  {'error': f'image error {status}'}, status


@app.route('/recognize_plate_number/<string:image_ids>', methods=['GET'])
def recognize_some_plates(image_ids: str):
    images_data = image_client.get_images(image_ids)

    result = {}
    for image_id, image_data in images_data.items():
        if image_data[:5] != 'image':
            result[f'image{image_id}'] = plate_reader_client.read_plate_number(
                image_data
            )
        else:
            result[f'image{image_id}'] = {'plate_number': image_data}

    return result


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(levelname)s] [%(asctime)s] %(message)s',
        level=logging.INFO,
    )

    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', port=8080, debug=True)
