import io
import os
import sys
import traceback
from base64 import b64encode
from urllib.request import urlopen, Request

import boto3
from PIL import Image, ImageDraw, ImageFont

def upload_to_aws(local_file, s3_file):

    s3 = boto3.client('s3')

    try:
        s3.upload_file(local_file, os.environ['BUCKET_NAME'], s3_file)
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': os.environ['BUCKET_NAME'],
                'Key': s3_file
            },
            ExpiresIn=24 * 3600
        )

        print("Upload Successful", url)
        return url
    except FileNotFoundError:
        print("The file was not found")
        return None

def exception_to_string():
    '''
    https://stackoverflow.com/a/58938751/8455692
    credits to
    @Rune Kaagaard
    '''
    parts = ["Traceback (most recent call last):\n"]
    parts.extend(traceback.format_stack(limit=25)[:-2])
    parts.extend(traceback.format_exception(*sys.exc_info())[1:])
    return "".join(parts)

def load_or_download_font(font: str, **font_params) -> ImageFont:
    """Given a URL or a lowercase TrueType fontname, returns an ImageFont object"""
    try:
        root, ext = os.path.splitext(font)
        ttf = ImageFont.truetype(os.path.join('fonts', root) + (f".{ext or 'ttf'}"), **font_params)
    except:
        ttf = ImageFont.truetype(urlopen(Request(font, headers={"User-Agent": "Mozilla/5.0"})), **font_params)
    return ttf
 
def handler(event, context):
    try:
        url = event.pop('image_url')
        return_type = event.pop('return_type', 'base64')
        texts = event.pop('texts', [])
        image_data  = urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"})).read()
        image = Image.open(io.BytesIO(image_data))
        I1 = ImageDraw.Draw(image)
        print(f"Number of texts: {len(texts)}")
        for text_params in texts:
            print("Text Info:", text_params)
            font = text_params.pop('font', {'font': 'arial'})
            text = text_params.pop('text')
            fill = tuple(text_params.pop('fill', [255, 0, 0]))
            print("Font Params:", font)
            ttf = load_or_download_font(**font)
            xy = text_params.pop('xy', [image.width // 2, image.height // 2])
            I1.text(xy=xy, text=text, font=ttf, fill=fill, **text_params) #**event)
        if return_type == 'base64':
            # Write image to buffer and encode b64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_str = b64encode(buffered.getvalue())
            return {"success": True, "b64_edited_image": img_str}
        elif return_type == "s3":
            image_name = os.path.basename(url)
            saved = image.save(image_name)
            edited_url = upload_to_aws(image_name, "edited-" + image_name)
            return {"success": True, "edited_image_url": edited_url}
    except Exception as e:
        return {'success': False, 'error_message': exception_to_string()}
