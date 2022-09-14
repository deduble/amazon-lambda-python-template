# A sample AWS Lambda using Python Base Image

Writes text on the given image URL. For S3 Bucket to be used, Lambda Function should be given an Environment Variable from console for `BUCKET_NAME` with the `GetObject` and `PutObject` permissions for Lambda allowed.

## Request:

    request =    {
        "image_url": url, -> Required
        "texts": [TextObject] -> Optional: Array of Text Objects
        "return_type": "base64" or "s3" -> Optional (default: "base64")
    }

    TextObject = {
        "text": String, -> Required,
        "font": FontObject, -> Optional -> PIL.ImageFont.truetype,
        "Rest of the paramters are passed to [PIL.ImageDraw.Draw.text]"
    }

    FontObject = {
        "font": String or URL -> Optional (default: arial) "name of the font lowercase (check fonts folder
                                                            if no extension defaults to .ttf) or TrueType font download xURL."
        "Rest of the parameters are passed to [PIL.ImageFont.truetype]"
        }
[PIL.ImageDraw.Draw.text](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html#PIL.ImageDraw.ImageDraw.text)"
[PIL.ImageFont.truetype](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.truetype)"

## Response:

    {"success": True, "b64_edited_image": "BASE64_STRING_OF_EDITED_IMAGE"} 
        or if return type is "s3"
    {"success": True, "edited_image_url": "SIGNED_TEMP_URL_FOR_IMAGE_ON_S3"}
        or
    {"success": False, "error_message": "LAST_25_LINES_OF_ERROR_STACK"}


## Create Python Docker from  Lambda Base

On your local machine, create a project directory for your new function.

In your project directory, add a file named app.py containing your function code. The following example shows a simple Python handler.

import sys
def handler(event, context):
    return 'Hello from AWS Lambda using Python' + sys.version + '!'        
In your project directory, add a file named requirements.txt. List each required library as a separate line in this file. Leave the file empty if there are no dependencies.

Use a text editor to create a Dockerfile in your project directory. The following example shows the Dockerfile for the handler that you created in the previous step. Install any dependencies under the ${LAMBDA_TASK_ROOT} directory alongside the function handler to ensure that the Lambda runtime can locate them when the function is invoked.

    FROM public.ecr.aws/lambda/python:3.8

    # Copy function code
    COPY app.py ${LAMBDA_TASK_ROOT}

    # Install the function's dependencies using file requirements.txt
    # from your project folder.

    COPY requirements.txt  .
    RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

    # Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
    CMD [ "app.handler" ]

To create the container image, follow steps 4 through 7 in Create an image from an AWS base image for Lambda.

## Create Image from an AWS base image (4-7)

4 - Build your Docker image with the docker build command. Enter a name for the image. The following example names the image hello-world.

    docker build -t lambda-function .

5 - Start the Docker image with the docker run command. For this example, enter hello-world as the image name.

    docker run -p 9000:8080 lambda-function

6 - (Optional) Test your application locally using the runtime interface emulator. From a new terminal window, post an event to the following endpoint using a curl command.


example request:


    import requests
    import base64
    from PIL import Image
    from io import BytesIO

    json = {
            "image_url": "https://images.pexels.com/photos/1223649/pexels-photo-1223649.jpeg",
            "texts": [
                        {"text": "foo",
                        "xy": [200, 300],
                        "font": {"font": "arial",
                                 "size": 200},
                        "fill": [255, 0, 0]},
                        {"text": "bar",
                             "xy": [600, 700],
                             "font": {"font": "http://www.ustyapi.com/assets/fonts/barlow/Barlow-Black.ttf",
                                      "size": 500},
                             "fill": [255, 255, 0],
                        }
                    ]
            }

    resp = requests.post("http://localhost:9000/2015-03-31/functions/function/invocations",json=json)
    Image.open(BytesIO(base64.b64decode(resp.json()['b64_edited_image']))).show()

# Upload image to AWS

## 1-Install AWS CLI.

In the following commands, replace 123456789012 with your AWS account ID and set the region value to the region where you want to create the Amazon ECR repository.

Note
In Amazon ECR, if you reassign the image tag to another image, Lambda does not update the image version.

## 2-Authenticate the Docker CLI to your Amazon ECR registry.

    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com    

## 3-Create a repository in Amazon ECR using the create-repository command.

    aws ecr create-repository --repository-name hello-world --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

## 4-Tag your image to match your repository name, and deploy the image to Amazon ECR using the docker push command

    docker tag  hello-world:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/hello-world:latest
    docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/hello-world:latest        
Now that your container image resides in the Amazon ECR container registry, you can create and run the Lambda function.